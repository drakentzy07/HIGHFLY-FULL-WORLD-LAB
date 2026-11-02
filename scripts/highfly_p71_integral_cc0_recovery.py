#!/usr/bin/env python3
"""P71 one-shot exact CC0 recovery in isolated P69 (no game source edits).
Default: dry-run. --apply installs only binary files verified against original
v0.44.7 CC0 conversion specs + credits. Creates a P69-only link forest;
NEVER writes through P69's shared P64 public symlinks.
Unverified/project-only/KayKit upstream assets are ALWAYS excluded.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p21_runtime_asset_recovery as p21

WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p69-restore-lab'
P64=WORK/'highfly-origin-stage-p0'
ORIGINAL=WORK/'claudecraft-v0.44.7'
P70=WORK/'reports/highfly-world7/P70_FULL_FORENSIC_AUDIT.json'
REPORT=WORK/'reports/highfly-world7/P71_CC0_ISOLATED_RECOVERY.json'
ROOTS=('models','textures','vfx')
ALLOWED={'CC0_QUATERNIUS','CC0_KENNEY','CC0_AMBIENTCG','CC0_POLYHAVEN'}

def sha(file):
 h=hashlib.sha256()
 with file.open('rb') as fd:
  for block in iter(lambda:fd.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def validate():
 if not LAB.is_dir() or LAB.is_symlink() or not P64.is_dir() or P64.is_symlink():
  raise RuntimeError('P71_PRIVATE_STAGE_OR_LAB_MISSING')
 if not ORIGINAL.is_dir() or ORIGINAL.is_symlink() or not P70.is_file() or P70.is_symlink():
  raise RuntimeError('P71_PINNED_ORIGINAL_OR_P70_AUDIT_MISSING')
 for p in (LAB,P64,ORIGINAL,P70,REPORT):
  if not p.resolve().is_relative_to(WORK.resolve()):raise RuntimeError('P71_OUTSIDE_WORKSPACE')
 if REPORT.exists() or REPORT.is_symlink():raise RuntimeError('P71_ALREADY_APPLIED_OR_RESULT_EXISTS')
 for root in ROOTS:
  source=P64/'public'/root
  link=LAB/'public'/root
  if not source.is_dir() or source.is_symlink() or not link.is_symlink() or link.resolve()!=source.resolve():
   raise RuntimeError('P71_SHARED_PUBLIC_LINK_DRIFT_'+root)
  for name in ('.hf-p71-new-'+root,'.hf-p71-old-'+root):
   t=LAB/'public'/name
   if t.exists() or t.is_symlink():raise RuntimeError('P71_STALE_OVERLAY_REVIEW_'+name)
 data=json.loads(P70.read_text('utf8'))
 if data.get('name')!='HIGHFLY_P70_FULL_P69_FORENSIC_AUDIT':raise RuntimeError('P71_NOT_P70_AUDIT')
 return data

def candidates():
 data=validate()
 spec=p21.build_spec_index(ORIGINAL,p21.credits_state(ORIGINAL))
 selected=[];excluded=[]
 for item in data['allResources']:
  url=item.get('url','')
  if not p21.safe_asset_path(url):continue
  rel=url.lstrip('/')
  if (P64/'public'/rel).is_file():continue
  file=ORIGINAL/'public'/rel
  entries=spec.get(url,[])
  proofs={e.get('provenance') for e in entries}
  sources={e.get('sourceDescription') for e in entries}
  why=None
  if not file.is_file() or file.is_symlink():why='NO_PINNED_BINARY'
  elif not entries:why='NO_EXACT_SOURCE_SPEC'
  elif len(proofs)!=1 or len(sources)!=1:why='AMBIGUOUS_SOURCE_SPECS'
  elif next(iter(proofs)) not in ALLOWED:why='UNVERIFIED_RESTRICTED_OR_UPSTREAM_KAYKIT'
  elif not p21.check_binary(file,url):why='BAD_OR_UNSUPPORTED_BINARY'
  if why:excluded.append({'url':url,'reason':why});continue
  selected.append({'url':url,'provider':next(iter(proofs)),
   'sourceSpecs':sorted({e.get('sourceSpec','') for e in entries}),
   'bytes':file.stat().st_size,'sha256':sha(file)})
 if len(selected)>900 or sum(x['bytes'] for x in selected)>650_000_000:
  raise RuntimeError('P71_REVIEW_REQUIRED_EXCEEDS_SAFE_IMPORT_BUDGET')
 return selected,excluded

def mirror(source,destination):
 if source.is_symlink() or not source.is_dir():raise RuntimeError('P71_UNSAFE_MODEL_SOURCE')
 destination.mkdir(mode=0o700)
 for folder,dirs,files in os.walk(source,followlinks=False):
  base=Path(folder)
  rel=base.relative_to(source)
  dest=destination/rel
  for d in dirs:
   if (base/d).is_symlink():raise RuntimeError('P71_UNEXPECTED_NESTED_DIR_LINK')
   (dest/d).mkdir(exist_ok=True)
  for f in files:
   file=base/f
   if file.is_symlink() or not file.is_file():raise RuntimeError('P71_UNEXPECTED_NESTED_FILE')
   (dest/f).symlink_to(file)

def apply():
 approved,excluded=candidates()
 roots=sorted({PurePosixPath(x['url'].lstrip('/')).parts[0] for x in approved})
 print('[P71] approved',len(approved),'excluded',len(excluded),'roots',roots)
 if not approved:print('[P71] no safe exact files found; game unchanged');return
 original_hashes={str(f.relative_to(LAB)):sha(f) for f in
  (LAB/'index.html',LAB/'src/main.ts') if f.is_file() and not f.is_symlink()}
 built=[];moved=[]
 try:
  for root in roots:
   temp=LAB/'public'/('.hf-p71-new-'+root)
   mirror(P64/'public'/root,temp)
   built.append(temp)
  for item in approved:
   rel=PurePosixPath(item['url'].lstrip('/'))
   dest=LAB/'public'/('.hf-p71-new-'+rel.parts[0])/Path(*rel.parts[1:])
   source=ORIGINAL/'public'/str(rel)
   if dest.exists() or dest.is_symlink() or sha(source)!=item['sha256']:
    raise RuntimeError('P71_BINARY_CHANGED_OR_DESTINATION_EXISTS_'+item['url'])
   dest.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source,dest)
   if sha(dest)!=item['sha256']:raise RuntimeError('P71_COPY_VERIFY_FAILED_'+item['url'])
  for rel,h in original_hashes.items():
   if sha(LAB/rel)!=h:raise RuntimeError('P71_CONCURRENT_GAME_SOURCE_CHANGE')
  for root in roots:
   current=LAB/'public'/root
   target=(P64/'public'/root).resolve()
   if not current.is_symlink() or current.resolve()!=target:
    raise RuntimeError('P71_STAGE_LINK_CHANGED_BEFORE_SWAP')
   old=LAB/'public'/('.hf-p71-old-'+root)
   new=LAB/'public'/('.hf-p71-new-'+root)
   current.rename(old)
   moved.append(root)
   new.rename(current)
  result={'phase':'P71_EXACT_CC0_P69_ONLY','status':'APPLIED_BROWSER_NOT_VERIFIED',
   'utc':datetime.now(timezone.utc).isoformat(),'approved':approved,
   'excluded':excluded,'approvedCount':len(approved),'excludedCount':len(excluded),
   'byProvider':dict(Counter(x['provider'] for x in approved)),
   'rootsSwapped':roots,'gameSourceSha256':original_hashes,
   'P64Modified':False,'P43Modified':False,'ownedKayKitImported':False,
   'sourceModified':False,'createdPlaceholders':False,
   'note':'Other missing project-only/unknown art and native renderer issues remain blocked for separate verified recovery.'}
  REPORT.parent.mkdir(exist_ok=True,parents=True)
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
  print('[P71 SUCCESS] only verified CC0 restored in isolated P69')
  print('REPORT_PATH='+str(REPORT))
 except BaseException:
  for root in reversed(moved):
   current=LAB/'public'/root
   old=LAB/'public'/('.hf-p71-old-'+root)
   if current.is_dir() and not current.is_symlink():shutil.rmtree(current)
   if old.is_symlink():old.rename(current)
  for temp in built:
   if temp.is_dir() and not temp.is_symlink():shutil.rmtree(temp)
  raise

def dry_run():
 approved,excluded=candidates()
 print('[P71 DRY RUN] '+json.dumps({
   'approvedCC0':len(approved),'approvedBytes':sum(x['bytes'] for x in approved),
   'providers':dict(Counter(x['provider'] for x in approved)),
   'blocked':len(excluded),'blockedReasons':dict(Counter(x['reason'] for x in excluded)),
   'examplesApproved':approved[:10],'examplesBlocked':excluded[:10],
   'gameModified':False,'P64Modified':False,'browserVerified':False
  },ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--apply',action='store_true')
 args=parser.parse_args()
 if args.apply:apply()
 else:dry_run()
