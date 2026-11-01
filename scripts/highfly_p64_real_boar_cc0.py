#!/usr/bin/env python3
"""P64 private-only REAL CC0 Gobkit animated boar. Verifies official provider
manifest, named GLB clips, source URL and bytes. Does not touch sim, NPC, AI,
drops, quests, spawns, saves, original project art or public Git repository.
Requires P63, guarded source replacement, builds P9 and rolls back on failure.
"""
import argparse,hashlib,json,shutil,struct,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
S=p9.STAGE;O=p9.ORIGINAL
OUT=ROOT/'.workspace/reports/highfly-p64-real-boar'
URL='https://gobkit.com/freebies/animalB/Boar.glb'
INDEX='https://gobkit.com/api/free'
DEST='public/models/creatures/highfly_gobkit_boar_cc0.glb'
MEDIA='src/render/assets/media.ts'
ASSETS='src/render/characters/assets.ts'
MANIFEST='src/render/characters/manifest.ts'
MARK='HIGHFLY_P64_REAL_BOAR_CC0'
MAX_BYTES=9*1024*1024

def download(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'HIGHFLY-CC0-asset-import/1.0'})
    with urllib.request.urlopen(req,timeout=25) as response:
        if response.geturl()!=url:raise RuntimeError('P64_PROVIDER_REDIRECT_NOT_PINNED')
        b=response.read(limit+1)
    if len(b)>limit:raise RuntimeError('P64_DOWNLOAD_SIZE_LIMIT')
    return b

def provider_metadata(raw):
    catalog=json.loads(raw)
    if URL not in catalog.get('glbs',[]):raise RuntimeError('P64_BOAR_NOT_IN_FREE_CATALOG')
    found=[m for p in catalog.get('packs',[]) for m in p.get('models',[])
           if m.get('url')==URL]
    if len(found)!=1:raise RuntimeError('P64_BOAR_SOURCE_NOT_UNIQUE')
    m=found[0]
    if m.get('id')!='boar' or m.get('rigged') is not True or m.get('format')!='glb':
        raise RuntimeError('P64_NOT_ANIMATED_REAL_BOAR')
    if 'CC0 1.0' not in m.get('license',''):
        raise RuntimeError('P64_PROVIDER_LICENSE_NOT_CC0')
    labels={c.get('name') for c in m.get('animations',[])}
    if not {'idle','walk','attack','dead'}.issubset(labels):
        raise RuntimeError('P64_PROVIDER_BOAR_NAMED_CLIPS_UNEXPECTED')
    return {'source':URL,'provider':'Gobkit Free Animal Pack Vol.2',
            'license':m['license'],'animations':sorted(labels)}

def inspect_glb(data):
    if len(data)<40:raise RuntimeError('P64_TRUNCATED_GLB')
    magic,version,length=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or length!=len(data):
        raise RuntimeError('P64_INVALID_GLB_HEADER')
    chunkLen,kind=struct.unpack_from('<I4s',data,12)
    if kind!=b'JSON' or not (12<chunkLen<len(data)-20):
        raise RuntimeError('P64_INVALID_GLTF_JSON')
    gltf=json.loads(data[20:20+chunkLen])
    named={a.get('name') for a in gltf.get('animations',[])}
    if not {'idle','walk','attack','dead'}.issubset(named):
        raise RuntimeError('P64_GLB_MISSING_SEPARATE_ANIMATIONS')
    if not gltf.get('meshes') or not gltf.get('skins'):
        raise RuntimeError('P64_GLTF_NOT_RIGGED')
    for k in ('buffers','images'):
        for item in gltf.get(k,[]):
            uri=item.get('uri')
            if uri and not uri.startswith('data:'):
                raise RuntimeError('P64_GLB_EXTERNAL_URI_NOT_ACCEPTED')
    return {'sha256':hashlib.sha256(data).hexdigest(),
            'bytes':len(data),'meshes':len(gltf['meshes']),
            'skins':len(gltf['skins']),'clips':sorted(named)}

def replace_once(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError('P64_SOURCE_ANCHOR_'+label+'_'+str(n))
    return src.replace(old,new,1)

def edit_manifest(src):
    old=('  mob_boar: {\n'
         '    url: '+chr(96)+'$'+'{CREATURES}/wild_boar.glb'+chr(96)+',\n'
         '    height: 1.45,\n'
         '    clips: WILD_BOAR,\n'
         "    tint: 'entity',\n"
         '    tintStrength: 0.4,\n'
         '  },')
    new=('  // '+MARK+': real rigged Gobkit boar, source and CC0 verified.\n'
         '  mob_boar: {\n'
         '    url: '+chr(96)+'$'+'{CREATURES}/highfly_gobkit_boar_cc0.glb'+chr(96)+',\n'
         '    height: 1.45,\n'
         "    clips: {idle:'idle', walk:'walk', run:'walk',\n"
         "      attack:['attack'], hit:['idle'], death:'dead'},\n"
         "    tint:'entity', tintStrength:0.4,\n"
         '  },')
    return replace_once(src,old,new,'BOAR_VISUAL_DEF')

def edit_media(src):
    return replace_once(src,"  'models/creatures/crab_ability_anims.glb',",
       "  'models/creatures/crab_ability_anims.glb',\n"
       "  // "+MARK+": CC0 Gobkit pack verified by source manifest.\n"
       "  'models/creatures/highfly_gobkit_boar_cc0.glb',",
       'DIRECT_MEDIA_ALLOWLIST')

def edit_assets(src):
    return replace_once(src,
       "const HIGHFLY_P39B_MOB_CC0_URLS = new Set<string>([",
       "// "+MARK+": approved lazy-load model.\n"
       "const HIGHFLY_P39B_MOB_CC0_URLS = new Set<string>([\n"
       "  'models/creatures/highfly_gobkit_boar_cc0.glb',",
       'BOAR_LAZY_LOAD')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda:f.read(1048576),b''):h.update(buf)
    return h.hexdigest()

def run(apply=False):
    p9.preflight(O,S,p9.REPORT)
    originals={}
    for rel in (MEDIA,ASSETS,MANIFEST):
        p=S/rel
        if not p.is_file() or p.is_symlink():raise RuntimeError('P64_MISSING_STAGE_'+rel)
        originals[rel]=p.read_text('utf8')
        if MARK in originals[rel]:raise RuntimeError('P64_ALREADY_APPLIED')
    if 'HIGHFLY_P63_COMBAT_C1' not in (S/'src/sim/combat/auto_attack.ts').read_text('utf8'):
        raise RuntimeError('P64_REQUIRES_P63_COMBAT')
    zone=(S/'src/sim/content/zone1.ts').read_text('utf8')
    if zone.count("mobId: 'wild_boar'")<2:
        raise RuntimeError('P64_ORIGINAL_WILD_BOAR_CAMPS_MISSING')
    target=S/DEST
    if target.exists() or target.is_symlink():
        raise RuntimeError('P64_TARGET_ALREADY_EXISTS')
    edits={MEDIA:edit_media(originals[MEDIA]),
           ASSETS:edit_assets(originals[ASSETS]),
           MANIFEST:edit_manifest(originals[MANIFEST])}
    provenance=provider_metadata(download(INDEX,5*1024*1024))
    data=download(URL,MAX_BYTES)
    binary=inspect_glb(data)
    report={'phase':'P64_REAL_ANIMATED_BOAR_CC0','mode':'DRY_RUN',
       'provider':provenance,'integrity':binary,
       'boars':'9 original mobs in 2 camps kept',
       'physicsQuestsLootAIChanged':False,'assetsPublished':False,
       'browserVerified':False}
    if not apply:
        print('[HIGHFLY P64] '+json.dumps(report,ensure_ascii=False,indent=2));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():raise RuntimeError('P64_UNSAFE_BACKUP_DIR')
        if (OUT/'P64_STATUS.json').exists():raise RuntimeError('P64_ALREADY_BUILT')
        history=OUT.parent/'highfly-p64-old-attempts'
        if history.is_symlink():raise RuntimeError('P64_HISTORY_SYMLINK')
        history.mkdir(parents=True,exist_ok=True)
        OUT.rename(history/('attempt-'+str(time.time_ns())))
    backups=[];created=[]
    try:
        for rel in originals:
            file=S/rel;bak=OUT/'backups'/rel
            bak.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,bak)
            if digest(file)!=digest(bak):raise RuntimeError('P64_BAD_BACKUP')
            backups.append((file,bak))
        for rel,new in edits.items():
            file=S/rel
            if file.read_text('utf8')!=originals[rel]:
                raise RuntimeError('P64_CONCURRENT_STAGE_CHANGE')
            file.write_text(new,encoding='utf8')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
        created.append(target)
        if digest(target)!=binary['sha256']:
            raise RuntimeError('P64_DOWNLOADED_GLB_HASH_MISMATCH')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],
                       cwd=ROOT,check=True)
    except BaseException:
        for file,bak in backups:
            if bak.is_file():shutil.copy2(bak,file)
        for file in created:
            if file.is_file():file.unlink()
        print('[HIGHFLY P64] RED — restored P63 stage',file=sys.stderr)
        raise
    report['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P64_STATUS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('[HIGHFLY P64] '+json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--apply',action='store_true')
    run(p.parse_args().apply)
