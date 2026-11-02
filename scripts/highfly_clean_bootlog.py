#!/usr/bin/env python3
"""HIGHFLY CLEAN boot logger: earliest HTML execution + HTTP launch probe.

Scope: only .workspace/highfly-origin-clean-0447. No game/runtime/asset
modification. --install inserts an early passive logger, independent CSS
fallback and download buttons. --probe checks local Vite HTTP status/content
type, never assumes a 200 response is a valid GLB. --remove is lossless.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-origin-clean-0447'
INDEX=LAB/'index.html'
BACKUP=LAB/'.hf-clean-bootlog-original-index.html'
REPORT=WORK/'reports/highfly-clean-0447/BOOT_HTTP_PROBE.json'
TAG='HIGHFLY_CLEAN_BOOTLOG_V1'
INSERT_CSS='<link rel="stylesheet" href="/src/styles/index.css" data-hf-clean-css-fallback="1" />\n'
SCRIPT= r"""<script id="hf-clean-bootlog-bootstrap">
/* HIGHFLY_CLEAN_BOOTLOG_V1: FIRST head script, before any Vite/main.ts code.
   Records only metadata (no requests bodies, names, saved data or tokens). */
(function(){
'use strict';
if(window.__HF_CLEAN_LOG__)return;
var started=performance.now(),events=[],dropped=0,MAX=4000;
function safeUrl(value){
 try{
  var url=new URL(String(value||''),location.href);
  var same=url.origin===location.origin;
  return (same?'':url.origin)+url.pathname.slice(0,200);
 }catch(_){return '<unparsed-url>';}
}
function clean(value){
 if(value===null||value===undefined)return String(value);
 if(value instanceof Error)return (value.name+': '+value.message).slice(0,200);
 if(typeof value==='object'){
  try{return JSON.stringify(value).slice(0,200).replace(/https?:\/\/[^\s"']+/g,'[URL]')}
  catch(_){return '[object]';}
 }
 return String(value).slice(0,240)
  .replace(/https?:\/\/[^\s"']+/g,'[URL]')
  .replace(/(token|authorization|password|secret|api_key)\s*[:=]\s*\S+/gi,'$1=[REDACTED]');
}
function rec(type,detail){
 if(events.length===MAX){dropped++;return;}
 events.push({atMs:Math.round(performance.now()-started),type:type,
  detail:detail||{}});
}
function sampleDom(){
 var s= document.getElementById('start-screen');
 var c=document.getElementById('offline-select');
 var l=document.getElementById('loading-screen');
 var f=document.getElementById('ls-fill');
 var status=document.getElementById('ls-status');
 var cs=document.querySelectorAll('#offline-select .mini-class[data-class]');
 return {readyState:document.readyState,body:!!document.body,
   startVisible:!!s&&getComputedStyle(s).display!=='none',
   creatorVisible:!!c&&!c.hidden&&getComputedStyle(c).display!=='none',
   nineClassNodes:cs.length,loadingVisible:!!l&&l.classList.contains('visible'),
   loadingText:(status?.textContent||'').slice(0,75),
   loadingBar:f?.style.width||null,
   canvasCount:document.querySelectorAll('canvas').length,
   stylesheets:document.styleSheets.length,
   viteClient:!!document.querySelector('script[src*="/@vite/client"]')};
}
window.__HF_CLEAN_LOG__={
 events:events,
 snapshot:function(){return {label:'HIGHFLY CLEAN / 0.44.7 / BOOT LOG',
  createdAt:new Date().toISOString(),userAgent:navigator.userAgent,
  ageMs:Math.round(performance.now()-started),dropped:dropped,
  dom:sampleDom(),events:events.slice()};},
 download:function(){
  var blob=new Blob([JSON.stringify(this.snapshot(),null,2)],{type:'application/json'});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;a.download='HIGHFLY_CLEAN_BOOTLOG_'+Date.now()+'.json';
  a.style.display='none';document.body.appendChild(a);a.click();a.remove();
  setTimeout(function(){URL.revokeObjectURL(url)},2000);
 }
};
rec('BOOT_TRACE_STARTED',{href:location.pathname,readyState:document.readyState});
window.addEventListener('error',function(e){
 if(e.target&&e.target!==window&&(e.target.src||e.target.href)){
  rec('RESOURCE_ERROR',{url:safeUrl(e.target.src||e.target.href),
   element:e.target.tagName||'',type:e.target.type||''});
 }else rec('SCRIPT_ERROR',{message:clean(e.message),file:safeUrl(e.filename),
  line:e.lineno||0,col:e.colno||0,stack:clean(e.error&&e.error.stack)});
},true);
window.addEventListener('unhandledrejection',function(e){
 rec('UNHANDLED_REJECTION',{reason:clean(e.reason),stack:clean(e.reason&&e.reason.stack)});
});
window.addEventListener('securitypolicyviolation',function(e){
 rec('CSP_VIOLATION',{directive:e.violatedDirective,
  blocked:safeUrl(e.blockedURI)});
});
['error','warn'].forEach(function(level){
 var original=console[level];
 console[level]=function(){
  var args=Array.prototype.slice.call(arguments);
  rec('CONSOLE_'+level.toUpperCase(),{messages:args.slice(0,3).map(clean)});
  return original.apply(console,args);
 };
});
try{
 if(PerformanceObserver.supportedEntryTypes?.includes('resource')){
  new PerformanceObserver(function(list){
   list.getEntries().forEach(function(entry){
    var status=entry.responseStatus;
    if(status&&status<400)return;
    if(status===0&&entry.duration<0)return;
    // Capture every failed/non-2xx resource; success is counted via summary.
    if(status>=400)rec('HTTP_RESOURCE_ERROR',{url:safeUrl(entry.name),status:status,
      durationMs:Math.round(entry.duration)});
   });
  }).observe({type:'resource',buffered:true});
 }
}catch(e){rec('PERF_OBSERVER_UNAVAILABLE',{message:clean(e)})}
document.addEventListener('readystatechange',function(){
 rec('DOCUMENT_STATE',{state:document.readyState});
});
document.addEventListener('DOMContentLoaded',function(){
 rec('DOM_CONTENT_LOADED',sampleDom());mount();
},{once:true});
window.addEventListener('load',function(){rec('WINDOW_LOAD',sampleDom())},{once:true});
setTimeout(function(){
 rec('STARTUP_CHECK_3S',sampleDom());
},3000);
setTimeout(function(){
 rec('STARTUP_CHECK_10S',sampleDom());
},10000);
setInterval(function(){
 if(!document.body)return;
 var phase=sampleDom();
 if(!phase.creatorVisible&&!phase.loadingVisible&&phase.nineClassNodes!==9){
  rec('ENTRY_NOT_INITIALIZED_OR_NINE_CLASSES_MISSING',phase);
 }
},20000);
function mount(){
 if(document.getElementById('hf-clean-trace-control'))return;
 var bar=document.createElement('div');
 bar.id='hf-clean-trace-control';
 bar.style.cssText='position:fixed;z-index:2147483640;right:8px;bottom:8px;'+
  'display:flex;gap:6px;align-items:center;padding:7px;background:#071426;'+
  'border:1px solid #62d6ff;border-radius:8px;font:600 12px system-ui;color:white;'+
  'box-shadow:0 4px 18px #0008;';
 var title=document.createElement('span');
 title.textContent='HIGHFLY BOOT LOG';
 var btn=document.createElement('button');
 btn.type='button';btn.textContent='DESCARGAR LOG';
 btn.style.cssText='font:700 12px system-ui;cursor:pointer;color:white;background:#4b2cb4;'+
  'padding:8px;border:1px solid #a988ff;border-radius:6px;';
 btn.onclick=function(){rec('USER_DOWNLOADED_BOOT_LOG',sampleDom());
  window.__HF_CLEAN_LOG__.download()};
 bar.append(title,btn);
 document.body.appendChild(bar);
 rec('BOOT_TRACE_CONTROL_READY',sampleDom());
}
})();
</script>
"""
INJECT=f'<!-- {TAG} -->\n{SCRIPT}\n'

def require_clean():
 if LAB.is_symlink() or not LAB.is_dir() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('BOOTLOG_ONLY_CLEAN_0447_LAB')
 if INDEX.is_symlink() or not INDEX.is_file():raise RuntimeError('BOOTLOG_INDEX_MISSING')
 text=INDEX.read_text('utf8')
 if text.count('<head>')!=1 or text.count('</head>')!=1:
  raise RuntimeError('BOOTLOG_UNEXPECTED_INDEX_STRUCTURE')
 if 'id="offline-select"' not in text or 'data-class="warrior"' not in text:
  raise RuntimeError('BOOTLOG_NOT_NATIVE_NINE_CLASS_INDEX')
 return text

def install():
 old=require_clean()
 if TAG in old:
  print('[BOOTLOG] ALREADY_INSTALLED');return
 if BACKUP.exists() or BACKUP.is_symlink():raise RuntimeError('BOOTLOG_BACKUP_EXISTS_NO_OVERWRITE')
 if not (LAB/'src/styles/index.css').is_file() or not (LAB/'src/styles/index.extra.css').is_file():
  raise RuntimeError('BOOTLOG_ORIGINAL_CSS_FILES_MISSING')
 BACKUP.write_bytes(INDEX.read_bytes())
 replacement=old.replace('<head>',f'<head>\n{INJECT}',1)
 if INSERT_CSS not in replacement:
  replacement=replacement.replace('</head>',INSERT_CSS+'</head>',1)
 if INDEX.read_text('utf8')!=old:raise RuntimeError('BOOTLOG_CONCURRENT_EDIT')
 INDEX.write_text(replacement,'utf8')
 print('[BOOTLOG INSTALLED] First script precedes any game module; independent CSS fallback installed.')
 print('[BOOTLOG] Original exact backup:',BACKUP)
 print('[BOOTLOG] Reload port 4180 and click DESCARGAR LOG at bottom-right.')

def remove():
 current=require_clean()
 if TAG not in current or not BACKUP.is_file() or BACKUP.is_symlink():
  raise RuntimeError('BOOTLOG_NOT_INSTALLED_OR_BACKUP_LOST')
 orig=BACKUP.read_bytes()
 expected=orig.decode('utf8').replace('<head>',f'<head>\n{INJECT}',1)
 expected=expected.replace('</head>',INSERT_CSS+'</head>',1) if INSERT_CSS not in expected else expected
 if expected!=current:raise RuntimeError('BOOTLOG_INDEX_DRIFT_NO_DESTRUCTIVE_RESTORE')
 INDEX.write_bytes(orig);BACKUP.unlink()
 print('[BOOTLOG REMOVED] Exact original HTML restored.')

def check_url(url):
 try:
  request=urllib.request.Request(url,headers={'User-Agent':'HIGHFLY-CLEAN-BOOT-LOCAL-PROBE'})
  with urllib.request.urlopen(request,timeout=12) as response:
   raw=response.read(8192)
   status=response.status
   content=response.headers.get('Content-Type','')
 except urllib.error.HTTPError as e:
  status=e.code;content=e.headers.get('Content-Type','')
  raw=e.read(8192)
 except Exception as e:
  return {'urlPath':urllib.request.urlparse(url).path,'state':'UNREACHABLE',
    'error':str(e)[:210]}
 body=raw[:160].decode('utf8','replace').replace('\n',' ')
 return {'urlPath':urllib.request.urlparse(url).path,'status':status,
   'contentType':content,'sample':body if status>=400 else '',
   'looksLikeHtmlFallback':('text/html' in content and
      '/src/' in url),'bytesSampled':len(raw)}

def probe(port):
 lab=require_clean()
 paths=['/','/@vite/client','/src/main.ts','/src/styles/index.css',
        '/src/styles/index.extra.css','/models/chars/players/knight.glb',
        '/models/creatures/wolf.glb']
 results=[check_url(f'http://127.0.0.1:{port}'+p) for p in paths]
 failures=[r for r in results if r.get('status',0)>=400 or
           r.get('state')=='UNREACHABLE' or r.get('looksLikeHtmlFallback')]
 report={'scope':'CLEAN_0447_LOCAL_VITE_HTTP_ONLY',
  'capturedUtc':datetime.now(timezone.utc).isoformat(),
  'port':port,'checks':results,'failures':len(failures),
  'note':'HTTP checks cannot prove that the world can be entered; browser log shows module/CSS failures'}
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
 for item in results:
  print('[BOOT HTTP]',item['urlPath'],item.get('status',item.get('state')),
   item.get('contentType',''),item.get('error',''),
   ('DETAIL: '+item.get('sample','')[:250]) if item.get('status',200)>=400 else '')
 print('[BOOT HTTP RESULT]',len(failures),'failure(s); report:',REPORT)

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 group=ap.add_mutually_exclusive_group(required=True)
 group.add_argument('--install',action='store_true')
 group.add_argument('--remove',action='store_true')
 group.add_argument('--probe',action='store_true')
 ap.add_argument('--port',type=int,default=4180)
 args=ap.parse_args()
 if args.install:install()
 elif args.remove:remove()
 else:probe(args.port)
