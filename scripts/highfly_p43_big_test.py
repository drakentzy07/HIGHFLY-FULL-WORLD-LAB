#!/usr/bin/env python3
"""P43 — single guarded P39B->P42 staging run and ONE private full build.

P39B must already be APPLIED, as user confirmed GREEN; never reapply.
P40 icons, P41 offline save and P42 Spanish/Hunter are dry-run checked first.
Stage source checkpoint is saved BEFORE any changes. On any apply/build error,
restore original stage source and remove only files this installer created.
No deployment, no modification of original v0.44.7 or public repo assets.
"""
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p40_icon_art as p40
import highfly_p41_offline_save as p41
import highfly_p42_spanish_hunter as p42
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p43-big-test"
CHECKPOINT=ROOT/".workspace/checkpoints/HIGHFLY-P39B-BEFORE-P43.tar.gz"

def preflight():
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 media=(STAGE/"src/render/assets/media.ts").read_text(encoding="utf8")
 index=(STAGE/"src/render/characters/index.ts").read_text(encoding="utf8")
 if "HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD" not in media:
  raise RuntimeError("P43_REQUIRES_ALREADY_APPLIED_P39B")
 if "HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK" not in index:
  raise RuntimeError("P43_NPC_SAFETY_NET_MISSING")
 if "HIGHFLY_P39A_CC0_CRAB_PRELOAD" not in media:
  raise RuntimeError("P43_CRAB_REPAIR_MISSING")
 if not (STAGE/"public/models/biome/hex_target.glb").is_file():
  raise RuntimeError("P43_P38_DUMMY_NOT_PRESENT")

def dry_checks():
 return [p40.run(False),p41.run(False),p42.run(False)]

def save_checkpoint():
 if CHECKPOINT.exists() or CHECKPOINT.is_symlink():
  raise RuntimeError("P43_CHECKPOINT_ALREADY_EXISTS")
 CHECKPOINT.parent.mkdir(parents=True,exist_ok=True)
 with tarfile.open(CHECKPOINT,mode="w:gz") as archive:
  for relative in ("src","index.html"):
   archive.add(STAGE/relative,arcname=relative,recursive=True)

def rollback():
 if not CHECKPOINT.is_file():raise RuntimeError("P43_MISSING_CHECKPOINT")
 # Restore only the source tree and HTML backed up by this run, never the
 # user's owned media; P40's new generated SVG/JS and P41/P42 JS are removed.
 with tarfile.open(CHECKPOINT,mode="r:gz") as archive:
  members=archive.getmembers()
  for member in members:
   dest=(STAGE/member.name).resolve()
   dest.relative_to(STAGE.resolve())
   if member.issym() or member.islnk() or member.isdev():
    raise RuntimeError("P43_CHECKPOINT_UNSAFE_MEMBER")
  source=STAGE/"src"
  if source.is_symlink():raise RuntimeError("P43_STAGE_SRC_SYMLINK")
  shutil.rmtree(source)
  (STAGE/"index.html").unlink(missing_ok=True)
  archive.extractall(STAGE,filter="data")
 for path in (STAGE/p40.JS_PATH,STAGE/p42.JS_PATH):
  path.unlink(missing_ok=True)
 (STAGE/p41.NEW).unlink(missing_ok=True)
 for url in p40.ART:
  p=(STAGE/"public/highfly-icons"/url.replace("/","__").replace(".webp",".svg"))
  p.unlink(missing_ok=True)
 for r in (p40.OUT,p41.OUT,p42.OUT):
  # these were guaranteed not previously applied by the dry-run validation
  if r.exists():shutil.rmtree(r)

def report(mode,stages,extra=None):
 OUT.mkdir(parents=True,exist_ok=True)
 status={"phase":"HIGHFLY_P43_BIG_BANG_P39B_TO_P42","mode":mode,
   "p39bPreviouslyApplied":True,
   "phases":stages,"checkpoint":str(CHECKPOINT),
   "originalAndGameplayUntouched":True,
   "fullWorldAndSaveBrowserVerified":False,
   "timestampUtc":datetime.now(timezone.utc).isoformat()}
 if extra:status.update(extra)
 (OUT/"P43_INTEGRATION_STATUS.json").write_text(json.dumps(status,indent=2)+"\n")
 print("[HIGHFLY] P43 INTEGRATION: "+json.dumps(status,ensure_ascii=False))
 return status

def run(apply=False):
 preflight()
 checks=dry_checks()
 if not apply:
  return report("DRY_RUN",[{"phase":x["phase"],"mode":x["mode"]} for x in checks])
 save_checkpoint()
 phase="not-started"
 try:
  phase="P40 original icons"
  p40.run(True)
  phase="P41 offline save"
  p41.run(True)
  phase="P42 Spanish and Hunter"
  p42.run(True)
  phase="P9 private Vite build"
  subprocess.run(
   [sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
   cwd=ROOT,check=True)
 except Exception as exc:
  try:
   rollback()
   restored=True
  except Exception as rollback_error:
   restored=False
   print("[HIGHFLY] P43 ROLLBACK FAILED:",str(rollback_error),file=sys.stderr)
  report("RED_ROLLBACK",[],{"failedPhase":phase,"error":str(exc),
      "stageRolledBack":restored})
  raise
 return report("BUILT_NOT_BROWSER_VERIFIED",[
  {"phase":"P39B monsters","status":"PREVIOUSLY_APPLIED"},
  {"phase":"P40 inventory icons","status":"APPLIED"},
  {"phase":"P41 offline save","status":"APPLIED"},
  {"phase":"P42 Spanish Hunter selector","status":"APPLIED"},
  {"phase":"P9 build","status":"PASS"}])

if __name__=="__main__":
 cli=argparse.ArgumentParser()
 cli.add_argument("--apply",action="store_true")
 run(cli.parse_args().apply)
