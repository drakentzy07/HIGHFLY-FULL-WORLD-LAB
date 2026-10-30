#!/usr/bin/env python3
"""HIGHFLY P4 private world bridge: own KayKit bodies + compatible animation donors.

Stages assets and a reversible env-gated renderer mapping in HIGHFLY code-only
copy. Does NOT edit the ClaudeCraft reference, simulation, player classes, loot,
NPCs, saves, or Git-tracked source. Does NOT produce a playable/releasable build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
LIBRARY = ROOT / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
ANCHOR = "// Dispatch: entity -> visual key (mirrors the old buildRigFor selection:"
START = "// HIGHFLY_P4_VISUAL_BRIDGE_START"
END = "// HIGHFLY_P4_VISUAL_BRIDGE_END"

sys.path.insert(0, str(ROOT / "scripts"))
from highfly_probe_rig_compatibility_p2 import model_info


def sha256(file: Path) -> str:
    result = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def choose_animation_files(lib: Path) -> list[Path]:
    dirs = (
        lib / "KayKit Character Animations 1.1/Animations/gltf/Rig_Medium",
        lib / "KayKit Adventurers 2.0/Animations/gltf/Rig_Medium",
    )
    result = []
    for hint in ("movementbasic", "general", "combatmelee", "combatranged"):
        found = []
        for directory in dirs:
            if not directory.is_dir():
                continue
            for path in directory.glob("*.glb"):
                if path.is_symlink() or path.stem.lower().replace("_", "") != "rigmedium" + hint:
                    continue
                data = model_info(path, lib)
                if data["animationCount"] and data["jointCount"] >= 20:
                    found.append((str(path).lower(), path, data))
        if not found:
            raise RuntimeError("MISSING_RIG_MEDIUM_DONOR: " + hint)
        found.sort()
        result.append(found[0][1])
    return result


def select_clips(donors: list[Path], lib: Path) -> dict[str, str]:
    all_clips = []
    for file in donors:
        data = model_info(file, lib)
        all_clips.extend(a["name"] for a in data["animations"])
    names = set(all_clips)
    choices = {
        "idle": ("Idle", "Idle_A", "Melee_Unarmed_Idle", "Melee_2H_Idle"),
        "walk": ("Walking_A", "Walk", "Walking", "Walking_Forward"),
        "run": ("Running_A", "Run", "Running", "Running_Forward"),
        "attack": ("Melee_1H_Attack_Chop", "1H_Melee_Attack_Chop", "Melee_1H_Attack_Slice_Diagonal"),
        "death": ("Death_A", "Death", "Dying_A"),
        "hit": ("Hit_A", "Hit", "Hit_B"),
    }
    selected = {}
    for kind, possibilities in choices.items():
        chosen = next((name for name in possibilities if name in names), None)
        if not chosen:
            # A missing clip must fail before copying any files.
            raise RuntimeError("REQUIRED_P4_CLIP_MISSING: " + kind + ". Found " + ", ".join(sorted(names)[:35]))
        selected[kind] = chosen
    return selected


def assert_paths(stage: Path, library: Path) -> tuple[Path, Path]:
    if not stage.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("STAGE_OUTSIDE_PRIVATE_WORKSPACE")
    if not library.resolve().is_relative_to((ROOT / ".workspace/private-imports").resolve()):
        raise RuntimeError("SOURCE_OUTSIDE_PRIVATE_ASSET_LIBRARY")
    status_file = stage / "HIGHFLY_STAGE_STATUS.json"
    if not status_file.is_file():
        raise RuntimeError("HIGHFLY_CODE_STAGE_MISSING: run commercial P0 preparation")
    status = json.loads(status_file.read_text(encoding="utf8"))
    if status.get("sourceCommit") != PIN or status.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("UNEXPECTED_STAGE_METADATA")
    manifest = stage / "src/render/characters/manifest.ts"
    if not manifest.is_file():
        raise RuntimeError("CHARACTER_MANIFEST_NOT_IN_STAGE")
    original = ROOT / ".workspace/claudecraft-v0.44.7/src/render/characters/manifest.ts"
    if not original.is_file():
        raise RuntimeError("REFERENCE_MANIFEST_MISSING")
    if (original.read_text(encoding="utf8")).find(START) != -1:
        raise RuntimeError("REFERENCE_WAS_MODIFIED: refusing bridge")
    return manifest, original


def bridge_block(clip: dict[str, str], donor_paths: list[str]) -> str:
    def quoted(s: str) -> str:
        return json.dumps(s, ensure_ascii=False)
    urls = ", ".join(quoted(p) for p in donor_paths)
    hero = "highfly-private-p4/hero.glb"
    skeleton = "highfly-private-p4/skeleton.glb"
    lines = [
        START,
        "// Private P4 only: original engine logic stays unchanged; enable via VITE_HIGHFLY_P4=1.",
        "// These visuals are a first bridge, NOT the final Hunter Universal or skin editor.",
        "if (import.meta.env.VITE_HIGHFLY_P4 === '1') {",
        "  const hfDonors = [" + urls + "];",
        "  const heroBase = VISUALS.player_warrior;",
        "  if (heroBase) VISUALS.player_warrior = {",
        "    ...heroBase,",
        "    url: " + quoted(hero) + ",",
        "    animUrls: [...hfDonors, ...(heroBase.animUrls ?? [])],",
        "    clips: { ...heroBase.clips,",
        "      idle: " + quoted(clip["idle"]) + ", walk: " + quoted(clip["walk"]) + ",",
        "      run: " + quoted(clip["run"]) + ", attack: [" + quoted(clip["attack"]) + "],",
        "      death: " + quoted(clip["death"]) + ", hit: [" + quoted(clip["hit"]) + "],",
        "    },",
        "  };",
        "  const skeletonBase = VISUALS.skel_minion;",
        "  if (skeletonBase) VISUALS.skel_minion = {",
        "    ...skeletonBase,",
        "    url: " + quoted(skeleton) + ",",
        "    animUrls: [...hfDonors, ...(skeletonBase.animUrls ?? [])],",
        "    clips: { ...skeletonBase.clips,",
        "      idle: " + quoted(clip["idle"]) + ", walk: " + quoted(clip["walk"]) + ",",
        "      run: " + quoted(clip["run"]) + ", attack: [" + quoted(clip["attack"]) + "],",
        "      death: " + quoted(clip["death"]) + ", hit: [" + quoted(clip["hit"]) + "],",
        "      flourish: undefined,",
        "    },",
        "  };",
        "}",
        END,
        "",
    ]
    return "\n".join(lines)


def plan(stage: Path = STAGE, library: Path = LIBRARY) -> dict:
    manifest, reference = assert_paths(stage, library)
    sources = [
        ("hero.glb", library / "KayKit Adventurers 2.0/Characters/gltf/Knight.glb"),
        ("skeleton.glb", library / "KayKit Skeletons 1.1/characters/gltf/Skeleton_Minion.glb"),
    ]
    for _name, source in sources:
        info = model_info(source, library)
        if info["jointCount"] < 20:
            raise RuntimeError("UNEXPECTED_RIG_FOR_" + _name)
    donor_files = choose_animation_files(library)
    clips = select_clips(donor_files, library)
    for index, path in enumerate(donor_files):
        sources.append((f"donor_{index:02}.glb", path))
    source_text = manifest.read_text(encoding="utf8")
    if START in source_text:
        if END not in source_text:
            raise RuntimeError("PARTIAL_P4_SOURCE_BLOCK")
        fresh = source_text
    else:
        if source_text.count(ANCHOR) != 1:
            raise RuntimeError("UNEXPECTED_MANIFEST_LAYOUT")
        marker = "// ---------------------------------------------------------------------------\n" + ANCHOR
        if marker not in source_text:
            raise RuntimeError("MANIFEST_DISPATCH_MARKER_NOT_FOUND")
        donor_urls = ["highfly-private-p4/donor_" + str(i).zfill(2) + ".glb" for i in range(len(donor_files))]
        fresh = source_text.replace(marker, bridge_block(clips, donor_urls) + marker, 1)
    targets = [(name, source, stage / "public/highfly-private-p4" / name) for name, source in sources]
    for name, source, target in targets:
        if not source.is_file() or source.is_symlink():
            raise RuntimeError("MISSING_SOURCE: " + name)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or sha256(target) != sha256(source):
                raise RuntimeError("P4_TARGET_CONFLICT: " + str(target))
    report = {
        "project": "HIGHFLY ORIGIN", "phase": "P4_PRIVATE_WORLD_CODE_VISUAL_BRIDGE",
        "sourceCommit": PIN, "noMediaFromClaudeCraftCopied": True,
        "originalReferenceUntouched": True, "gameplayVerified": False,
        "licenseClearedForRelease": False,
        "clips": clips,
        "privateFiles": [name for name, _, _ in targets],
        "modifiedStageSource": "src/render/characters/manifest.ts",
        "remaining": "Buildable playable HIGHFLY still requires rights-reviewed replacements for other missing public media and downstream runtime checks.",
    }
    return {"report": report, "manifest": manifest, "updated": fresh, "targets": targets}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="Copy only selected owned assets and patch ignored private stage")
    args = parser.parse_args()
    p = plan()
    print("[HIGHFLY] P4 WORLD BRIDGE PLAN: " + json.dumps(p["report"], ensure_ascii=False))
    if not args.install:
        print("[HIGHFLY] DRY-RUN ONLY; use --install to stage PRIVATE assets and renderer mapping.")
        return
    for _name, source, target in p["targets"]:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    manifest = p["manifest"]
    if manifest.read_text(encoding="utf8") != p["updated"]:
        manifest.write_text(p["updated"], encoding="utf8")
    report = ROOT / ".workspace/reports/highfly-p4/WORLD_VISUAL_BRIDGE.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(p["report"], indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P4 PRIVATE WORLD CODE BRIDGE INSTALLED")
    print("[HIGHFLY] Stage only: .workspace/highfly-origin-stage-p0. No runtime build yet.")
    print("[HIGHFLY] ClaudeCraft reference, game saves and Git repo unchanged; NO PUBLIC RELEASE.")


if __name__ == "__main__":
    main()
