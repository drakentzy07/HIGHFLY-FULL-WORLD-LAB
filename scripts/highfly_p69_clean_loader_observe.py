#!/usr/bin/env python3
"""P69 isolated loading fix: remove embedded fake UI from actual loader.

Intended only for .workspace/highfly-p69-restore-lab on 4176. Does NOT
change splash art, native #ls-fill progress, RPG/sim, GLB, NPC, saves, P64,
P43, original assets, or build outputs. Adds new stylesheet and observational
native loader readout, with backups of index.html. --apply guarded.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p69-restore-lab'
HTML=LAB/'index.html'
PUBLIC=LAB/'public/highfly'
CSS=PUBLIC/'p69_loader_clean.css'
JS=PUBLIC/'p69_loader_observe.js'
BACKUP=LAB/'.hf-p69-loader-before-index.html'
REPORT=WORK/'reports/highfly-world7/P69_LOADER_CLEAN_OBSERVE.json'
MARK='HIGHFLY_P69_NATIVE_LOADER_CLEAN'
HTML_INJECT=(
    '<!-- '+MARK+': original splash only on landing; real native loader on its own -->\n'
    '<link rel="stylesheet" href="/highfly/p69_loader_clean.css" />\n'
    '<script defer src="/highfly/p69_loader_observe.js"></script>\n'
)
CSS_TEXT=r"""/* HIGHFLY P69 loader: no screenshot/fake bars under the real loader.
   The original splash file is unchanged; this style applies to visible loading only.
   CSS does NOT set native #ls-fill width, progress, or game completion. */
body #loading-screen.visible {
  position:fixed!important;inset:0!important;
  z-index:2147482000!important;
  box-sizing:border-box!important;
  display:flex!important;flex-direction:column!important;
  align-items:center!important;justify-content:center!important;
  overflow:hidden!important;
  width:100vw!important;height:100dvh!important;
  margin:0!important;padding:0!important;
  background-color:#090d20!important;
  background-image:
    radial-gradient(ellipse at 50% 38%,rgba(108,49,163,.29),transparent 62%),
    linear-gradient(135deg,#07121f,#16122d 58%,#070d1b)!important;
  background-position:center!important;
}
body #loading-screen.visible::before,
body #loading-screen.visible::after {
  display:none!important;content:none!important;
  background:none!important;
}
/* Don't let the original start splash (with baked fake UI) peek through. */
body:has(#loading-screen.visible) #start-screen,
body:has(#loading-screen.visible) #highfly-p46-landing {
  visibility:hidden!important;pointer-events:none!important;
}
body:has(#loading-screen.visible) #mobile-controls,
body:has(#loading-screen.visible) #mobile-action-ring,
body:has(#loading-screen.visible) #mobile-dodge {
  visibility:hidden!important;pointer-events:none!important;
}
/* Only REAL engine-owned progress and status. */
body #loading-screen.visible .ls-progress {
  position:fixed!important;
  inset:auto auto max(9dvh,env(safe-area-inset-bottom,0px)) 50%!important;
  transform:translateX(-50%)!important;
  z-index:2147482001!important;
  display:flex!important;flex-direction:column!important;
  justify-content:center!important;align-items:stretch!important;
  gap:6px!important;
  box-sizing:border-box!important;
  width:min(720px,92vw)!important;
  height:auto!important;min-height:116px!important;max-height:41dvh!important;
  margin:0!important;padding:12px 18px!important;
  overflow:auto!important;
  border:1px solid #a879e0!important;border-radius:12px!important;
  background:rgba(9,13,32,.96)!important;
  box-shadow:0 12px 32px rgba(0,0,0,.65)!important;
}
body #loading-screen.visible #ls-status {
  position:static!important;inset:auto!important;
  order:0!important;display:block!important;
  transform:none!important;
  height:auto!important;min-height:17px!important;
  width:100%!important;margin:0!important;padding:0!important;
  border:0!important;background:none!important;
  color:#f5edff!important;text-align:center!important;
  white-space:normal!important;
  font:700 clamp(12px,1.6vw,15px)/1.3 system-ui,sans-serif!important;
}
body #loading-screen.visible .ls-bar {
  position:relative!important;inset:auto!important;
  order:1!important;display:block!important;
  box-sizing:border-box!important;
  width:100%!important;height:12px!important;min-height:12px!important;
  margin:0!important;padding:0!important;
  overflow:hidden!important;
  border:1px solid #bc93eb!important;border-radius:20px!important;
  background:#221637!important;
  box-shadow:none!important;
}
body #loading-screen.visible #ls-fill {
  display:block!important;height:100%!important;
  min-height:0!important;max-width:100%!important;
  border-radius:20px!important;
  background:linear-gradient(90deg,#7734c5,#d57ffd,#79d8ff)!important;
}
body #loading-screen.visible #ls-tip,
body #loading-screen.visible #ls-slow-hint {
  position:static!important;inset:auto!important;transform:none!important;
  order:3!important;margin:0!important;padding:0!important;
  width:100%!important;height:auto!important;max-height:none!important;
  overflow-wrap:break-word!important;
  font:400 11px/1.3 system-ui,sans-serif!important;
  text-align:center!important;color:#d4c5ea!important;
  background:none!important;
}
body #loading-screen.visible #hf-p69-load-readout{
  order:2;display:block;position:static;
  min-height:17px;width:100%;
  font:600 clamp(10px,1.3vw,12px)/1.4 system-ui,sans-serif;
  text-align:center;color:#cfb8f7;
  overflow-wrap:anywhere;
}
body #loading-screen.visible #hf-p69-load-detail{
  order:4;display:block;position:static;
  width:100%;max-height:90px;margin:0;
  white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;
  font:10px/1.3 monospace;color:#f4d3ba;
}
body #loading-screen.visible #hf-p69-load-copy{
  order:5;align-self:center;
  color:#fff;background:#3e2c61;border:1px solid #a879e0;
  border-radius:7px;min-height:30px;padding:4px 13px;
  font:600 11px system-ui;cursor:pointer;
}
@media(max-height:480px) and (orientation:landscape){
  body #loading-screen.visible .ls-progress{
    bottom:max(2dvh,env(safe-area-inset-bottom,0px))!important;
    min-height:78px!important;max-height:64dvh!important;
    padding:7px 12px!important;gap:4px!important;
  }
  body #loading-screen.visible .ls-bar{height:9px!important;min-height:9px!important}
}
"""
JS_TEXT=r"""/* HIGHFLY_P69_NATIVE_LOADER_CLEAN — READ ONLY: never set loader % or UI state.
   ?hf_p69_diag=1 adds error details and a COPY button to the native loader. */
(function(){
 'use strict';
 const events=[];
 const expanded=new URLSearchParams(location.search).has('hf_p69_diag');
 const start=Date.now();
 function remember(type,detail){
   events.push({seconds:Math.round((Date.now()-start)/1000),type,
     detail:String(detail||'').slice(0,270)});
   if(events.length>32)events.shift();
 }
 window.addEventListener('error',function(e){
   if(e.target && e.target!==window && (e.target.src||e.target.href)){
     remember('RECURSO',(e.target.src||e.target.href).replace(location.origin,''));
   } else if(e.message){
     remember('JS ERROR',e.message+' at '+(e.filename||'')+':'+(e.lineno||'?'));
   }
 },true);
 window.addEventListener('unhandledrejection',function(e){
   remember('PROMESA',(e.reason&& (e.reason.message||e.reason.stack))||e.reason||'desconocido');
 });
 function mount(){
   const loader=document.getElementById('loading-screen');
   const progress=loader&&loader.querySelector('.ls-progress');
   const fill=document.getElementById('ls-fill');
   const status=document.getElementById('ls-status');
   if(!loader||!progress||!fill||!status)return;
   if(document.getElementById('hf-p69-load-readout'))return;
   const display=document.createElement('div');
   display.id='hf-p69-load-readout';
   display.setAttribute('role','status');
   display.setAttribute('aria-live','off');
   progress.append(display);
   let activeAt=0,lastWidth='',lastStatus='',lastChanged=0;
   let active=false;
   let detail=null,copy=null;
   if(expanded){
     detail=document.createElement('pre');
     detail.id='hf-p69-load-detail';
     progress.append(detail);
     copy=document.createElement('button');
     copy.id='hf-p69-load-copy';copy.type='button';
     copy.textContent='COPIAR DIAGNÓSTICO';
     progress.append(copy);
   }
   function report(now){
     const width=fill.style.width.trim();
     const nativeStatus=(status.textContent||'').trim().slice(0,180);
     const seconds=Math.round((now-activeAt)/1000);
     const age=Math.round((now-lastChanged)/1000);
     return ['HIGHFLY P69 — CARGA REAL',
       'Tiempo visible: '+seconds+' s',
       'Estado nativo: '+nativeStatus,
       'Ancho real de #ls-fill: '+(width||'no declarado'),
       'Sin cambios del motor desde: '+age+' s',
       'Recursos/eventos capturados: '+events.length,
       ...events.slice(-12).map(e=>e.seconds+'s '+e.type+' '+e.detail)].join('\n');
   }
   if(copy)copy.onclick=()=>{
     const content=report(Date.now());
     navigator.clipboard?.writeText(content).then(()=>{
       copy.textContent='COPIADO';
     }).catch(()=>{copy.textContent='SELECCIONÁ TEXTO';});
   };
   function update(){
     const now=Date.now();
     const visible=loader.classList.contains('visible');
     if(!visible){
       if(active)remember('FIN','Cortina de carga ya no visible');
       active=false;activeAt=0;lastWidth='';lastStatus='';lastChanged=0;
       display.textContent='';
       if(detail)detail.textContent='';
       return;
     }
     if(!active){active=true;activeAt=now;lastChanged=now;}
     const width=fill.style.width.trim();
     const nativeStatus=(status.textContent||'').trim();
     if(width!==lastWidth || nativeStatus!==lastStatus){
       lastChanged=now;lastWidth=width;lastStatus=nativeStatus;
     }
     const age=Math.round((now-lastChanged)/1000);
     const seconds=Math.round((now-activeAt)/1000);
     const stalled=age>=15;
     display.textContent='Motor: '+(nativeStatus||'iniciando…')+
       ' · barra real '+(width||'sin %')+' · '+seconds+' s'+
       (stalled?' · SIN CAMBIO VISIBLE '+age+' s (no prueba bloqueo)':'')+
       (events.length?' · errores/eventos '+events.length:'');
     if(detail)detail.textContent=report(now);
   }
   const handle=setInterval(update,1000);
   update();
   window.addEventListener('pagehide',()=>clearInterval(handle),{once:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
 else mount();
})();
"""

def sha(s:str)->str:return hashlib.sha256(s.encode()).hexdigest()

def safe(file:Path,lab:Path)->bool:
 return not file.is_symlink() and file.resolve().is_relative_to(lab.resolve())

def plan():
 if not LAB.is_dir() or LAB.is_symlink() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('P69_LAB_NOT_FOUND_OR_UNSAFE')
 for item in (HTML,CSS,JS,BACKUP):
  if not safe(item,LAB):raise RuntimeError('P69_UNSAFE_PATH_'+str(item))
 if not HTML.is_file() or not PUBLIC.is_dir() or PUBLIC.is_symlink():
  raise RuntimeError('P69_HTML_OR_PUBLIC_MISSING')
 if CSS.exists() or JS.exists() or BACKUP.exists() or REPORT.exists():
  raise RuntimeError('P69_LOADER_ALREADY_INSTALLED')
 src=HTML.read_text('utf8')
 for needle in ('id="loading-screen"','id="ls-fill"','id="ls-status"',
                'id="start-screen"','/highfly/p68_fury_recovery.css',
                '/highfly/p69_fury_core.css'):
  if needle not in src:raise RuntimeError('P69_LOADER_REQUIRED_NATIVE_MARKER_MISSING '+needle)
 if 'HIGHFLY_P69_FURY_CORE' not in src:
  raise RuntimeError('P69_HISTORICAL_HTML_MARK_MISSING')
 if src.count('</head>')!=1:raise RuntimeError('P69_HTML_HEAD_ANCHOR_DRIFT')
 updated=src.replace('</head>',HTML_INJECT+'</head>',1)
 return src,updated

def run(apply:bool=False):
 old,new=plan()
 output={'phase':'P69_NATIVE_LOADING_VISIBILITY',
  'mode':'DRY_RUN' if not apply else 'APPLY',
  'lab':str(LAB),'privatePort':4176,
  'artImageModified':False,
  'nativeLoaderAndSimUnchanged':True,
  'nativeProgressWidthIsReadOnly':True,
  'activeP64Modified':False,'P43Modified':False,'savedGamesModified':False,
  'browserVerified':False,
  'css':str(CSS),'observerJs':str(JS),'backup':str(BACKUP),
  'diagnosticsOptIn':'?hf_p69_diag=1'}
 if not apply:
  print('[P69 LOADER CLEAN] '+json.dumps(output,ensure_ascii=False,indent=2))
  return
 BACKUP.write_text(old,'utf8')
 if BACKUP.read_text('utf8')!=old:raise RuntimeError('P69_BACKUP_VERIFICATION_FAIL')
 created=[]
 try:
  if HTML.read_text('utf8')!=old:raise RuntimeError('P69_CONCURRENT_HTML_EDIT')
  for f,contents in ((CSS,CSS_TEXT),(JS,JS_TEXT)):
   with f.open('x',encoding='utf8') as stream:stream.write(contents)
   created.append(f)
  HTML.write_text(new,'utf8')
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps({**output,'htmlSha256':sha(new),
     'timestampUtc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False,indent=2)+'\n','utf8')
 except BaseException:
  HTML.write_text(old,'utf8')
  for f in created:
   if f.is_file() and not f.is_symlink():f.unlink()
  raise
 print('[P69 LOADER CLEAN] '+json.dumps(output,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--apply',action='store_true')
 args=parser.parse_args()
 run(args.apply)
