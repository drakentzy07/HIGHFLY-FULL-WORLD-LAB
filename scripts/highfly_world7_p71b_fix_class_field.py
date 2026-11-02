#!/usr/bin/env python3
"""P71B: surgical DrakenLAB class-field correction in an already-installed private stage.

P71 inserted offlineSim.player.cls, but ClaudeCraft Entity has no cls field;
its player class lives in player.templateId. Vite transpiles without TypeScript
type-checking; a green build alone did not reveal the invisible selector.
Never change gameplay, class definitions, save files, GLBs, or the pinned source.
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

STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
OUT = ROOT / ".workspace/reports/highfly-world7/p71"
MAIN = "src/main.ts"
OLD = "currentClass: offlineSim.player.cls,"
NEW = "currentClass: offlineSim.player.templateId as PlayerClass,"
BACKUP = "backup/P71B_BEFORE_CLASS_FIELD_FIX.ts"
MARK = "HIGHFLY_WORLD7_P71_DRAKENLAB"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked_path(path: Path, root: Path) -> bool:
    return not path.is_symlink() and path.resolve().is_relative_to(root.resolve())

def preflight(*, stage: Path = STAGE, out: Path = OUT, repo: Path = ROOT) -> dict:
    work = repo / ".workspace"
    if (not checked_path(stage, work) or not stage.is_dir()
            or not checked_path(out, work) or not out.is_dir()):
        raise RuntimeError("P71B_STAGE_OR_REPORT_MISSING_OR_UNSAFE")
    main = stage / MAIN
    stat = out / "P71_STATUS.json"
    bkp = out / BACKUP
    after = out / "P71B_STATUS.json"
    for file in (main, stat):
        if not file.is_file() or not checked_path(file, repo):
            raise RuntimeError("P71B_REQUIRED_INPUT_MISSING_OR_UNSAFE: " + str(file))
    for file in (bkp, after):
        if file.is_symlink() or not checked_path(file, repo):
            raise RuntimeError("P71B_UNSAFE_REPORT_TARGET")
    if (out / "backup").is_symlink():
        raise RuntimeError("P71B_UNSAFE_BACKUP_DIRECTORY")
    current = main.read_text("utf8")
    if current.count(MARK) != 2:
        raise RuntimeError("P71B_INVALID_MARKER_COUNT")
    installed = json.loads(stat.read_text("utf8"))
    if installed.get("mode") != "BUILD_GREEN_BROWSER_PENDING":
        raise RuntimeError("P71B_P71_BUILD_NOT_COMPLETE")
    prior_sha = installed.get("sourceHashes", {}).get(MAIN)
    if not isinstance(prior_sha, str) or len(prior_sha) != 64:
        raise RuntimeError("P71B_INVALID_PRIOR_HASH")
    if current.count(NEW) == 1 and current.count(OLD) == 0:
        if after.is_file() and json.loads(after.read_text("utf8")).get("updatedSha256") == digest(main):
            return {"state": "ALREADY_REPAIRED", "main": main}
        raise RuntimeError("P71B_REPAIRED_WITHOUT_STATUS")
    if current.count(OLD) != 1 or current.count(NEW) != 0:
        raise RuntimeError("P71B_EXPECTED_EXACT_OLD_FIELD_ONCE")
    if digest(main) != prior_sha:
        raise RuntimeError("P71B_STAGE_MODIFIED_SINCE_P71_BUILD")
    if bkp.exists() or after.exists():
        raise RuntimeError("P71B_PREVIOUS_REPAIR_BACKUP_OR_STATUS_EXISTS")
    if "import type" not in current or "PlayerClass" not in current:
        raise RuntimeError("P71B_PLAYERCLASS_IMPORT_NOT_FOUND")
    return {"state": "READY", "main": main, "old": current, "new": current.replace(OLD, NEW, 1),
            "backup": bkp, "after": after}

def run(apply: bool = False, *, stage: Path = STAGE, out: Path = OUT,
        repo: Path = ROOT, build=None) -> dict:
    # Structural guard is deliberately before any touching of the stage.
    plan = preflight(stage=stage, out=out, repo=repo)
    result = {
        "phase": "HIGHFLY_WORLD7_P71B_DRAKENLAB_CLASS_FIELD_FIX",
        "mode": plan["state"],
        "gameplayVerified": False,
        "originalModified": False,
        "modelFilesChanged": False,
    }
    if plan["state"] == "ALREADY_REPAIRED" or not apply:
        return result
    backup = plan["backup"]
    main = plan["main"]
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open("x", encoding="utf8") as target:
        target.write(plan["old"])
    if digest(backup) != digest(main):
        raise RuntimeError("P71B_BACKUP_INTEGRITY_FAILED")
    try:
        if main.read_text("utf8") != plan["old"]:
            raise RuntimeError("P71B_CONCURRENT_CHANGE")
        main.write_text(plan["new"], encoding="utf8")
        if main.read_text("utf8").count(NEW) != 1:
            raise RuntimeError("P71B_WRITE_MISMATCH")
        smoke = build if build is not None else p9.smoke
        bld = smoke()
        if bld.get("exitCode") != 0:
            raise RuntimeError("P71B_BUILD_FAILED_SEE_P9_LOG")
        result["mode"] = "BUILD_GREEN_BROWSER_PENDING"
        result["updatedSha256"] = digest(main)
        plan["after"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
        return result
    except BaseException:
        shutil.copy2(backup, main)
        print("[P71B] RED: original private main.ts restored; old backup retained.", file=sys.stderr)
        raise

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--apply", action="store_true")
    mode = args.parse_args()
    print("[P71B] " + json.dumps(run(mode.apply), indent=2, ensure_ascii=False))
