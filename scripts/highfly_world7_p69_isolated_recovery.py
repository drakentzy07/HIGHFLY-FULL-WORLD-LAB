#!/usr/bin/env python3
"""Recover exact P69 runtime sources into a NEW isolated private lab (port 4176).

P69 is a candidate, not browser-verified stable. Uses the immutable P71->P64
pre-restore snapshot and the P71 pre-change P69 main.ts, and preserves its
original P65/P66/P68/P69 CSS and skill modules byte-for-byte.

Dry run by default. --apply will NEVER modify the active P64 stage, historical
P43 lab, checkpoints, browser saves, or any original user library. Public assets
are symlinked from active P64; this must NEVER be publicly distributed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p69_fury_core as p69

WORK=ROOT/'.workspace'
STAGE=WORK/'highfly-origin-stage-p0'
LAB=WORK/'highfly-p69-restore-lab'
REPORT=WORK/'reports/highfly-world7/P69_ISOLATED_RESCUE.json'
ARCH=WORK/'reports/highfly-world7/p64-clean-recovery/pre_restore_snapshot'
MANIFEST=WORK/'reports/highfly-world7/p64-clean-recovery/SNAPSHOT_MANIFEST.json'
P64_STATUS=WORK/'reports/highfly-world7/p64-clean-recovery/P64_CLEAN_STATUS.json'
P69_STATUS=WORK/'reports/highfly-p69-fury-core/P69_STATUS.json'
P69_MAIN=WORK/'reports/highfly-world7/p71/backup/src/main.ts'
P69_BEFORE_MAIN=WORK/'reports/highfly-p69-fury-core/backups/src/main.ts'
OVERLAY=(
 'index.html',
 'src/game/mobile_controls.ts',
 'src/game/input.ts',
 'src/ui/hud/action_bar/mobile_action_ring_controller.ts',
 'src/ui/hud.ts',
 'src/sim/sim.ts',
 'src/sim/combat/auto_attack.ts',
)
CREATED=(
 'src/game/highfly_fury_skill_touch.ts',
 'src/sim/combat/highfly_manual_taps.ts',
 'public/highfly/p65.css',
 'public/highfly/p66_p67_premium.css',
 'public/highfly/p68_fury_recovery.css',
 'public/highfly/p69_fury_core.css',
)
SKIP_ROOT={'.git','.cache','dist','src','public','index.html','node_modules'}
PRIVATE_DIRS={'server','shared','packages','vendor'}
def hash_(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def require_safe(path:Path,base:Path,label:str,must_exist=True)->Path:
 if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
  raise RuntimeError('P69_UNSAFE_'+label+' '+str(path))
 if must_exist and not path.is_file():raise RuntimeError('P69_MISSING_'+label+' '+str(path))
 return path

def read(path:Path,base:Path,label:str)->bytes:
 return require_safe(path,base,label).read_bytes()

def preflight():
 if not STAGE.is_dir() or STAGE.is_symlink() or not WORK.is_dir():
  raise RuntimeError('P69_CURRENT_PRIVATE_STAGE_NOT_FOUND')
 if LAB.exists() or LAB.is_symlink():
  raise RuntimeError('P69_LAB_ALREADY_EXISTS_STOP_NO_OVERWRITE')
 if REPORT.exists() or REPORT.is_symlink():
  raise RuntimeError('P69_PREVIOUS_RESULT_EXISTS_STOP_NO_OVERWRITE')
 if (STAGE/'src').is_symlink() or not (STAGE/'src').is_dir():
  raise RuntimeError('P69_STAGE_SRC_UNSAFE')
 if (STAGE/'public').is_symlink() or not (STAGE/'public').is_dir():
  raise RuntimeError('P69_STAGE_PUBLIC_UNSAFE')
 nodes=STAGE/'node_modules'
 if not nodes.is_dir() or not (nodes/'vite/bin/vite.js').is_file():
  raise RuntimeError('P69_NODE_MODULES_MISSING')
 try:
  p64=json.loads(read(P64_STATUS,WORK,'p64_status'))
  p69s=json.loads(read(P69_STATUS,WORK,'p69_status'))
  hashes=json.loads(read(MANIFEST,WORK,'p64_snapshot_manifest'))
 except (ValueError,UnicodeError) as e:
  raise RuntimeError('P69_BAD_HISTORIC_STATUS_OR_MANIFEST') from e
 if (p64.get('mode')!='BUILD_GREEN_BROWSER_PENDING' or
     p69s.get('mode')!='BUILD_GREEN_BROWSER_PENDING'):
  raise RuntimeError('P69_HISTORY_NOT_BUILD_GREEN')
 p64_hashes=p64.get('sourceSha256',{})
 for rel,digest in p64_hashes.items():
  f=STAGE/rel
  actual=hash_(read(f,STAGE,'p64_source_'+rel))
  if actual!=digest:
   # Entry V2 modifies only CSS/JS, not source; refuse any unknown code drift.
   raise RuntimeError('P69_P64_STAGE_CHANGED_'+rel)
 restored={}
 for rel in OVERLAY+CREATED:
  f=ARCH/rel
  data=read(f,WORK,'historical_snapshot_'+rel)
  if hashes.get(rel)!=hash_(data):
   raise RuntimeError('P69_HISTORIC_SNAPSHOT_HASH_MISMATCH_'+rel)
  restored[rel]=data
 main=read(P69_MAIN,WORK,'p69_original_main')
 original=read(P69_BEFORE_MAIN,WORK,'p69_prepatch_main').decode('utf8')
 if main != p69.patch_main(original).encode('utf8'):
  raise RuntimeError('P69_EXACT_MAIN_TRANSFORM_MISMATCH')
 if b'HIGHFLY_P69_FURY_CORE' not in main:
  raise RuntimeError('P69_EXPECTED_FURY_CODE_MISSING')
 # The previous rollback verified P71->P69 source chain; ensure P69
 # components weren't subsequently changed before snapshot creation.
 for rel,method in (
   ('src/ui/hud/action_bar/mobile_action_ring_controller.ts',p69.patch_ring),
   ('src/ui/hud.ts',p69.patch_hud),
   ('src/sim/sim.ts',p69.patch_sim),
   ('src/sim/combat/auto_attack.ts',p69.patch_auto),
 ):
  prev=WORK/'reports/highfly-p69-fury-core/backups'/rel
  original_bytes=read(prev,WORK,'pre_p69_'+rel)
  if restored[rel] != method(original_bytes.decode('utf8')).encode('utf8'):
   raise RuntimeError('P69_HISTORIC_COMPONENT_DRIFT_'+rel)
 for rel,original_text in (
    ('src/game/highfly_fury_skill_touch.ts',p69.TOUCH_CODE),
    ('src/sim/combat/highfly_manual_taps.ts',p69.TAPS_CODE),
    ('public/highfly/p69_fury_core.css',p69.CSS_CODE)):
  if restored[rel]!=original_text.encode('utf8'):
   raise RuntimeError('P69_HISTORIC_CREATED_FILE_DRIFT_'+rel)
 if b'highfly/p69_fury_core.css' not in restored['index.html']:
  raise RuntimeError('P69_HTML_MISSING_CSS_LINK')
 for rel in CREATED:
  if (STAGE/rel).exists() or (STAGE/rel).is_symlink():
   raise RuntimeError('P69_ACTIVE_STAGE_HAS_OLD_OVERLAY_'+rel)
 if not (STAGE/'public/highfly').is_dir():
  raise RuntimeError('P69_STAGE_HIGHFLY_PUBLIC_MISSING')
 restored['src/main.ts']=main
 return restored,p64,p69s

def apply():
 restored,p64,p69s=preflight()
 LAB.mkdir(parents=True,exist_ok=False)
 # Copy source so all P69 edits are completely isolated from P64.
 # Public media and node_modules are symlinked, not copied or distributed.
 shutil.copytree(STAGE/'src',LAB/'src',symlinks=False)
 for file in STAGE.iterdir():
  if file.name in SKIP_ROOT or file.name.startswith('.hf_manual_backup'):continue
  dest=LAB/file.name
  if dest.exists() or dest.is_symlink():continue
  if file.is_file() and not file.is_symlink() and file.stat().st_size<8_000_000:
   shutil.copy2(file,dest)
  elif file.is_dir() and not file.is_symlink() and file.name in PRIVATE_DIRS:
   dest.symlink_to(file,target_is_directory=True)
 original_scripts=WORK/'claudecraft-v0.44.7/scripts'
 if not (LAB/'scripts').exists() and original_scripts.is_dir():
  (LAB/'scripts').symlink_to(original_scripts,target_is_directory=True)
 (LAB/'node_modules').symlink_to(STAGE/'node_modules',target_is_directory=True)
 (LAB/'public').mkdir()
 for item in (STAGE/'public').iterdir():
  if item.name=='highfly':continue
  (LAB/'public'/item.name).symlink_to(item,target_is_directory=item.is_dir())
 (LAB/'public/highfly').mkdir()
 for item in (STAGE/'public/highfly').iterdir():
  if item.name in {Path(x).name for x in CREATED if x.startswith('public/highfly/')}:
   raise RuntimeError('P69_STAGE_PUBLIC_OVERLAY_UNEXPECTED_'+item.name)
  (LAB/'public/highfly'/item.name).symlink_to(item,target_is_directory=item.is_dir())
 for rel,blob in restored.items():
  f=LAB/rel
  if f.is_symlink():raise RuntimeError('P69_LAB_FILE_LINK_'+rel)
  f.parent.mkdir(exist_ok=True,parents=True)
  f.write_bytes(blob)
  if hash_(f.read_bytes())!=hash_(blob):
   raise RuntimeError('P69_RESTORED_FILE_VERIFICATION_FAILED_'+rel)
 state={
  'phase':'P69_HISTORIC_ISOLATED_SOURCE_RECOVERY',
  'mode':'APPLY',
  'sourceP69':'original historic P69 snapshot and pre-P71 main',
  'destination':str(LAB),'port':4176,'stageP64Modified':False,
  'labP43Modified':False,'saveModified':False,
  'sourceFilesRestored':sorted(restored),
  'sourceHashes':{rel:hash_(blob) for rel,blob in restored.items()},
  'serverAssetsSharedWithP64':True,
  'commercialReleaseApproved':False,
  'browserVerified':False,
  'note':'P69 had a build-green status, not verified gameplay. Keep port private, do not publish.'
 }
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf8')
 return state

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--apply',action='store_true')
 args=parser.parse_args()
 if args.apply:
  result=apply()
 else:
  restored,p64,p69s=preflight()
  result={'phase':'P69_HISTORIC_ISOLATED_SOURCE_RECOVERY','mode':'DRY_RUN',
          'sourcesReady':sorted(restored),'privatePreviewPort':4176,
          'willCreate':str(LAB),'willModifyActiveP64':False,
          'browserVerified':False,'commercialReleaseApproved':False}
 print('[HIGHFLY P69 ISOLATED] '+json.dumps(result,indent=2,ensure_ascii=False))
