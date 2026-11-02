#!/usr/bin/env python3
"""HIGHFLY P70: integral P69 forensic audit + removable, opt-in browser log.

Only touches .workspace/highfly-p69-restore-lab/index.html and its own NEW
public/highfly/p70_browser_trace.js on --install. --audit only writes a report.
No model substitution, asset copying, license assumption, world/save/FURY edits.
P64, P43, checkpoints and the 0.44.7 source tree are strictly read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import struct
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".workspace"
LAB = WORK / "highfly-p69-restore-lab"
P64 = WORK / "highfly-origin-stage-p0"
P43 = WORK / "highfly-p43-restore-lab"
ORIGINAL = WORK / "claudecraft-v0.44.7"
REPORT = WORK / "reports/highfly-world7/P70_FULL_FORENSIC_AUDIT.json"
INDEX = LAB / "index.html"
BACKUP = LAB / ".hf-p70-browser-trace-before-index.html"
SCRIPT = LAB / "public/highfly/p70_browser_trace.js"
INJECT = '<!-- HIGHFLY_P70_FORENSIC_BROWSER_TRACE -->\n<script defer src="/highfly/p70_browser_trace.js"></script>\n'
SAMPLES = [
    "models/creatures/mech.glb",
    "models/creatures/pyre_colossus.glb",
    "models/creatures/glimmerwisp.glb",
    "models/chars/enemies/skeleton_minion.glb",
    "models/chars/enemies/skeleton_warrior.glb",
    "models/chars/players/warrior.glb",
    "models/chars/players/rogue.glb",
]
ASSET_RE = re.compile(
    r"""(?<![\w./-])/?((?:models|textures|vfx|audio|ui|fonts|skybox|skyboxes|env|assets)/[A-Za-z0-9_./-]+\.(?:glb|gltf|png|jpg|jpeg|webp|ktx2|hdr|ogg|mp3|wav))""",
    re.I,
)
ALLOWED_EXT = {".glb", ".gltf", ".png", ".jpg", ".jpeg", ".webp", ".ktx2", ".hdr", ".ogg", ".mp3", ".wav"}
MAX_SCAN_BYTES = 3_000_000

BROWSER_JS = r"""/* HIGHFLY P70 opt-in forensic logger: memory only, removable, no asset edits.
   Enable with ?hf_p70_diag=1; export JSON using the on-screen button.
   No game state, localStorage, network destinations or saves are modified. */
(function () {
'use strict';
if (!new URLSearchParams(location.search).has('hf_p70_diag')) return;
if (window.__HIGHFLY_P70_TRACE__) return;
const started = performance.now();
const events = [];
const MAX_EVENTS = 20000;
let dropped = 0;
let snapshot = {};
let lastSnapshot = '';
const originalConsole = {error: console.error, warn: console.warn};
const short = (x, n=1300) => {
  try {
    if (x instanceof Error) return String(x.stack || x.message).slice(0,n);
    if (typeof x === 'string') return x.slice(0,n);
    return JSON.stringify(x)?.slice(0,n) || String(x).slice(0,n);
  } catch (_) { return String(x).slice(0,n); }
};
function record(kind, data) {
  const entry = {second: +(performance.now()-started).toFixed(0)/1000, kind, data};
  if (events.length < MAX_EVENTS) events.push(entry);
  else dropped++;
}
window.addEventListener('error', e => {
  if (e.target && e.target !== window && (e.target.src || e.target.href)) {
    record('RESOURCE_ERROR', {url: String(e.target.src || e.target.href).split('?')[0]});
  } else {
    record('JS_ERROR', {message:short(e.message), stack:short(e.error), filename:e.filename, line:e.lineno, column:e.colno});
  }
}, true);
window.addEventListener('unhandledrejection', e =>
  record('UNHANDLED_REJECTION', {reason:short(e.reason,2500)}));
console.error = function(...args) {
  record('CONSOLE_ERROR', args.map(x => short(x)));
  return originalConsole.error.apply(this,args);
};
console.warn = function(...args) {
  record('CONSOLE_WARN', args.map(x => short(x)));
  return originalConsole.warn.apply(this,args);
};
try {
  const origFetch = window.fetch;
  window.fetch = function(...args) {
    const begin=performance.now();
    let url='';
    try {url=String(args[0]?.url || args[0]).split('?')[0];}catch(_){}
    const promise=origFetch.apply(this,args);
    promise.then(r=>{
      const ct=r.headers?.get('content-type') || '';
      if (!r.ok || /\.(glb|gltf|png|jpg|jpeg|webp|ktx2)(?:$|#)/i.test(url)) {
        record('FETCH_RESPONSE',{url,status:r.status,redirected:r.redirected,contentType:ct,ms:Math.round(performance.now()-begin),
          suspectGlbHtml:/\.glb$/i.test(url)&&/text\/html/i.test(ct)});
      }
    },e=>record('FETCH_FAILED',{url,error:short(e),ms:Math.round(performance.now()-begin)}));
    return promise;
  };
} catch(e) {record('INSTRUMENTATION_ERROR',{part:'fetch',error:short(e)});}
try {
  const open=XMLHttpRequest.prototype.open, send=XMLHttpRequest.prototype.send;
  const refs=new WeakMap();
  XMLHttpRequest.prototype.open=function(method,url,...rest) {
    refs.set(this,{method,url:String(url).split('?')[0],since:performance.now()});
    return open.call(this,method,url,...rest);
  };
  XMLHttpRequest.prototype.send=function(...args) {
    this.addEventListener('loadend',()=>{
      const meta=refs.get(this)||{};
      if (this.status>=400 || this.status===0 || /\.(glb|gltf)$/i.test(meta.url||'')) {
        let ct='';try{ct=this.getResponseHeader('content-type')||'';}catch(_){}
        record('XHR_RESPONSE',{...meta,status:this.status,contentType:ct,
          ms:Math.round(performance.now()-(meta.since||performance.now()))});
      }
    },{once:true});
    return send.apply(this,args);
  };
} catch(e) {record('INSTRUMENTATION_ERROR',{part:'xhr',error:short(e)});}
try {
  const obs=new PerformanceObserver(list=>{
    for(const entry of list.getEntries()){
      const name=String(entry.name||'').split('?')[0];
      const status=entry.responseStatus;
      if (/\.(glb|gltf)$/i.test(name) || (typeof status==='number' && status>=400))
        record('PERFORMANCE_RESOURCE',{name,status:status??null,bytes:entry.transferSize||0,ms:Math.round(entry.duration)});
    }
  });
  obs.observe({type:'resource', buffered:true});
} catch(e){record('INSTRUMENTATION_ERROR',{part:'performance',error:short(e)});}
function info(id){
  const e=document.getElementById(id);
  if (!e)return {exists:false};
  const s=getComputedStyle(e),r=e.getBoundingClientRect();
  return {exists:true,hidden:e.hidden,display:s.display,visibility:s.visibility,
    opacity:s.opacity,width:Math.round(r.width),height:Math.round(r.height),
    classes:e.className?.toString().slice(0,170),childCount:e.children.length};
}
function inspect(){
  const creator=document.getElementById('offline-select');
  const preview=document.getElementById('offline-preview-container');
  const buttons=creator?[...creator.querySelectorAll('.mini-class[data-class]')]:[];
  const data={
    start:info('start-screen'),
    server:info('server-select'),
    selectedRealm:document.getElementById('server-select')?.dataset.mode || '',
    creator:info('offline-select'),
    loading:info('loading-screen'),
    loadingStatus:(document.getElementById('ls-status')?.textContent || '').slice(0,170),
    loadingProgress:document.getElementById('ls-fill')?.style.width || '',
    preview:info('offline-preview-container'),
    previewChildren:preview?.children.length||0,
    previewCanvas:preview?.querySelectorAll('canvas').length||0,
    previewImages:preview?.querySelectorAll('img').length||0,
    classesDOM:buttons.map(b=>({key:b.dataset.class,display:getComputedStyle(b).display,
      width:Math.round(b.getBoundingClientRect().width)})),
    canvasesTotal:document.querySelectorAll('canvas').length,
    errorTextNodes:document.querySelectorAll('.error,.error-message,#error-overlay,.vite-error-overlay').length,
    viewport:[innerWidth,innerHeight],
    documentWidth:document.documentElement.scrollWidth
  };
  snapshot=data;
  const str=JSON.stringify(data);
  if (str!==lastSnapshot) {
    record('UI_TRANSITION',data);
    lastSnapshot=str;
  }
}
function exportLog(){
  inspect();
  const report={
    label:'HIGHFLY P70 BROWSER FULL FORENSICS',version:1,
    capturedAt:new Date().toISOString(),
    locationPath:location.pathname,
    queryFlags:[...new URLSearchParams(location.search).keys()],
    browser:navigator.userAgent,events, dropped, snapshot
  };
  return report;
}
function download(){
  const blob=new Blob([JSON.stringify(exportLog(),null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download='HIGHFLY_P70_BROWSER_TRACE_'+Date.now()+'.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
}
window.__HIGHFLY_P70_TRACE__={export:exportLog,download,events};
function mount(){
  const panel=document.createElement('div');
  panel.id='hf-p70-trace-panel';
  panel.style.cssText='position:fixed;z-index:2147483641;right:8px;top:8px;background:#071323ee;border:1px solid #55c6ee;color:#fff;border-radius:8px;padding:8px;max-width:min(390px,75vw);font:11px/1.4 monospace;box-shadow:0 3px 12px #000a';
  const headline=document.createElement('div');
  headline.style.cssText='margin-bottom:4px;font-weight:700';
  const button=document.createElement('button');
  button.textContent='DESCARGAR LOG COMPLETO';
  button.style.cssText='font:700 11px system-ui;background:#124966;border:1px solid #60cbee;color:white;padding:5px 8px;border-radius:5px;cursor:pointer';
  button.addEventListener('click',download);
  const hide=document.createElement('button');
  hide.textContent='OCULTAR';
  hide.style.cssText='font:10px system-ui;margin-left:5px';
  hide.addEventListener('click',()=>{panel.style.opacity=panel.style.opacity==='0.1'?'1':'0.1';});
  panel.append(headline,button,hide);
  document.body.appendChild(panel);
  let previous='';
  setInterval(()=>{
    inspect();
    const kinds={};
    for(const event of events){
      if(/ERROR|FAILED|REJECTION|WARN|RESPONSE/.test(event.kind))
        kinds[event.kind]=(kinds[event.kind]||0)+1;
    }
    const headlineText='P70 LOG · '+events.length+' eventos · '+dropped+' omitidos · '+JSON.stringify(kinds);
    if(headlineText!==previous){headline.textContent=headlineText;previous=headlineText;}
  },1500);
  inspect();
  record('LOGGER_READY',{message:'Solo lectura del estado de juego; exportar tras reproducir el fallo'});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
else mount();
})();
"""

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safety():
    if not WORK.is_dir() or LAB.is_symlink() or not LAB.is_dir():
        raise RuntimeError("P70_PRIVATE_P69_LAB_MISSING")
    if not LAB.resolve().is_relative_to(WORK.resolve()):
        raise RuntimeError("P70_LAB_OUTSIDE_WORKSPACE")
    if INDEX.is_symlink() or not INDEX.is_file():
        raise RuntimeError("P70_LAB_INDEX_MISSING_OR_LINK")
    if SCRIPT.parent.is_symlink() or not SCRIPT.parent.is_dir():
        raise RuntimeError("P70_LAB_HIGHFLY_PUBLIC_MISSING_OR_LINK")
    for protected in [P64, P43, ORIGINAL]:
        if protected.exists() and not protected.resolve().is_relative_to(WORK.resolve()):
            raise RuntimeError("P70_UNEXPECTED_PROTECTED_SOURCE_PATH")
    return INDEX.read_bytes()

def glb_check(path: Path):
    try:
        size=path.stat().st_size
        with path.open("rb") as f:
            header=f.read(20)
        if size<20 or len(header)<20: return "BAD_SHORT_GLB"
        magic,version,length=struct.unpack("<4sII",header[:12])
        if magic!=b"glTF" or version!=2 or length!=size:
            return "BAD_GLB_HEADER_OR_LENGTH"
        if header[16:20]!=b"JSON":return "BAD_GLB_FIRST_CHUNK"
        return "GLB_HEADER_OK"
    except OSError as e:
        return "UNREADABLE_GLB:"+str(e)

def find_references(src: Path):
    found={}
    if not src.is_dir():return found
    for p in src.rglob("*"):
        if not p.is_file() or p.is_symlink() or p.suffix.lower() not in {".ts",".tsx",".js",".json",".css",".html"}:
            continue
        try:
            if p.stat().st_size>MAX_SCAN_BYTES:continue
            contents=p.read_text("utf8",errors="replace")
        except OSError:continue
        for m in ASSET_RE.finditer(contents):
            rel=m.group(1).lstrip("/")
            found.setdefault(rel,[]).append(str(p.relative_to(src)))
    return found

def path_info(root: Path, rel: str):
    target=root/"public"/rel
    if not root.is_dir():return {"state":"SOURCE_ABSENT"}
    if target.is_symlink() and not target.exists():return {"state":"BROKEN_FILE_SYMLINK"}
    if not target.is_file():return {"state":"MISSING"}
    try:
        info={"state":"EXISTS","bytes":target.stat().st_size}
        if target.suffix.lower()==".glb":info["glb"]=glb_check(target)
        return info
    except OSError as e:return {"state":"UNREADABLE","detail":str(e)}

def probe(url):
    try:
        with urlopen(url,timeout=3) as r:
            sample=r.read(24)
            return {"status":r.status,"contentType":r.headers.get("Content-Type"),
                "glbMagic":sample.startswith(b"glTF") if url.endswith(".glb") else None}
    except (HTTPError,URLError,OSError) as e:
        return {"error":str(e)[:240]}

def audit():
    safety()
    references=find_references(LAB/"src")
    html=INDEX.read_text("utf8",errors="replace")
    for m in ASSET_RE.finditer(html):
        references.setdefault(m.group(1).lstrip("/"),[]).append("index.html")
    paths=sorted(set(references)|set(SAMPLES))
    rows=[]
    for rel in paths:
        lab=path_info(LAB,rel)
        stage=path_info(P64,rel)
        old=path_info(P43,rel)
        original=path_info(ORIGINAL,rel)
        label="ACCESSIBLE" if lab["state"]=="EXISTS" else "NOT_ACCESSIBLE_IN_P69"
        if lab.get("glb","").startswith("BAD_"):label="INVALID_GLB"
        if lab["state"]!="EXISTS" and original["state"]=="EXISTS":
            label="ORIGINAL_EXISTS_LICENSE_NOT_YET_REVERIFIED"
        rows.append({"url":"/"+rel,"sources":sorted(set(references.get(rel,[])))[:16],
            "p69":lab,"p64":stage,"p43":old,"claudecraftReference":original,
            "decision":label,"license":"NOT_DETERMINED_BY_PATH_ALONE"})
    summary=dict(Counter(r["decision"] for r in rows))
    top_problems=[r for r in rows if r["decision"]!="ACCESSIBLE"]
    links={}
    for item in sorted((LAB/"public").iterdir()):
        if item.is_symlink():
            links[item.name]={"target":os.readlink(item),"works":item.exists(),
                "directory":item.is_dir()}
    highfly=LAB/"public/highfly"
    if highfly.is_dir():
        links["highflyChildLinks"]={
            p.name:p.exists() for p in sorted(highfly.iterdir()) if p.is_symlink()
        }
    variants={}
    for label,p in {"p69":INDEX,"p64":P64/"index.html","p43":P43/"index.html"}.items():
        if p.is_file():
            text=p.read_text("utf8",errors="replace")
            variants[label]={"sha256":sha(p.read_bytes()),
                "hasNativeOffline":"id=\"offline-select\"" in text,
                "hasNineClasses":sum(bool(re.search(r'data-class="'+cl+'"',text)) for cl in
                    ('warrior','paladin','hunter','rogue','priest','shaman','mage','warlock','druid')),
                "entryModule":'<script type="module" src="/src/main.ts"></script>' in text,
                "p42HunterFilter":"/highfly_p42_hunter.js" in text,
                "p47UiFilter":"/highfly/p47.js" in text,
                "p69BootRetry":"p69_native_boot_retry.js" in text,
                "p69CreatorCSS":"p69_native_creator_clean.css" in text,
                "p70Trace":INJECT in text}
    report={
        "name":"HIGHFLY_P70_FULL_P69_FORENSIC_AUDIT","utc":datetime.now(timezone.utc).isoformat(),
        "scope":"READ_ONLY_SOURCES_NO_MODEL_COPY",
        "purpose":"P69 vs P64/P43 and pinned ClaudeCraft reference; provenance is not license approval",
        "p69":str(LAB),"staticRefsFound":len(references),
        "assetPathsChecked":len(paths),"counts":summary,"problems":top_problems,
        "sampleRows":[r for r in rows if r["url"].lstrip("/") in SAMPLES],
        "allResources":rows,"p69PublicLinks":links,"entryVariants":variants,
        "httpLive":{
            "index":probe(f"http://127.0.0.1:{os.environ.get('HF_P70_PORT', '4176')}/"),
            "main":probe(f"http://127.0.0.1:{os.environ.get('HF_P70_PORT', '4176')}/src/main.ts"),
            "sampleMech":probe(f"http://127.0.0.1:{os.environ.get('HF_P70_PORT', '4176')}/models/creatures/mech.glb"),
        },
        "limitations":[
            "Static string paths miss dynamically constructed URLs; browser log completes evidence",
            "A valid GLB header does not prove that its meshes/materials load",
            "A matching upstream name is NOT a license grant",
            "No browser gameplay validation performed here",
            "No binary or original asset is copied by P70"
        ]
    }
    if REPORT.is_symlink():raise RuntimeError("P70_REPORT_SYMLINK")
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n","utf8")
    print("[P70 AUDIT] paths",len(paths),"summary",json.dumps(summary,ensure_ascii=False))
    print("[P70 AUDIT] p69 links",json.dumps({k:v for k,v in links.items() if k!="highflyChildLinks"},ensure_ascii=False))
    print("[P70 AUDIT] sample failures",json.dumps([{"url":r["url"],"decision":r["decision"],"p69":r["p69"],"p64":r["p64"]} for r in top_problems[:12]],ensure_ascii=False))
    print("[P70 AUDIT] output:",REPORT)
    print("[P70 AUDIT] IMPORTANT: no assets were changed; do not infer license from filename")
    return report

def install():
    old=safety()
    if BACKUP.exists() or BACKUP.is_symlink() or SCRIPT.exists() or SCRIPT.is_symlink() or INJECT.encode() in old:
        raise RuntimeError("P70_ALREADY_INSTALLED_OR_EXISTING_DIAGNOSTIC_REVIEW_BEFORE_RETRY")
    if old.count(b"</head>")!=1:raise RuntimeError("P70_INDEX_HEAD_DRIFT")
    if b"p69_native_boot_retry.js" not in old or b'id="offline-select"' not in old:
        raise RuntimeError("P70_EXPECTED_NATIVE_P69_ENTRY_NOT_FOUND")
    new=old.replace(b"</head>",INJECT.encode()+b"</head>",1)
    BACKUP.write_bytes(old)
    if BACKUP.read_bytes()!=old:raise RuntimeError("P70_BACKUP_VERIFY_FAILED")
    try:
        with SCRIPT.open("x",encoding="utf8") as f:f.write(BROWSER_JS)
        if INDEX.read_bytes()!=old:raise RuntimeError("P70_CONCURRENT_INDEX_EDIT")
        INDEX.write_bytes(new)
        if INDEX.read_bytes()!=new:raise RuntimeError("P70_INDEX_VERIFY_FAILED")
    except BaseException:
        if INDEX.is_file() and not INDEX.is_symlink():INDEX.write_bytes(old)
        if SCRIPT.is_file() and not SCRIPT.is_symlink() and SCRIPT.read_text("utf8")==BROWSER_JS:SCRIPT.unlink()
        raise
    print("[P70 INSTALLED] Reversible browser logger installed in P69 only.")
    print("[P70 INSTALLED] Enable at ?hf_p69_boot=1&hf_p70_diag=1")
    print("[P70 INSTALLED] DOWNLOAD LOG COMPLETO after reproducing the error.")

def remove():
    current=safety()
    if not BACKUP.is_file() or BACKUP.is_symlink() or not SCRIPT.is_file() or SCRIPT.is_symlink():
        raise RuntimeError("P70_REMOVE_BACKUP_OR_DIAG_MISSING")
    if SCRIPT.read_text("utf8")!=BROWSER_JS:
        raise RuntimeError("P70_REMOVE_SCRIPT_CHANGED_MANUALLY")
    if current.count(INJECT.encode())!=1:
        raise RuntimeError("P70_REMOVE_INJECTION_DRIFT")
    restored=current.replace(INJECT.encode(),b"",1)
    if BACKUP.read_bytes()!=restored:
        raise RuntimeError("P70_REMOVE_INDEX_CHANGED_SINCE_INSTALL_STOP")
    INDEX.write_bytes(restored)
    SCRIPT.unlink()
    BACKUP.unlink()
    print("[P70 REMOVED] Original P69 index restored byte-for-byte. No other files touched.")

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    mode=cli.add_mutually_exclusive_group()
    mode.add_argument("--install",action="store_true",help="Audit and install removable opt-in browser logger")
    mode.add_argument("--remove",action="store_true",help="Remove the installed logger after hash checks")
    args=cli.parse_args()
    if args.remove:remove()
    else:
        audit()
        if args.install:install()
