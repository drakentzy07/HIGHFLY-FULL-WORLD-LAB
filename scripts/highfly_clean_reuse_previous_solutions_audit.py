#!/usr/bin/env python3
"""HIGHFLY CLEAN: recover WHAT WORKED, before rebuilding any asset.

Compares actual previous P8/P33/P34/P37/P39B work and receipts with CLEAN 4181.
No source changes, no assets copied, no guessing that identical names confer
the same mesh or that user-owned source packs are redistributable.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,subprocess,sys
from collections import Counter
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p25_source_first_asset_audit as p25
import highfly_p21_runtime_asset_recovery as p21

WORK=ROOT/'.workspace'
ORIG=WORK/'claudecraft-v0.44.7'
OLD=WORK/'highfly-origin-stage-p0'
CLEAN=WORK/'highfly-origin-clean-0447'
DIST=CLEAN/'.highfly-private-offline-dist'
R=WORK/'reports'
OUT=R/'highfly-clean-0447/REUSE_PREVIOUS_SOLUTIONS_P8_P33_P37.json'
PIN='493c35a108cef6c8aa290e8793107b1cd117886e'
PATHS=(
 'models/chars/modular/warrior_modular.glb',
 'models/chars/players/knight.glb',
 'models/chars/players/mage.glb',
 'models/chars/players/paladin.glb',
 'models/chars/players/mage_classic.glb',
 'models/chars/players/knight_hit_variety_anims.glb',
 'models/chars/players/warrior_fury_anims.glb',
 'models/biome/hexb_townhall.glb',
 'models/biome/hexb_workshop.glb',
 'models/biome/hexb_tavern.glb',
 'models/biome/hex_church.glb',
 'models/biome/hexb_home_a.glb',
 'models/biome/hexb_home_b.glb',
 'models/biome/hexb_market.glb',
 'models/props/fence.glb',
 'models/props/bonfire.glb',
 'models/props/tent_open.glb',
 'models/props/anvil.glb',
 'models/dungeon/delve_entrance_2.glb',
 'models/props/wisp_maze_kit.glb',
 'ui/classes/warrior.webp',
 'ui/chrome/map.webp',
)
REPORT_PATHS={
 'P8 buildings':R/'highfly-p8/EASTBROOK_OWNED_BUILDINGS_P8.json',
 'P30 full media':R/'highfly-p30-master/P30_ALL_MEDIA_AND_USAGE.csv',
 'P33 recovery':R/'highfly-p33-reuse-world/P33_WORLD_SUMMARY.json',
 'P33 all decisions':R/'highfly-p33-reuse-world/P33_ALL_CC0_DECISIONS.csv',
 'P34 actor fallback':R/'highfly-p34-fixed-actors/P34_FIXED_ACTOR_FALLBACK.json',
 'P36 NPC fallback':R/'highfly-p36-npc-fallback/P36_NPC_FALLBACK.json',
 'P37 NPC six rigs':R/'highfly-p37-npc-role-rigs/P37_CC0_NPC_ROLES.json',
 'P39B mob loading':R/'highfly-p39b-all-mobs/P39B_MOB_SUMMARY.json',
 'P70 runtime sweep':R/'highfly-world7/P70_FULL_DIAGNOSIS.json',
}
def hash_file(f):
 h=hashlib.sha256()
 with f.open('rb') as source:
  for block in iter(lambda:source.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def basic(f,base):
 if f.is_symlink() or not f.is_file():return {'exists':False,'symlink':f.is_symlink()}
 if not f.resolve().is_relative_to(base.resolve()):return {'exists':False,'unsafe':True}
 info={'exists':True,'bytes':f.stat().st_size,'sha256':hash_file(f)}
 if f.suffix.casefold()=='.glb':
  with f.open('rb') as source:info['glbMagic']=source.read(4)==b'glTF'
 return info
def readjson(f):
 return json.loads(f.read_text('utf8')) if f.is_file() and not f.is_symlink() else {}
def rows_for_csv(f,needle):
 if not f.is_file() or f.is_symlink():return []
 selected=[]
 with f.open('r',encoding='utf-8-sig',errors='replace',newline='') as inp:
  reader=csv.DictReader(inp)
  for row in reader:
   if needle.casefold() in json.dumps(row,ensure_ascii=False).casefold():
    selected.append(dict(list(row.items())[:15]))
    if len(selected)>=3:break
 return selected
def safe_rel(r):
 p=PurePosixPath(r)
 return not p.is_absolute() and '..' not in p.parts and re.fullmatch(r'[A-Za-z0-9_./-]+',r) and p.suffix.casefold() in {'.glb','.gltf','.webp','.png','.jpg','.jpeg'}
def preflight():
 for root in (ORIG,CLEAN,DIST):
  if root.is_symlink() or not root.is_dir() or not root.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError('REUSE_AUDIT_PRIVATE_STAGE_OR_REFERENCE_MISSING '+str(root))
 sha=subprocess.check_output(['git','-C',str(ORIG),'rev-parse','HEAD'],text=True).strip()
 if sha!=PIN:raise RuntimeError('REUSE_AUDIT_ORIGINAL_COMMIT_CHANGED')
def audit(paths=PATHS):
 preflight()
 proofs=p25.outspec_index(ORIG)
 credits=p25.credited(ORIG)
 p8=readjson(REPORT_PATHS['P8 buildings'])
 p33=readjson(REPORT_PATHS['P33 recovery'])
 p34=readjson(REPORT_PATHS['P34 actor fallback'])
 p37=readjson(REPORT_PATHS['P37 NPC six rigs'])
 p8models={str(r.get('publicUrl','')).lstrip('/'):r for r in p8.get('buildings',[])}
 actor_status={x.get('path'):x for x in p33.get('actorStatus',[])}
 items=[]
 for rel in paths:
  if not safe_rel(rel):raise RuntimeError('REUSE_AUDIT_UNSAFE_REQUEST '+rel)
  expected='/'+rel
  src_rows=proofs.get(expected,[])
  provider_names={x.get('sourceProvider') for x in src_rows}
  source_paths={x.get('exactRawSource') for x in src_rows}
  provider=next(iter(provider_names)) if len(provider_names)==1 else None
  eligible=bool(len(provider_names)==1 and len(source_paths)==1 and provider in p25.SOURCE_PROVIDERS and credits.get(provider,False))
  current=basic(CLEAN/'public'/rel,CLEAN)
  bundled=basic(DIST/rel,DIST)
  stage=basic(OLD/'public'/rel,OLD)
  original=basic(ORIG/'public'/rel,ORIG)
  old_path=OLD/'public'/rel
  # Naming alone is a lead, never an automated conversion/copy license.
  alias_matches=[]
  if not stage['exists']:
   folder=(OLD/'public'/PurePosixPath(rel).parent)
   if folder.is_dir() and not folder.is_symlink():
    for other in sorted(folder.glob(PurePosixPath(rel).stem+'*'))[:7]:
     if other.is_file() and not other.is_symlink():alias_matches.append(other.name)
  receipt=p8models.get(rel)
  if bundled['exists']:state='PRESENT_IN_PRIVATE_BUNDLE'
  elif current['exists']:state='PRESENT_ONLY_IN_CLEAN_STAGE_NEEDS_PRIVATE_BUILD'
  elif stage['exists'] and receipt and stage['sha256']==receipt.get('glbSha256'):
   state='P8_OWNED_PRIVATE_BUILDING_REUSE_WITH_HASH_COMMERCIAL_REVIEW'
  elif stage['exists']:
   state='OLDER_STAGE_HAS_FILE_BUT_SOURCE_RECEIPT_NOT_CONFIRMED'
  elif receipt:
   state='P8_RECEIPT_FOUND_BUT_OLDER_PRIVATE_BUILDING_FILE_ABSENT'
  elif original['exists'] and eligible:
   state='ORIGINAL_EXACT_SPEC_CC0_CANDIDATE'
  elif rel=='models/chars/modular/warrior_modular.glb':
   state='P34_P36_P37_PREVIOUS_FIXED_RIG_FALLBACK_NOT_BINARY_COPY'
  else:state='NO_VERIFIED_LOCAL_FILE_FOR_THIS_URL'
  items.append({'url':expected,'status':state,'original':original,'oldStage':stage,
   'cleanStage':current,'private4181':bundled,
   'specSource':next(iter(source_paths)) if len(source_paths)==1 else None,
   'provider':provider,'providerCC0Credits':credits.get(provider,False) if provider else False,
   'upstreamExactCC0Candidate':eligible,'p8':receipt,
   'p33ActorStatus':actor_status.get(rel),'sameDirectoryAliasLeads':alias_matches,
   'p30EvidenceSamples':rows_for_csv(REPORT_PATHS['P30 full media'],rel),
   'p33EvidenceSamples':rows_for_csv(REPORT_PATHS['P33 all decisions'],rel)})
 existing_sources={
  'P8 building mapping':bool(p8.get('buildings')),
  'P33 actor status':bool(actor_status),
  'P34 missing modular fallback':bool(p34),
  'P37 six-role fixed rigs':bool(p37),
  'P30 detailed original media table':REPORT_PATHS['P30 full media'].is_file(),
  'P39B mob lazy load report':REPORT_PATHS['P39B mob loading'].is_file(),
 }
 return {'phase':'HIGHFLY_CLEAN_REUSE_PREVIOUS_SOLUTIONS_NO_COPY',
   'originalCommit':PIN,'readOnly':True,'assetCopyCount':0,
   'gameSourceEdited':False,'olderStageEdited':False,
   'reportsFound':{k:str(v) if v.is_file() else None for k,v in REPORT_PATHS.items()},
   'verifiedPriorFixes':existing_sources,
   'olderStageAccessible':OLD.is_dir() and not OLD.is_symlink(),
   'importantLessons':[
    'P8 source Medieval Hexagon model files are glTF and renamed to seven hexb_* targets for eleven Eastbrook buildings; exact P8 glbSha256 is required to reuse.',
    'P33 did not fix warrior_modular: P34 disabled missing modular provider, P36/P37 used six proven CC0 fixed-rig KayKit NPC bodies.',
    'P39B resolved eligible monsters with CC0-only sources and lazy load, rather than eager preload; its patch is OLD stage source code, not CLEAN.',
    'P30 counts and lists are an inventory, not redistribution permission.',
    'Do not restore project-only or CraftPix assets. Stage owners rights and browser completeness remain unverified.'],
   'counts':dict(Counter(x['status'] for x in items)),'items':items,
   'recommendedNextAction':'Review P34/P37 selective source transforms and exact P8 receipts; never bulk copy missing world models.'}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--save',action='store_true')
 p.add_argument('--path',action='append')
 args=p.parse_args()
 rows=tuple(x.lstrip('/') for x in args.path) if args.path else PATHS
 data=audit(rows)
 if args.save:
  if OUT.exists() or OUT.is_symlink():raise RuntimeError('REUSE_AUDIT_REPORT_ALREADY_EXISTS')
  OUT.parent.mkdir(parents=True,exist_ok=True)
  OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n','utf8')
 print('[HIGHFLY PREVIOUS SOLUTIONS AUDIT] '+json.dumps({
  'modelPathsChecked':len(rows),
  'priorFixesAvailable':data['verifiedPriorFixes'],
  'counts':data['counts'],
  'firstTargets':[{'path':x['url'],'status':x['status'],
    'priorStageExists':x['oldStage']['exists'],
    'CC0ExactSourceCandidate':x['upstreamExactCC0Candidate']}
   for x in data['items'][:25]],
  'readOnly':True,'report':str(OUT) if args.save else 'not saved'
 },indent=2,ensure_ascii=False))
