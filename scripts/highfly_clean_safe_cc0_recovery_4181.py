#!/usr/bin/env python3
"""Safely recover EXACT KayKit/Quaternius/etc CC0 models from pinned original.

Unlike prior CLEAN preparation, this includes original KayKit-derived GLBs
only if the original conversion manifest has ONE CC0 pack source, CREDITS.md
allows that provider, AND the output is not named in a restricted CREDITS row.
Never accepts project-generated items or CraftPix; never invents placeholder
meshes. Copies into private CLEAN stage and private Vite preview 4181.
--audit is read-only; --apply writes only missing proven copies and a receipt.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p25_source_first_asset_audit as p25
import highfly_p21_runtime_asset_recovery as p21
import highfly_origin_clean_v0447 as clean
WORK=ROOT/'.workspace'
ORIG=WORK/'claudecraft-v0.44.7'
STAGE=WORK/'highfly-origin-clean-0447'
DIST=STAGE/'.highfly-private-offline-dist'
REPORT=WORK/'reports/highfly-clean-0447/SAFE_CC0_RECOVERY_4181.json'
PIN='493c35a108cef6c8aa290e8793107b1cd117886e'
PROVIDERS={'KayKit','Quaternius','Kenney','ambientCG','Poly Haven','loafbrr'}
MAX_BYTES=650_000_000
MAX_FILES=1200
EXT={'.glb','.png','.jpg','.jpeg','.webp'}
RESTRICTED_FLAGS=('with the project only','no, permission required','non-commercial only')

def digest(f):
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for blob in iter(lambda:stream.read(1<<20),b''):h.update(blob)
 return h.hexdigest()

def preflight():
 for p in (ORIG,STAGE,DIST):
  if p.is_symlink() or not p.is_dir() or not p.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError('CC0_RECOVERY_PRIVATE_LAB_MISSING '+str(p))
 for p in (ORIG/'CREDITS.md',STAGE/'index.html',DIST/'index.html'):
  if not p.is_file() or p.is_symlink():raise RuntimeError('CC0_RECOVERY_REQUIRED_FILE_MISSING '+str(p))
 actual=subprocess.check_output(['git','-C',str(ORIG),'rev-parse','HEAD'],text=True).strip()
 if actual!=PIN:raise RuntimeError('CC0_RECOVERY_WRONG_PINNED_CLAUDECRAFT_COMMIT')

def restricted_mentions():
 blocked=[]
 for line in (ORIG/'CREDITS.md').read_text('utf8').splitlines():
  if not line.startswith('|') or not any(q in line.casefold() for q in RESTRICTED_FLAGS):continue
  # A narrower, conservative row-level exclusion. For paths present in an
  # explicitly restricted credit row, reject even if other docs say CC0.
  blocked.extend(re.findall(r'(?:public/)?models/[A-Za-z0-9_./-]+\.glb',line))
  blocked.extend(re.findall(r'(?:public/)?ui/[A-Za-z0-9_./-]+\.(?:webp|png)',line))
 return {q.removeprefix('public/') for q in blocked}

def analyze():
 preflight()
 credits=p25.credited(ORIG)
 specs=p25.outspec_index(ORIG)
 explicit=restricted_mentions()
 result=[]
 reasons=collections.Counter()
 for url,rows in sorted(specs.items()):
  rel=url.lstrip('/')
  if not clean.safe_path(url) or PurePosixPath(rel).suffix.casefold() not in EXT:
   continue
  if rel in explicit:
   reasons['RESTRICTED_CREDITS_EXPLICIT_PATH']+=1
   continue
  srcs={r.get('exactRawSource') for r in rows}
  providers={r.get('sourceProvider') for r in rows}
  if len(srcs)!=1 or len(providers)!=1:
   reasons['MIXED_OR_AMBIGUOUS_PROVENANCE']+=1;continue
  src=next(iter(srcs));prov=next(iter(providers))
  if prov not in PROVIDERS or not credits.get(prov,False):
   reasons['UNVERIFIED_OR_PROJECT_ASSET']+=1;continue
  if not isinstance(src,str) or not src.replace('\\','/').startswith('tmp/asset_src/'):
   reasons['SOURCE_NOT_PINNED_CC0_PACK']+=1;continue
  if prov=='KayKit' and not src.replace('\\','/').casefold().startswith('tmp/asset_src/kaykit/'):
   reasons['KAYKIT_SOURCE_NOT_EXACT_PACK']+=1;continue
  original=ORIG/'public'/rel
  if original.is_symlink() or not original.is_file() or not p21.check_binary(original,url):
   reasons['ORIGINAL_CC0_BINARY_MISSING_OR_INVALID']+=1;continue
  stage=STAGE/'public'/rel;dist=DIST/rel
  if stage.exists() or stage.is_symlink() or dist.exists() or dist.is_symlink():
   if stage.is_file() and dist.is_file() and not stage.is_symlink() and not dist.is_symlink() and digest(original)==digest(stage)==digest(dist):
    reasons['ALREADY_PRESENT_AND_IDENTICAL']+=1
   else:reasons['ALREADY_PRESENT_OR_CONFLICT_NO_OVERWRITE']+=1
   continue
  result.append({'path':rel,'provider':prov,'sourceSpec':rows[0]['upstreamSpec'],
   'sourcePackFile':src,'sha256':digest(original),'bytes':original.stat().st_size})
 return result,reasons,credits

def apply():
 if REPORT.exists() or REPORT.is_symlink():raise RuntimeError('CC0_RECOVERY_REPORT_ALREADY_EXISTS')
 candidates,reasons,credits=analyze()
 size=sum(x['bytes'] for x in candidates)
 if len(candidates)>MAX_FILES or size>MAX_BYTES:
  raise RuntimeError(f'CC0_RECOVERY_SAFETY_BUDGET_EXCEEDED count={len(candidates)} bytes={size}')
 installed=[]
 try:
  for row in candidates:
   rel=row['path'];orig=ORIG/'public'/rel
   if digest(orig)!=row['sha256'] or orig.is_symlink():
    raise RuntimeError('CC0_RECOVERY_ORIGINAL_BINARY_DRIFT '+rel)
   for dest in (STAGE/'public'/rel,DIST/rel):
    if dest.exists() or dest.is_symlink():raise RuntimeError('CC0_RECOVERY_CONCURRENT_DESTINATION '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True)
    with orig.open('rb') as src,dest.open('xb') as out:shutil.copyfileobj(src,out)
    installed.append(dest)
    if digest(dest)!=row['sha256']:raise RuntimeError('CC0_RECOVERY_HASH_COPY_FAILED '+rel)
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps({
   'phase':'PINNED_CC0_ONLY_KAYKIT_AND_PEERS','sourceCommit':PIN,
   'sourceUntouched':True,'stagePrivate':True,'previewPrivate':True,
   'userOwnedArchiveNotModified':True,
   'applied':True,'filesInstalledToEachLocation':len(candidates),
   'totalBytesEach':size,'sources':candidates,'reasons':dict(reasons),
   'licenseBasis':'Original exact-source converter spec + CREDITS.md CC0 Yes; explicit restricted path veto',
   'excludedMedia':'project art, CraftPix, project-only, no-permission, ambiguous sources',
   'legalGuarantee':False,'completeWorldVerified':False,
   'publicReleaseApproved':False},indent=2,ensure_ascii=False)+'\n','utf8')
  print('[CLEAN CC0 RECOVERED] '+json.dumps({
   'restoredFiles':len(candidates),'verifiedBytes':size,'reasons':dict(reasons),
   'privatePreviewPort':4181,'originalSourceUntouched':True,
   'worldPlayableVerified':False,'report':str(REPORT)
  },indent=2,ensure_ascii=False))
 except BaseException:
  for f in reversed(installed):
   if f.is_file() and not f.is_symlink():f.unlink()
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--apply',action='store_true')
 args=p.parse_args()
 if args.apply:apply()
 else:
  candidates,reasons,credits=analyze()
  print('[CLEAN CC0 RECOVERY PREFLIGHT] '+json.dumps({
   'eligibleAbsent':len(candidates),'eligibleBytes':sum(x['bytes'] for x in candidates),
   'byProvider':dict(collections.Counter(x['provider'] for x in candidates)),
   'statusCounts':dict(reasons),'licenseProof':{x:credits.get(x,False) for x in sorted(PROVIDERS)},
   'criticalModularWarriorEligible':next((x for x in candidates if x['path']=='models/chars/modular/warrior_modular.glb'),None),
   'examplePaths':[x['path'] for x in candidates[:22]],
   'isFullWorldLicensed':False,'safeForPublicRelease':False,'mode':'READ_ONLY'
  },indent=2,ensure_ascii=False))
