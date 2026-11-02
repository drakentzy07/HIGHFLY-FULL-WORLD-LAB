#!/usr/bin/env python3
"""HIGHFLY P72: reconstruct last P71B-era game minus DrakenLAB, privately.

Recover verified P71B pre-P64 rollback source snapshot and replace ONLY the
P71 DrakenLAB-modified main entry with its exact independently backed-up
pre-DrakenLAB P69 source. Preserve P65-P69 combat/HUD/FURY, original RPG world,
NPC, loot and all existing resources. Native 9-class filters/Offline routing
are restored in the independent lab; only presentation/routing, no Sim changes.

Default --dry-run; --apply creates NEW .workspace/highfly-p71b-no-drakenlab-lab.
NEVER overwrite/mutate active P64, P69, P43, game saves, original or checkpoint.
Does not claim GLB/license or playable-browser verification.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
STAGE=WORK/'highfly-origin-stage-p0'
SNAP=WORK/'reports/highfly-world7/p64-clean-recovery/pre_restore_snapshot'
SNAP_HASHES=WORK/'reports/highfly-world7/p64-clean-recovery/SNAPSHOT_MANIFEST.json'
P64_STATUS=WORK/'reports/highfly-world7/p64-clean-recovery/P64_CLEAN_STATUS.json'
P71_STATUS=WORK/'reports/highfly-world7/p71/P71_STATUS.json'
P71B_STATUS=WORK/'reports/highfly-world7/p71/P71B_STATUS.json'
P71B_BEFORE=WORK/'reports/highfly-world7/p71/backup/P71B_BEFORE_CLASS_FIELD_FIX.ts'
P69_MAIN=WORK/'reports/highfly-world7/p71/backup/src/main.ts'
LAB=WORK/'highfly-p71b-no-drakenlab-lab'
REPORT=WORK/'reports/highfly-world7/P72_P71B_NO_DRAKENLAB.json'
CLEAN_BASE=WORK/'highfly-p69-restore-lab'
CLASSES=('warrior','paladin','hunter','rogue','priest','shaman','mage','warlock','druid')
SKIP_ROOT={'.git','.cache','dist','src','public','index.html','node_modules'}
OTHER_DIRS={'server','shared','packages','vendor'}
DRAKEN_FILES={'src/highfly/drakenlab_p71.ts','src/highfly/drakenlab_p71.css'}
REMOVABLE_LINKS=(
 '<script defer src="/highfly_p42_hunter.js"></script>',
 '<script defer src="/highfly_p45_branding.js"></script>',
 '<script defer src="/highfly/p47.js"></script>',
 '<link rel="stylesheet" href="/highfly/p47.css" />',
)
REMOVABLE_STYLES=(
 r'<style id="highfly-p42-hunter-styles">\s*.*?</style>\s*',
 r'<style id="highfly-p45-brand-css">\s*.*?</style>\s*',
)
MEDIA_SAMPLES=(
 'models/chars/players/knight.glb',
 'models/chars/players/warrior_fury_anims.glb',
 'models/chars/players/knight_hit_variety_anims.glb',
 'models/weapons/sword_1handed.glb',
 'ui/classes/warrior.webp'
)

def digest(blob:bytes)->str:
 return hashlib.sha256(blob).hexdigest()

def checked(path:Path,base:Path,*,kind='file')->bytes:
 if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
  raise RuntimeError('P72_UNSAFE_'+str(path))
 if kind=='file':
  if not path.is_file():raise RuntimeError('P72_MISSING_'+str(path))
  return path.read_bytes()
 if not path.is_dir():raise RuntimeError('P72_MISSING_DIR_'+str(path))
 return b''

def json_checked(path:Path,base:Path)->dict:
 val=json.loads(checked(path,base).decode('utf8'))
 if not isinstance(val,dict):raise RuntimeError('P72_INVALID_JSON_DICT_'+str(path))
 return val

def exact_once(text:str,old:str,new:str,label:str)->str:
 n=text.count(old)
 if n!=1:raise RuntimeError('P72_EXPECTED_ONE_'+label+'_FOUND_'+str(n))
 return text.replace(old,new,1)

def native_entry(original_html:str,p69_main:str):
 if 'HIGHFLY_WORLD7_P71_DRAKENLAB' in original_html+p69_main:
  raise RuntimeError('P72_DRAKENLAB_NOT_REMOVED')
 if 'HIGHFLY_P69_FURY_CORE' not in original_html or 'HIGHFLY_P69_FURY_CORE' not in p69_main:
  raise RuntimeError('P72_P69_FURY_MARKER_MISSING')
 for cls in CLASSES:
  if len(re.findall(r'<button\b[^>]*data-class="'+cls+r'"',original_html))<1:
   raise RuntimeError('P72_NINE_CLASSES_MARKUP_MISSING_'+cls)
 html=original_html
 removed=[]
 for pattern in REMOVABLE_STYLES:
  new,n=re.subn(pattern,'',html,count=1,flags=re.S)
  if n:removed.append('hunter_brand_style')
  html=new
 for link in REMOVABLE_LINKS:
  if html.count(link)>1:raise RuntimeError('P72_DUPLICATED_HIDER_LINK_'+link)
  if link in html:html=html.replace(link,'',1);removed.append(link)
 if not any('p42_hunter' in x for x in removed) and 'highfly-p42-hunter-styles' in html:
  raise RuntimeError('P72_P42_HIDER_STILL_PRESENT')
 gate=re.compile(r'(?m)^([ \t]*)const[ \t]+offlineAvailable(?:[ \t]*:[ \t]*boolean)?[ \t]*=[ \t]*([\s\S]{0,400}?);[ \t]*(?=\r?$)')
 matches=list(gate.finditer(p69_main))
 if len(matches)!=1:raise RuntimeError('P72_OFFLINE_GATE_DRIFT_'+str(len(matches)))
 if 'handleOfflineSelect' not in p69_main or 'HIGHFLY_P41_OFFLINE_SAVE' not in p69_main:
  raise RuntimeError('P72_ORIGINAL_OFFLINE_AND_SAVE_MISSING')
 match=matches[0]
 main=p69_main[:match.start()]+match.group(1)+(
  "const offlineAvailable = import.meta.env.DEV; // P72: private native Offline QA"
 )+p69_main[match.end():]
 # Prefer the real offline mode in this PRIVATE Vite server only.
 main=exact_once(main,"    applyServerMode('online');",
  "    applyServerMode(offlineAvailable ? 'offline' : 'online');",
  'OFFLINE_DEFAULT')
 if main.count('HIGHFLY_WORLD7_P71_DRAKENLAB') or 'drakenlab_p71' in main:
  raise RuntimeError('P72_DRAKENLAB_IMPORT_LEFTOVER')
 if html.count('</head>')!=1:raise RuntimeError('P72_HTML_HEAD_DRIFT')
 html=html.replace('</head>',
  '<!-- HIGHFLY_P72_P71B_WITHOUT_DRAKENLAB: native 9 classes; isolated Offline QA -->\n</head>',1)
 return html.encode('utf8'),main.encode('utf8'),removed

def preflight():
 checked(WORK,WORK,kind='dir')
 checked(STAGE,WORK,kind='dir')
 checked(SNAP,WORK,kind='dir')
 if LAB.exists() or LAB.is_symlink() or REPORT.exists() or REPORT.is_symlink():
  raise RuntimeError('P72_LAB_OR_REPORT_ALREADY_EXISTS_NO_OVERWRITE')
 if (STAGE/'src').is_symlink() or (STAGE/'public').is_symlink():
  raise RuntimeError('P72_ACTIVE_STAGE_UNSAFE_SOURCE_DIR')
 checked(STAGE/'src',STAGE,kind='dir')
 checked(STAGE/'public',STAGE,kind='dir')
 if not (STAGE/'node_modules/vite/bin/vite.js').is_file():
  raise RuntimeError('P72_VITE_DEPENDENCY_MISSING')
 m=json_checked(SNAP_HASHES,WORK)
 p64=json_checked(P64_STATUS,WORK)
 p71=json_checked(P71_STATUS,WORK)
 p71b=json_checked(P71B_STATUS,WORK)
 if not all(x.get('mode')=='BUILD_GREEN_BROWSER_PENDING' for x in (p64,p71,p71b)):
  raise RuntimeError('P72_HISTORIC_SUCCESS_MANIFEST_INCOMPLETE')
 if 'src/main.ts' not in m or 'index.html' not in m:
  raise RuntimeError('P72_SNAPSHOT_NOT_COMPLETE')
 recovered={}
 for rel,sha in m.items():
  path=PurePosixPath(rel)
  if path.is_absolute() or '..' in path.parts or not (
   rel=='index.html' or rel.startswith('src/') or rel.startswith('public/highfly/')
  ):
   raise RuntimeError('P72_SNAPSHOT_PATH_NOT_ALLOWED_'+rel)
  data=checked(SNAP/rel,SNAP)
  if digest(data)!=sha:raise RuntimeError('P72_SNAPSHOT_SHA_DRIFT_'+rel)
  recovered[rel]=data
 snap_main=recovered['src/main.ts']
 if digest(snap_main)!=p71b.get('updatedSha256'):
  raise RuntimeError('P72_P71B_MAIN_HASH_DOES_NOT_MATCH_SNAPSHOT')
 before=checked(P71B_BEFORE,WORK)
 if digest(before)!=p71.get('sourceHashes',{}).get('src/main.ts'):
  raise RuntimeError('P72_P71_BACKUP_HASH_MISMATCH')
 if 'HIGHFLY_WORLD7_P71_DRAKENLAB' not in before.decode('utf8'):
  raise RuntimeError('P72_P71_MARKER_MISSING')
 if 'HIGHFLY_WORLD7_P71_DRAKENLAB' not in snap_main.decode('utf8'):
  raise RuntimeError('P72_P71B_MARKER_MISSING')
 for rel in DRAKEN_FILES:
  if digest(recovered[rel])!=p71.get('sourceHashes',{}).get(rel):
   raise RuntimeError('P72_DRAKENLAB_MODULE_SHA_DRIFT_'+rel)
 original_p69=checked(P69_MAIN,WORK).decode('utf8')
 if 'HIGHFLY_P69_FURY_CORE' not in original_p69 or 'HIGHFLY_WORLD7_P71_DRAKENLAB' in original_p69:
  raise RuntimeError('P72_NOT_EXACT_PRE_DRAKENLAB_MAIN')
 # Original P71 source was produced from this exact P69 main with DrakenLAB injection.
 # Require strict snapshot correspondence (no guesswork about earlier game changes).
 old=original_p69
 if 'HIGHFLY_P68_FURY_GOLDEN_RECOVERY' not in old:raise RuntimeError('P72_P68_MISSING')
 html,main,removed=native_entry(recovered['index.html'].decode('utf8'),old)
 if 'HIGHFLY_P41_OFFLINE_SAVE' not in main.decode('utf8'):
  raise RuntimeError('P72_OFFLINE_SAVE_LOST')
 if not all(x in recovered for x in (
  'src/game/mobile_controls.ts','src/game/input.ts',
  'src/ui/hud/action_bar/mobile_action_ring_controller.ts',
  'src/ui/hud.ts','src/sim/sim.ts','src/sim/combat/auto_attack.ts',
  'src/game/highfly_fury_skill_touch.ts','src/sim/combat/highfly_manual_taps.ts'
 )):
  raise RuntimeError('P72_P65_P69_COMPONENT_SNAPSHOT_INCOMPLETE')
 for rel in ('src/render/characters/manifest.ts','src/sim/content/classes.ts'):
  if not (STAGE/rel).is_file():raise RuntimeError('P72_BASE_RPG_SYSTEM_MISSING_'+rel)
 if not (STAGE/'public/highfly').is_dir() or (STAGE/'public/highfly').is_symlink():
  raise RuntimeError('P72_PRIVATE_MEDIA_SOURCE_UNSAFE')
 # Enforce protected current stage is the rolled-back P64 expected baseline.
 for rel,sha in p64.get('sourceSha256',{}).items():
  if rel=='index.html':continue # P64 entry UI V2 legitimately changed index
  if digest(checked(STAGE/rel,STAGE))!=sha:
   raise RuntimeError('P72_P64_SOURCE_CHANGED_UNEXPECTEDLY_'+rel)
 recovered={rel:blob for rel,blob in recovered.items() if rel not in DRAKEN_FILES}
 recovered['src/main.ts']=main
 recovered['index.html']=html
 samples={}
 for rel in MEDIA_SAMPLES:
  f=STAGE/'public'/rel
  samples['/'+rel]={
   'inCurrentApprovedStage':f.is_file(),
   'bytes':f.stat().st_size if f.is_file() else None
  }
 return recovered,removed,samples,p71b

def create(recovered,removed,samples):
 LAB.mkdir(mode=0o700)
 shutil.copytree(STAGE/'src',LAB/'src',symlinks=False)
 for item in STAGE.iterdir():
  if item.name in SKIP_ROOT or item.name.startswith('.hf_manual_backup'):continue
  dest=LAB/item.name
  if item.is_file() and not item.is_symlink() and item.stat().st_size<8_000_000:
   shutil.copy2(item,dest)
  elif item.is_dir() and not item.is_symlink() and item.name in OTHER_DIRS:
   dest.symlink_to(item,target_is_directory=True)
 (LAB/'node_modules').symlink_to(STAGE/'node_modules',target_is_directory=True)
 (LAB/'public').mkdir()
 for item in (STAGE/'public').iterdir():
  if item.name=='highfly':continue
  (LAB/'public'/item.name).symlink_to(item,target_is_directory=item.is_dir())
 (LAB/'public/highfly').mkdir()
 for item in (STAGE/'public/highfly').iterdir():
  (LAB/'public/highfly'/item.name).symlink_to(item,target_is_directory=item.is_dir())
 for rel,blob in recovered.items():
  file=LAB/rel
  if not file.resolve().is_relative_to(LAB.resolve()) or file.is_symlink():
   raise RuntimeError('P72_UNSAFE_INSTALL_PATH_'+rel)
  file.parent.mkdir(exist_ok=True,parents=True)
  if file.is_file() and file.stat().st_size>0 and rel.startswith('public/highfly/'):
   # Existing symlinks must be replaced in LAB, not followed into P64.
   pass
  file.write_bytes(blob)
  if digest(file.read_bytes())!=digest(blob):
   raise RuntimeError('P72_WRITE_VERIFY_FAILED_'+rel)
 if any((LAB/rel).exists() for rel in DRAKEN_FILES):
  raise RuntimeError('P72_DRAKENLAB_LEFT_IN_LAB')
 state={
  'phase':'P72_LAST_P71B_SOURCE_RESTORED_NO_DRAKENLAB',
  'mode':'INSTALLED_BROWSER_PENDING','createdAt':datetime.now(timezone.utc).isoformat(),
  'lab':str(LAB),'port':4178,'mainSource':'P71 saved pre-DrakenLAB P69 main',
  'otherSources':'P71B exact pre-P64 snapshot',
  'drakenlabDisabled':True,'nineClassesInNativeMarkup':True,
  'offlineAvailableOnlyForPrivateViteDev':True,
  'preservedP69Fury':True,'protectedStagesModified':False,
  'licenseApprovalRechecked':False,'browserGameplayVerified':False,
  'restoredSourceHashes':{rel:digest(blob) for rel,blob in recovered.items()},
  'filteredLegacyClassHiders':removed,'sampleStageMedia':samples,
  'important':'NO automatic GLB import. Existing P64 public media shared read-only. Browser may still show missing assets.'
 }
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf8')
 print('[P72 LAB CREATED] '+json.dumps({
  'lab':str(LAB),'restoredFiles':len(recovered),
  'drakenlabDisabled':True,'FURYPreserved':True,
  'port':4178,'P64_P69_P43_modified':False,
  'browserVerified':False,'mediaSample':samples,
  'report':str(REPORT)},indent=2,ensure_ascii=False))
 return state

def cli():
 parser=argparse.ArgumentParser()
 parser.add_argument('--apply',action='store_true',help='Create independent P72 lab once')
 args=parser.parse_args()
 recovered,removed,samples,_=preflight()
 print('[P72 PREFLIGHT] '+json.dumps({
  'status':'READY','filesToRecover':len(recovered),
  'keptSystems':'P65-P69 RPG/FURY/HUD + P71B unchanged world/AI/loot',
  'drakenlabImportsRemoved':True,'restoringOnlyIn':str(LAB),
  'removedLegacyFilters':removed,'assetSample':samples,
  'mode':'APPLY' if args.apply else 'DRY_RUN'
 },ensure_ascii=False,indent=2))
 if args.apply:
  try:create(recovered,removed,samples)
  except BaseException:
   print('[P72 FAILED] New lab may be incomplete; never rerun over it. Protected stages not touched.',file=sys.stderr)
   raise
if __name__=='__main__':cli()
