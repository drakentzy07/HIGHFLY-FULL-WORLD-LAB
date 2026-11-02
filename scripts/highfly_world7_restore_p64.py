#!/usr/bin/env python3
"""HIGHFLY WORLD7 clean rollback to P64 using already-existing ORIGINAL stage backups.

Read-only by default. Never re-run P65..P71 installers. Verifies successive
P65/P66/P68/P69 transformations and current P71B hash, then restores only
their changed text source files from the right pre-change snapshots. Removes
new files ONLY when exactly matching original installer source/hash. Creates
an independent backup before any write and compiles via P9, rolling back
exactly on failure. World, mobs, NPCs, KayKit models, map, skills, saves,
quests, user data, browser localStorage, and original v0.44.7 are untouched.
P41 currently has a legacy single offline save key: do NOT claim multi-slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p65_mobile_combat_hud_c2 as p65
import highfly_p66_p67_premium_combat as p66
import highfly_p68_fury_golden_recovery as p68
import highfly_p69_fury_core as p69

STAGE = p9.STAGE
WORK = ROOT / ".workspace"
OUT = WORK / "reports/highfly-world7/p64-clean-recovery"
REPORTS = WORK / "reports"
P71 = REPORTS / "highfly-world7/p71"
STATUS = OUT / "P64_CLEAN_STATUS.json"
SNAPSHOT = OUT / "pre_restore_snapshot"

# Explicit, minimal set of source files to roll back.
P65_BASE = REPORTS / "highfly-p65-hud-combat-c2/backups"
P66_BASE = REPORTS / "highfly-p66-p67-combat-premium/backups"
P68_BASE = REPORTS / "highfly-p68-fury-golden-recovery/backups"
P69_BASE = REPORTS / "highfly-p69-fury-core/backups"
MAIN = "src/main.ts"
HTML = "index.html"
MOBILE = "src/game/mobile_controls.ts"
INPUT = "src/game/input.ts"
RING = "src/ui/hud/action_bar/mobile_action_ring_controller.ts"
HUD = "src/ui/hud.ts"
SIM = "src/sim/sim.ts"
AUTO = "src/sim/combat/auto_attack.ts"
REPLACE = {
    MAIN: P65_BASE / MAIN,
    HTML: P65_BASE / HTML,
    MOBILE: P65_BASE / MOBILE,
    INPUT: P68_BASE / INPUT,
    RING: P68_BASE / RING,
    HUD: P69_BASE / HUD,
    SIM: P69_BASE / SIM,
    AUTO: P69_BASE / AUTO,
}
CREATED = {
    "public/highfly/p65.css": p65.CSS,
    "public/highfly/p66_p67_premium.css": p66.CSS,
    "public/highfly/p68_fury_recovery.css": p68.CSS,
    "public/highfly/p69_fury_core.css": p69.CSS_CODE,
    p69.TOUCH: p69.TOUCH_CODE,
    p69.TAPS: p69.TAPS_CODE,
}
P71_CREATED = (
    "src/highfly/drakenlab_p71.ts",
    "src/highfly/drakenlab_p71.css",
)
ALL_TOUCHED = tuple(REPLACE) + tuple(CREATED) + P71_CREATED

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def ensure_safe(path: Path, base: Path, label: str) -> None:
    if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
        raise RuntimeError("P64_UNSAFE_" + label + "_" + str(path))

def read(path: Path, base: Path, label: str) -> bytes:
    ensure_safe(path, base, label)
    if not path.is_file():
        raise RuntimeError("P64_MISSING_" + label + "_" + str(path))
    return path.read_bytes()

def eq(label: str, expected: bytes, actual: bytes) -> None:
    if expected != actual:
        raise RuntimeError(
            "P64_CHAIN_DRIFT_" + label +
            " EXPECTED_SHA_" + sha(expected)[:16] +
            " ACTUAL_SHA_" + sha(actual)[:16]
        )

def text(data: bytes) -> str:
    return data.decode("utf-8")

def preflight(stage: Path=STAGE, repo: Path=ROOT, reports: Path=REPORTS, out: Path=OUT) -> dict:
    work = repo / ".workspace"
    if not stage.is_dir() or not reports.is_dir():
        raise RuntimeError("P64_MISSING_STAGE_OR_REPORTS")
    for name, path in (("stage",stage),("reports",reports),("out",out)):
        ensure_safe(path, work, name)
    if out.exists():
        if not out.is_dir():
            raise RuntimeError("P64_OUT_NOT_DIRECTORY")
        existing = out / "P64_CLEAN_STATUS.json"
        if existing.is_file():
            status = json.loads(read(existing,out,"status"))
            if status.get("mode") != "BUILD_GREEN_BROWSER_PENDING":
                raise RuntimeError("P64_UNEXPECTED_STATUS")
            for rel, digest in status.get("sourceSha256",{}).items():
                actual = read(stage / rel,stage,rel)
                if sha(actual) != digest:
                    raise RuntimeError("P64_ALREADY_CLEAN_BUT_SOURCE_DRIFT_" + rel)
            for rel in tuple(CREATED) + P71_CREATED:
                if (stage / rel).exists() or (stage / rel).is_symlink():
                    raise RuntimeError("P64_ALREADY_CLEAN_BUT_OVERLAY_PRESENT_" + rel)
            if len(status.get("sourceSha256",{})) != len(REPLACE):
                raise RuntimeError("P64_INCOMPLETE_STATUS")
            return {"already":True,"result":status}
        if (out / "pre_restore_snapshot").exists() or (out / "pre_restore_snapshot").is_symlink():
            raise RuntimeError("P64_PREVIOUS_SNAPSHOT_EXISTS_REVIEW_MANUALLY")

    snap = {
        "P65M": read(reports/"highfly-p65-hud-combat-c2/backups"/MAIN,reports,"P65main"),
        "P65H": read(reports/"highfly-p65-hud-combat-c2/backups"/HTML,reports,"P65html"),
        "P65C": read(reports/"highfly-p65-hud-combat-c2/backups"/MOBILE,reports,"P65mobile"),
        "P66M": read(reports/"highfly-p66-p67-combat-premium/backups"/MAIN,reports,"P66main"),
        "P66H": read(reports/"highfly-p66-p67-combat-premium/backups"/HTML,reports,"P66html"),
        "P68M": read(reports/"highfly-p68-fury-golden-recovery/backups"/MAIN,reports,"P68main"),
        "P68H": read(reports/"highfly-p68-fury-golden-recovery/backups"/HTML,reports,"P68html"),
        "P68C": read(reports/"highfly-p68-fury-golden-recovery/backups"/MOBILE,reports,"P68mobile"),
        "P68I": read(reports/"highfly-p68-fury-golden-recovery/backups"/INPUT,reports,"P68input"),
        "P68R": read(reports/"highfly-p68-fury-golden-recovery/backups"/RING,reports,"P68ring"),
        "P69M": read(reports/"highfly-p69-fury-core/backups"/MAIN,reports,"P69main"),
        "P69H": read(reports/"highfly-p69-fury-core/backups"/HTML,reports,"P69html"),
        "P69R": read(reports/"highfly-p69-fury-core/backups"/RING,reports,"P69ring"),
        "P69U": read(reports/"highfly-p69-fury-core/backups"/HUD,reports,"P69hud"),
        "P69S": read(reports/"highfly-p69-fury-core/backups"/SIM,reports,"P69sim"),
        "P69A": read(reports/"highfly-p69-fury-core/backups"/AUTO,reports,"P69auto"),
        "P71pre": read(reports/"highfly-world7/p71/backup/src/main.ts",reports,"P71main"),
    }

    # Check each link in the actual P64 -> P65 -> P67 -> P68 -> P69 chain
    # using the exact unchanged installer transformation that wrote the stage.
    eq("P65_P66_MAIN", p65.patch_main(text(snap["P65M"])).encode(), snap["P66M"])
    eq("P65_P66_HTML", p65.patch_html(text(snap["P65H"])).encode(), snap["P66H"])
    eq("P65_P68_MOBILE", p65.patch_mobile(text(snap["P65C"])).encode(), snap["P68C"])
    eq("P66_P68_MAIN", p66.patch_main(text(snap["P66M"])).encode(), snap["P68M"])
    eq("P66_P68_HTML", p66.patch_html(text(snap["P66H"])).encode(), snap["P68H"])
    eq("P68_P69_MAIN", p68.patch_main(text(snap["P68M"])).encode(), snap["P69M"])
    eq("P68_P69_HTML", p68.patch_html(text(snap["P68H"])).encode(), snap["P69H"])
    eq("P68_P69_RING", p68.patch_ring(text(snap["P68R"])).encode(), snap["P69R"])
    eq("P69_P71_MAIN", p69.patch_main(text(snap["P69M"])).encode(), snap["P71pre"])

    old_status = json.loads(read(reports/"highfly-world7/p71/P71_STATUS.json",reports,"P71status"))
    fix_status = json.loads(read(reports/"highfly-world7/p71/P71B_STATUS.json",reports,"P71Bstatus"))
    if (old_status.get("mode") != "BUILD_GREEN_BROWSER_PENDING" or
            fix_status.get("mode") != "BUILD_GREEN_BROWSER_PENDING"):
        raise RuntimeError("P64_P71_STATUS_NOT_READY")
    eq("P71_MAIN_SHA", old_status.get("sourceHashes",{}).get(MAIN,"").encode(),
       sha(snap["P71pre"]).encode())
    eq("P71B_BACKUP_MAIN_HASH",
       old_status.get("sourceHashes",{}).get(MAIN,"").encode(),
       sha(read(reports/"highfly-world7/p71/backup/P71B_BEFORE_CLASS_FIELD_FIX.ts",
               reports,"P71Bbackup")).encode())
    current = {rel:read(stage/rel,stage,"stage_"+rel) for rel in ALL_TOUCHED}
    eq("P71B_CURRENT_MAIN_SHA",
       fix_status.get("updatedSha256","").encode(),sha(current[MAIN]).encode())

    eq("P69_HTML_CURRENT",
       p69.once(text(snap["P69H"]), "</head>",
                "<!-- " + p69.MARK + ": real skill gesture + manual basics -->\n"
                '<link rel="stylesheet" href="/highfly/p69_fury_core.css" />\n</head>',
                "INDEX_HEAD").encode(),current[HTML])
    eq("P68_INPUT_CURRENT",p68.patch_input(text(snap["P68I"])).encode(),current[INPUT])
    eq("P68_MOBILE_CURRENT",p68.patch_mobile(text(snap["P68C"])).encode(),current[MOBILE])
    eq("P69_RING_CURRENT",p69.patch_ring(text(snap["P69R"])).encode(),current[RING])
    eq("P69_HUD_CURRENT",p69.patch_hud(text(snap["P69U"])).encode(),current[HUD])
    eq("P69_SIM_CURRENT",p69.patch_sim(text(snap["P69S"])).encode(),current[SIM])
    eq("P69_AUTO_CURRENT",p69.patch_auto(text(snap["P69A"])).encode(),current[AUTO])
    for rel, source in CREATED.items():
        eq("CREATED_"+rel,source.encode(),current[rel])
    for rel in P71_CREATED:
        eq("P71_MODULE_"+rel,
           old_status.get("sourceHashes",{}).get(rel,"").encode(),
           sha(current[rel]).encode())
    eq("P71B_OLD_MAIN_HASH",
       old_status.get("sourceHashes",{}).get(MAIN,"").encode(),
       sha(snap["P71pre"]).encode())

    replacements = {
        MAIN:snap["P65M"], HTML:snap["P65H"], MOBILE:snap["P65C"],
        INPUT:snap["P68I"], RING:snap["P68R"], HUD:snap["P69U"],
        SIM:snap["P69S"], AUTO:snap["P69A"],
    }
    # These source files were not touched by P65-P71 and are intentionally
    # protected from deletion or overwriting (P41, P57, P63, P64 stay).
    for marker, rel in (
        ("HIGHFLY_P41_OFFLINE_SAVE", MAIN),
        ("HIGHFLY_P63_COMBAT_C1", AUTO),
        ("HIGHFLY_P64_REAL_BOAR_CC0", "src/render/characters/manifest.ts"),
    ):
        source = replacements.get(rel)
        if source is None: source = read(stage/rel,stage,"preserved_"+rel)
        if marker not in text(source):
            raise RuntimeError("P64_REQUIRED_PRESERVED_MARKER_MISSING_"+marker)
    return {"already":False,"current":current,"replacements":replacements,
            "delete":tuple(CREATED)+P71_CREATED,"stage":stage,"out":out}

def run(apply:bool=False, *, stage:Path=STAGE, repo:Path=ROOT,
        reports:Path=REPORTS, out:Path=OUT, build=None, check_p9=True)->dict:
    if check_p9:
        p9.preflight(p9.ORIGINAL,stage,p9.REPORT)
    plan=preflight(stage,repo,reports,out)
    if plan["already"]:
        return plan["result"]
    result={
        "phase":"HIGHFLY_WORLD7_CLEAN_RESTORE_P64",
        "mode":"DRY_RUN",
        "restoredBaseline":"P64_SOURCE_SNAPSHOT_PRE_P65",
        "originalRpgCodeChanged":False,
        "worldNpcEditorAssetsChanged":False,
        "saveImplementationChanged":False,
        "browserLocalStorageChanged":False,
        "gameplayVerified":False,
        "joystick360Fixed":False,
        "cleanStageFiles":list(REPLACE),
        "removedOverlayFiles":list(plan["delete"]),
    }
    if not apply:
        return result
    if out.exists():
        raise RuntimeError("P64_OUTPUT_ALREADY_EXISTS_WITHOUT_STATUS")
    stage_snapshot = out / "pre_restore_snapshot"
    stage_snapshot.mkdir(parents=True,exist_ok=False)
    current=plan["current"]
    try:
        # Exclusive, byte-for-byte snapshot of ALL affected files, including
        # everything slated for deletion, before modifying even one file.
        for rel, data in current.items():
            dst=stage_snapshot/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open("xb") as target: target.write(data)
            eq("STAGE_SNAPSHOT_"+rel,data,dst.read_bytes())
        (out/"SNAPSHOT_MANIFEST.json").write_text(
            json.dumps({rel:sha(data) for rel,data in current.items()},indent=2)+"\n","utf8")
        for rel, data in plan["replacements"].items():
            if read(stage/rel,stage,"recheck_"+rel) != current[rel]:
                raise RuntimeError("P64_CONCURRENT_EDIT_"+rel)
            (stage/rel).write_bytes(data)
        for rel in plan["delete"]:
            f=stage/rel
            if read(f,stage,"delete_recheck_"+rel) != current[rel]:
                raise RuntimeError("P64_CONCURRENT_EDIT_"+rel)
            f.unlink()
        runner = build if build is not None else p9.smoke
        smoke = runner()
        if smoke.get("exitCode") != 0:
            raise RuntimeError("P64_BUILD_FAILED_CHECK_HIGHFLY_P9_LOG")
        result["mode"]="BUILD_GREEN_BROWSER_PENDING"
        result["sourceSha256"]={
            rel:sha(read(stage/rel,stage,rel)) for rel in REPLACE
        }
        STATUS.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
        return result
    except BaseException:
        for rel,data in current.items():
            dst=stage/rel
            ensure_safe(dst,stage,"rollback")
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(data)
        print("[HIGHFLY P64 CLEAN] RED: all affected source files rolled back to P71B; "
              "immutable snapshot retained. Build output/dist may need rebuilding.",
              file=sys.stderr)
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    options=parser.parse_args()
    print("[HIGHFLY P64 CLEAN] "+json.dumps(run(options.apply),indent=2,ensure_ascii=False))
