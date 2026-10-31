#!/usr/bin/env python3
"""P45D: one Codespaces invocation to run P44 if needed + P45A/B/C + build.

All phases dry-run BEFORE writing. Creates a local compressed source checkpoint.
If any install or build fails, reverts the stage code and deletes only new
assets produced by THIS invocation, preserving private KayKit, game saves,
and the user-verified stable P43 build. Never publishes.
"""
import argparse,json,shutil,subprocess,sys,tarfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p44_world_visuals as p44
import highfly_p45a_eastbrook_guard as a
import highfly_p45b_branding as b
import highfly_p45c_fury_foundation as c
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p45-big-batch"
CHECKPOINT=ROOT/".workspace/checkpoints/HIGHFLY-P43-BEFORE-P45.tar.gz"
WOLF=STAGE/"public/models/creatures/wolf.glb"
P44_ICON_FILES=[STAGE/"public/highfly-icons"/v for v in p44.ICONS.values()]
P45_ART_FILES=[STAGE/b.SCRIPT,STAGE/b.ART,STAGE/c.CSS_FILE]
MARK="HIGHFLY_P44_ORIGINAL_WOLF"

def already_p44():
 manifest=(STAGE/"src/render/characters/manifest.ts").read_text(encoding="utf8")
 has=MARK in manifest
 # Avoid treating a partially applied earlier P44 as a completed patch.
 if has:
  for rel in (p44.FILES[1],p44.FILES[2],p44.FILES[3],p44.FILES[4]):
   if MARK not in (STAGE/rel).read_text(encoding="utf8"):
    raise RuntimeError("P45D_P44_PARTIALLY_APPLIED "+rel)
  if any(not file.is_file() for file in P44_ICON_FILES):
   raise RuntimeError("P45D_P44_ICONS_PARTIAL")
 return has

def preflight():
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 if not (STAGE/"src/game/highfly_offline_saves.ts").is_file():
  raise RuntimeError("P45D_P41_OFFLINE_SAVES_MISSING")
 if "HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD" not in (
   STAGE/"src/render/assets/media.ts").read_text(encoding="utf8"):
  raise RuntimeError("P45D_P39B_MOB_REPAIR_MISSING")
 return already_p44()

def create_checkpoint():
 if CHECKPOINT.exists() or CHECKPOINT.is_symlink():
  raise RuntimeError("P45D_CHECKPOINT_ALREADY_EXISTS")
 CHECKPOINT.parent.mkdir(parents=True,exist_ok=True)
 with tarfile.open(CHECKPOINT,"w:gz") as tar:
  for rel in ("src","index.html","public/highfly_p40_icons.js"):
   target=STAGE/rel
   if not target.is_file() and not target.is_dir():raise RuntimeError("P45D_CHECKPOINT_MISSING "+rel)
   tar.add(target,arcname=rel,recursive=True)

def restore_checkpoint():
 if not CHECKPOINT.is_file():raise RuntimeError("P45D_NO_CHECKPOINT")
 # Locally created snapshot and reject every unsafe member before extract.
 with tarfile.open(CHECKPOINT,"r:gz") as tar:
  members=tar.getmembers()
  for member in members:
   if member.issym() or member.islnk() or member.isdev() or member.name.startswith('/'):
    raise RuntimeError("P45D_UNSAFE_CHECKPOINT_MEMBER")
   if any(part in ("..","") for part in Path(member.name).parts):
    raise RuntimeError("P45D_UNSAFE_CHECKPOINT_PATH")
   if not (STAGE/member.name).resolve().is_relative_to(STAGE.resolve()):
    raise RuntimeError("P45D_UNSAFE_CHECKPOINT_TRAVERSAL")
  src=STAGE/"src"
  if src.is_symlink():raise RuntimeError("P45D_STAGE_SRC_SYMLINK")
  shutil.rmtree(src)
  (STAGE/"index.html").unlink(missing_ok=True)
  (STAGE/"public/highfly_p40_icons.js").unlink(missing_ok=True)
  tar.extractall(STAGE)

def clean_newfiles(need_p44,oldwolf):
 for f in P45_ART_FILES:
  f.unlink(missing_ok=True)
 if need_p44:
  for f in P44_ICON_FILES:f.unlink(missing_ok=True)
  if not oldwolf:WOLF.unlink(missing_ok=True)
 # Report-only backup dirs created by these phases; no previous applied
 # script should be in this list due to dry-run rejection before snapshots.
 for folder in [a.OUT,b.OUT,c.OUT]+([p44.OUT] if need_p44 else []):
  if folder.exists():shutil.rmtree(folder)

def status(mode,**kwargs):
 OUT.mkdir(parents=True,exist_ok=True)
 result={"phase":"HIGHFLY_P45_BIG_BATCH","mode":mode,
  "originalAndPrivateZipUntouched":True,"browserVerified":False,
  "checkpoint":str(CHECKPOINT),
  "timestampUtc":datetime.now(timezone.utc).isoformat(),**kwargs}
 (OUT/"P45D_STATUS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print("[HIGHFLY] P45D: "+json.dumps(result,ensure_ascii=False))
 return result

def run(apply=False):
 has_p44=preflight()
 checks=[]
 if not has_p44:checks.append(p44.run(False))
 checks.extend([a.run(False),b.run(False),c.run(False)])
 phases=[x["phase"] for x in checks]
 if not apply:return status("DRY_RUN",p44PreviouslyApplied=has_p44,dryChecks=phases)
 old_wolf=WOLF.is_file()
 create_checkpoint()
 part="nothing"
 try:
  if not has_p44:
   part="P44 wolf + Madreperla + Eastbrook NPCs"
   p44.run(True)
  part="P45A Eastbrook giant object guard"
  a.run(True)
  part="P45B HIGHFLY splash + Hunter appearance"
  b.run(True)
  part="P45C FURY mobile foundation and icon audit"
  c.run(True)
  part="P9 Vite private build"
  subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
    cwd=str(ROOT),check=True)
 except Exception as exc:
  recovered=False
  try:
   restore_checkpoint()
   clean_newfiles(not has_p44,old_wolf)
   recovered=True
  except Exception as rollback_err:
   print("[HIGHFLY] P45D ROLLBACK FAILED",rollback_err,file=sys.stderr)
  status("RED_ROLLBACK",failedPhase=part,error=str(exc),
         stageRecovered=recovered,p44PreviouslyApplied=has_p44)
  raise
 return status("BUILD_GREEN_NOT_BROWSER_VERIFIED",
   installed=phases,onePrivateBuild=True,p44PreviouslyApplied=has_p44,
   eastbrookGiantVisualGuard=True,hunterBrandingAndSkins=True,
   androidHudStyling=True,furyDamageAndAnimationWired=False,
   inventoryPremiumArtFullyRestored=False)

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--apply",action="store_true")
 args=parser.parse_args();run(args.apply)
