#!/usr/bin/env python3
"""Restore the eight real CC0 KayKit player GLBs already built in ClaudeCraft 0.44.7.

No re-import from ZIP, no attempt to invent or change animations.
Require exact ORIGINAL pinned SHA, original characters_v2.json mapping and
CREDITS.md proving KayKit models/rig animations CC0 1.0 redistribution.
Only copy missing verified binaries into isolated HIGHFLY CLEAN private lab.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
ORIG=WORK/'claudecraft-v0.44.7'
LAB=WORK/'highfly-origin-clean-0447'
SPEC=ORIG/'scripts/assets/specs/characters_v2.json'
CREDITS=ORIG/'CREDITS.md'
REPORT=WORK/'reports/highfly-clean-0447/RESTORED_PINNED_CC0_PLAYERS.json'
PIN='493c35a108cef6c8aa290e8793107b1cd117886e'
ALLOWED={'knight','mage','barbarian','rogue','rogue_hooded','druid','ranger','paladin'}

def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for chunk in iter(lambda:stream.read(2*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def glb(f):
 with f.open('rb') as src:
  b=src.read(20)
  if len(b)<20 or b[:4]!=b'glTF':return None
  v,n=struct.unpack_from('<II',b,4)
  if v!=2 or n!=f.stat().st_size or b[16:20]!=b'JSON':return None
  size=struct.unpack_from('<I',b,12)[0]
  if size>8_000_000:return None
  obj=json.loads(src.read(size).decode('utf8'))
 return {'skins':len(obj.get('skins',[])),
  'skinnedNodes':sum('skin' in n for n in obj.get('nodes',[])),
  'animations':len(obj.get('animations',[])),
  'meshCount':len(obj.get('meshes',[])),
  'clipSample':[x.get('name','') for x in obj.get('animations',[])[:12]]}

def plan():
 for p in (ORIG,LAB):
  if p.is_symlink() or not p.is_dir() or not p.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError('CLEAN_CC0_WRONG_OR_UNSAFE_LAB')
 for f in (SPEC,CREDITS,LAB/'src/main.ts',LAB/'index.html'):
  if f.is_symlink() or not f.is_file():raise RuntimeError('CLEAN_CC0_REQUIRED_FILE_MISSING '+str(f))
 commit=subprocess.check_output(['git','-C',str(ORIG),'rev-parse','HEAD'],text=True).strip()
 if commit!=PIN:raise RuntimeError('CLEAN_CC0_SOURCE_NOT_PINNED')
 credits=CREDITS.read_text('utf8')
 for evidence in ('Character models + animations','Kay Lousberg (KayKit)','CC0 1.0','Extra character animation library (Rig_Medium)'):
  if evidence not in credits:raise RuntimeError('CLEAN_CC0_RIGHTS_EVIDENCE_MISSING '+evidence)
 spec=json.loads(SPEC.read_text('utf8'))
 if len(spec.get('items',[]))!=8 or 'addClipsFrom' not in spec.get('defaults',{}):
  raise RuntimeError('CLEAN_CC0_UNEXPECTED_SOURCE_SPEC')
 rows=[]
 for item in spec['items']:
  rel=item.get('out','')
  src_label=item.get('src','')
  if (rel!='models/chars/players/'+Path(rel).stem+'.glb'
      or Path(rel).stem not in ALLOWED
      or not src_label.startswith('tmp/asset_src/kaykit/')
      or not src_label.endswith('.glb')):
   raise RuntimeError('CLEAN_CC0_UNEXPECTED_MODEL_LINEAGE '+rel)
  src=ORIG/'public'/rel
  dst=LAB/'public'/rel
  if not src.is_file() or src.is_symlink():
   rows.append({'path':rel,'state':'ORIGINAL_BINARY_UNAVAILABLE'});continue
  info=glb(src)
  if not info or info['meshCount']<1 or info['skins']<1 or info['skinnedNodes']<1 or info['animations']<8:
   rows.append({'path':rel,'state':'ORIGINAL_GLB_NOT_FULL_CHARACTER',
    'glb':info});continue
  if dst.exists() or dst.is_symlink():
   same=dst.is_file() and not dst.is_symlink() and sha(src)==sha(dst)
   rows.append({'path':rel,'state':'ALREADY_IDENTICAL' if same else 'EXISTING_DIFFERENT_NEVER_OVERWRITE'})
   continue
  rows.append({'path':rel,'state':'READY','source':str(src),'sha256':sha(src),
   'bytes':src.stat().st_size,'glb':info,'upstreamSpec':str(SPEC.relative_to(ORIG))})
 if len({r['path'] for r in rows})!=8:raise RuntimeError('CLEAN_CC0_EIGHT_PLAYER_CONTRACT_MISSING')
 return rows

def apply():
 if REPORT.exists() or REPORT.is_symlink():raise RuntimeError('CLEAN_CC0_REPORT_ALREADY_EXISTS')
 rows=plan()
 done=[]
 try:
  for row in rows:
   if row['state']!='READY':continue
   src=Path(row['source']);dst=LAB/'public'/row['path']
   if sha(src)!=row['sha256']:raise RuntimeError('CLEAN_CC0_SOURCE_CHANGED')
   dst.parent.mkdir(parents=True,exist_ok=True)
   with src.open('rb') as inf,dst.open('xb') as outf:
    shutil.copyfileobj(inf,outf)
   done.append(dst)
   if sha(dst)!=row['sha256']:raise RuntimeError('CLEAN_CC0_COPY_HASH_BAD')
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps({
   'phase':'RESTORE_EIGHT_NATIVE_KAYKIT_CC0_PLAYERS_FROM_PINNED_CLAUDECRAFT',
   'timestampUtc':datetime.now(timezone.utc).isoformat(),
   'codeModified':False,'sourceModified':False,'otherLabsModified':False,
   'copyrightEvidence':'CREDITS.md KayKit CC0 + scripts/assets/specs/characters_v2.json',
   'mode':'APPLY','installed':len(done),'rows':rows,
   'worldPlayableVerified':False,
   'note':'This solves ONLY 8 player base bodies; other animation and world asset references still need their own provenance checks.'
  },indent=2,ensure_ascii=False)+'\n','utf8')
  print('[CLEAN CC0 CHARACTERS APPLIED] '+json.dumps({
   'added':len(done),'readyInitially':sum(x['state']=='READY' for x in rows),
   'unchangedOriginal':True,'otherLabsUntouched':True,
   'statusCounts':dict(__import__('collections').Counter(x['state'] for x in rows)),
   'report':str(REPORT),'browserVerified':False
  },ensure_ascii=False,indent=2))
 except BaseException:
  for f in reversed(done):
   if f.is_file() and not f.is_symlink():f.unlink()
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true')
 args=p.parse_args()
 if args.apply:apply()
 else:
  rows=plan()
  print('[CLEAN CC0 CHARACTERS PREFLIGHT] '+json.dumps({
   'pinnedSource':PIN,'verifiedRows':len(rows),
   'statusCounts':dict(__import__('collections').Counter(x['state'] for x in rows)),
   'rows':[{k:v for k,v in row.items() if k!='source'} for row in rows],
   'codeModified':False,'browserVerified':False},indent=2,ensure_ascii=False))
