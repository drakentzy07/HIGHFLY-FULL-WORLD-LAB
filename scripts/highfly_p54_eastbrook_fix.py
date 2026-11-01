#!/usr/bin/env python3
"""HIGHFLY P54: source-scoped Eastbrook blacksmith normalization + UI + inventory.

Applies ONLY inside the private, pre-existing P53 stage. The authored x=2,z=-112
blacksmith decor record, physics footprint and NPC remain intact. Its visual
is replaced with the P8-approved hexb_workshop and fitted to the authored
8.4 x 9 x 8.1 footprint; the distant impostor is fitted consistently.
Requires P51, P53, P8, and P9 preflight; never copies private GLBs to git.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
OUT = ROOT / '.workspace/reports/highfly-p54'
PROPS_REL = 'src/render/props.ts'
TOWN_REL = 'src/render/eastbrook_town.ts'
HTML_REL = 'index.html'
CSS_REL = 'public/highfly/p54_eastbrook_ui.css'
JS_REL = 'public/highfly/p54_eastbrook_ui.js'
MARK = 'HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION'

PROPS_NEAR_OLD = '''    const g = new THREE.Group();
    const holder = addParts(g, d.key as PropKey, { scale: d.scale ?? 1 });'''
PROPS_NEAR_NEW = '''    const g = new THREE.Group();
    // HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION: this is the single authored
    // Smith Haldren decor at (2,-112), NOT the Eastbrook building registry.
    // Preserve its source placement, sim collider (hw=4.2/hd=4.05) and NPC.
    // The P8-approved workshop GLB is fit to its physical 8.4x9x8.1 box.
    const hfP54Smith = d.key === 'kmedBlacksmith' &&
      Math.abs(d.x - 2) < 0.001 && Math.abs(d.z + 112) < 0.001;
    const hfP54Key: PropKey = hfP54Smith ? 'hexbWorkshop' : d.key as PropKey;
    const hfP54Asset = hfP54Smith ? propAsset(hfP54Key) : null;
    const hfP54Scale: Scale = hfP54Asset ? [
      8.4 / Math.max(0.0001, hfP54Asset.size.x),
      9.0 / Math.max(0.0001, hfP54Asset.size.y),
      8.1 / Math.max(0.0001, hfP54Asset.size.z),
    ] : d.scale ?? 1;
    const holder = addParts(g, hfP54Key, { scale: hfP54Scale });'''

PROPS_FAR_OLD = '''    const a = propAsset(d.key as PropKey);
    const scale = typeof d.scale === 'number' ? d.scale : 1;
    // only skyline-scale decor earns a sprite; small dressing is sub-pixel
    // out where the sprites live
    if (a.size.y * scale < 7) continue;
    used.set(d.key, a);'''
PROPS_FAR_NEW = '''    // HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION: far skyline sprites must use
    // the exact same licensed workshop as the near scene (no KMED ghost).
    const hfP54Smith = d.key === 'kmedBlacksmith' &&
      Math.abs(d.x - 2) < 0.001 && Math.abs(d.z + 112) < 0.001;
    const hfP54Key: PropKey = hfP54Smith ? 'hexbWorkshop' : d.key as PropKey;
    const a = propAsset(hfP54Key);
    const scale = typeof d.scale === 'number' ? d.scale : 1;
    if (!hfP54Smith && a.size.y * scale < 7) continue;
    used.set(hfP54Key, a);'''

INVENTORY_ANCHOR = '  const houseHeight = HOUSE_HEIGHT;'
INVENTORY_TS = '''  // HIGHFLY_P54_INVENTORY: read-only exact placement provenance, opt-in only.
  if (typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).get('hf_p54_inventory') === '1') {
    const hfP54Records: Array<Record<string, string | number | boolean>> = [];
    for (const b of activeContent.props.buildings) {
      if (b.x < -110 || b.x > 55 || b.z < -155 || b.z > -45) continue;
      hfP54Records.push({source:'buildings', id:b.id ?? '-',
        model:b.assetId ?? '-', kind:b.kind, x:b.x,z:b.z,
        w:b.w,d:b.d,rot:b.rot, height:b.height ?? 0,
        officialEastbrook:builtInWorld && isEastbrookRebuildBuilding(b)});
    }
    for (const d of activeContent.props.decorProps ?? []) {
      if (d.x < -110 || d.x > 55 || d.z < -155 || d.z > -45) continue;
      const smith = d.key === 'kmedBlacksmith' &&
        Math.abs(d.x-2) < 0.001 && Math.abs(d.z+112) < 0.001;
      const key = smith ? 'hexbWorkshop' : d.key;
      hfP54Records.push({source:'decorProps', id:smith?'eastbrook_smith_haldren_decor':'-',
        model:PROP_ASSET_DEFS[key]?.url ?? '-', kind:d.key, x:d.x,z:d.z,
        scale:d.scale ?? 1, r:d.r ?? 0, h:d.h ?? 0,
        officialEastbrook:false});
    }
    console.info('[HIGHFLY P54] Estructuras y decoraciones de Eastbrook:',hfP54Records);
    console.table(hfP54Records);
    (window as typeof window & { __HIGHFLY_P54_EASTBROOK?: unknown })
      .__HIGHFLY_P54_EASTBROOK = hfP54Records;
  }
'''

FAR_IMPOSTOR_ASSET = '''    instances.push({
      asset: d.key,
      x: d.x,'''
FAR_IMPOSTOR_REPLACE = '''    instances.push({
      asset: hfP54Key,
      x: d.x,'''
FAR_IMPOSTOR_SCALES = '''      widthScale: scale,
      heightScale: scale,
    });'''
FAR_IMPOSTOR_SCALES_REPLACE = '''      widthScale: hfP54Smith ? 8.4 / Math.max(0.0001, a.size.x, a.size.z) : scale,
      heightScale: hfP54Smith ? 9.0 / Math.max(0.0001, a.size.y) : scale,
    });'''

TOWN_ANCHOR = '''  const monumentBody = buildRealmBuilderMonumentBody(monumentTemplate.raw, monumentSeat);
  group.add(monumentBody.group);
  const monumentFx = buildRealmBuilderMonumentFx(monumentSeat);
  group.add(monumentFx.group);'''
TOWN_REPLACE = TOWN_ANCHOR + '''
  // HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION: measure the actual statue and FX
  // independently BEFORE the P51 optional hide. Never touch the service ID.
  if (new URLSearchParams(window.location.search).get('hf_p54_inventory') === '1') {
    group.updateMatrixWorld(true);
    const hfP54BodySize = new THREE.Box3().setFromObject(monumentBody.group)
      .getSize(new THREE.Vector3());
    const hfP54FxSize = new THREE.Box3().setFromObject(monumentFx.group)
      .getSize(new THREE.Vector3());
    console.info('[HIGHFLY P54] Monumento original: id=eastbrook_realm_builder_monument',{
      x:monumentSeat.x,z:monumentSeat.z,expectedHeight:monumentSeat.nativeHeight,
      body: hfP54BodySize.toArray(), effects: hfP54FxSize.toArray(),
      status:'AUDIT ONLY - compare with ?hf_probe_monument=hide',
    });
  }'''

CSS = '''/* HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION — final loading layout.
   Native #ls-fill is still driven by game progress. No fake percentage. */
#loading-screen { isolation:isolate; }
#loading-screen .ls-progress {
  display:block!important; position:absolute!important; box-sizing:border-box!important;
  z-index:3!important; top:auto!important; bottom:clamp(8px,3.5dvh,30px)!important;
  left:50%!important; right:auto!important; transform:translateX(-50%)!important;
  width:min(820px,82vw)!important; height:clamp(80px,19dvh,120px)!important;
  min-height:0!important; max-height:none!important; padding:0!important;
  margin:0!important; border:0!important; background:transparent!important;
  box-shadow:none!important; overflow:visible!important;
}
#loading-screen #ls-status {
  display:block!important; position:absolute!important; inset:0 0 auto!important;
  height:29px!important; width:100%!important; margin:0!important; padding:0!important;
  text-align:center!important; font:700 clamp(13px,1.9vw,22px)/29px Georgia,serif!important;
}
#loading-screen .ls-bar {
  display:block!important; position:absolute!important; left:0!important; right:0!important;
  top:32px!important; height:16px!important; width:100%!important;
  box-sizing:border-box!important; padding:0!important; margin:0!important;
  border:2px solid #e7b77c!important; border-radius:16px!important;
  background:#09051ccf!important; overflow:hidden!important;
}
#loading-screen #ls-fill {display:block!important; height:100%!important;}
#loading-screen #ls-tip {
  display:grid!important; place-items:center!important;
  position:absolute!important; top:54px!important; bottom:auto!important;
  left:50%!important; right:auto!important; transform:translateX(-50%)!important;
  box-sizing:border-box!important; width:100%!important; max-width:100%!important;
  height:44px!important; min-height:44px!important; max-height:44px!important;
  margin:0!important; padding:3px 14px!important; overflow:hidden!important;
  text-align:center!important; align-content:center!important; justify-content:center!important;
  font:clamp(10px,1.05vw,13px)/17px Arial,sans-serif!important;
  background:#06031ac9!important; border:1px solid #bc8ddd55!important;
  border-radius:8px!important; white-space:normal!important;
}
html:not(.hf-p54-debug-ui) #highfly-p35-download,
html:not(.hf-p54-debug-ui) [data-highfly-p54-qa-hidden="1"] {
 display:none!important; visibility:hidden!important; pointer-events:none!important;
}
@media (pointer:coarse) and (orientation:landscape), (max-height:430px) and (orientation:landscape) {
 #loading-screen .ls-progress {bottom:max(5px,1.5dvh)!important;height:79px!important;width:83vw!important;}
 #loading-screen #ls-status {height:19px!important;font-size:13px!important;line-height:19px!important;}
 #loading-screen .ls-bar {top:22px!important;height:13px!important;}
 #loading-screen #ls-tip {top:39px!important;height:35px!important;min-height:35px!important;
  max-height:35px!important;padding:2px 9px!important;font-size:10px!important;line-height:14px!important;}
}
'''
JS = '''// HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION: keep QA data, hide only QA controls.
(function(){
 'use strict';
 const qp=new URLSearchParams(window.location.search);
 if(qp.get('hf_debug_ui')==='1') {document.documentElement.classList.add('hf-p54-debug-ui');return;}
 let queued=false;
 function scan(){
   queued=false;
   for(const el of document.querySelectorAll('button,a,[role="button"],#highfly-p35-download,[id*="highfly-log"],[class*="highfly-log"]')){
     if(el.id==='highfly-p35-download'){
       el.setAttribute('data-highfly-p54-qa-hidden','1');continue;
     }
     const s=(el.textContent||'').replace(/\\s+/g,' ').trim();
     if((/^HIGHFLY P35\\s*[-·]\\s*NPC\\s*\\/\\s*BOLSA$/i.test(s) ||
         (/HIGHFLY\\s+LOG/i.test(s) && /DESCARGAR/i.test(s) && /fallos?/i.test(s))) &&
         s.length<180){
       el.setAttribute('data-highfly-p54-qa-hidden','1');
     }
   }
   const tip=document.getElementById('ls-tip');
   if(tip && /\\b(?:9|nine)\\s+(?:clases|classes)\\b/i.test(tip.textContent||'')){
     tip.textContent='Tu cazador aprende habilidades físicas y mágicas: combiná movimientos y ataques.';
   }
 }
 function schedule(){if(queued)return;queued=true;requestAnimationFrame(scan);}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',schedule,{once:true});else schedule();
 new MutationObserver(schedule).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();
'''

def once(source: str, old: str, new: str, label: str) -> str:
    count=source.count(old)
    if count!=1:
        raise RuntimeError('P54_ANCHOR_DRIFT_'+label+' count='+str(count))
    return source.replace(old,new,1)

def patch_props(source: str) -> str:
    if MARK in source: raise RuntimeError('P54_ALREADY_APPLIED_PROPS')
    source=once(source,PROPS_NEAR_OLD,PROPS_NEAR_NEW,'DECOR_NEAR')
    source=once(source,INVENTORY_ANCHOR,INVENTORY_TS+'\n'+INVENTORY_ANCHOR,'INVENTORY')
    anchor='export function collectBuildingImpostors(seed: number): {'
    left,right=source.split(anchor,1) if source.count(anchor)==1 else (None,None)
    if left is None:raise RuntimeError('P54_IMPOSTOR_FUNCTION_DRIFT')
    right=once(right,PROPS_FAR_OLD,PROPS_FAR_NEW,'DECOR_FAR')
    right=once(right,FAR_IMPOSTOR_ASSET,FAR_IMPOSTOR_REPLACE,'FAR_ASSET')
    right=once(right,FAR_IMPOSTOR_SCALES,FAR_IMPOSTOR_SCALES_REPLACE,'FAR_DIMENSIONS')
    return left+anchor+right

def patch_town(source: str) -> str:
    if MARK in source:raise RuntimeError('P54_ALREADY_APPLIED_TOWN')
    if 'HIGHFLY_P51_MONUMENT_VISUAL_PROBE' not in source:
        raise RuntimeError('P54_REQUIRES_P51')
    return once(source,TOWN_ANCHOR,TOWN_REPLACE,'MONUMENT_AUDIT')

def patch_html(source: str) -> str:
    if MARK in source:raise RuntimeError('P54_ALREADY_APPLIED_HTML')
    if 'HIGHFLY_P50_SHELL_CLEANUP' not in source:raise RuntimeError('P54_REQUIRES_P50')
    links=('<!-- '+MARK+' -->\n'
      '<link rel="stylesheet" href="/highfly/p54_eastbrook_ui.css" />\n'
      '<script defer src="/highfly/p54_eastbrook_ui.js"></script>\n')
    return once(source,'</head>',links+'</head>','HTML')

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    renderer=STAGE/'src/render/renderer.ts'
    if not renderer.is_file() or 'HIGHFLY_P53_EASTBROOK_KMED_CLUSTER_VISUAL_PROBE' not in renderer.read_text(encoding='utf8'):
        raise RuntimeError('P54_REQUIRES_P53_STAGE')
    input_files={}
    for rel in (PROPS_REL,TOWN_REL,HTML_REL):
        f=STAGE/rel
        if not f.is_file() or f.is_symlink():raise RuntimeError('P54_PRIVATE_STAGE_FILE_MISSING '+rel)
        input_files[rel]=f.read_text(encoding='utf8')
    # Verified-by-P8 owned media: in the private stage only, never copied to Git.
    workshop=STAGE/'public/models/biome/hexb_workshop.glb'
    if not workshop.is_file() or workshop.is_symlink() or workshop.stat().st_size < 100:
        raise RuntimeError('P54_P8_APPROVED_WORKSHOP_NOT_AVAILABLE')
    transformed={PROPS_REL:patch_props(input_files[PROPS_REL]),
                 TOWN_REL:patch_town(input_files[TOWN_REL]),
                 HTML_REL:patch_html(input_files[HTML_REL])}
    for rel in (CSS_REL,JS_REL):
        if (STAGE/rel).exists() or (STAGE/rel).is_symlink():raise RuntimeError('P54_OUTPUT_ALREADY_EXISTS '+rel)
    result={'phase':'HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION','mode':'DRY_RUN',
        'sourceDecor':'ZONE1_PROPS.decorProps kmedBlacksmith (2,-112)',
        'replacement':'P8-owned hexb_workshop fitted to 8.4x9x8.1',
        'nearAndFar':'matched by exact source coordinate',
        'monument':'READ_ONLY_MEASURE; do not identify cone without probe',
        'miniHouses':'?hf_p54_inventory=1 plus existing P50 exact town audit',
        'qaUi':'?hf_debug_ui=1 to reveal diagnostic buttons',
        'gameplaySimulationNpcQuestsCollidersSavesChanged':False,
        'browserVerified':False,'androidVerified':False}
    if not apply:
        print('[HIGHFLY P54] '+json.dumps(result,ensure_ascii=False,indent=2));return result
    backups=[];created=[]
    try:
        for rel in transformed:
            file=STAGE/rel;dest=OUT/'backups'/rel
            if dest.exists() or dest.is_symlink():raise RuntimeError('P54_BACKUP_EXISTS '+rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,dest)
            if sha(file)!=sha(dest):raise RuntimeError('P54_BACKUP_INTEGRITY '+rel)
            backups.append((file,dest))
        for rel,data in ((CSS_REL,CSS),(JS_REL,JS)):
            dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('x',encoding='utf8') as f:f.write(data)
            created.append(dest)
        for rel,text in transformed.items():
            file=STAGE/rel
            if file.read_text(encoding='utf8')!=input_files[rel]:
                raise RuntimeError('P54_STAGE_CHANGED_CONCURRENTLY '+rel)
            file.write_text(text,encoding='utf8')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        for path,backup in backups:
            if backup.is_file():shutil.copy2(backup,path)
        for path in created:
            if path.is_file():path.unlink()
        print('[HIGHFLY P54] RED - ROLLBACK COMPLETE',file=sys.stderr)
        raise
    OUT.mkdir(parents=True,exist_ok=True)
    result['mode']='BUILD_GREEN_NOT_BROWSER_VERIFIED'
    (OUT/'P54_STATUS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('[HIGHFLY P54] '+json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--apply',action='store_true')
    args=cli.parse_args()
    run(args.apply)
