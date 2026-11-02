#!/usr/bin/env python3
"""HIGHFLY WORLD7: restore ClaudeCraft native class creation, repair only touch wiring.

Removes DrakenLAB P71/P71B through verified P71 backup; does NOT undo P68/P69
other than disabling P69 manual ATK in favor of
native ATK, and making monster screen taps target-only. Leaves the existing 9-class selector and player editor untouched; no new gate. Honors P41 save
if installed and upgrades the previous single-name save slot to per-name slots.
Never touches the original pin, models, abilities, quest data, server or classes.
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
BASE = "backup/src/main.ts"
P71 = "P71_STATUS.json"
P71B = "P71B_STATUS.json"
MODS = ("src/highfly/drakenlab_p71.ts", "src/highfly/drakenlab_p71.css")
MAIN = "src/main.ts"
INDEX = "index.html"
SAVE = "src/game/highfly_offline_saves.ts"
NEW_CSS = "public/highfly/classic_controls.css"
MARK = "HIGHFLY_CLASSIC_RESTORE_20261102"
RESTORE_BACKUP = "classic_restore_backup"
STATUS = "CLASSIC_RESTORE_STATUS.json"

CSS = """
/* HIGHFLY CLASSIC RESTORE: use ONE existing native passive control, not
   stacked glyphs and circles. Preserve actual spellbook click binding. */
body.mobile-touch.game-active #mobile-action-ring #mobile-passive::before {
  content:none!important;display:none!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive::after {
  content:"PASIVA"!important;display:block!important;
  position:static!important;inset:auto!important;
  width:auto!important;height:auto!important;border:0!important;
  outline:0!important;border-radius:0!important;
  box-shadow:none!important;background:none!important;
  transform:none!important;pointer-events:none!important;
  color:#eee3ff!important;font:800 8px/1 system-ui!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive {
  display:flex!important;align-items:center!important;justify-content:center!important;
  background:radial-gradient(circle at 35% 25%,#392659,#10132e)!important;
  isolation:isolate;pointer-events:auto!important;
}
""".lstrip()

def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe(path: Path, base: Path) -> bool:
    return not path.is_symlink() and path.resolve().is_relative_to(base.resolve())

def read_file(path: Path, base: Path) -> bytes:
    if not safe(path, base) or not path.is_file():
        raise RuntimeError("CLASSIC_REQUIRED_FILE_MISSING_OR_UNSAFE " + str(path))
    return path.read_bytes()

def once(s: str, before: str, after: str, label: str) -> str:
    n = s.count(before)
    if n != 1:
        raise RuntimeError("CLASSIC_ANCHOR_DRIFT_" + label + "_COUNT_" + str(n))
    return s.replace(before, after, 1)

def patch_original(main: str, index: str, saves: str | None) -> tuple[str,str,str | None]:
    if "HIGHFLY_WORLD7_P71_DRAKENLAB" in main:
        raise RuntimeError("CLASSIC_BACKUP_CONTAINS_DRAKENLAB")
    # REUSE FIRST: The 9-class selector and creation UI already existed in
    # the private HIGHFLY stage before P71. This rollback MUST NOT alter them.
    # In particular, do not assume the exact upstream offlineAvailable source:
    # P41 and subsequent changes may have customized the local-only gate.
    # ClaudeCraft stepPlayerMotion (sim/player_motion.ts) uses right=(-cos f,+sin f).
    # P69 already matches that native convention. Do not invert world X/Z again!
    native_heading = (
        "const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);\n"
        "        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);"
    )
    if main.count(native_heading) != 1:
        raise RuntimeError("CLASSIC_JOYSTICK_NATIVE_HEADING_DRIFT")
    main = once(
        main,
        "hud.onHighflyBasicTap = () => highflyBasicTap();",
        "// " + MARK + ": fall back to P68 native button ATK; do not queue P69 manual tap.\n"
        "  hud.onHighflyBasicTap = null;",
        "NATIVE_ATK_BUTTON")
    main = once(
        main,
        "      highflyBasicTap(enemy.id);\n      return true;",
        "      // " + MARK + ": world touch selects ONLY; ATK must be pressed deliberately.\n"
        "      world.targetEntity(enemy.id);\n      return true;",
        "WORLD_TOUCH_TARGET_ONLY")
    index = once(index, "</head>",
        '<link rel="stylesheet" href="/highfly/classic_controls.css" />\n</head>',
        "PASSIVE_CSS_LINK")
    if saves is not None:
        if "HIGHFLY_P41_OFFLINE_SAVE" not in saves:
            raise RuntimeError("CLASSIC_EXISTING_SAVES_UNKNOWN_FORMAT")
        saves = once(
            saves,
            "const KEY='highfly.origin.offline.v1';",
            "const KEY='highfly.origin.offline.v1';\n"
            "// " + MARK + ": each character name owns its own offline save slot.\n"
            "const slotKey=(name:string)=>KEY+':'+encodeURIComponent(name.toLowerCase());",
            "SAVE_NAME_SLOT")
        saves = once(
            saves,
            "const raw=localStorage.getItem(KEY);",
            "const raw=localStorage.getItem(slotKey(name)) ?? localStorage.getItem(KEY);",
            "SAVE_LEGACY_READ")
        saves = once(
            saves,
            "localStorage.setItem(KEY,json);return s;",
            "localStorage.setItem(slotKey(name),json);return s;",
            "SAVE_NAMESPACED_WRITE")
    return main,index,saves

def plan(stage: Path=STAGE, out: Path=OUT, repo: Path=ROOT) -> dict:
    if not safe(stage, repo / ".workspace") or not stage.is_dir():
        raise RuntimeError("CLASSIC_UNSAFE_STAGE")
    if not safe(out, repo / ".workspace") or not out.is_dir():
        raise RuntimeError("CLASSIC_UNSAFE_REPORT_DIR")
    after = out / STATUS
    if after.exists() or after.is_symlink():
        if not safe(after, out):
            raise RuntimeError("CLASSIC_UNSAFE_STATUS")
        status = json.loads(after.read_text("utf8"))
        if status.get("mode") != "BUILD_GREEN_BROWSER_PENDING":
            raise RuntimeError("CLASSIC_UNKNOWN_PREVIOUS_STATUS")
        main = stage / MAIN
        if (digest_bytes(read_file(main, stage)) != status.get("mainSha256") or
                any((stage / m).exists() or (stage / m).is_symlink() for m in MODS)):
            raise RuntimeError("CLASSIC_ALREADY_RESTORED_BUT_STAGE_DRIFT")
        return {"already": True, "status": status}
    status_a = json.loads(read_file(out / P71, out).decode("utf8"))
    status_b = json.loads(read_file(out / P71B, out).decode("utf8"))
    if (status_a.get("mode") != "BUILD_GREEN_BROWSER_PENDING" or
            status_b.get("mode") != "BUILD_GREEN_BROWSER_PENDING"):
        raise RuntimeError("CLASSIC_P71_NOT_INSTALLED")
    current_main = read_file(stage / MAIN, stage)
    if digest_bytes(current_main) != status_b.get("updatedSha256"):
        raise RuntimeError("CLASSIC_MAIN_HASH_CHANGED_SINCE_P71B")
    prior = read_file(out / BASE, out)
    before_b = read_file(out / "backup/P71B_BEFORE_CLASS_FIELD_FIX.ts", out)
    if digest_bytes(before_b) != status_a.get("sourceHashes", {}).get(MAIN):
        raise RuntimeError("CLASSIC_P71B_BACKUP_INTEGRITY")
    if "HIGHFLY_WORLD7_P71_DRAKENLAB" in prior.decode("utf8"):
        raise RuntimeError("CLASSIC_P71_BACKUP_NOT_NATIVE")
    module_bytes = {}
    for module in MODS:
        raw = read_file(stage / module, stage)
        if digest_bytes(raw) != status_a.get("sourceHashes", {}).get(module):
            raise RuntimeError("CLASSIC_MODULE_HASH_CHANGED " + module)
        module_bytes[module] = raw
    idx = read_file(stage / INDEX, stage)
    save_path = stage / SAVE
    save = read_file(save_path, stage) if save_path.exists() else None
    if save is None or "HIGHFLY_P41_OFFLINE_SAVE" not in save.decode("utf8"):
        raise RuntimeError("CLASSIC_P41_NAMED_SAVE_MISSING_REVIEW_REQUIRED")
    css_path = stage / NEW_CSS
    if css_path.exists() or css_path.is_symlink():
        raise RuntimeError("CLASSIC_CSS_EXISTS_UNRELATED")
    # Retry a failed build only if every immutable backup equals the rolled-back stage.
    existing_backup = out / RESTORE_BACKUP
    if existing_backup.is_symlink() or (existing_backup.exists() and not existing_backup.is_dir()):
        raise RuntimeError("CLASSIC_RESTORE_BACKUP_UNSAFE")
    if existing_backup.exists():
        for rel, raw in {MAIN:current_main, INDEX:idx, SAVE:save, **module_bytes}.items():
            earlier = read_file(existing_backup / rel, existing_backup)
            if earlier != raw:
                raise RuntimeError("CLASSIC_RETRY_BACKUP_MISMATCH " + rel)
    new_main,new_index,new_save = patch_original(
        prior.decode("utf8"), idx.decode("utf8"), save.decode("utf8"))
    if "HIGHFLY_P69_FURY_CORE" not in new_main or "HIGHFLY_P41_OFFLINE_SAVE" not in new_main:
        raise RuntimeError("CLASSIC_ORIGINAL_FURY_OR_SAVE_MISSING")
    return {"already": False,
        "sources":{MAIN: current_main, INDEX: idx, SAVE: save, **module_bytes},
        "updates":{MAIN:new_main.encode(), INDEX:new_index.encode(),
                   SAVE:new_save.encode(), NEW_CSS:CSS.encode()},
        "deletes":MODS, "stage":stage, "out":out}

def run(apply=False, *, stage=STAGE, out=OUT, repo=ROOT, build=None) -> dict:
    # P9 preflight confirms original pin, stage manifest, Vite availability.
    p9.preflight(p9.ORIGINAL,stage,p9.REPORT)
    checked=plan(stage,out,repo)
    if checked["already"]:
        return checked["status"]
    result = {
        "phase": "HIGHFLY_CLASSIC_RESTORE",
        "mode": "DRY_RUN",
        "nativeNineClassSelector": "PRESERVED_EXISTING_NO_REWRITE",
        "drakenlabRemoved": False,
        "nativeAtkButton": True,
        "touchWorldOnlyTargets": True,
        "joystickAngleMapping": "P69_NATIVE_SIGN_PRESERVED_FURTHER_RUNTIME_QA_NEEDED",
        "passiveButton": "ONE_NATIVE_BUTTON_STYLED",
        "offlineSaveSlot": "BY_NAME_WITH_LEGACY_FALLBACK",
        "sourceOriginalUnmodified": True,
        "gameplayBrowserVerified": False,
    }
    if not apply:
        return result
    bdir = out / RESTORE_BACKUP
    if bdir.is_symlink():
        raise RuntimeError("CLASSIC_RESTORE_BACKUP_UNSAFE")
    if not bdir.exists():
        bdir.mkdir(parents=True, exist_ok=False)
    sources = checked["sources"]
    written = []
    try:
        for rel, data in sources.items():
            backup = bdir / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            if backup.exists():
                if read_file(backup, bdir) != data:
                    raise RuntimeError("CLASSIC_BACKUP_OVERWRITE_DENIED " + rel)
            else:
                with backup.open("xb") as file:
                    file.write(data)
            if digest_bytes(backup.read_bytes()) != digest_bytes(data):
                raise RuntimeError("CLASSIC_BACKUP_FAILED " + rel)
        for rel, data in checked["updates"].items():
            target = stage / rel
            if not safe(target, stage):
                raise RuntimeError("CLASSIC_UNSAFE_PATCH_TARGET " + rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            if rel == NEW_CSS:
                with target.open("xb") as file:
                    file.write(data)
            else:
                if read_file(target, stage) != sources[rel]:
                    raise RuntimeError("CLASSIC_CONCURRENT_CHANGE " + rel)
                target.write_bytes(data)
            written.append(rel)
        for rel in checked["deletes"]:
            target = stage / rel
            if read_file(target, stage) != sources[rel]:
                raise RuntimeError("CLASSIC_CONCURRENT_CHANGE " + rel)
            target.unlink()
        runner = build if build is not None else p9.smoke
        bundled = runner()
        if bundled.get("exitCode") != 0:
            raise RuntimeError("CLASSIC_PRIVATE_BUILD_FAILED_SEE_P9_LOG")
        result["mode"] = "BUILD_GREEN_BROWSER_PENDING"
        result["drakenlabRemoved"] = True
        result["mainSha256"] = digest_bytes(read_file(stage / MAIN, stage))
        (out / STATUS).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", "utf8")
        return result
    except BaseException:
        # Recover all original P71B sources in place, including DrakenLAB modules.
        for rel, data in sources.items():
            (stage / rel).parent.mkdir(parents=True, exist_ok=True)
            (stage / rel).write_bytes(data)
        css = stage / NEW_CSS
        if css.is_file() and not css.is_symlink():
            css.unlink()
        print("[HIGHFLY CLASSIC] RED: stage sources restored; preexisting P71 backups retained.",
              file=sys.stderr)
        raise

if __name__ == "__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--apply", action="store_true")
    opt=args.parse_args()
    print("[HIGHFLY CLASSIC] "+json.dumps(run(opt.apply),indent=2,ensure_ascii=False))
