#!/usr/bin/env python3
"""HIGHFLY P50: single corrective UI layer and precise Eastbrook scene audit.

Fixes the P48 duplicated splash in loading, reuses the unpainted official
splash rather than a loading background with a baked black rectangle.
Only hides *literal QA buttons* (P35 and LOG), not their underlying diagnostics.
The Eastbrook audit is OPT-IN via ?hf_audit_eastbrook=1; it measures actual
render objects (including static town batches) and NEVER deletes buildings.
Offline save, tutorial, entities, collision, movement and assets unchanged.
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
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
OUT = ROOT / ".workspace/reports/highfly-p50"
CSS_PATH = "public/highfly/p50_shell.css"
JS_PATH = "public/highfly/p50_shell.js"
HTML_PATH = "index.html"
TOWN_PATH = "src/render/eastbrook_town.ts"
MARK = "HIGHFLY_P50_SHELL_CLEANUP"

CSS = r"""
/* HIGHFLY_P50_SHELL_CLEANUP
   A CLEAN, SINGLE IMAGE for loading. P46's loading_bg has a baked black plate,
   while P48's ::before added another big duplicate HIGHFLY logo. Do not use
   either of those pieces for the final loading composition. The native engine
   controls #ls-status, #ls-fill and #ls-tip and they remain fully interactive. */
#loading-screen {
  background:#09091f url('/highfly/official/highfly_splash.png') center center / cover no-repeat !important;
}
#loading-screen::before, #loading-screen::after {
  content:none!important;
  display:none!important;
  background:none!important;
}
#loading-screen .ls-progress {
  display:block!important;
  position:absolute!important;
  top:auto!important;
  bottom:max(3dvh,8px)!important;
  left:50%!important;
  right:auto!important;
  transform:translateX(-50%)!important;
  width:min(850px,76vw)!important;
  max-width:94vw!important;
  height:104px!important;
  min-height:0!important;
  max-height:104px!important;
  border:0!important;
  background:transparent!important;
  box-shadow:none!important;
  backdrop-filter:none!important;
  margin:0!important;
  padding:0!important;
  overflow:visible!important;
}
#loading-screen .ls-progress::before,
#loading-screen .ls-progress::after {
  content:none!important;display:none!important
}
#loading-screen #ls-status {
  display:block!important;
  position:absolute!important;
  top:0!important;left:0!important;
  height:27px!important;width:100%!important;
  margin:0!important;padding:0!important;
  border:0!important;background:transparent!important;
  color:#fff6ff!important;
  text-shadow:0 2px 8px #04010e,0 0 14px #9e41df!important;
  font:700 clamp(15px,2vw,24px)/27px Georgia,serif!important;
  text-align:center!important;
}
#loading-screen .ls-bar {
  display:block!important;
  position:absolute!important;
  top:32px!important;
  left:0!important;
  width:100%!important;
  height:16px!important;
  padding:0!important;margin:0!important;
  background:#0b0825ac!important;
  border:2px solid #edbb85!important;
  border-radius:16px!important;
  box-shadow:0 0 14px #8d3eddbf!important;
  overflow:hidden!important;
}
#loading-screen #ls-fill {
  height:100%!important;
  background:linear-gradient(90deg,#6e19be,#c553ea,#f6b8fe)!important;
  border-radius:13px!important;
}
#loading-screen #ls-tip {
  display:-webkit-box!important;
  -webkit-line-clamp:2!important;
  -webkit-box-orient:vertical!important;
  position:absolute!important;
  top:55px!important;
  left:50%!important;
  transform:translateX(-50%)!important;
  width:100%!important;
  height:44px!important;
  max-height:44px!important;
  min-height:0!important;
  padding:4px 10px!important;
  margin:0!important;
  border:0!important;
  background:#07051ab0!important;
  border-radius:8px!important;
  box-shadow:none!important;
  color:#f8edff!important;
  text-align:center!important;
  text-shadow:0 1px 4px #000!important;
  font:12px/18px Arial,sans-serif!important;
  overflow:hidden!important;
}
#loading-screen #ls-slow-hint {display:none!important}
/* Actual existing P46 UI button, not an image overlay. */
#start-screen.hf-p46-entry #mode-select {
  background:transparent!important;
  box-shadow:none!important;
  border:0!important;
}
/* Source diagnostics stay available; the two user-facing QA badges disappear.
   Exact text nodes are identified by P50 JS, not by broad game-wide selectors. */
[data-highfly-p50-qa-hidden="1"] {
  display:none!important; visibility:hidden!important;
}
#highfly-p50-eastbrook-panel {
  position:fixed;left:8px;top:14%;width:min(570px,92vw);
  max-height:55dvh;overflow:auto;z-index:2147483640;
  background:#08121df5;color:#e2fcff;
  border:1px solid #49d2f3;border-radius:10px;
  box-shadow:0 10px 25px #000a;padding:10px;
  font:11px/1.4 ui-monospace,Consolas,monospace;
  white-space:pre-wrap;pointer-events:auto;
}
#highfly-p50-eastbrook-panel summary {cursor:pointer;font-weight:bold}
#highfly-p50-eastbrook-panel button {
  background:#173b52;color:#fff;border:1px solid #3db5e7;
  border-radius:5px;padding:7px;margin:6px 0;cursor:pointer
}
@media (pointer:coarse) and (orientation:landscape){
 #loading-screen .ls-progress {
   bottom:max(2dvh,4px)!important;
   height:82px!important;max-height:82px!important;
   width:78vw!important;
 }
 #loading-screen #ls-status {height:21px!important;font:700 13px/21px Georgia,serif!important}
 #loading-screen .ls-bar {top:24px!important;height:13px!important}
 #loading-screen #ls-tip {top:45px!important;height:35px!important;max-height:35px!important;
   font:10px/15px Arial,sans-serif!important}
}
"""

JS = r"""
// HIGHFLY_P50_SHELL_CLEANUP: remove two exact debug buttons, NOT parent panels,
// and NOT game UI. Local game diagnostics remain accessible by explicit debug.
(function(){
  'use strict';
  const debug = new URLSearchParams(location.search).get('hf_debug_ui') === '1';
  if(debug)return;
  function exactDebugBadge(value){
    const text = value.replace(/\s+/g,' ').trim();
    return /^HIGHFLY P35\s*-\s*NPC\s*\/\s*BOLSA$/i.test(text) ||
      /^HIGHFLY LOG\s*[·\-]\s*\d+\s*fallos?\s*[·\-]\s*DESCARGAR$/i.test(text);
  }
  function removeQaBadges(){
    // Limit scanning to button-like leaves so a parent screen that merely
    // CONTAINS these phrases can never be hidden.
    for(const el of document.querySelectorAll('button, a, [role="button"], span, div')){
      if(el.hasAttribute('data-highfly-p50-qa-hidden'))continue;
      if(el.children.length>0)continue;
      if(exactDebugBadge(el.textContent||'')){
        const card=el.closest('button, a, [role="button"]')||el;
        card.setAttribute('data-highfly-p50-qa-hidden','1');
        card.setAttribute('aria-hidden','true');
        card.tabIndex=-1;
      }
    }
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',removeQaBadges,{once:true});
  }else removeQaBadges();
  // Legacy P35 scripts may create badges after DOMContentLoaded.
  let passes=0;
  const timer=setInterval(()=>{
    removeQaBadges();
    if(++passes>=20)clearInterval(timer);
  },1000);
})();
"""

TOWN_AUDIT = r"""
  // HIGHFLY_P50_SHELL_CLEANUP: the source GLB bounding boxes are NOT enough
  // to diagnose the giant Eastbrook block. Measure actually built render roots
  // after every placement and scaling operation. This is an opt-in diagnostic
  // only; do not delete props, collision or any quest-related world object.
  if (new URLSearchParams(window.location.search).get('hf_audit_eastbrook') === '1') {
    group.updateMatrixWorld(true);
    const highflyRows = group.children.map((obj, idx) => {
      obj.updateWorldMatrix(true, true);
      const box = new THREE.Box3().setFromObject(obj);
      const size = new THREE.Vector3();
      const center = new THREE.Vector3();
      box.getSize(size); box.getCenter(center);
      const label = obj.name || '(sin nombre)';
      return {
        index: idx, name: label,
        id: String(obj.userData.eastbrookBuildingId ?? obj.userData.assetId ?? '-'),
        x: Number(center.x.toFixed(1)), y: Number(center.y.toFixed(1)),
        z: Number(center.z.toFixed(1)),
        width: Number(size.x.toFixed(1)), height: Number(size.y.toFixed(1)),
        depth: Number(size.z.toFixed(1)),
      };
    });
    highflyRows.sort((a,b)=>Math.max(b.width,b.height,b.depth)-Math.max(a.width,a.height,a.depth));
    console.info('[HIGHFLY P50] Objetos reales de Eastbrook:',highflyRows);
    console.table(highflyRows.slice(0,30));
    window.setTimeout(()=>{
      const old=document.getElementById('highfly-p50-eastbrook-panel');
      if(old)old.remove();
      const box=document.createElement('details');
      box.id='highfly-p50-eastbrook-panel';
      box.open=true;
      const summary=document.createElement('summary');
      summary.textContent='HIGHFLY P50 · EASTBROOK · Objetos 3D reales';
      const view=document.createElement('div');
      const allRows=highflyRows.slice(0,35).map(r=>
        [r.index,r.name,r.id,
         r.width+'×'+r.height+'×'+r.depth,'x='+r.x,'z='+r.z].join(' | '));
      const data='EASTBROOK RENDER ROOTS\n'+allRows.join('\n')+
        '\n\nSi el bloque gigante no figura, probablemente viene de OTRO renderer.';
      view.textContent=data;
      const copy=document.createElement('button');
      copy.type='button';copy.textContent='COPIAR DIAGNOSTICO';
      copy.onclick=()=>void navigator.clipboard?.writeText(data);
      box.append(summary,copy,view);
      document.body.append(box);
    },0);
  }
"""

def one(source,needle,replacement,label):
    found=source.count(needle)
    if found!=1:raise RuntimeError(f"P50_ANCHOR_DRIFT_{label}: {found}")
    return source.replace(needle,replacement,1)

def patch_html(content):
    if MARK in content:raise RuntimeError("P50_ALREADY_APPLIED")
    for previous in ("HIGHFLY_P46_OFFICIAL_IDENTITY","HIGHFLY_P47_UI_LOOT_REAL_EDITOR","HIGHFLY_P48_FURY_MOBILE"):
        if previous not in content:raise RuntimeError("P50_STAGE_MISSING_"+previous)
    return one(content,"</head>",
        '<!-- '+MARK+' -->\n'
        '<link rel="stylesheet" href="/highfly/p50_shell.css" />\n'
        '<script defer src="/highfly/p50_shell.js"></script>\n'
        '</head>','INDEX_HEAD')

def patch_town(content):
    if MARK in content:raise RuntimeError("P50_ALREADY_APPLIED_TOWN")
    anchor="  group.userData.wallSegmentCount = EASTBROOK_LAYOUT.wall.segments.length;"
    return one(content,anchor,TOWN_AUDIT+"\n"+anchor,"EASTBROOK_ROOT_AUDIT")

def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    originals={}
    for name in (HTML_PATH,TOWN_PATH):
        f=STAGE/name
        if not f.is_file() or f.is_symlink():raise RuntimeError("P50_STAGE_MISSING "+name)
        originals[name]=f.read_text(encoding="utf8")
    changed={HTML_PATH:patch_html(originals[HTML_PATH]),TOWN_PATH:patch_town(originals[TOWN_PATH])}
    newfiles=[STAGE/CSS_PATH,STAGE/JS_PATH]
    if any(f.exists() or f.is_symlink() for f in newfiles):
        raise RuntimeError("P50_NEW_ASSET_ALREADY_EXISTS")
    state={"phase":"HIGHFLY_P50_CLEAN_SHELL_REAL_EASTBROOK_AUDIT",
           "mode":"DRY_RUN","cleanLoadingOneBackground":True,
           "usesNativeEngineLoadingProgress":True,"hidesExactTwoQaBadges":True,
           "eastbrookSceneAudit":"?hf_audit_eastbrook=1","giantBlockRemoved":False,
           "boarVisualFixed":False,"fury360FullComplete":False,
           "saveTutorialCombatsChanged":False,"browserVerified":False}
    if not apply:
        print("[HIGHFLY] P50 "+json.dumps(state,ensure_ascii=False))
        return state
    backups=[]
    for name in originals:
        dest=OUT/"backup"/name
        if dest.exists() or dest.is_symlink():raise RuntimeError("P50_BACKUP_ALREADY_EXISTS "+name)
    for name in originals:
        original=STAGE/name
        backup=OUT/"backup"/name
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,backup)
        if hashlib.sha256(backup.read_bytes()).digest()!=hashlib.sha256(original.read_bytes()).digest():
            raise RuntimeError("P50_BACKUP_INTEGRITY_ERROR "+name)
        backups.append((original,backup))
    created=[]
    try:
        for rel,text in ((CSS_PATH,CSS),(JS_PATH,JS)):
            dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("x",encoding="utf8") as out:out.write(text)
            created.append(dest)
        for name,result in changed.items():
            dest=STAGE/name
            if dest.read_text(encoding="utf8")!=originals[name]:
                raise RuntimeError("P50_CONCURRENT_EDIT "+name)
            dest.write_text(result,encoding="utf8")
        subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
          cwd=ROOT,check=True)
    except BaseException:
        for original,backup in backups:
            if backup.is_file():shutil.copy2(backup,original)
        for dest in created:
            if dest.is_file():dest.unlink()
        print("[HIGHFLY] P50 RED: rollback to P48 stage",file=sys.stderr)
        raise
    state["mode"]="BUILD_GREEN_NOT_BROWSER_VERIFIED"
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"P50_STATUS.json").write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("[HIGHFLY] P50 "+json.dumps(state,ensure_ascii=False))
    return state

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    options=parser.parse_args()
    run(options.apply)
