#!/usr/bin/env python3
"""P71: protected DrakenLAB private-stage install, one fresh offline Sim per class.

NEVER modifies pinned original, classes, skills, save format, XP, physics,
FURY, HUD actions, abilities, item permissions, models, or online sessions.
Requires P69 installed; read-only dry-run by default. --apply builds with P9.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
OUT = ROOT / ".workspace/reports/highfly-world7/p71"
MARK = "HIGHFLY_WORLD7_P71_DRAKENLAB"
MAIN = "src/main.ts"
MODULE = "src/highfly/drakenlab_p71.ts"
CSS = "src/highfly/drakenlab_p71.css"
IMPORTS = (
    "import { mountDrakenLab, isDrakenLabEnabled, consumeDrakenLabBootRequest, "
    "restartDrakenLab } from './highfly/drakenlab_p71';\n"
    "import './highfly/drakenlab_p71.css';\n"
)
GAME_ANCHOR = "  document.body.classList.add('game-active');"
GAME_INSERT = (
    GAME_ANCHOR + "\n"
    "  // " + MARK + ": never mutate a live class or a server character.\n"
    "  if (import.meta.env.VITE_HIGHFLY_OFFLINE_LAB === '1' && offlineSim &&\n"
    "      isDrakenLabEnabled(location.search)) {\n"
    "    mountDrakenLab({\n"
    "      currentClass: offlineSim.player.templateId as PlayerClass,\n"
    "      playerName: offlineSim.player.name,\n"
    "      onChoose: (nextClass) => restartDrakenLab(nextClass, offlineSim.player.name),\n"
    "    });\n"
    "  }"
)
BOOT_ANCHOR = "const startupParams = new URLSearchParams(location.search);"
BOOT_INSERT = (
    BOOT_ANCHOR + "\n"
    "// " + MARK + ": only enabled by the private P9 offline-lab build.\n"
    "const highflyDrakenLabBoot = import.meta.env.VITE_HIGHFLY_OFFLINE_LAB === '1'\n"
    "  ? consumeDrakenLabBootRequest()\n"
    "  : null;"
)
DIAG_ANCHOR = "} else if (diagnosticsAutoOffline) {"
DIAG_INSERT = (
    "} else if (highflyDrakenLabBoot) {\n"
    "  startSitePresence('home');\n"
    "  void startOffline(highflyDrakenLabBoot.cls, highflyDrakenLabBoot.name, 0);\n"
    + DIAG_ANCHOR
)
EXPECTED_CLASSES = (
    "'warrior'", "'paladin'", "'hunter'", "'rogue'", "'priest'",
    "'shaman'", "'mage'", "'warlock'", "'druid'",
)

def safe(path: Path, base: Path) -> bool:
    return not path.is_symlink() and path.resolve().is_relative_to(base.resolve())

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def plan(stage: Path = STAGE, repo: Path = ROOT) -> dict:
    workspace = repo / ".workspace"
    if not safe(stage, workspace) or not stage.is_dir():
        raise RuntimeError("P71_UNSAFE_OR_MISSING_PRIVATE_STAGE")
    main, dest_ts, dest_css = (stage / p for p in (MAIN, MODULE, CSS))
    source_ts, source_css = (repo / p for p in (
        "pilot/highfly_drakenlab_p71.ts", "pilot/highfly_drakenlab_p71.css"))
    for path in (main, source_ts, source_css):
        if not path.is_file() or path.is_symlink() or not safe(path, repo):
            raise RuntimeError("P71_SOURCE_UNSAFE_OR_MISSING: " + str(path))
    for path in (dest_ts, dest_css):
        if path.is_symlink() or not safe(path, stage):
            raise RuntimeError("P71_TARGET_UNSAFE: " + str(path))
    types = stage / "src/sim/types.ts"
    if not types.is_file() or types.is_symlink() or not safe(types, stage):
        raise RuntimeError("P71_MISSING_CLASS_TYPES")
    types_text = types.read_text("utf8")
    if not all(cls in types_text for cls in EXPECTED_CLASSES):
        raise RuntimeError("P71_EXPECTED_NINE_CLASSES_MISSING")
    original = main.read_text("utf8")
    code_ts, code_css = source_ts.read_text("utf8"), source_css.read_text("utf8")
    already = MARK in original
    if already:
        if (original.count(MARK) != 2 or original.count(IMPORTS) != 1 or
                not dest_ts.is_file() or not dest_css.is_file() or
                dest_ts.read_text("utf8") != code_ts or
                dest_css.read_text("utf8") != code_css):
            raise RuntimeError("P71_PARTIAL_OR_MODIFIED_INSTALL")
        return {"already": True, "main": main, "destTs": dest_ts, "destCss": dest_css,
                "oldMain": original, "newMain": original, "ts": code_ts, "css": code_css}
    if "HIGHFLY_P69_FURY_CORE" not in original:
        raise RuntimeError("P71_P69_NOT_DETECTED")
    if "HIGHFLY_P68_FURY_GOLDEN_RECOVERY" not in original:
        raise RuntimeError("P71_P68_NOT_DETECTED")
    for anchor in (GAME_ANCHOR, BOOT_ANCHOR, DIAG_ANCHOR):
        if original.count(anchor) != 1:
            raise RuntimeError("P71_ANCHOR_DRIFT: " + anchor[:64])
    if original.count("async function startGame(") != 1 or original.count("async function startOffline(") != 1:
        raise RuntimeError("P71_GAME_ENTRY_MISSING")
    if original.count("import ") == 0 or original.index("import ") > original.index("async function startGame("):
        raise RuntimeError("P71_IMPORTS_MISSING")
    if dest_ts.exists() or dest_css.exists():
        raise RuntimeError("P71_EXISTING_UNRELATED_MODULE")
    first = original.index("import ")
    modified = original[:first] + IMPORTS + original[first:]
    modified = modified.replace(GAME_ANCHOR, GAME_INSERT, 1)
    modified = modified.replace(BOOT_ANCHOR, BOOT_INSERT, 1)
    modified = modified.replace(DIAG_ANCHOR, DIAG_INSERT, 1)
    if modified.count(MARK) != 2 or modified.count(IMPORTS) != 1:
        raise RuntimeError("P71_BAD_PATCH_COUNT")
    return {"already": False, "main": main, "destTs": dest_ts, "destCss": dest_css,
            "oldMain": original, "newMain": modified, "ts": code_ts, "css": code_css}

def run(apply: bool = False, *, stage: Path = STAGE, repo: Path = ROOT,
        out: Path = OUT) -> dict:
    if not safe(out, repo / ".workspace") or out.is_symlink():
        raise RuntimeError("P71_UNSAFE_REPORT_PATH")
    # In production, the pinned v0.44.7 reference and P8 stage manifest are required.
    p9.preflight(p9.ORIGINAL, stage, p9.REPORT)
    info = plan(stage, repo)
    result = {
        "phase": "WORLD7_P71_NINE_CLASSES_DRAKENLAB",
        "mode": "ALREADY_INSTALLED" if info["already"] else "DRY_RUN",
        "expectedClasses": 9,
        "offlineOnly": True,
        "classMutation": False,
        "onlinePlayerChanged": False,
        "skillsChanged": False,
        "physicsChanged": False,
        "originalChanged": False,
        "assetsCopiedFromClaudeCraft": False,
        "skinsIndependentCompleted": False,
        "gameplayVerifiedOnS23": False,
    }
    if not apply or info["already"]:
        return result
    # The sibling P71 visual audit legitimately creates OUT to store its report.
    # Reject *only* an existing installer backup/status, never a report folder.
    # Fail closed if someone left a previous install attempt: never overwrite it.
    if out.is_symlink() or (out.exists() and not out.is_dir()):
        raise RuntimeError("P71_REPORT_DIRECTORY_UNSAFE")
    backup_root = out / "backup"
    status_file = out / "P71_STATUS.json"
    if (backup_root.exists() or backup_root.is_symlink()
            or status_file.exists() or status_file.is_symlink()):
        raise RuntimeError("P71_EXISTING_INSTALL_BACKUP_OR_STATUS")
    backed = None
    touched = []
    try:
        backup = out / "backup/src/main.ts"
        backup.parent.mkdir(parents=True, exist_ok=False)
        shutil.copy2(info["main"], backup)
        if sha(backup) != sha(info["main"]):
            raise RuntimeError("P71_BACKUP_HASH_MISMATCH")
        backed = backup
        if info["main"].read_text("utf8") != info["oldMain"]:
            raise RuntimeError("P71_CONCURRENT_SOURCE_CHANGE")
        info["destTs"].parent.mkdir(parents=True, exist_ok=True)
        for dest, content in ((info["destTs"], info["ts"]), (info["destCss"], info["css"])):
            with dest.open("x", encoding="utf8") as handle:
                handle.write(content)
            touched.append(dest)
        info["main"].write_text(info["newMain"], "utf8")
        result["mode"] = "BUILDING"
        build = p9.smoke()
        if build.get("exitCode") != 0:
            raise RuntimeError("P71_VITE_BUILD_FAILED_SEE_P9_LOG")
        result["mode"] = "BUILD_GREEN_BROWSER_PENDING"
        result["sourceHashes"] = {
            MAIN: sha(info["main"]),
            MODULE: sha(info["destTs"]),
            CSS: sha(info["destCss"]),
        }
        (out / "P71_STATUS.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
        return result
    except BaseException:
        if backed is not None and backed.is_file():
            shutil.copy2(backed, info["main"])
        for dest in reversed(touched):
            if dest.is_file() and not dest.is_symlink():
                dest.unlink()
        print("[WORLD7 P71] RED: private source restored. Existing dist may need rebuilding.", file=sys.stderr)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    options = parser.parse_args()
    print("[WORLD7 P71] " + json.dumps(run(options.apply), ensure_ascii=False, indent=2))
