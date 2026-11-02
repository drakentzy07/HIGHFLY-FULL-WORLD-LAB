#!/usr/bin/env python3
"""HIGHFLY CLEAN P84: fix actual cause of GLB load errors at private 4182.

PROVEN in browser log: 200 text/html response for
/media/models/chars/players/knight.*.glb. Models exist at /models/... in the
private public inventory, but the pinned production media manifest maps them
to hashed /media/... paths that this isolated Vite build never generated.

Fix ONLY private CLEAN assetUrl conditional; never copy unlicensed assets.
One retry only for private QA so missing files cannot stall 700 tasks for 7 min.
Build to TEMP output; verify real legal GLBs; back up and swap 4182 only on
success. Preserve old 4181, all RPG source, player saves and private archives.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'.workspace/highfly-origin-clean-0447'
R=ROOT/'.workspace/reports/highfly-clean-0447'
MEDIA=LAB/'src/render/assets/media.ts'
RETRY=LAB/'src/render/assets/load_retry.ts'
CFG=LAB/'.highfly-private-reuse-p8-p37-vite.config.mjs'
DIST=LAB/'.highfly-reuse-p8-p37-dist'
TMP_CFG=LAB/'.highfly-p84-temp-build.config.mjs'
TMP_DIST=LAB/'.highfly-p84-temp-dist'
PREV=LAB/'.highfly-reuse-p8-p37-dist-before-p84'
BAK=R/'P84_SOURCE_BACKUPS'
RESULT=R/'P84_MEDIA_ROUTE_CORRECTION.json'
LOG=R/'P84_MEDIA_ROUTE_BUILD_LOG.txt'
MEDIA_OLD='if (import.meta.env.DEV) return'
MEDIA_NEW="if (import.meta.env.DEV || import.meta.env.MODE === 'highfly-clean-private-offline') return"
RETRY_OLD='export const MAX_LOAD_ATTEMPTS = 3;'
RETRY_NEW="export const MAX_LOAD_ATTEMPTS = import.meta.env.MODE === 'highfly-clean-private-offline' ? 1 : 3;"
SAMPLES=('models/chars/players/knight.glb',
         'models/chars/players/mage.glb',
         'models/chars/players/paladin.glb',
         'models/biome/hexb_townhall.glb')

def hashfile(file):
 h=hashlib.sha256()
 with file.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def check():
 W=ROOT/'.workspace'
 if not LAB.is_dir() or LAB.is_symlink() or not LAB.resolve().is_relative_to(W.resolve()):
  raise RuntimeError('P84_CLEAN_LAB_MISSING')
 for f in (MEDIA,RETRY,CFG,DIST/'index.html'):
  if f.is_symlink() or not f.is_file():raise RuntimeError('P84_REQUIRED_FILE_MISSING '+str(f))
 if not DIST.is_dir() or DIST.is_symlink():raise RuntimeError('P84_4182_BUILD_MISSING')
 if any(f.exists() or f.is_symlink() for f in (TMP_CFG,TMP_DIST,PREV,BAK,RESULT)):
  raise RuntimeError('P84_ALREADY_STARTED_OR_OUTPUT_COLLISION')
 text=MEDIA.read_text('utf8')
 retry=RETRY.read_text('utf8')
 if text.count(MEDIA_OLD)!=1 or retry.count(RETRY_OLD)!=1:
  raise RuntimeError('P84_PRIVATE_MEDIA_OR_RETRY_SOURCE_DRIFT')
 config=CFG.read_text('utf8')
 if config.count('.highfly-reuse-p8-p37-dist')!=1:
  raise RuntimeError('P84_ORIGINAL_BUILD_CONFIG_DRIFT')
 for rel in SAMPLES:
  before=LAB/'public'/rel
  built=DIST/rel
  if (not before.is_file() or before.is_symlink() or
      not built.is_file() or built.is_symlink() or
      hashfile(before)!=hashfile(built)):
   raise RuntimeError('P84_PROVEN_CC0_MODEL_NOT_IN_4182 '+rel)
  with before.open('rb') as f:
   if f.read(4)!=b'glTF':raise RuntimeError('P84_BAD_GLB '+rel)
 orig_html=(DIST/'index.html').read_text('utf8')
 if orig_html.count('HIGHFLY_CLEAN_UNIFIED_LIFECYCLE_LOG_V1')!=1:
  raise RuntimeError('P84_UNIFIED_LOGGER_NOT_PRESENT')
 import re
 match=re.search(r'<script id="hf-clean-unified-lifecycle-logger">[\s\S]*?</script>',orig_html)
 if not match:raise RuntimeError('P84_UNIFIED_LOGGER_SCRIPT_MISSING')
 return text,retry,config,match.group(0)

def apply():
 original_media,original_retry,config,logger=check()
 temp_config=config.replace('.highfly-reuse-p8-p37-dist','.highfly-p84-temp-dist')
 R.mkdir(parents=True,exist_ok=True)
 changed=False
 migrated=False
 try:
  BAK.mkdir(parents=True,exist_ok=False)
  (BAK/'media.ts').write_text(original_media,'utf8')
  (BAK/'load_retry.ts').write_text(original_retry,'utf8')
  if (hashfile(BAK/'media.ts')!=hashfile(MEDIA) or
      hashfile(BAK/'load_retry.ts')!=hashfile(RETRY)):
   raise RuntimeError('P84_BACKUP_MISMATCH')
  MEDIA.write_text(original_media.replace(MEDIA_OLD,MEDIA_NEW,1),'utf8')
  RETRY.write_text(original_retry.replace(RETRY_OLD,RETRY_NEW,1),'utf8')
  changed=True
  TMP_CFG.write_text(temp_config,'utf8')
  check_js=subprocess.run(['node','--check',str(TMP_CFG)],capture_output=True,text=True)
  if check_js.returncode:raise RuntimeError('P84_TEMP_CONFIG_SYNTAX '+check_js.stderr)
  env=os.environ.copy();env['NODE_OPTIONS']='--max-old-space-size=3072'
  result=subprocess.run(['node','node_modules/vite/bin/vite.js','build',
    '--config',str(TMP_CFG),'--mode','highfly-clean-private-offline'],
    cwd=LAB,env=env,capture_output=True,text=True,timeout=270)
  LOG.write_text((result.stdout+'\n'+result.stderr)[-200000:],'utf8')
  if result.returncode:raise RuntimeError('P84_BUNDLE_BUILD_FAILED '+str(result.returncode))
  index=TMP_DIST/'index.html'
  if not index.is_file():raise RuntimeError('P84_TEMP_INDEX_NOT_BUILT')
  content=index.read_text('utf8')
  if '<head>' not in content:raise RuntimeError('P84_TEMP_HTML_MALFORMED')
  if 'HIGHFLY_CLEAN_UNIFIED_LIFECYCLE_LOG_V1' not in content:
   content=content.replace('<head>','<head>\n'+logger+'\n',1)
   index.write_text(content,'utf8')
  if index.read_text('utf8').count('HIGHFLY_CLEAN_UNIFIED_LIFECYCLE_LOG_V1')!=1:
   raise RuntimeError('P84_UNIFIED_LOGGER_INCONSISTENT')
  for rel in SAMPLES:
   target=TMP_DIST/rel
   if not target.is_file() or hashfile(target)!=hashfile(LAB/'public'/rel):
    raise RuntimeError('P84_NEW_BUNDLE_MISSING_VALID_MODEL '+rel)
  # Store old static build, then promote verified temp; no original source copied.
  DIST.rename(PREV)
  TMP_DIST.rename(DIST)
  migrated=True
  TMP_CFG.unlink()
  status={'phase':'P84_PRIVATE_MEDIA_ROUTE_REPAIR',
   'status':'BUILT_AWAITING_CHROME_VERIFICATION',
   'builtAtUtc':datetime.now(timezone.utc).isoformat(),
   'servedModelPaths':'/models/... (not stale hashed /media/...)',
   'privateLoadAttempts':1,'port':4182,'sourceFilesChanged':[str(MEDIA),str(RETRY)],
   'sourcesBackedUp':str(BAK),'previous4182BackedUp':str(PREV),
   'old4181Untouched':True,'originalClaudeCraftUntouched':True,
   'unlicensedModelsCopied':0,'nineClassesPreserved':True,
   'singleLoggerPreserved':True,'browserVerified':False,
   'commercialPublicationApproved':False,'buildLog':str(LOG)}
  RESULT.write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n','utf8')
  print('[HIGHFLY P84 PRIVATE MEDIA FIX] '+json.dumps({
   'status':status['status'],'newModelRoutes':'/models/...',
   'samplesVerified':list(SAMPLES),'privateRetryAttempts':1,
   'previous4182BackedUp':True,'old4181Untouched':True,
   'currentPort':4182,'browserVerified':False},indent=2,ensure_ascii=False))
 except BaseException:
  # Only revert files whose bytes are still ours, never overwrite user edits.
  if changed:
   amended=original_media.replace(MEDIA_OLD,MEDIA_NEW,1)
   if MEDIA.is_file() and not MEDIA.is_symlink() and MEDIA.read_text('utf8')==amended:
    MEDIA.write_text(original_media,'utf8')
   amended_retry=original_retry.replace(RETRY_OLD,RETRY_NEW,1)
   if RETRY.is_file() and not RETRY.is_symlink() and RETRY.read_text('utf8')==amended_retry:
    RETRY.write_text(original_retry,'utf8')
  if migrated:
   if DIST.is_dir() and not DIST.is_symlink():shutil.rmtree(DIST)
   if PREV.is_dir() and not PREV.is_symlink():PREV.rename(DIST)
  elif not DIST.exists() and PREV.is_dir() and not PREV.is_symlink():
   PREV.rename(DIST)
  if TMP_CFG.is_file() and not TMP_CFG.is_symlink():TMP_CFG.unlink()
  if TMP_DIST.is_dir() and not TMP_DIST.is_symlink():shutil.rmtree(TMP_DIST)
  print('[HIGHFLY P84] FAILED — previous private 4182 restored, old 4181 intact.')
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true')
 args=p.parse_args()
 if args.apply:apply()
 else:
  check()
  print('[HIGHFLY P84 PREFLIGHT] READY: private /media -> /models logic fix, '
        'backup+atomic 4182 build, 1 retry, no new assets or license changes.')
