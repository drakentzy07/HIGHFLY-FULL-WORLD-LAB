#!/usr/bin/env python3
"""HIGHFLY private P11: stop preloading original 9-class media to preview KayKit Knight.

Only adjusts the ignored HIGHFLY stage: P4 visual donor URLs, character boot
preload and offline entry. No protected RPG simulation, original checkout,
upstream public media, game saves or release settings are modified.

IMPORTANT: world preload is still blocked by missing licensed-replacement media.
This fix targets the character preview + class preload, NOT full playability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
REPORT = ROOT / ".workspace/reports/highfly-p11"
OWNED_URLS = [
    "highfly-private-p4/hero.glb",
    "highfly-private-p4/skeleton.glb",
    "highfly-private-p4/donor_00.glb",
    "highfly-private-p4/donor_01.glb",
    "highfly-private-p4/donor_02.glb",
    "highfly-private-p4/donor_03.glb",
]
START = "// HIGHFLY_P11_GAME_FIRST"
END = "// END_HIGHFLY_P11_GAME_FIRST"
ORIGINAL_PRELOAD = "const allPreloadUrls = characterPreloadUrls(false);"
ORIGINAL_OFFLINE = "isOfflineModeAvailable(import.meta.env.DEV)"
NEW_OFFLINE = "isOfflineModeAvailable(import.meta.env.DEV || import.meta.env.VITE_HIGHFLY_OFFLINE_LAB === '1')"
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def plan(stage: Path = STAGE) -> dict:
    if not stage.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("PRIVATE_STAGE_REQUIRED")
    manifest = stage / "src/render/characters/manifest.ts"
    assets = stage / "src/render/characters/assets.ts"
    main = stage / "src/main.ts"
    for path in (manifest, assets, main):
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("MISSING_OR_UNSAFE_STAGE_SOURCE: " + str(path))
    for url in OWNED_URLS:
        file = stage / "public" / url
        if not file.is_file() or file.is_symlink():
            raise RuntimeError("OWNED_P4_MODEL_NOT_PRESENT: " + url)
    manifest_before = manifest.read_text(encoding="utf8")
    if "HIGHFLY_P4_VISUAL_BRIDGE_START" not in manifest_before:
        raise RuntimeError("P4_HUNTER_BRIDGE_NOT_FOUND")
    manifest_after = manifest_before
    for name in ("heroBase", "skeletonBase"):
        old = "animUrls: [...hfDonors, ...(" + name + ".animUrls ?? [])],"
        new = "animUrls: hfDonors, // P11 owned KayKit clips ONLY, not original donors"
        if old in manifest_after:
            if manifest_after.count(old) != 1:
                raise RuntimeError("UNEXPECTED_DUPLICATE_P4_ANIM_MAPPING: " + name)
            manifest_after = manifest_after.replace(old, new)
        elif new not in manifest_after:
            raise RuntimeError("P4_ANIM_MAPPING_UNEXPECTED: " + name)
    assets_before = assets.read_text(encoding="utf8")
    code = (
        START + "\n"
        + "// Only the privately owned character assets needed by this early HIGHFLY visual bridge.\n"
        + "// Gameplay/AI/loot code and all other visual definitions remain present.\n"
        + "const highflyP4CharacterUrls = " + json.dumps(OWNED_URLS, ensure_ascii=False) + ";\n"
        + "const allPreloadUrls = import.meta.env.VITE_HIGHFLY_P4 === '1'\n"
        + "  ? highflyP4CharacterUrls\n"
        + "  : characterPreloadUrls(false);\n"
        + END
    )
    if START in assets_before:
        if assets_before.count(START) != 1 or END not in assets_before:
            raise RuntimeError("P11_PRELOAD_BLOCK_CORRUPTED")
        assets_after = assets_before
    else:
        if assets_before.count(ORIGINAL_PRELOAD) != 1:
            raise RuntimeError("PRELOAD_ANCHOR_NOT_UNIQUE")
        assets_after = assets_before.replace(ORIGINAL_PRELOAD, code)
    main_before = main.read_text(encoding="utf8")
    if ORIGINAL_OFFLINE in main_before:
        if main_before.count(ORIGINAL_OFFLINE) != 1:
            raise RuntimeError("OFFLINE_GATE_ANCHOR_NOT_UNIQUE")
        main_after = main_before.replace(ORIGINAL_OFFLINE, NEW_OFFLINE)
    elif NEW_OFFLINE in main_before:
        main_after = main_before
    else:
        raise RuntimeError("OFFLINE_GATE_UNEXPECTED")
    return {
        "changes": {
            manifest: (manifest_before, manifest_after),
            assets: (assets_before, assets_after),
            main: (main_before, main_after),
        },
        "ownedP4Resources": OWNED_URLS,
        "result": {
            "target": "PRIVATE_HUNTER_CHARACTER_PREVIEW_ONLY",
            "characterBootUrls": len(OWNED_URLS),
            "legacyClassesStillInSimulation": True,
            "originalGameChanged": False,
            "worldAssetsComplete": False,
            "worldPlayableVerified": False,
            "publicReleaseApproved": False,
            "offlineModeEnabledInPrivateBuild": True,
        }
    }


def apply(prepared: dict, report: Path = REPORT) -> dict:
    if not report.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("PRIVATE_REPORT_REQUIRED")
    for file, (before, after) in prepared["changes"].items():
        if file.read_text(encoding="utf8") != before:
            raise RuntimeError("STAGE_FILE_CHANGED_DURING_P11: " + str(file))
        if file.is_symlink():
            raise RuntimeError("UNSAFE_STAGE_TARGET")
    report.mkdir(parents=True, exist_ok=True)
    for file, (before, after) in prepared["changes"].items():
        label = file.name if file.name != "manifest.ts" else "character_manifest.ts"
        backup = report / (label + ".before")
        if before != after and not backup.exists():
            backup.write_text(before, encoding="utf8")
        if before != after:
            file.write_text(after, encoding="utf8")
    output = prepared["result"].copy()
    output["applied"] = True
    output["filesEdited"] = [
        file.relative_to(STAGE).as_posix()
        for file, (before, after) in prepared["changes"].items() if before != after
    ]
    (report / "HUNTER_PREVIEW_P11.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    # P9 checks original pin, RPG source integrity, seven private buildings, etc.
    p9.preflight(p9.ORIGINAL, p9.STAGE, p9.REPORT)
    planned = plan()
    if args.apply:
        result = apply(planned)
    else:
        result = {**planned["result"], "applied": False}
    print("[HIGHFLY] P11 PRIVATE HUNTER PREVIEW: " + json.dumps(result, ensure_ascii=False))
    print("[HIGHFLY] Existing 713-asset world preload remains INCOMPLETE; do not claim playable world.")


if __name__ == "__main__":
    main()
