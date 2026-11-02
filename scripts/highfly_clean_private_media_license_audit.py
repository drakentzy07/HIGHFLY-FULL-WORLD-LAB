#!/usr/bin/env python3
"""Read-only by default: audit ALL private CLEAN public media by SHA+receipt.

Verifies that media in the actual 4181 Vite preview directory are traceable to
initial CC0 SOURCE manifest, exact upstream KayKit CC0 restored players, or
subsequent per-file CC0 recovery report. Flags unknown media and any path
explicitly listed in restricted CREDITS.md rows. Never declares production
legal clearance; JS/CSS embedded asset rights need independent review.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace';STAGE=WORK/'highfly-origin-clean-0447'
ORIG=WORK/'claudecraft-v0.44.7'
DIST=STAGE/'.highfly-private-offline-dist'
REPORTDIR=WORK/'reports/highfly-clean-0447'
INSTALL=REPORTDIR/'INSTALL_STATUS.json'
RESTORED=REPORTDIR/'RESTORED_PINNED_CC0_PLAYERS.json'
RECOVERY=REPORTDIR/'SAFE_CC0_RECOVERY_4181.json'
RESULT=REPORTDIR/'MEDIA_PROVENANCE_4181_AUDIT.json'
PIN='493c35a108cef6c8aa290e8793107b1cd117886e'
MEDIA_EXT={'.glb','.gltf','.fbx','.obj','.bin','.png','.jpg','.jpeg','.webp',
 '.svg','.gif','.bmp','.ktx','.ktx2','.hdr','.exr','.ogg','.wav','.mp3','.flac',
 '.opus','.woff','.woff2','.ttf','.otf','.mp4','.webm'}
RESTRICTED=('with the project only','no, permission required','non-commercial only')

def sha(file):
 h=hashlib.sha256()
 with file.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def safe():
 for p in (ORIG,STAGE,DIST):
  if p.is_symlink() or not p.is_dir() or not p.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError('MEDIA_LICENSE_AUDIT_UNSAFE_OR_MISSING_DIR '+str(p))
 commit=subprocess.check_output(['git','-C',str(ORIG),'rev-parse','HEAD'],text=True).strip()
 if commit!=PIN:raise RuntimeError('MEDIA_LICENSE_AUDIT_ORIGINAL_NOT_PINNED')
 if not (ORIG/'CREDITS.md').is_file():raise RuntimeError('MEDIA_LICENSE_AUDIT_MISSING_CREDITS')
def load(path):
 if path.is_symlink():raise RuntimeError('MEDIA_LICENSE_AUDIT_RECEIPT_SYMLINK '+str(path))
 return json.loads(path.read_text('utf8')) if path.is_file() else {}
def restricted():
 paths=set()
 for line in (ORIG/'CREDITS.md').read_text('utf8').splitlines():
  if not line.startswith('|') or not any(x in line.casefold() for x in RESTRICTED):continue
  for match in re.findall(r'(?:public/)?(?:models|ui|textures|vfx)/[a-z0-9_./-]+\.(?:glb|png|webp|jpg|jpeg)',line,re.I):
   paths.add(match.removeprefix('public/'))
 return paths
def known_provenance():
 manifest=load(INSTALL);players=load(RESTORED);recover=load(RECOVERY)
 out={}
 for x in manifest.get('mediaManifest',[]):
  path=str(x.get('path','')).lstrip('/')
  if not path or not re.fullmatch(r'[A-Za-z0-9_./-]+',path):continue
  out[path]={'sha256':x.get('sha256'),
   'category':'INITIAL_VERIFIED_CC0' if x.get('provider')!='USER_OWNED_KAYKIT_V7' else 'USER_OWNED_SHA_RECEIPT',
   'provider':x.get('provider'),'provenance':x.get('licenseEvidence'),
   'proof':x.get('sourceSpecOrReceipt')}
 for x in players.get('rows',[]):
  if x.get('state')!='READY':continue
  path=x.get('path','')
  if not path:continue
  out[path]={'sha256':x.get('sha256'),'category':'PINNED_CC0_KAYKIT_PLAYER',
   'provider':'KayKit','proof':'characters_v2.json and CREDITS.md CC0 Yes'}
 for x in recover.get('sources',[]):
  path=x.get('path','')
  if not path:continue
  out[path]={'sha256':x.get('sha256'),'category':'PINNED_CC0_EXACT_SOURCE_SPEC',
   'provider':x.get('provider'),'proof':x.get('sourceSpec'),
   'rawSource':x.get('sourcePackFile')}
 return out

def audit():
 safe()
 proofs=known_provenance();bad=restricted()
 rows=[];counts=collections.Counter();untrusted=[]
 root=STAGE/'public'
 for path in sorted(root.rglob('*')):
  if path.is_symlink():untrusted.append({'path':str(path.relative_to(root)),'issue':'SYMLINK_PUBLIC'});continue
  if not path.is_file() or path.suffix.casefold() not in MEDIA_EXT:continue
  rel=path.relative_to(root).as_posix()
  receipt=proofs.get(rel)
  actual=sha(path)
  built=DIST/rel
  if rel in bad:status='RESTRICTED_CREDITS_PATH_FOUND'
  elif not receipt:status='MEDIA_MISSING_PROVENANCE_RECEIPT'
  elif receipt.get('sha256')!=actual:status='MEDIA_SHA_MISMATCH'
  elif not built.is_file() or built.is_symlink():status='MEDIA_MISSING_FROM_BUNDLE'
  elif sha(built)!=actual:status='MEDIA_BUNDLE_HASH_MISMATCH'
  else:status=receipt['category']
  counts[status]+=1
  if status in {'RESTRICTED_CREDITS_PATH_FOUND','MEDIA_MISSING_PROVENANCE_RECEIPT',
   'MEDIA_SHA_MISMATCH','MEDIA_MISSING_FROM_BUNDLE','MEDIA_BUNDLE_HASH_MISMATCH'}:
   untrusted.append({'path':rel,'status':status,'receipt':receipt})
  rows.append({'path':rel,'status':status,'sha256':actual,
   'receipt':receipt})
 for f in sorted(DIST.rglob('*')):
  if f.is_symlink():untrusted.append({'path':str(f.relative_to(DIST)),'issue':'DIST_SYMLINK'});continue
  if not f.is_file() or f.suffix.casefold() not in MEDIA_EXT:continue
  rel=f.relative_to(DIST).as_posix()
  if rel.startswith('assets/'):
   counts['GENERATED_BUNDLE_MEDIA_NOT_AUDITED']+=1
   untrusted.append({'path':rel,'issue':'BUILD_ARTIFACT_MEDIA_LICENSE_NOT_AUDITED'})
  elif not (root/rel).is_file():
   counts['BUNDLE_MEDIA_WITHOUT_SOURCE_PUBLIC']+=1
   untrusted.append({'path':rel,'issue':'BUNDLE_MEDIA_UNTRACED'})
 counts['UNKNOWN_INLINED_JS_CSS_SOURCES']=1
 report={
  'label':'HIGHFLY CLEAN PRIVATE 4181 LICENSE / FILE PROVENANCE AUDIT',
  'sourceCommit':PIN,'stagePrivate':True,'expectedOriginalCodeLicense':'MIT',
  'mediaCount':len(rows),'mediaStatuses':dict(counts),
  'blockedOrUnverified':untrusted,'mediaRows':rows,
  'credittedMediaFilesInBundleConfirmed':not bool(untrusted),
  'allProjectAssetRightsApproved':False,
  'allBundledCodeAndEmbeddedMediaFullyAudited':False,
  'publicCommercialReleaseApproved':False,
  'notes':['No reclassification of original with-the-project-only or CraftPix images.',
   'Compiled JS/CSS, third-party dependencies, and embedded content require a separate review.',
   'Missing files in browser are NOT evidence those files are distributed.',
   'User-owned pack source rights may differ from CC0; hash receipts do not prove redistribution permission.'],
 }
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--save',action='store_true')
 args=p.parse_args()
 report=audit()
 if args.save:
  RESULT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
 print('[CLEAN 4181 MEDIA LICENSE AUDIT] '+json.dumps({
  'mediaTotal':report['mediaCount'],'counts':report['mediaStatuses'],
  'unverifiedCount':len(report['blockedOrUnverified']),
  'unverifiedFirst15':report['blockedOrUnverified'][:15],
  'publicReleaseApproved':False,
  'log':str(RESULT) if args.save else 'READ_ONLY_NOT_SAVED'
 },indent=2,ensure_ascii=False))
