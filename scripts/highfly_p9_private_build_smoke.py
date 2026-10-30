#!/usr/bin/env python3
"""HIGHFLY P9: try an independent PRIVATE Vite compile without original game media.

This is a diagnostic build, not proof of runtime gameplay or rights. It NEVER
copies ClaudeCraft public/ media, touches the original source or publishes.
All new content is inside the ignored independent stage and reports.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
REPORT = ROOT / ".workspace/reports/highfly-p9"
SHA = "493c35a108cef6c8aa290e8793107b1cd117886e"
BUILDING_NAMES = (
    "hexb_townhall.glb", "hexb_workshop.glb", "hexb_tavern.glb",
    "hex_church.glb", "hexb_home_a.glb", "hexb_home_b.glb", "hexb_market.glb",
)
# These are original text/config (not world media). P0 only copied main/play/editor.
REQUIRED_BUILD_TEXT = (
    ".browserslistrc", "admin.html", "guide.html", "wallet-handoff.html",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def under_private(path: Path) -> bool:
    return path.resolve().is_relative_to((ROOT / ".workspace").resolve())


def preflight(original: Path, stage: Path, report: Path) -> dict:
    if not all(under_private(p) for p in (original, stage, report)):
        raise RuntimeError("ONLY_PRIVATE_WORKSPACE_ALLOWED")
    if not (original / ".git").is_dir():
        raise RuntimeError("ORIGINAL_REFERENCE_NOT_FOUND")
    commit = subprocess.check_output(
        ["git", "-C", str(original), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != SHA:
        raise RuntimeError("REFERENCE_NOT_0447_PINNED")
    manifest = stage / "HIGHFLY_STAGE_STATUS.json"
    if not manifest.is_file():
        raise RuntimeError("HIGHFLY_INDEPENDENT_P0_STAGE_MISSING")
    state = json.loads(manifest.read_text(encoding="utf8"))
    if state.get("sourceCommit") != SHA or state.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("P0_MEDIA_AND_COMMIT_POLICY_FAILED")
    p4 = stage / "src/render/characters/manifest.ts"
    if not p4.is_file() or "HIGHFLY_P4_VISUAL_BRIDGE_START" not in p4.read_text(encoding="utf8"):
        raise RuntimeError("P4_CHARACTER_BRIDGE_MISSING")
    p8 = ROOT / ".workspace/reports/highfly-p8/EASTBROOK_OWNED_BUILDINGS_P8.json"
    if not p8.is_file():
        raise RuntimeError("P8_PRIVATE_BUILDINGS_REPORT_MISSING")
    p8_info = json.loads(p8.read_text(encoding="utf8"))
    if p8_info.get("sourceCommit") != SHA or p8_info.get("noClaudeCraftMediaCopied") is not True:
        raise RuntimeError("P8_PROVENANCE_UNEXPECTED")
    if len(p8_info.get("buildings", [])) != 7:
        raise RuntimeError("P8_EXPECTED_SEVEN_BUILDINGS")
    for name in BUILDING_NAMES:
        target = stage / "public/models/biome" / name
        if target.is_symlink() or not target.is_file():
            raise RuntimeError("P8_PRIVATE_BUILDING_MISSING: " + name)
        entry = next((b for b in p8_info["buildings"] if b.get("publicUrl") == "/models/biome/" + name), None)
        if entry is None or sha256(target) != entry.get("glbSha256"):
            raise RuntimeError("P8_PRIVATE_BUILDING_HASH_CHANGED: " + name)
    for relative in ("src/sim/eastbrook_layout.ts", "src/sim/items.ts",
                     "src/sim/corpse_loot_state.ts", "src/sim/mob/lifecycle.ts"):
        a = original / relative
        b = stage / relative
        if not a.is_file() or not b.is_file() or sha256(a) != sha256(b):
            raise RuntimeError("PROTECTED_RPG_FILE_CHANGED: " + relative)
    files = []
    for relative in REQUIRED_BUILD_TEXT:
        source, target = original / relative, stage / relative
        if not source.is_file() or source.is_symlink() or source.stat().st_size > 2_000_000:
            raise RuntimeError("ORIGINAL_BUILD_TEXT_MISSING_OR_UNSAFE: " + relative)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file() or sha256(source) != sha256(target):
                raise RuntimeError("BUILD_TEXT_CONFLICT: " + relative)
        files.append((source, target))
    node_modules = original / "node_modules"
    vite = node_modules / "vite/bin/vite.js"
    if not node_modules.is_dir() or not vite.is_file():
        raise RuntimeError("REFERENCE_DEPENDENCIES_NOT_INSTALLED: use existing private reference preview setup")
    stage_modules = stage / "node_modules"
    if stage_modules.exists() or stage_modules.is_symlink():
        # The stage may use its own private dependencies; do not overwrite.
        if not stage_modules.is_dir():
            raise RuntimeError("STAGE_NODE_MODULES_NOT_A_DIRECTORY")
    return {"textFiles": files, "vite": vite, "nodeModules": node_modules, "stageModules": stage_modules}


def prepare(original: Path, stage: Path, report: Path, state: dict) -> None:
    for source, target in state["textFiles"]:
        if not target.exists():
            shutil.copy2(source, target)
    if not state["stageModules"].exists():
        state["stageModules"].symlink_to(state["nodeModules"], target_is_directory=True)
    report.mkdir(parents=True, exist_ok=True)


def smoke(original: Path=ORIGINAL, stage: Path=STAGE, report: Path=REPORT,
          timeout: int=240) -> dict:
    state = preflight(original, stage, report)
    prepare(original, stage, report, state)
    # Vite builds JS bundles, but assets not present in HIGHFLY public/ remain
    # unavailable at runtime. Never use this output for a playable claim.
    env = os.environ.copy()
    env.update({
        "VITE_HIGHFLY_P4": "1",
        "VITE_HIGHFLY_OFFLINE_LAB": "1",
        "NODE_OPTIONS": "--max-old-space-size=4096",
    })
    try:
        outcome = subprocess.run(
            ["node", str(state["vite"]), "build", "--base=/"],
            cwd=str(stage), env=env, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        success = outcome.returncode == 0
        transcript = (outcome.stdout + "\n" + outcome.stderr)[-60000:]
        exit_code = outcome.returncode
    except subprocess.TimeoutExpired as err:
        success = False
        exit_code = 124
        transcript = "VITE_PRIVATE_BUILD_TIMEOUT\n" + str(err)
    result = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P9_PRIVATE_INDEPENDENT_VITE_BUILD_DIAGNOSTIC",
        "sourceCommit": SHA,
        "result": "BUNDLE_BUILT_NOT_PLAYABLE_VERIFIED" if success else "BUNDLE_BLOCKED_REVIEW_LOG",
        "exitCode": exit_code,
        "originalReferenceModified": False,
        "protectedRpgCodeModified": False,
        "originalWorldMediaImported": False,
        "sourceMediaLicenseApproved": False,
        "independentRuntimeVerified": False,
        "p8PrivateBuildingsChecked": 7,
        "p4ActorBridgePresent": True,
        "log": str(report / "VITE_BUILD_P9.log"),
        "note": "A successful bundler exit does NOT prove the world is playable. Asset and gameplay integration remain outstanding.",
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
    }
    (report / "VITE_BUILD_P9.log").write_text(transcript, encoding="utf8")
    (report / "VITE_BUILD_P9.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P9 PRIVATE BUILD: " + json.dumps({
        "result": result["result"], "exitCode": exit_code,
        "sevenOwnedBuildingModels": True, "originalMediaCopied": False,
        "playableVerified": False
    }, ensure_ascii=False))
    if not success:
        print("[HIGHFLY] P9 ERROR LOG TAIL (last 28 lines):")
        print("\n".join(transcript.splitlines()[-28:]))
    print("[HIGHFLY] P9 PRIVATE LOG: " + str(report / "VITE_BUILD_P9.log"))
    print("[HIGHFLY] NO PUBLIC DEPLOY. ORIGINAL GAME UNCHANGED.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        p = preflight(ORIGINAL, STAGE, REPORT)
        print("[HIGHFLY] P9 PRIVATE BUILD PRECHECK OK: " + json.dumps({
            "missingTextBuildInputsStagedOnBuild": [dest.name for _, dest in p["textFiles"] if not dest.exists()],
            "vitePresent": True, "privateStageOnly": True,
        }))
        return
    result = smoke()
    if result["exitCode"]:
        raise SystemExit("HIGHFLY_P9_BUILD_BLOCKED — copy P9 ERROR LOG TAIL to diagnose the next fix")


if __name__ == "__main__":
    main()
