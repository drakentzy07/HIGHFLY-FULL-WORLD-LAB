#!/usr/bin/env python3
"""P70-B: install a classless HIGHFLY hunter identity bound to the real offline Sim.

This is a minimal, safe live-engine integration, NOT the final removal of Warrior.
It does not alter any legacy class, stats, skill unlocks, saves, visual assets,
animation routing, physics or network protocol. Builds via P9 with rollback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
ORIGINAL = p9.ORIGINAL
OUT = ROOT / ".workspace/reports/highfly-world7/p70b"
MAIN = "src/main.ts"
MODULE = "src/highfly/hunter_universal_identity.ts"
SOURCE = ROOT / "pilot/highfly_hunter_runtime_p70b.ts"
MARK = "HIGHFLY_WORLD7_P70B_SESSION_IDENTITY"
IMPORT = (
    "import { defineHighflyHunterIdentity, registerHighflyHunterSession } "
    "from './highfly/hunter_universal_identity';\n"
)
ANCHOR = "  sim.setPlayerSkin(sim.playerId, skin);"
PATCH = (
    "  // " + MARK + ": read-only HIGHFLY identity; legacy RPG Sim remains authoritative.\n"
    "  registerHighflyHunterSession(sim, defineHighflyHunterIdentity(name, skin));\n"
    + ANCHOR
)

def safe(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve()) and not path.is_symlink()

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def plan(stage: Path = STAGE, source: Path = SOURCE) -> dict:
    if not safe(stage, ROOT / ".workspace"):
        raise RuntimeError("P70B_ONLY_PRIVATE_STAGE")
    main = stage / MAIN
    module = stage / MODULE
    if not safe(main, stage) or not main.is_file():
        raise RuntimeError("P70B_MAIN_MISSING_OR_UNSAFE")
    if module.exists() or module.is_symlink():
        raise RuntimeError("P70B_MODULE_ALREADY_EXISTS")
    if source.is_symlink() or not source.is_file() or not safe(source, ROOT):
        raise RuntimeError("P70B_SOURCE_MISSING_OR_UNSAFE")
    text = main.read_text("utf8")
    if MARK in text or IMPORT in text:
        raise RuntimeError("P70B_ALREADY_INSTALLED")
    if "HIGHFLY_P13_OWNED_KNIGHT_PREVIEW" not in text:
        raise RuntimeError("P70B_REQUIRES_P13")
    if "HIGHFLY_P69_FURY_CORE" not in text:
        raise RuntimeError("P70B_REQUIRES_P69")
    if text.count(ANCHOR) != 1:
        raise RuntimeError("P70B_SKIN_ANCHOR_DRIFT")
    if text.count("async function startOffline(") != 1:
        raise RuntimeError("P70B_OFFLINE_ENTRY_DRIFT")
    if not text.lstrip().startswith("import ") and "\nimport " not in text:
        raise RuntimeError("P70B_IMPORT_ANCHOR_MISSING")
    # Guard: ensure that skin assignment is inside the startOffline function.
    offline = text.index("async function startOffline(")
    skin_at = text.index(ANCHOR)
    if not (offline < skin_at < offline + 10000):
        raise RuntimeError("P70B_SKIN_ANCHOR_WRONG_CONTEXT")
    first_import = text.index("import ")
    revised = text[:first_import] + IMPORT + text[first_import:]
    if revised.count(ANCHOR) != 1:
        raise RuntimeError("P70B_ANCHOR_CHANGED")
    revised = revised.replace(ANCHOR, PATCH, 1)
    if revised.count(MARK) != 1 or revised.count(IMPORT) != 1:
        raise RuntimeError("P70B_PATCH_COUNT")
    return {"main": main, "module": module, "source": text, "revised": revised,
            "moduleText": source.read_text("utf8"), "moduleSha256": sha(source)}

def run(apply: bool = False, *, stage: Path = STAGE, out: Path = OUT) -> dict:
    if not safe(out, ROOT / ".workspace"):
        raise RuntimeError("P70B_UNSAFE_REPORT")
    # Runtime preflight also detects protected resources and stage drift.
    p9.preflight(ORIGINAL, stage, p9.REPORT)
    info = plan(stage)
    result = {
        "phase": "HIGHFLY_WORLD7_P70B",
        "mode": "DRY_RUN",
        "identityAttachedToLiveOfflineSim": False,
        "legacyClassRemoved": False,
        "statsSkillsResourcesReplaced": False,
        "gameplayDamagePhysicsModified": False,
        "visualSkinSelectorCompleted": False,
        "privateOnly": True,
        "moduleSha256": info["moduleSha256"],
    }
    if not apply:
        return result
    if out.exists() or out.is_symlink():
        raise RuntimeError("P70B_BACKUP_ALREADY_EXISTS")
    written = []
    backed_up = None
    try:
        (out / "backups/src").mkdir(parents=True)
        backed_up = out / "backups" / MAIN
        shutil.copy2(info["main"], backed_up)
        if sha(backed_up) != sha(info["main"]):
            raise RuntimeError("P70B_BACKUP_HASH_MISMATCH")
        if info["main"].read_text("utf8") != info["source"]:
            raise RuntimeError("P70B_CONCURRENT_EDIT")
        info["module"].parent.mkdir(parents=True, exist_ok=True)
        with info["module"].open("x", encoding="utf8") as f:
            f.write(info["moduleText"])
        written.append(info["module"])
        info["main"].write_text(info["revised"], "utf8")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/highfly_p9_private_build_smoke.py")],
            cwd=ROOT, check=True,
        )
        result["mode"] = "BUILD_GREEN_BROWSER_PENDING"
        result["identityAttachedToLiveOfflineSim"] = True
        (out / "P70B_STATUS.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    except BaseException:
        if backed_up and backed_up.is_file():
            shutil.copy2(backed_up, info["main"])
        for file in written:
            if file.is_file() and not file.is_symlink():
                file.unlink()
        print("[HIGHFLY WORLD7 P70-B] RED -> reverted private stage", file=sys.stderr)
        raise
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("[HIGHFLY WORLD7 P70-B] " +
          json.dumps(run(args.apply), ensure_ascii=False, indent=2))
