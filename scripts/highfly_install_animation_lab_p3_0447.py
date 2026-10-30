#!/usr/bin/env python3
"""HIGHFLY P3: install an isolated PRIVATE animation laboratory for KayKit v7.

Adds one new Vite page to the ignored v0.44.7 working checkout. Original
gameplay/saves, P1 viewer, public GitHub source and original media are untouched.
Read-only by default; --install opts in to copying selected owned GLBs locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from highfly_probe_rig_compatibility_p2 import model_info

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
KAYKIT = ROOT / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
FOLDER = "highfly-private-p3"
PRIORITY = ("movementbasic", "movement", "general", "combatmelee", "combatranged", "special", "tools")


def sha256(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sources(upstream: Path, library: Path) -> None:
    if not (upstream / ".git").is_dir():
        raise RuntimeError("MISSING_PRIVATE_CLAUDECRAFT_0447")
    actual = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    if actual != PIN:
        raise RuntimeError("PIN_MISMATCH: refusing to modify another ClaudeCraft version")
    if not str(upstream.resolve()).startswith(str((ROOT / ".workspace").resolve()) + "/"):
        raise RuntimeError("ONLY_IGNORED_WORKSPACE_ALLOWED")
    if not str(library.resolve()).startswith(str((ROOT / ".workspace/private-imports").resolve()) + "/"):
        raise RuntimeError("ONLY_PRIVATE_ASSET_LIBRARY_ALLOWED")
    if not (upstream / "public/highfly-private-pilot/manifest.json").is_file():
        raise RuntimeError("P1_VIEWER_MISSING: run the existing P1 installer first")
    for model in ("hero", "skeleton"):
        if not (upstream / ("public/highfly-private-pilot/" + model + ".glb")).is_file():
            raise RuntimeError("P1_MODEL_MISSING: " + model)


def model_nodes(library: Path) -> dict:
    paths = {
        "hero": library / "KayKit Adventurers 2.0/Characters/gltf/Knight.glb",
        "skeleton": library / "KayKit Skeletons 1.1/characters/gltf/Skeleton_Minion.glb",
    }
    info = {}
    for name, p in paths.items():
        if not p.is_file() or p.is_symlink():
            raise RuntimeError("P2_TARGET_MISSING: " + str(p))
        info[name] = model_info(p, library)
        if info[name]["jointCount"] < 20:
            raise RuntimeError("UNEXPECTED_BONE_COUNT: " + name)
    return info


def plan(upstream: Path = ORIGINAL, library: Path = KAYKIT) -> tuple[dict, list[tuple[Path, Path]]]:
    verify_sources(upstream, library)
    targets = model_nodes(library)
    directories = (
        library / "KayKit Character Animations 1.1/Animations/gltf/Rig_Medium",
        library / "KayKit Adventurers 2.0/Animations/gltf/Rig_Medium",
    )
    if not all(d.is_dir() for d in directories):
        raise RuntimeError("RIG_MEDIUM_ANIMATION_PACKS_MISSING")
    candidates = []
    used_stems = set()
    for directory in directories:
        for file in sorted(directory.glob("*.glb")):
            if file.is_symlink() or file.stem.lower() in used_stems:
                continue
            data = model_info(file, library)
            if not data["animationCount"]:
                continue
            animated = set(data["animationTargetNames"])
            if not animated:
                continue
            matched = {
                key: len(animated & set(value["nodeNames"]))
                for key, value in targets.items()
            }
            # Require exact animation-node coverage across BOTH targets.
            if any(n != len(animated) for n in matched.values()):
                continue
            used_stems.add(file.stem.lower())
            key = file.stem.lower().replace("_", "")
            rank = next((i for i, hint in enumerate(PRIORITY) if hint in key), len(PRIORITY))
            candidates.append((rank, file, data))
    candidates.sort(key=lambda x: (x[0], x[1].name.lower()))
    if not candidates:
        raise RuntimeError("NO_RIG_MEDIUM_DONORS: inspect P2 report before proceeding")
    chosen = candidates[:18]
    if sum(f.stat().st_size for _, f, _ in chosen) > 180 * 1024 * 1024:
        raise RuntimeError("ANIMATION_SET_TOO_LARGE: reduce donor selection")
    donors = []
    copies = []
    for index, (_, file, info) in enumerate(chosen):
        destination = "donor_" + str(index).zfill(2) + ".glb"
        copies.append((file, upstream / "public" / FOLDER / destination))
        donors.append({
            "title": file.stem,
            "file": "/" + FOLDER + "/" + destination,
            "clipCount": info["animationCount"],
            "clips": [a["name"] for a in info["animations"]],
            "matchedBones": 23,
        })
    manifest = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P3_PRIVATE_ANIMATION_VISUAL_TEST_NOT_GAMEPLAY",
        "sourceCommit": PIN,
        "models": [
            {"key": "hero", "title": "Hunter KayKit · Knight", "file": "/highfly-private-pilot/hero.glb"},
            {"key": "skeleton", "title": "Enemigo KayKit · Skeleton Minion", "file": "/highfly-private-pilot/skeleton.glb"},
        ],
        "donors": donors,
        "note": "Name overlap is diagnostic; inspect deformation, movement and attack in Chrome.",
    }
    return manifest, copies


def put_if_missing(source: Path, target: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise RuntimeError("MISSING_OR_SYMLINK_SOURCE: " + str(source))
    if target.exists() or target.is_symlink():
        if target.is_symlink() or sha256(source) != sha256(target):
            raise RuntimeError("DIFFERENT_EXISTING_P3_FILE: " + str(target))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def install(upstream: Path, manifest: dict, copies: list[tuple[Path, Path]]) -> None:
    html = ROOT / "pilot/highfly-animation-lab-p3.html"
    code = ROOT / "pilot/highfly_animation_lab_p3.ts"
    page = upstream / "highfly-animation-lab-p3.html"
    module = upstream / "src/highfly_animation_lab_p3.ts"
    vite = upstream / "vite.config.ts"
    before = "        editor: fileURLToPath(new URL('editor.html', import.meta.url)),"
    after = before + "\n        highflyP3: fileURLToPath(new URL('highfly-animation-lab-p3.html', import.meta.url)),"
    config = vite.read_text(encoding="utf-8")
    if after not in config:
        if config.count(before) != 1:
            raise RuntimeError("VITE_INPUT_CHANGED: no files installed")
        config = config.replace(before, after, 1)
    dest = upstream / "public" / FOLDER
    manifest_path = dest / "manifest.json"
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if manifest_path.is_symlink() or (manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != serialized):
        raise RuntimeError("DIFFERENT_EXISTING_P3_MANIFEST: no files installed")
    # Preflight all changes before any copying.
    for source, target in copies + [(html, page), (code, module)]:
        if not source.is_file() or source.is_symlink():
            raise RuntimeError("P3_SOURCE_MISSING_OR_LINK: " + str(source))
        if target.exists() or target.is_symlink():
            if target.is_symlink() or sha256(source) != sha256(target):
                raise RuntimeError("DIFFERENT_EXISTING_P3_FILE: " + str(target))
    for source, target in copies + [(html, page), (code, module)]:
        put_if_missing(source, target)
    dest.mkdir(parents=True, exist_ok=True)
    if not manifest_path.exists():
        manifest_path.write_text(serialized, encoding="utf-8")
    if vite.read_text(encoding="utf-8") != config:
        vite.write_text(config, encoding="utf-8")
    report = ROOT / ".workspace/reports/kaykit-v7/ANIMATION_P3_PRIVATE.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(serialized, encoding="utf-8")
    print("[HIGHFLY] P3 PRIVATE ANIMATION LAB INSTALLED")
    print("[HIGHFLY] DONORS: " + str(len(manifest["donors"])))
    print("[HIGHFLY] REBUILD: bash scripts/start_preview_0447.sh")
    print("[HIGHFLY] PRIVATE URL: /highfly-animation-lab-p3.html on port 4173")
    print("[HIGHFLY] Original world, gameplay, loot and saves untouched. NO PUBLIC RELEASE.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--upstream", type=Path, default=ORIGINAL)
    parser.add_argument("--kaykit", type=Path, default=KAYKIT)
    args = parser.parse_args()
    manifest, copies = plan(args.upstream, args.kaykit)
    print("[HIGHFLY] P3 RIG_MEDIUM DONORS: " + json.dumps([
        {"name": item["title"], "clips": item["clipCount"]}
        for item in manifest["donors"]
    ], ensure_ascii=False))
    if args.install:
        install(args.upstream, manifest, copies)
    else:
        print("[HIGHFLY] DRY RUN ONLY: add --install to configure private P3.")


if __name__ == "__main__":
    main()
