#!/usr/bin/env python3
"""P43 only: add opt-in Android runtime error display without changing game logic.

Enable with ?hf_p43_diag=1. Captures window errors and rejected promises BEFORE
the game module loads, plus native offline select, script failures and details.
No effect for normal URL, no user storage, no changes to active P64 sources.
"""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p43-restore-lab'
HTML=LAB/'index.html'
TARGET=LAB/'public/highfly_p43_android_diag.js'
BACKUP=LAB/'.hf-p43-android-diag-backup-index.html'
REPORT=WORK/'reports/highfly-world7/P43_ANDROID_RUNTIME_DIAG_INSTALL.json'
TAG='<script src="/highfly_p43_android_diag.js"></script>'
MARK='HIGHFLY_P43_ANDROID_DIAGNOSTIC'
JS=r"""/* HIGHFLY P43 ANDROID DIAGNOSTIC — opt in ?hf_p43_diag=1; passive only */
(function(){
  'use strict';
  if(!new URLSearchParams(location.search).has('hf_p43_diag'))return;
  const logs=[];
  const add=(type,detail)=>{
    const value=String(detail??'').slice(0,900);
    logs.push(type+': '+value);
    if(logs.length>18)logs.shift();
  };
  window.addEventListener('error',function(e){
    const t=e.target;
    if(t && t!==window && t!==document &&
       (t.src||t.href)){
      add('RECURSO FALLÓ',t.src||t.href);
      return;
    }
    add('JS ERROR',(e.message||'Error desconocido')+' @ '+(e.filename||'')+':'+(e.lineno||''));
  },true);
  window.addEventListener('unhandledrejection',function(e){
    const reason=e.reason;
    add('PROMESA FALLÓ',reason && (reason.stack||reason.message)||reason||'desconocido');
  });
  window.addEventListener('securitypolicyviolation',function(e){
    add('BLOQUEO CSP',e.blockedURI||e.violatedDirective||'desconocido');
  });
  const summarize=(id)=>{
    const e=document.getElementById(id);
    if(!e)return id+': NO EXISTE';
    const st=getComputedStyle(e);
    const rect=e.getBoundingClientRect();
    return id+': '+(e.hasAttribute('hidden')?'hidden':'visible')+
      ' | display='+st.display+' | size='+Math.round(rect.width)+'x'+Math.round(rect.height)+
      ' | mode='+(e.dataset.mode||'-')+
      ' | txt='+String((e.textContent||'').trim().replace(/\s+/g,' ')).slice(0,65);
  };
  function report(){
    let perf=[];
    try{
      perf=performance.getEntriesByType('resource')
        .filter(e=>e.responseStatus>=400)
        .slice(-8)
        .map(e=>e.responseStatus+' '+e.name.split(location.origin).join(''));
    }catch{}
    return [
      'HIGHFLY P43 ANDROID — '+new Date().toLocaleTimeString(),
      'URL: '+location.pathname+location.search,
      'DOM: '+document.readyState,
      'Navegador: '+navigator.userAgent.slice(0,160),
      'BODY: '+(document.body?.className||'-'),
      summarize('server-select'),
      summarize('server-select-trigger'),
      summarize('server-select-value'),
      summarize('server-opt-offline'),
      summarize('offline-select'),
      summarize('btn-play'),
      summarize('hf-p43-fullscreen-btn'),
      'CSS de juego: '+(getComputedStyle(document.body).backgroundColor),
      'Errores de recursos HTTP: '+(perf.length?perf.join(' | '):'ninguno registrado'),
      'ERRORES JS ('+logs.length+'):\n'+(logs.length?logs.join('\n'):'Ninguno capturado'),
    ].join('\n');
  }
  function mount(){
    if(!document.body)return;
    if(document.getElementById('hf-p43-android-diagnostics'))return;
    const host=document.createElement('section');
    host.id='hf-p43-android-diagnostics';
    host.style.cssText='position:fixed;top:4px;right:4px;width:min(94vw,560px);max-height:90dvh;display:flex;flex-direction:column;gap:5px;z-index:2147483647;background:#0a1526;color:#e5f5ff;border:2px solid #50c9fc;border-radius:9px;padding:9px;box-shadow:0 8px 25px #000b;box-sizing:border-box;font:12px/1.35 monospace';
    const bar=document.createElement('div');
    bar.style.cssText='display:flex;justify-content:space-between;align-items:center;gap:8px';
    const title=document.createElement('strong');
    title.textContent='P43 DIAGNÓSTICO ANDROID';
    const buttons=document.createElement('div');
    buttons.style.cssText='display:flex;gap:6px';
    const copy=document.createElement('button');
    const hide=document.createElement('button');
    for(const button of [copy,hide]){
      button.type='button';
      button.style.cssText='background:#173b60;color:#fff;border:1px solid #50c9fc;border-radius:5px;min-height:30px;padding:5px 8px';
    }
    copy.textContent='COPIAR'; hide.textContent='OCULTAR';
    const pre=document.createElement('pre');
    pre.style.cssText='margin:0;white-space:pre-wrap;overflow:auto;max-height:72dvh;user-select:text;overflow-wrap:anywhere';
    buttons.append(copy,hide);bar.append(title,buttons);host.append(bar,pre);document.body.append(host);
    let count=0;
    const tick=()=>{
      pre.textContent=report();
      if(++count>=90)clearInterval(timer);
    };
    copy.onclick=async()=>{
      try{await navigator.clipboard.writeText(report());copy.textContent='COPIADO';}
      catch{pre.focus();copy.textContent='CAPTURÁ PANTALLA';}
    };
    hide.onclick=()=>host.remove();
    const timer=setInterval(tick,1200);tick();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
"""

def run():
    if (not LAB.is_dir() or LAB.is_symlink() or
            not LAB.resolve().is_relative_to(WORK.resolve())):
        raise RuntimeError('P43_LAB_UNSAFE_OR_NOT_FOUND')
    if TARGET.exists() or TARGET.is_symlink() or BACKUP.exists():
        raise RuntimeError('P43_DIAG_ALREADY_INSTALLED_OR_BACKUP_EXISTS')
    if (not HTML.is_file() or HTML.is_symlink() or
            (LAB/'public').is_symlink()):
        raise RuntimeError('P43_HTML_OR_PUBLIC_UNSAFE')
    original=HTML.read_text('utf8')
    if original.count('<head>')!=1 or original.count('</head>')!=1:
        raise RuntimeError('P43_HTML_INVALID_HEAD')
    if 'HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES' not in original:
        raise RuntimeError('P43_EXPECTED_RECOVERY_MARKER_MISSING')
    if 'id="server-opt-offline"' not in original or TAG in original:
        raise RuntimeError('P43_OFFLINE_NODE_MISSING_OR_ALREADY_INSTALLED')
    # Insert BEFORE all other head scripts so load/import failures are visible.
    new=original.replace('<head>','<head>\n<!-- '+MARK+'; only active on ?hf_p43_diag=1 -->\n'+TAG,1)
    BACKUP.write_text(original,'utf8')
    if BACKUP.read_bytes()!=original.encode('utf8'):
        raise RuntimeError('P43_DIAG_BACKUP_MISMATCH')
    try:
        TARGET.write_text(JS,'utf8')
        HTML.write_text(new,'utf8')
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        status={'mode':'APPLY','lab':str(LAB),'reportOnly':True,
                'normalUrlUnchangedBehavior':True,'browserVerified':False,
                'gameLogicModified':False,'offlineSavesModified':False,
                'activeP64Modified':False,'htmlBackup':str(BACKUP),
                'diagScript':str(TARGET),
                'urlSuffix':'?hf_p43_diag=1',
                'sha256':hashlib.sha256(HTML.read_bytes()).hexdigest()}
        REPORT.write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n','utf8')
        print('[HIGHFLY P43 ANDROID DIAG] '+json.dumps(status,indent=2,ensure_ascii=False))
    except Exception:
        if TARGET.is_file() and not TARGET.is_symlink() and TARGET.read_text('utf8')==JS:
            TARGET.unlink()
        HTML.write_text(original,'utf8')
        raise

if __name__=='__main__':run()
