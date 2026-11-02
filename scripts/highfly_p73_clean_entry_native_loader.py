#!/usr/bin/env python3
"""HIGHFLY P73 — P72-only clean start/loader and native load observability.

--apply installs ONE reversible visual layer + passive, in-memory readout.
Neither progress values, game source, DrakenLAB, GLB paths, nor saves change.
Does not touch other labs, world, source media, shared symlinks or licensed art.
--remove restores exact index bytes and removes only the authored files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p71b-no-drakenlab-lab'
INDEX=LAB/'index.html'
PUBLIC=LAB/'public/highfly'
BACKUP=LAB/'.hf-p73-before-clean-ui.html'
CSS=PUBLIC/'p73_clean_entry_loader.css'
JS=PUBLIC/'p73_native_load_observer.js'
REPORT=WORK/'reports/highfly-world7/P73_CLEAN_ENTRY_ONLY.json'
MARK='HIGHFLY_P73_CLEAN_ENTRY_NATIVE_LOADER_ONLY'
LINKS=(
 '<!-- '+MARK+': one real loader; baked art UI masked, no gameplay changes -->\n'
 '<link rel="stylesheet" href="/highfly/p73_clean_entry_loader.css" />\n'
 '<script defer src="/highfly/p73_native_load_observer.js"></script>\n'
)

CSS_TEXT=r"""/* HIGHFLY_P73_CLEAN_ENTRY_NATIVE_LOADER_ONLY
   Covers baked-in buttons/bars in the SPLASH IMAGE with a gradient.
   Never touches the source image, real game buttons or native load state. */
html:has(body:not(.game-active)){
  width:100%!important;max-width:100%!important;height:100%!important;
  overflow:hidden!important;overscroll-behavior:none!important;
}
body:not(.game-active){
  width:100vw!important;max-width:100vw!important;
  min-height:100dvh!important;height:100dvh!important;
  margin:0!important;overflow:hidden!important;overscroll-behavior:none!important;
}
body:not(.game-active) #start-screen.hf-p46-entry{
  position:fixed!important;inset:0!important;
  width:100vw!important;height:100dvh!important;min-height:0!important;
  max-width:100vw!important;max-height:100dvh!important;
  margin:0!important;overflow:hidden!important;
  box-sizing:border-box!important;
  background-color:#08091e!important;
  background-image:
    linear-gradient(to bottom,
      rgba(6,8,24,0) 0%,rgba(6,8,24,0) 64%,
      rgba(6,8,24,.26) 68%,rgba(6,8,24,.93) 76%,
      #08091e 85%,#08091e 100%),
    url('/highfly/official/highfly_splash.png')!important;
  background-position:center center!important;background-size:cover!important;
  background-repeat:no-repeat!important;
}
/* Keep original interactive start controls in front of the artwork. */
body:not(.game-active) #start-screen.hf-p46-entry :is(button,input,select,[role="button"]){
  pointer-events:auto;
}
/* Completely separate the actual loader from fake image UI. */
body #loading-screen.visible{
  position:fixed!important;inset:0!important;
  width:100vw!important;height:100dvh!important;
  min-height:100dvh!important;max-height:100dvh!important;
  box-sizing:border-box!important;margin:0!important;padding:0 12px!important;
  overflow:hidden!important;z-index:2147483000!important;
  display:flex!important;flex-direction:column!important;
  align-items:center!important;justify-content:center!important;
  background:#090d1f!important;
  background-image:
    radial-gradient(ellipse 50% 56% at 50% 40%,rgba(111,53,177,.26),transparent 82%),
    linear-gradient(135deg,#080b1e,#151029 58%,#080c1a)!important;
  background-position:center center!important;background-size:cover!important;
  isolation:isolate!important;
}
body #loading-screen.visible::before{
  content:"HIGHFLY"!important;
  display:block!important;position:relative!important;
  inset:auto!important;transform:none!important;
  z-index:1!important;width:auto!important;height:auto!important;
  margin:0 0 22px!important;padding:0!important;border:0!important;
  background:none!important;box-shadow:none!important;
  color:#f7e8ff!important;font:900 clamp(23px,5vw,54px)/1.15 system-ui,sans-serif!important;
  letter-spacing:.17em!important;text-align:center!important;
  text-shadow:0 0 20px rgba(154,89,238,.75)!important;
  pointer-events:none!important;
}
body #loading-screen.visible::after{content:none!important;display:none!important;}
body #loading-screen.visible .ls-logo{display:none!important;}
body #loading-screen.visible .ls-progress{
  position:relative!important;inset:auto!important;left:auto!important;
  right:auto!important;top:auto!important;bottom:auto!important;
  transform:none!important;z-index:2!important;
  display:flex!important;flex-direction:column!important;
  align-items:stretch!important;justify-content:center!important;
  box-sizing:border-box!important;
  width:min(560px,92vw)!important;min-height:0!important;height:auto!important;
  max-width:92vw!important;max-height:50dvh!important;
  margin:0!important;padding:15px 20px!important;gap:10px!important;
  overflow:hidden!important;
  background:rgba(13,11,34,.94)!important;
  border:1px solid #8d64cb!important;border-radius:13px!important;
  box-shadow:0 12px 35px rgba(0,0,0,.55)!important;
}
body #loading-screen.visible #ls-status{
  position:static!important;inset:auto!important;transform:none!important;
  display:block!important;order:0!important;
  width:100%!important;max-width:100%!important;
  margin:0!important;padding:0!important;background:none!important;
  border:0!important;white-space:normal!important;
  color:#fff!important;text-align:center!important;
  font:700 clamp(12px,1.75vw,16px)/1.35 system-ui,sans-serif!important;
}
body #loading-screen.visible .ls-bar{
  display:block!important;position:relative!important;
  order:1!important;inset:auto!important;
  width:100%!important;height:13px!important;min-height:13px!important;
  max-height:13px!important;margin:0!important;padding:0!important;
  border:1px solid #b48fe1!important;border-radius:100px!important;
  overflow:hidden!important;background:#1c1534!important;
  box-sizing:border-box!important;
}
body #loading-screen.visible #ls-fill{
  display:block!important;position:relative!important;inset:auto!important;
  height:100%!important;min-height:100%!important;max-width:100%!important;
  border-radius:100px!important;
  background:linear-gradient(90deg,#7541ce,#c67eff,#6ad8f3)!important;
}
/* Original engine has one real progress bar: hide only decorative extra tips. */
body #loading-screen.visible #ls-tip,
body #loading-screen.visible #ls-slow-hint,
body #loading-screen.visible #hf-entry-progress-detail{
  display:none!important;
}
body:has(#loading-screen.visible) #start-screen,
body:has(#loading-screen.visible) #highfly-p46-landing,
body:has(#loading-screen.visible) #mobile-controls,
body:has(#loading-screen.visible) #mobile-action-ring,
body:has(#loading-screen.visible) #mobile-dodge{
  visibility:hidden!important;pointer-events:none!important;
}
body #hf-p73-native-readout{
  position:fixed!important;top:max(8px,env(safe-area-inset-top))!important;
  right:max(8px,env(safe-area-inset-right))!important;
  z-index:2147483500!important;
  box-sizing:border-box!important;max-width:min(340px,58vw)!important;
  padding:7px 10px!important;border:1px solid rgba(113,204,252,.6)!important;
  border-radius:8px!important;background:rgba(5,15,32,.93)!important;
  color:#dff4ff!important;text-align:left!important;pointer-events:none!important;
  font:600 11px/1.4 system-ui,sans-serif!important;
  box-shadow:0 3px 18px #0007!important;
  white-space:normal!important;overflow-wrap:anywhere!important;
}
body.game-active:not(:has(#loading-screen.visible)) #hf-p73-native-readout{
  display:none!important;
}
@media(max-height:480px) and (orientation:landscape){
  body #loading-screen.visible::before{margin-bottom:10px!important;}
  body #loading-screen.visible .ls-progress{
    padding:8px 13px!important;gap:6px!important;max-height:60dvh!important;
  }
  body #loading-screen.visible .ls-bar{height:10px!important;min-height:10px!important;max-height:10px!important}
  body #hf-p73-native-readout{font-size:10px!important;max-width:min(295px,43vw)!important;}
}
"""
JS_TEXT=r"""/* HIGHFLY_P73_CLEAN_ENTRY_NATIVE_LOADER_ONLY
   Read-only status: never call startOffline, modify the native #ls-fill,
   force completion, alter player saves or intercept fetch. */
(function(){
'use strict';
if(window.__HF_P73_READOUT__)return;
const state={phase:'',since:performance.now(),lastProgress:'',lastChange:performance.now(),errors:0,resourceErrors:0};
window.__HF_P73_READOUT__=state;
window.addEventListener('error',e=>{
 if(e.target&&e.target!==window&&(e.target.src||e.target.href))state.resourceErrors++;
 else if(e.message)state.errors++;
},true);
window.addEventListener('unhandledrejection',()=>state.errors++);
function visible(el){
 if(!el || el.hidden)return false;
 const s=getComputedStyle(el);
 const r=el.getBoundingClientRect();
 return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
}
function current(){
 const loader=document.getElementById('loading-screen');
 const creator=document.getElementById('offline-select');
 const start=document.getElementById('start-screen');
 const realm=document.getElementById('server-select')?.dataset.mode||'desconocido';
 const active=!!document.body?.classList.contains('game-active');
 let phase='Inicializando...';
 if(visible(loader)&&loader.classList.contains('visible')) phase='Cargando motor';
 else if(visible(creator))phase='Creador de personaje';
 else if(active)phase='Escena activa (verificar mundo)';
 else if(visible(start))phase='Portada / ingresar';
 else phase='Transición de interfaz';
 const text=(document.getElementById('ls-status')?.textContent||'').replace(/\s+/g,' ').trim().slice(0,90);
 const bar=document.getElementById('ls-fill')?.style.width||'sin dato';
 return {phase,realm,text,bar,active};
}
function update(){
 const el=document.getElementById('hf-p73-native-readout');
 if(!el)return;
 const now=performance.now(),read=current();
 if(read.phase!==state.phase){state.phase=read.phase;state.since=now;state.lastProgress='';state.lastChange=now;}
 const progress=read.text+'|'+read.bar;
 if(progress!==state.lastProgress){state.lastProgress=progress;state.lastChange=now;}
 const duration=Math.round((now-state.since)/1000);
 const idle=Math.round((now-state.lastChange)/1000);
 const waiting=read.phase==='Cargando motor'&&idle>=20?' · sin cambios visibles hace '+idle+'s':'';
 const counts=state.errors+state.resourceErrors;
 el.textContent='P72 · '+read.phase+' · '+duration+'s'+
  (read.phase==='Cargando motor'?' | '+read.text+' | barra '+read.bar:'')+
  waiting+
  (counts?' | '+counts+' eventos de error (JS/recursos)':'');
 el.setAttribute('aria-label',el.textContent);
 if(read.phase.startsWith('Escena activa') && !new URLSearchParams(location.search).has('hf_p73_diag')){
  el.style.display='none';
 }else{
  el.style.display='';
 }
}
function mount(){
 if(!document.body)return;
 const el=document.createElement('div');
 el.id='hf-p73-native-readout';el.setAttribute('role','status');
 document.body.appendChild(el);
 update();setInterval(update,1400);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
else mount();
})();
"""

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def preflight():
 if not LAB.is_dir() or LAB.is_symlink() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('P73_ONLY_PRIVATE_P72_LAB_ALLOWED')
 if INDEX.is_symlink() or not INDEX.is_file() or PUBLIC.is_symlink() or not PUBLIC.is_dir():
  raise RuntimeError('P73_PRIVATE_INDEX_OR_PUBLIC_DIR_INVALID')
 for p in (BACKUP,CSS,JS):
  if p.exists() or p.is_symlink():raise RuntimeError('P73_ALREADY_INSTALLED_REVIEW_EXISTING')
 html=INDEX.read_bytes()
 src=html.decode('utf8')
 if ('HIGHFLY_P72_P71B_WITHOUT_DRAKENLAB' not in src
  or 'id="start-screen"' not in src or 'id="loading-screen"' not in src
  or 'id="offline-select"' not in src or '</head>' not in src
  or src.count('</head>')!=1):
  raise RuntimeError('P73_NOT_EXPECTED_P72_NATIVE_ENTRY')
 if MARK in src or 'drakenlab_p71' in src:
  raise RuntimeError('P73_UNEXPECTED_MARKER_OR_DRAKENLAB')
 if not (LAB/'src/main.ts').is_file() or 'HIGHFLY_P69_FURY_CORE' not in (LAB/'src/main.ts').read_text('utf8'):
  raise RuntimeError('P73_P69_FURY_MISSING')
 return html

def apply():
 old=preflight()
 updated=old.replace(b'</head>',LINKS.encode()+b'</head>',1)
 BACKUP.write_bytes(old)
 if BACKUP.read_bytes()!=old:raise RuntimeError('P73_BACKUP_FAILURE')
 try:
  with CSS.open('x',encoding='utf8') as f:f.write(CSS_TEXT)
  with JS.open('x',encoding='utf8') as f:f.write(JS_TEXT)
  if INDEX.read_bytes()!=old:raise RuntimeError('P73_CONCURRENT_INDEX_CHANGE')
  INDEX.write_bytes(updated)
  if INDEX.read_bytes()!=updated:raise RuntimeError('P73_INDEX_VERIFICATION_FAILURE')
 except BaseException:
  if INDEX.is_file() and not INDEX.is_symlink():INDEX.write_bytes(old)
  if CSS.is_file() and not CSS.is_symlink() and CSS.read_text('utf8')==CSS_TEXT:CSS.unlink()
  if JS.is_file() and not JS.is_symlink() and JS.read_text('utf8')==JS_TEXT:JS.unlink()
  raise
 report={'name':'HIGHFLY_P73_CLEAN_ENTRY_NATIVE_LOADER_ONLY',
  'status':'INSTALLED_BROWSER_VERIFICATION_PENDING',
  'timestamp':datetime.now(timezone.utc).isoformat(),
  'indexOriginalSha256':sha(old),'indexAfterSha256':sha(updated),
  'gameplaySourcesTouched':False,'sharedAssetsTouched':False,
  'nativeProgressChanged':False,'offlineSaveChanged':False,
  'scope':'P72 private index + P73 CSS/JS only',
  'limitations':['Does not resolve missing GLB/image resources',
    'A real loading screen showing 700/700 is not proof of world readiness',
    'No synthetic progress is written']}
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 if REPORT.exists() or REPORT.is_symlink():raise RuntimeError('P73_REPORT_EXISTS_REVIEW')
 REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
 print('[P73 APPLIED] Only P72 native entry visuals + observational loading panel installed.')
 print('[P73 APPLIED] Backup:',BACKUP)
 print('[P73 APPLIED] Report:',REPORT)

def remove():
 if not INDEX.is_file() or INDEX.is_symlink() or not BACKUP.is_file() or BACKUP.is_symlink():
  raise RuntimeError('P73_REMOVE_BACKUP_OR_INDEX_MISSING')
 if not CSS.is_file() or CSS.is_symlink() or CSS.read_text('utf8')!=CSS_TEXT:
  raise RuntimeError('P73_REMOVE_CSS_CHANGED')
 if not JS.is_file() or JS.is_symlink() or JS.read_text('utf8')!=JS_TEXT:
  raise RuntimeError('P73_REMOVE_JS_CHANGED')
 current=INDEX.read_bytes()
 if current.count(LINKS.encode())!=1:raise RuntimeError('P73_REMOVE_INDEX_DRIFT')
 restored=current.replace(LINKS.encode(),b'',1)
 if restored!=BACKUP.read_bytes():raise RuntimeError('P73_REMOVE_CONCURRENT_INDEX_CHANGE')
 INDEX.write_bytes(restored);CSS.unlink();JS.unlink();BACKUP.unlink()
 print('[P73 REMOVED] Original P72 index restored byte for byte.')

if __name__=='__main__':
 cli=argparse.ArgumentParser()
 group=cli.add_mutually_exclusive_group()
 group.add_argument('--apply',action='store_true')
 group.add_argument('--remove',action='store_true')
 args=cli.parse_args()
 if args.remove:remove()
 elif args.apply:apply()
 else:
  old=preflight()
  print('[P73 DRY RUN] P72 recognized. Only one index injection + two new CSS/JS files. No changes.')
  print('[P73 DRY RUN] P72 index sha256:',sha(old))
