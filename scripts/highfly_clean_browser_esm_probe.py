#!/usr/bin/env python3
"""Add a USER-CLICK browser ESM failure diagnostic to the EXISTING CLEAN boot log.

No Chromium / Playwright, no changes to native game modules, assets, or saves.
Adds a visible "PROBAR MOTOR" control that probes main.ts from the user's REAL
browser and retries exact same module specifier only after an explicit click.
Results go to the existing HIGHFLY BOOT LOG download.
--apply is safe idempotent. --remove restores exact backed-up HTML if unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_clean_bootlog as boot

LAB=ROOT/".workspace/highfly-origin-clean-0447"
HTML=LAB/"index.html"
BACKUP=LAB/".hf-clean-before-browser-esm-probe.html"
MARK="HIGHFLY_CLEAN_BROWSER_ESM_V1"
CLOSE_BOOT='</script>\n'
PLUGIN=r"""<!-- HIGHFLY_CLEAN_BROWSER_ESM_V1 -->
<script id="hf-clean-browser-esm-probe">
(function(){
'use strict';
if(window.__HF_BROWSER_ESM_PROBE__)return;
var t0=performance.now(),MAX=800;
function simple(value,max){
 return String(value==null?'':value).slice(0,max||500)
  .replace(/https?:\/\/[^\s"'<>]+/g,'[URL]')
  .replace(/(token|authorization|password|secret|api_key)\s*[:=]\s*\S+/gi,'$1=[REDACTED]');
}
function write(type,info){
 var record={atMs:Math.round(performance.now()-t0),type:type,detail:info||{}};
 var store=window.__HF_CLEAN_LOG__?.events;
 if(Array.isArray(store)&&store.length<4000)store.push(record);
 if(window.__HF_BROWSER_ESM_PROBE__.events.length<MAX)
  window.__HF_BROWSER_ESM_PROBE__.events.push(record);
}
window.__HF_BROWSER_ESM_PROBE__={events:[],last:null};
function dom(){
 var mode=document.getElementById('server-select');
 var option=document.getElementById('server-opt-offline');
 var preview=document.getElementById('offline-select');
 return {mode:mode?.dataset?.mode||null,
   offlineOptionPresent:!!option,offlineOptionHidden:option?.hidden??null,
   nativeClasses:preview?.querySelectorAll('.mini-class[data-class]')?.length||0,
   readyState:document.readyState};
}
function notice(line){
 var node=document.getElementById('hf-esm-probe-status');
 if(node)node.textContent=line.slice(0,1500);
}
async function run(){
 var button=document.getElementById('hf-esm-probe-button');
 if(button)button.disabled=true;
 write('USER_REQUESTED_BROWSER_MODULE_DIAG',{before:dom()});
 notice('COMPROBANDO MAIN.TS...');
 var result={started:new Date().toISOString(),before:dom()};
 try{
  var response=await fetch('/src/main.ts',{credentials:'same-origin',
   cache:'no-store',redirect:'follow'});
  var ct=response.headers.get('content-type')||'';
  var body=await response.text();
  var finalUrl=new URL(response.url,location.href);
  result.fetch={
   status:response.status,contentType:ct,redirected:response.redirected,
   sameOrigin:finalUrl.origin===location.origin,
   finalPath:finalUrl.pathname,
   bodyLength:body.length,
   html:/^\s*(?:<!doctype html|<html)/i.test(body.slice(0,300)),
   expectedJavascript:/javascript|typescript/i.test(ct)
  };
  write('BROWSER_FETCH_MAIN_RESULT',result.fetch);
 }catch(err){
  result.fetch={error:simple(err?.stack||err,1200)};
  write('BROWSER_FETCH_MAIN_FAILED',result.fetch);
 }
 notice('PROBANDO IMPORTACIÓN ESM...');
 try{
  // EXACT same module URL already referenced by index.html:
  // no cache-busting query, no duplicate entrypoint script injected.
  await import('/src/main.ts');
  result.moduleImport={ok:true};
  write('BROWSER_MAIN_IMPORT_OK',result.moduleImport);
 }catch(err){
  result.moduleImport={
   ok:false,name:simple(err?.name,80),message:simple(err?.message||err,1400),
   stack:simple(err?.stack||'',2300)
  };
  write('BROWSER_MAIN_IMPORT_FAILED',result.moduleImport);
 }
 result.after=dom();
 var resources=performance.getEntriesByType('resource')
  .filter(x=>x.name.includes('/src/')||x.name.includes('/@id/')||
    x.name.includes('/@fs/'))
  .slice(-130).map(x=>{
   try{return {path:new URL(x.name).pathname,
    responseStatus:x.responseStatus||0,
    durationMs:Math.round(x.duration),
    transferSize:x.transferSize||0};}
   catch(_){return {path:'[invalid]'};}
  });
 result.resources=resources;
 write('BROWSER_MAIN_DIAG_COMPLETE',{fetch:result.fetch,
  moduleImport:result.moduleImport,after:result.after,
  resourceTail:resources.filter(x=>x.responseStatus>=400||x.transferSize===0).slice(-30)});
 window.__HF_BROWSER_ESM_PROBE__.last=result;
 if(result.moduleImport?.ok===false){
  notice('FALLÓ: '+result.moduleImport.name+' — '+result.moduleImport.message+
    ' | Ahora tocá DESCARGAR LOG.');
 }else if(!result.fetch?.expectedJavascript||result.fetch?.html){
  notice('MAIN.TS NO ES JAVASCRIPT EN ESTE CHROME | DESCARGAR LOG');
 }else{
  notice('MÓDULO IMPORTADO. Estado Offline: '+(result.after.mode||'NO INICIALIZADO')+
    ' | DESCARGAR LOG');
 }
 if(button)button.disabled=false;
}
function install(){
 if(document.getElementById('hf-esm-probe-button'))return;
 var holder=document.createElement('div');
 holder.id='hf-esm-probe-control';
 holder.style.cssText='position:fixed;z-index:2147483639;right:8px;bottom:67px;'+
  'max-width:min(450px,90vw);background:#101627;color:white;'+
  'border:1px solid #5ad4e4;border-radius:9px;padding:8px;'+
  'font:12px system-ui;box-shadow:0 4px 18px #0009;';
 var button=document.createElement('button');
 button.id='hf-esm-probe-button';button.type='button';
 button.textContent='PROBAR MOTOR';
 button.style.cssText='background:#145c52;color:#fff;border:1px solid #75e4b8;'+
  'border-radius:6px;padding:9px 15px;font:700 12px system-ui;cursor:pointer';
 var status=document.createElement('div');
 status.id='hf-esm-probe-status';status.style.cssText=
  'max-height:65px;overflow:auto;margin-top:5px;white-space:normal';
 status.textContent='Prueba de importación en tu navegador. No modifica guardados.';
 button.addEventListener('click',()=>void run());
 holder.append(button,status);document.body.appendChild(holder);
 write('BROWSER_ESM_PROBE_BUTTON_READY',dom());
}
if(document.readyState==='loading'){
 document.addEventListener('DOMContentLoaded',install,{once:true});
}else install();
})();
</script>
"""

def current():
 if LAB.is_symlink() or not LAB.is_dir() or not LAB.resolve().is_relative_to((ROOT/".workspace").resolve()):
  raise RuntimeError("ESM_PROBE_CLEAN_LAB_REQUIRED")
 if HTML.is_symlink() or not HTML.is_file():raise RuntimeError("ESM_PROBE_HTML_MISSING")
 s=HTML.read_text("utf8")
 if boot.TAG not in s or 'id="hf-clean-bootlog-bootstrap"' not in s:
  raise RuntimeError("ESM_PROBE_EXISTING_BOOTLOG_NOT_INSTALLED")
 if s.count('src="/src/main.ts"')!=1:
  raise RuntimeError("ESM_PROBE_ORIGINAL_MAIN_SCRIPT_MISSING")
 return s

def apply():
 before=current()
 if MARK in before:
  print("[CLEAN BROWSER ESM] ALREADY_INSTALLED");return
 if BACKUP.exists() or BACKUP.is_symlink():
  raise RuntimeError("ESM_PROBE_BACKUP_EXISTS_NO_OVERWRITE")
 script_start=before.index('<script id="hf-clean-bootlog-bootstrap">')
 script_end=before.find("</script>",script_start)
 if script_end<0:raise RuntimeError("ESM_PROBE_BOOTLOG_SCRIPT_CLOSING_MISSING")
 insert_at=script_end+len("</script>")
 updated=before[:insert_at]+"\n"+PLUGIN+before[insert_at:]
 if updated.count(MARK)!=1 or updated.count('src="/src/main.ts"')!=1:
  raise RuntimeError("ESM_PROBE_PATCH_VALIDATION_FAILED")
 if HTML.read_text("utf8")!=before:raise RuntimeError("ESM_PROBE_HTML_CHANGED")
 BACKUP.write_text(before,encoding="utf8")
 if BACKUP.read_text("utf8")!=before:raise RuntimeError("ESM_PROBE_BACKUP_CORRUPT")
 HTML.write_text(updated,encoding="utf8")
 print("[CLEAN BROWSER ESM] INSTALLED; refresh Chrome port 4180.")
 print("[CLEAN BROWSER ESM] Click PROBAR MOTOR, then DESCARGAR LOG.")
 print("[CLEAN BROWSER ESM] No changes to player, world or game source.")

def remove():
 now=current()
 if MARK not in now or not BACKUP.is_file() or BACKUP.is_symlink():
  raise RuntimeError("ESM_PROBE_NOT_INSTALLED_OR_BACKUP_MISSING")
 old=BACKUP.read_text("utf8")
 boot_start=old.index('<script id="hf-clean-bootlog-bootstrap">')
 insert_at=old.find("</script>",boot_start)+len("</script>")
 expected=old[:insert_at]+"\n"+PLUGIN+old[insert_at:]
 if expected!=now:raise RuntimeError("ESM_PROBE_HTML_DRIFT_REFUSE_RESTORE")
 HTML.write_text(old,encoding="utf8")
 BACKUP.unlink()
 print("[CLEAN BROWSER ESM] REMOVED; exact HTML restored.")

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument("--apply",action="store_true")
 mode.add_argument("--remove",action="store_true")
 args=parser.parse_args()
 if args.apply:apply()
 else:remove()
