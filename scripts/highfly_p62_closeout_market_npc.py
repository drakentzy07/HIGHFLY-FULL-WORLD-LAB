#!/usr/bin/env python3
"""HIGHFLY P62 — one-step PRIVATE Eastbrook visual closing pass.

1) Replace the two wrong "mini house" stall visuals, both from the SAME URL,
   with licensed Quaternius Medieval Village Market_Stand_1 GLB (CC0).
2) Respect P37/P44 NPC's highfly_npc_ role in P36 fallback instead of
   falling through to rogue and then warrior regardless of authored role.

Keeps all NPC names, merchant services, coordinates, physics, quests and
saves unchanged. Requires P59 existing private stage; no P60 required.
P62 NEVER commits/publishes assets and never copies WOC project-only GLBs.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
ORIGINAL=p9.ORIGINAL
STAGE=p9.STAGE
OUT=ROOT/'.workspace/reports/highfly-p62'
INDEX='src/render/characters/index.ts'
STUDIO='src/editor/highfly_eastbrook_studio.ts'
MANIFEST='src/render/characters/manifest.ts'
SRC='public/models/props/market_stand_1.glb'
DST='public/models/props/eastbrook_market_stall.glb'
MARK='HIGHFLY_P62_ROLE_PRESERVING_FALLBACK'
# P61 established the known provisional asset's exact SHA-256 at user preview.
ALLOWED_OLD_SHA={
 'c476a5656874884fb08a943a084d2c4a68b1f6832ddb7fbef33e62d75c628a04',
}
ROLES=('knight','mage','rogue','barbarian','paladin','druid')
OLD='      const candidates = [roleRig, \'player_warrior\'];'
NEW="""      // HIGHFLY_P62_ROLE_PRESERVING_FALLBACK:
      // P37/P44 return highfly_npc_<role>. P36 was comparing these against
      // bare npc_... keys, so ALL of them fell back to rogue, then warrior.
      // On a failed first construction, retry the SAME role as a fixed player
      // rig, never silently replace a druid/smith/knight with rogue.
      const highflyP62Role = /^highfly_npc_(knight|mage|rogue|barbarian|paladin|druid)$/.test(key)
        ? 'player_' + key.slice('highfly_npc_'.length) : null;
      const candidates = [highflyP62Role ?? roleRig, 'player_warrior'];"""

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def patch_index(text:str)->str:
    if MARK in text:raise RuntimeError('P62_ALREADY_APPLIED')
    if 'HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK' not in text:
        raise RuntimeError('P62_P36_ORIGINAL_FALLBACK_MISSING')
    if text.count(OLD)!=1:raise RuntimeError('P62_FALLBACK_ANCHOR_DRIFT '+str(text.count(OLD)))
    return text.replace(OLD,NEW,1)

def licensed_quaternius_source()->dict:
    # Project source MIT does NOT grant WOC media rights. Quaternius is CC0
    # by this exact source -> output spec and original credits (not by filename).
    info=json.loads((ORIGINAL/'scripts/assets/specs/props.json').read_text(encoding='utf8'))
    entries=[x for x in info.get('items',[])
        if x.get('out')=='models/props/market_stand_1.glb']
    expected={'src':'tmp/asset_src/quaternius_village/Market_Stand_1.glb',
              'out':'models/props/market_stand_1.glb','type':'static'}
    if entries!=[expected]:raise RuntimeError('P62_CC0_MARKET_SOURCE_SPEC_CHANGED')
    credits=(ORIGINAL/'CREDITS.md').read_text(encoding='utf8')
    licensed=any('Medieval Village Pack (houses, inn, blacksmith, well, market, cart)' in line
        and '| Quaternius |' in line and '| CC0 1.0 | Yes |' in line
        for line in credits.splitlines())
    if not licensed:raise RuntimeError('P62_CC0_MARKET_CREDITS_NOT_VERIFIED')
    path=ORIGINAL/SRC
    if not path.is_file() or path.is_symlink():raise RuntimeError('P62_CC0_MARKET_GLB_MISSING')
    with path.open('rb') as f:header=f.read(12)
    if len(header)!=12:raise RuntimeError('P62_MARKET_GLB_TRUNCATED')
    magic,version,length=struct.unpack('<4sII',header)
    if magic!=b'glTF' or version!=2 or length!=path.stat().st_size:
        raise RuntimeError('P62_MARKET_GLB_INVALID')
    return {'provider':'Quaternius','pack':'Medieval Village Pack','license':'CC0 1.0',
        'rawSource':expected['src'],'sourcePath':SRC,'sha256':sha(path),
        'sizeBytes':path.stat().st_size}

def check()->dict:
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    studio=STAGE/STUDIO
    index=STAGE/INDEX
    manifest=STAGE/MANIFEST
    dst=STAGE/DST
    for path in (studio,index,manifest,dst):
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('P62_STAGE_INPUT_MISSING '+str(path))
    if 'HIGHFLY_P59_RAW_SCENE_PICK_TRACE' not in studio.read_text(encoding='utf8'):
        raise RuntimeError('P62_REQUIRES_P59_PRIVATE_STAGE')
    mtext=manifest.read_text(encoding='utf8')
    for marker in ('HIGHFLY_P37_NPC_CC0_ROLE_RIGS','HIGHFLY_P38_CC0_NPC_PRELOAD',
                   'HIGHFLY_P44_EASTBROOK_NPCS'):
        if marker not in mtext:raise RuntimeError('P62_NPC_DISPATCH_NOT_READY '+marker)
    index_text=index.read_text(encoding='utf8')
    new_index=patch_index(index_text)
    for role in ROLES:
        p=STAGE/'public/models/chars/players'/(role+'.glb')
        if not p.is_file() or p.is_symlink() or p.open('rb').read(4)!=b'glTF':
            raise RuntimeError('P62_ROLE_GLB_UNAVAILABLE '+role)
    previous=sha(dst)
    if previous not in ALLOWED_OLD_SHA:
        raise RuntimeError('P62_MARKET_ALREADY_CUSTOMIZED_DO_NOT_OVERWRITE '+previous)
    src=licensed_quaternius_source()
    return {'indexBefore':index_text,'indexAfter':new_index,
        'previousMarketSha256':previous,'market':src}

def run(apply=False):
    validated=check()
    status={'phase':'P62_EASTBROOK_CLOSEOUT_CC0_MARKET_AND_NPC_ROLES',
        'mode':'DRY_RUN','stallsAffectedBySameAssetUrl':[
            'eastbrook_market_stall_provisions','eastbrook_market_stall_world_market'],
        'marketBeforeSha256':validated['previousMarketSha256'],
        'marketAfterSha256':validated['market']['sha256'],
        'marketProvenance':validated['market'],
        'npcFix':'P36 fallback preserves authored HIGHFLY NPC role; P37/P44 dispatch retained',
        'gameplayChanged':False,'simChanged':False,'collidersChanged':False,
        'npcQuestsAndVendorsChanged':False,'browserVerified':False,
        'otherBuildingsChanged':False}
    if not apply:
        print('[HIGHFLY P62] '+json.dumps(status,ensure_ascii=False,indent=2));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():raise RuntimeError('P62_BACKUP_FOLDER_UNSAFE')
        if (OUT/'P62_STATUS.json').exists():raise RuntimeError('P62_ALREADY_COMPLETED')
        history=OUT.parent/'highfly-p62-preserved-attempts'
        if history.is_symlink():raise RuntimeError('P62_ARCHIVE_UNSAFE')
        history.mkdir(parents=True,exist_ok=True)
        target=history/('attempt-'+str(time.time_ns()))
        if target.exists():raise RuntimeError('P62_ARCHIVE_COLLISION')
        OUT.rename(target)
        print('[HIGHFLY P62] Older failed attempt preserved: '+str(target))
    originals={}
    try:
        for rel in (INDEX,DST):
            source=STAGE/rel;backup=OUT/'backups'/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,backup)
            if sha(source)!=sha(backup):raise RuntimeError('P62_BACKUP_HASH_FAILED '+rel)
            originals[rel]=backup
        index=STAGE/INDEX
        dst=STAGE/DST
        if index.read_text(encoding='utf8')!=validated['indexBefore']:
            raise RuntimeError('P62_CONCURRENT_NPC_CODE_CHANGE')
        if sha(dst)!=validated['previousMarketSha256']:
            raise RuntimeError('P62_CONCURRENT_MARKET_CHANGE')
        index.write_text(validated['indexAfter'],encoding='utf8')
        shutil.copy2(ORIGINAL/SRC,dst)
        if sha(dst)!=validated['market']['sha256']:
            raise RuntimeError('P62_MARKET_CC0_SHA_MISMATCH')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],
                       cwd=ROOT,check=True)
    except BaseException:
        for rel,backup in originals.items():
            if backup.is_file():shutil.copy2(backup,STAGE/rel)
        print('[HIGHFLY P62] RED — original P59 stage restored, backups saved',file=sys.stderr)
        raise
    status['mode']='BUILD_GREEN_BROWSER_PENDING'
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'P62_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',
                                      encoding='utf8')
    print('[HIGHFLY P62] '+json.dumps(status,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    run(parser.parse_args().apply)
