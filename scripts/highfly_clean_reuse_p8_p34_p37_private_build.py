#!/usr/bin/env python3
"""HIGHFLY CLEAN P8/P34/P36/P37 — reuse what ALREADY worked.

Original 4181 private static bundle is untouched. --apply:
- verifies 7 P8 KayKit user-owned building outputs against old P8 SHA receipts,
- restores only those SEVEN from old private stage to CLEAN private public,
- applies ORIGINAL P34 and P37 pure source transforms, and P36 NPC catch fallback
  (without P35 diagnostic prerequisite) to CLEAN src only,
- generates a NEW private build on port 4182 and installs ONE unified logger.
- aborts if any source-anchor drift or hash mismatch; rolls back clean src,
  copied buildings, and generated output/config on build failure.
Never copies original unlicensed 'with project only' world art, unknown maze kits,
CraftPix or the original missing warrior_modular/mage_classic.
Not approved for public hosting until media license review.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p34_fixed_actor_fallback as p34
import highfly_p36_npc_visible_fallback as p36
import highfly_p37_npc_cc0_roles as p37
import highfly_p8_import_eastbrook_gltf as p8
import highfly_clean_private_offline_bundle as bundle
import highfly_clean_unified_lifecycle_log as logger

WORK=ROOT/'.workspace'
CLEAN=WORK/'highfly-origin-clean-0447'
OLD=WORK/'highfly-origin-stage-p0'
ORIG=WORK/'claudecraft-v0.44.7'
DIST=CLEAN/'.highfly-reuse-p8-p37-dist'
CONFIG=CLEAN/'.highfly-private-reuse-p8-p37-vite.config.mjs'
REPORTDIR=WORK/'reports/highfly-clean-0447'
REPORT=REPORTDIR/'REUSE_P8_P34_P36_P37_BUILD.json'
LOG=REPORTDIR/'REUSE_P8_P34_P36_P37_BUILD_LOG.txt'
BACKUPS=REPORTDIR/'reuse-p8-p34-p36-p37-backups'
PIN='493c35a108cef6c8aa290e8793107b1cd117886e'
FILES=['src/render/characters/index.ts','src/render/characters/manifest.ts']
P8_REPORT=WORK/'reports/highfly-p8/EASTBROOK_OWNED_BUILDINGS_P8.json'
CLASSES=('warrior','mage','rogue','hunter','priest','paladin','shaman','warlock','druid')
PRIVATE_MODE='highfly-clean-private-offline'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def valid(path,base,kind='file'):
 if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()) or (
     not path.is_file() if kind=='file' else not path.is_dir()):
  raise RuntimeError('REUSE_UNSAFE_OR_MISSING '+str(path))

def apply_p36(index):
 if p36.MARK in index:raise RuntimeError('REUSE_P36_ALREADY_APPLIED')
 start=index.find('export function createCharacterVisual(')
 if start<0:raise RuntimeError('REUSE_P36_FACTORY_MISSING')
 tail=index[start:]
 if tail.count(p36.END_ANCHOR)!=1 or 'character visual unavailable, skipping view' not in tail:
  raise RuntimeError('REUSE_P36_CATCH_ANCHOR_CHANGED')
 pos=tail.index(p36.END_ANCHOR)
 return index[:start]+tail[:pos]+p36.PATCH+tail[pos:]

def building_plan():
 report=json.loads(P8_REPORT.read_text('utf8'))
 if report.get('sourceCommit')!=PIN or len(report.get('buildings',[]))!=7:
  raise RuntimeError('REUSE_P8_INVALID_OR_INCOMPLETE_RECEIPT')
 names=set(p8.BUILDINGS.values())
 rows=[]
 for x in report['buildings']:
  rel=str(x['publicUrl']).lstrip('/')
  if not rel.startswith('models/biome/') or Path(rel).name not in names:
   raise RuntimeError('REUSE_P8_UNEXPECTED_BUILDING_PATH '+rel)
  old=OLD/'public'/rel
  dest=CLEAN/'public'/rel
  valid(old,OLD)
  if sha(old)!=x.get('glbSha256'):
   raise RuntimeError('REUSE_P8_SOURCE_SHA_NOT_VERIFIED '+rel)
  p8.inspect_glb(old)
  if dest.exists() or dest.is_symlink():
   if dest.is_symlink() or sha(dest)!=sha(old):
    raise RuntimeError('REUSE_P8_DESTINATION_CONFLICT '+rel)
   status='EXACT_ALREADY_PRESENT'
  else:status='READY_OLD_VERIFIED_USER_OWNED_COPY'
  rows.append({'path':rel,'sha256':sha(old),'status':status,
   'source':str(old),'destination':str(dest),
   'originalOwnedSource':x.get('source'),
   'commercialLicenseRecheckRequired':True})
 if {Path(x['path']).name for x in rows}!=names:
  raise RuntimeError('REUSE_P8_INCOMPLETE_SEVEN_PATHS')
 return rows

def plan():
 for d in (WORK,CLEAN,OLD,ORIG):
  valid(d,WORK,'dir')
 for f in (P8_REPORT,CLEAN/'src/main.ts',CLEAN/'index.html',
           CLEAN/'node_modules/vite/bin/vite.js'):
  valid(f,WORK)
 if subprocess.check_output(['git','-C',str(ORIG),'rev-parse','HEAD'],
                            text=True).strip()!=PIN:
  raise RuntimeError('REUSE_ORIGINAL_COMMIT_CHANGED')
 for f in (CONFIG,REPORT,BACKUPS,DIST):
  if f.exists() or f.is_symlink():
   raise RuntimeError('REUSE_OUTPUT_EXISTS_STOP_NO_OVERWRITE '+str(f))
 original={x:(CLEAN/x).read_text('utf8') for x in FILES}
 for name in CLASSES:
  html=(CLEAN/'index.html').read_text('utf8')
  if f'data-class="{name}"' not in html:
   raise RuntimeError('REUSE_NATIVE_NINE_CLASS_MISSING '+name)
 required=('knight','mage','rogue','barbarian','paladin','druid')
 for cls in required:
  model=CLEAN/'public/models/chars/players'/(cls+'.glb')
  valid(model,CLEAN)
  with model.open('rb') as f:
   if f.read(4)!=b'glTF':raise RuntimeError('REUSE_CC0_CHARACTER_BAD_GLB '+cls)
 if any(token in ''.join(original.values()) for token in (p34.MARK,p36.MARK,p37.MARK)):
  raise RuntimeError('REUSE_PRIOR_PATCH_ALREADY_IN_CLEAN_SRC')
 # Strictly reuse old P34/P36/P37 transforms, not arbitrary new regex patches.
 p34out=p34.prepare(original[FILES[0]],original[FILES[1]],True,True)
 index=apply_p36(p34out[FILES[0]])
 manifest=p37.patch_manifest(p34out[FILES[1]])
 assert p34.MARK in index and p34.MARK in manifest
 assert p36.MARK in index and p37.MARK in manifest
 return original,{FILES[0]:index,FILES[1]:manifest},building_plan()

def makeconfig():
 config=bundle.CONFIG_BODY.replace('.highfly-private-offline-dist',
                                     '.highfly-reuse-p8-p37-dist')
 config=config.replace('port:4181,strictPort:true','port:4182,strictPort:true')
 if '.highfly-reuse-p8-p37-dist' not in config or 'port:4182' not in config:
  raise RuntimeError('REUSE_CONFIG_OUTPUT_OR_PREVIEW_ANCHOR_CHANGED')
 return config

def unify_html(path):
 text=path.read_text('utf8')
 for name in logger.OLD_IDS:
  pattern=r'<script\b[^>]*\bid=["\']'+name+r'["\'][^>]*>[\s\S]*?</script>'
  text=re.sub(pattern,'',text,count=1,flags=re.I)
 text=re.sub(r'<!--\s*HIGHFLY_CLEAN_BOOTLOG_V1\s*-->','',text)
 text=re.sub(r'<!--\s*HIGHFLY_CLEAN_BROWSER_ESM_V1\s*-->','',text)
 if logger.MARK in text:raise RuntimeError('REUSE_DUPLICATE_UNIFIED_LOG')
 if text.count('<head>')!=1:raise RuntimeError('REUSE_BAD_BUILT_HTML')
 updated=text.replace('<head>','<head>\n'+logger.SCRIPT+'\n',1)
 if updated.count(logger.MARK)!=1:raise RuntimeError('REUSE_UNIFIED_LOG_INVALID')
 path.write_text(updated,'utf8')

def run():
 orig,patched,buildings=plan()
 config=makeconfig()
 copied=[]
 changed=[]
 try:
  REPORTDIR.mkdir(parents=True,exist_ok=True)
  BACKUPS.mkdir(parents=True,exist_ok=False)
  for rel,txt in orig.items():
   backup=BACKUPS/rel
   backup.parent.mkdir(parents=True,exist_ok=True)
   backup.write_text(txt,'utf8')
   if sha(backup)!=sha(CLEAN/rel):raise RuntimeError('REUSE_BACKUP_INTEGRITY_FAILED')
  for x in buildings:
   if x['status']!='READY_OLD_VERIFIED_USER_OWNED_COPY':continue
   src=Path(x['source']);dest=Path(x['destination'])
   if sha(src)!=x['sha256']:raise RuntimeError('REUSE_P8_SOURCE_CHANGED')
   dest.parent.mkdir(parents=True,exist_ok=True)
   with src.open('rb') as f,dest.open('xb') as out:shutil.copyfileobj(f,out)
   copied.append(dest)
   if sha(dest)!=x['sha256']:raise RuntimeError('REUSE_P8_COPY_SHA_FAILED')
  for rel,text in patched.items():
   target=CLEAN/rel
   if target.read_text('utf8')!=orig[rel]:
    raise RuntimeError('REUSE_CONCURRENT_SOURCE_CHANGED '+rel)
   target.write_text(text,'utf8');changed.append(rel)
  CONFIG.write_text(config,'utf8')
  check=subprocess.run(['node','--check',str(CONFIG)],cwd=CLEAN,text=True,
    capture_output=True,timeout=15)
  if check.returncode:raise RuntimeError('REUSE_CONFIG_SYNTAX_ERROR '+check.stderr[-850:])
  env=os.environ.copy()
  env['NODE_OPTIONS']='--max-old-space-size=3072'
  proc=subprocess.run(['node',str(CLEAN/'node_modules/vite/bin/vite.js'),
    'build','--config',str(CONFIG),'--mode',PRIVATE_MODE],
    cwd=CLEAN,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
    timeout=270)
  LOG.write_text(proc.stdout[-250000:],'utf8')
  if proc.returncode:raise RuntimeError('REUSE_VITE_BUILD_FAILED '+str(proc.returncode))
  index=DIST/'index.html'
  if not index.is_file():raise RuntimeError('REUSE_BUILD_NO_INDEX')
  unify_html(index)
  for x in buildings:
   built=DIST/x['path']
   if not built.is_file() or sha(built)!=x['sha256']:
    raise RuntimeError('REUSE_P8_BUILD_FILE_MISSING_OR_CHANGED '+x['path'])
  result={'phase':'REUSE_WORKING_P8_P34_P36_P37_IN_CLEAN_PRIVATE_PREVIEW',
   'status':'BUILT_NOT_YET_BROWSER_VERIFIED','pinnedOriginal':PIN,
   'sourceChanges':FILES,'builtAtUtc':datetime.now(timezone.utc).isoformat(),
   'p8UserOwnedSourceHashVerified':True,'p8BuildingModels':buildings,
   'nativeNineClassesPreserved':True,
   'fixedRigFallback':'P34 + P36 + P37 existing successful code',
   'oneUnifiedLogger':True,'port':4182,
   'previous4181StaticBuildUntouched':True,
   'originalReferenceUntouched':True,'publicReleaseApproved':False,
   'commercialAssetLicenseVerified':False,
   'gameWorldEnteredVerified':False,
   'buildLog':str(LOG),
   'playCommand':'node node_modules/vite/bin/vite.js preview --config .highfly-private-reuse-p8-p37-vite.config.mjs --mode highfly-clean-private-offline --host 0.0.0.0 --port 4182 --strictPort'}
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
  print('[HIGHFLY P8/P34/P36/P37 REUSE BUILD] '+json.dumps({
   'status':result['status'],'port':4182,'sevenVerifiedBuildings':7,
   'addedP8Buildings':len(copied),'old4181Intact':True,
   'newCharacterSourceFiles':FILES,'oneLogger':True,
   'browserVerified':False,'report':str(REPORT),
   'playCommand':result['playCommand']
  },indent=2,ensure_ascii=False))
 except BaseException:
  for rel in changed:
   target=CLEAN/rel
   if target.is_file() and not target.is_symlink():
    if target.read_text('utf8')==patched[rel]:target.write_text(orig[rel],'utf8')
  for dst in reversed(copied):
   if dst.is_file() and not dst.is_symlink():dst.unlink()
  if CONFIG.is_file() and not CONFIG.is_symlink():CONFIG.unlink()
  if DIST.is_dir() and not DIST.is_symlink():shutil.rmtree(DIST)
  if BACKUPS.is_dir() and not BACKUPS.is_symlink():shutil.rmtree(BACKUPS)
  print('[HIGHFLY REUSE] FAILED: reverted clean code, P8 copies, output/config. '
   'Original 4181 static build untouched. Log: '+str(LOG),file=sys.stderr)
  raise

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true')
 args=ap.parse_args()
 if args.apply:run()
 else:
  original,patched,rows=plan()
  print('[HIGHFLY PRIOR-WORK REUSE PREFLIGHT] '+json.dumps({
   'status':'READY_NO_MUTATIONS','sourcePatches':list(patched),
   'existingOriginalP8':sum(x['status']=='EXACT_ALREADY_PRESENT' for x in rows),
   'ownedP8ToCopy':sum(x['status']=='READY_OLD_VERIFIED_USER_OWNED_COPY' for x in rows),
   'reusingP34P36P37':True,'sourceCloned':False,'old4181Intact':True,
   'newPort':4182,'outputDist':str(DIST),'singleLogger':True,
   'publicReleaseApproved':False,
  },ensure_ascii=False,indent=2))
