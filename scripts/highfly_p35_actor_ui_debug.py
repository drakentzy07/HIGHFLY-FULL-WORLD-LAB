#!/usr/bin/env python3
"""P35: PRIVATE stage-only NPC view + bag/inventory image diagnostics.
Never changes simulation or imports art. Dry-run by default, --apply instruments.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p35-actor-ui"
MARK="HIGHFLY_P35_ACTOR_UI"
PATHS=("index.html","src/render/renderer.ts","src/render/characters/index.ts")
JS_NAME="public/highfly_p35_actor_ui.js"
JS=r"""
// HIGHFLY_P35_ACTOR_UI. Diagnostic only; do not deploy publicly.
(function(){
  'use strict';
  if(window.__highflyP35)return;
  const started=Date.now(),records=[],totals={},limit=450;
  function safe(v){try{if(v instanceof Error)return {message:v.message,stack:String(v.stack).slice(0,1600)};return JSON.parse(JSON.stringify(v))}catch(e){return String(v).slice(0,1500)}}
  function record(kind,data){totals[kind]=(totals[kind]||0)+1;if(records.length<limit)records.push({ms:Date.now()-started,kind,data:safe(data)})}
  const oldError=console.error.bind(console),oldWarn=console.warn.bind(console);
  console.error=function(...args){record('console_error',args.slice(0,3).map(safe));oldError(...args)};
  console.warn=function(...args){record('console_warn',args.slice(0,3).map(safe));oldWarn(...args)};
  addEventListener('error',e=>record('window_error',{message:e.message,source:e.filename,line:e.lineno}),true);
  addEventListener('unhandledrejection',e=>record('unhandled_rejection',safe(e.reason)));
  function brokenImages(){
    return [...document.querySelectorAll('img')].filter(x=>x.complete&&x.naturalWidth===0).slice(0,250).map(x=>({
      url:x.currentSrc||x.src,alt:x.alt,html:x.outerHTML.slice(0,350),
      inventoryOrBag:!!x.closest('[id*="bag"],[class*="bag"],[id*="invent"],[class*="invent"],[id*="item"],[class*="item"]')
    }));
  }
  function download(){
    const payload={phase:'HIGHFLY_P35_ACTOR_UI',url:location.href,at:new Date().toISOString(),
      elapsedMs:Date.now()-started,totals,records,brokenImages:brokenImages()};
    const u=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=u;a.download='HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json';
    document.body.append(a);a.click();setTimeout(()=>{URL.revokeObjectURL(u);a.remove()},1000);
  }
  window.__highflyP35={record,download,records,totals,brokenImages};
  function mount(){if(!document.body||document.getElementById('highfly-p35-download'))return;
    const b=document.createElement('button');b.id='highfly-p35-download';
    b.textContent='HIGHFLY P35 - NPC/BOLSA';
    b.style.cssText='position:fixed;top:6px;left:6px;z-index:2147483000;background:#152131;color:#aaf1ff;border:1px solid #55b6df;border-radius:5px;padding:6px 8px;font:11px Arial;cursor:pointer';
    b.addEventListener('click',download);document.body.append(b);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
""".strip()+"\n"

def replace_one(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError("P35_EXPECTED_SOURCE_ANCHOR "+label+" "+str(n))
    return s.replace(old,new,1)

def prepare(files):
    html=replace_one(files[PATHS[0]],"</head>",
       '  <script src="/highfly_p35_actor_ui.js"></script>\n</head>','html')
    renderer=replace_one(files[PATHS[1]],
        "    const view = this.views.get(e.id);\n    if (!view) return;\n    const kind = viewBuildClass",
        "    const view = this.views.get(e.id);\n"
        "    // "+MARK+": actor created or skipped; one record per view attempt.\n"
        "    if (e.kind === 'npc' && typeof window !== 'undefined') {\n"
        "      const p = (window as unknown as {__highflyP35?: {record: (k: string,d: Record<string, unknown>) => void}}).__highflyP35;\n"
        "      p?.record('npc_view_attempt',{id:e.id,templateId:e.templateId,name:e.name,built:!!view,\n        hasVisual:!!view?.visual, rootVisible:view?.visual?.root.visible ?? null,\n        rootChildren:view?.visual?.root.children.length ?? null, x:e.pos.x,y:e.pos.y,z:e.pos.z});\n"
        "    }\n"
        "    if (!view) return;\n    const kind = viewBuildClass",
        'renderer')
    index=replace_one(files[PATHS[2]],
        "    const detail = err instanceof Error ? err.message : String(err);\n    logAssetMissOnce(",
        "    const detail = err instanceof Error ? err.message : String(err);\n"
        "    // "+MARK+": internal GLTF/animation/build errors are NOT fetch errors.\n"
        "    if (typeof window !== 'undefined') {\n"
        "      const p = (window as unknown as {__highflyP35?: {record: (k: string,d: Record<string, unknown>) => void}}).__highflyP35;\n"
        "      p?.record('actor_visual_error',{id:e.id,kind:e.kind,templateId:e.templateId,key,detail});\n"
        "    }\n"
        "    logAssetMissOnce(",
        'character-factory')
    return dict(zip(PATHS,(html,renderer,index)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');apply=ap.parse_args().apply
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    files={}
    for rel in PATHS:
        p=STAGE/rel
        if not p.is_file() or p.is_symlink():raise RuntimeError("P35_STAGE_FILE_MISSING "+rel)
        files[rel]=p.read_text(encoding='utf8')
    if any(MARK in s for s in files.values()):raise RuntimeError("P35_ALREADY_APPLIED")
    target=STAGE/JS_NAME
    if target.exists() or target.is_symlink():raise RuntimeError("P35_JS_EXISTS")
    replacements=prepare(files)
    if apply:
        # Validate backup destinations before writing any source files.
        for rel in PATHS:
            backup=OUT/"source-backups"/rel
            if backup.exists() or backup.is_symlink():raise RuntimeError("P35_BACKUP_EXISTS "+rel)
        for rel in PATHS:
            file=STAGE/rel;backup=OUT/"source-backups"/rel
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
            if hashlib.sha256(file.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
                raise RuntimeError("P35_BACKUP_INVALID "+rel)
        for rel in PATHS:
            if (STAGE/rel).read_text(encoding='utf8')!=files[rel]:raise RuntimeError("P35_SOURCE_DRIFT "+rel)
            (STAGE/rel).write_text(replacements[rel],encoding='utf8')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(JS,encoding='utf8')
    out={"mode":"APPLY" if apply else "DRY_RUN","stageOnly":True,"originalUnchanged":True,
         "gameplayChanged":False,"npcVisualsFixed":False,"browserVerified":False,
         "hooks":["npc_view_attempt","actor_visual_error","console_error","console_warn","brokenImages"],
         "timestampUtc":datetime.now(timezone.utc).isoformat()}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"P35_STATUS.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    print("[HIGHFLY] P35 ACTOR UI: "+json.dumps(out))
if __name__=='__main__':main()
