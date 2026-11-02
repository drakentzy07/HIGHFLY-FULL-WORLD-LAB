#!/usr/bin/env python3
"""HIGHFLY CLEAN: ONE full-lifecycle logger for private bundled offline 4181.

Injects FIRST head script in compiled private index.html; removes ONLY old
diagnostics script tags from output (not stage files). Tracks native Offline,
fetch/XHR/performance/network errors, UI + world progress, console and promise
failures. One DESCARGAR LOG button. No automatic downloads, no saved-game edits.
--apply idempotent; --remove exactly reverses if file unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
STAGE=WORK/'highfly-origin-clean-0447'
DIST=STAGE/'.highfly-private-offline-dist'
INDEX=DIST/'index.html'
BACKUP=DIST/'.highfly-before-unified-log-index.html'
MARK='HIGHFLY_CLEAN_UNIFIED_LIFECYCLE_LOG_V1'
OLD_IDS=('hf-clean-bootlog-bootstrap','hf-clean-browser-esm-probe')
SCRIPT=r"""<script id="hf-clean-unified-lifecycle-logger">
/* HIGHFLY_CLEAN_UNIFIED_LIFECYCLE_LOG_V1 — private browser QA, local only */
(function(){
'use strict';
if(window.__HF_CLEAN_UNIFIED__)return;
var started=performance.now(),events=[],dropped=0,MAX=14000,counts={};
var lastState='',lastProgress='',lastError='',lastResources='',lastMedia='';
function path(value){
 try{var u=new URL(String(value||''),location.href);
  return (u.origin===location.origin?'':u.origin)+u.pathname.slice(0,240);
 }catch(_){return '[unknown-path]';}
}
function clean(v,max){
 try{
  var s=typeof v==='string'?v:v instanceof Error?(v.stack||v.message):
   typeof v==='object'?JSON.stringify(v):String(v);
  return String(s||'').slice(0,max||1600)
   .replace(/https?:\/\/[^\s"']+/g,'[URL]')
   .replace(/(authorization|token|password|secret|api_key|bearer)\s*[:=]\s*\S+/gi,'$1=[REDACTED]');
 }catch(_){return '[unprintable]';}
}
function rec(type,detail){
 counts[type]=(counts[type]||0)+1;
 if(events.length<MAX)events.push({ms:Math.round(performance.now()-started),type:type,detail:detail||{}});
 else dropped++;
}
function visible(el){
 if(!el||el.hidden)return false;
 var s=getComputedStyle(el);
 return s.display!=='none'&&s.visibility!=='hidden'&&
   !el.closest('[hidden]');
}
function dom(){
 var st=document.getElementById('start-screen');
 var creator=document.getElementById('offline-select');
 var load=document.getElementById('loading-screen');
 var status=document.getElementById('ls-status');
 var fill=document.getElementById('ls-fill');
 var err=document.querySelector('[role="alert"], .error-overlay, #error-overlay, #loading-error');
 var option=document.getElementById('server-opt-offline');
 var sel=document.getElementById('server-select');
 return {ready:document.readyState,mode:sel?.dataset.mode||null,
  offlineAvailableInHtml:!!option,offlineOptionHidden:!!option?.hidden,
  startVisible:visible(st),creatorVisible:visible(creator),
  classCount:creator?.querySelectorAll('.mini-class[data-class]')?.length||0,
  worldLoadingVisible:visible(load),worldStatus:clean(status?.textContent||'',180),
  worldBar:fill?.style.width||'',canvasCount:document.querySelectorAll('canvas').length,
  overlayText:clean(err?.textContent||'',2200)};
}
function inspect(){
 if(!document.body)return;
 var d=dom(),state=JSON.stringify([d.mode,d.startVisible,d.creatorVisible,
  d.worldLoadingVisible,d.offlineOptionHidden,d.classCount]);
 if(state!==lastState){lastState=state;rec('UI_PHASE_CHANGED',d)}
 var prog=d.worldStatus+' '+d.worldBar;
 if(prog!==lastProgress){lastProgress=prog;rec('WORLD_LOADING_PROGRESS',{text:d.worldStatus,bar:d.worldBar})}
 var text=document.body.innerText||'';
 // Asset-loader fatal messages sometimes render as raw text instead of exceptions.
 var match=text.match(/(?:ERROR:\s*ASSET LOAD FAILED|ASSET LOAD FAILED|FAILED TO LOAD|MISSING FILE OR BAD GLB)[\s\S]*/i);
 var err=match?match[0].slice(0,13000):'';
 if(err&&err!==lastError){
  lastError=err;rec('VISIBLE_ASSET_FAILURE',{text:clean(err,13000),length:match[0].length})
 }
}
var savedConsole={};
['error','warn'].forEach(function(level){
 var old=console[level];savedConsole[level]=old;
 console[level]=function(){
  var arr=[].slice.call(arguments).slice(0,6).map(function(v){return clean(v,3500)});
  rec('CONSOLE_'+level.toUpperCase(),{arguments:arr});
  return old.apply(console,arguments);
 };
});
window.addEventListener('error',function(e){
 if(e.target&&e.target!==window&&(e.target.src||e.target.href)){
  rec('DOM_RESOURCE_FAILED',{url:path(e.target.src||e.target.href),
    tag:e.target.tagName||'',type:e.target.type||''});
 }else rec('WINDOW_SCRIPT_ERROR',{message:clean(e.message,3000),
   file:path(e.filename||''),line:e.lineno||0,column:e.colno||0,
   stack:clean(e.error?.stack,4000)});
},true);
window.addEventListener('unhandledrejection',function(e){
 rec('PROMISE_REJECTED',{reason:clean(e.reason,5000)});
});
window.addEventListener('securitypolicyviolation',function(e){
 rec('CSP_BLOCKED',{directive:e.violatedDirective,resource:path(e.blockedURI)});
});
if(typeof window.fetch==='function'){
 var originalFetch=window.fetch;
 window.fetch=function(){
  var arg=arguments[0],method='GET';
  try{method=String(arguments[1]?.method||arg?.method||'GET').toUpperCase()}catch(_){}
  var url=path(typeof arg==='string'||arg instanceof URL?arg:arg?.url);
  var t=performance.now();
  try{return originalFetch.apply(this,arguments).then(function(response){
   var ct=response.headers?.get('content-type')||'';
   var mismatch=/\.(glb|gltf|png|webp|jpg|jpeg)(?:$)/i.test(url)&&/text\/html/i.test(ct);
   if(!response.ok||mismatch||/\.(glb|gltf)(?:$)/i.test(url)){
    rec('FETCH_RESULT',{url:url,method:method,status:response.status,
     type:ct,mismatchHtmlForAsset:mismatch,ms:Math.round(performance.now()-t)});
   }return response;
  },function(err){
   rec('FETCH_REJECTED',{url:url,method:method,error:clean(err,1600)});throw err;
  })}catch(err){rec('FETCH_THROW',{url:url,error:clean(err,1600)});throw err;}
 };
}
if(window.XMLHttpRequest){
 var op=XMLHttpRequest.prototype.open,send=XMLHttpRequest.prototype.send;
 XMLHttpRequest.prototype.open=function(method,url){
  this.__hfmon={method:String(method||'GET'),url:path(url),at:performance.now()};
  return op.apply(this,arguments);
 };
 XMLHttpRequest.prototype.send=function(){
  var x=this,info=x.__hfmon;
  if(info){
   x.addEventListener('loadend',function(){
    try{
     var ct=x.getResponseHeader('content-type')||'';
     var mismatch=/\.(glb|gltf|png|webp|jpg|jpeg)$/i.test(info.url)&&/text\/html/i.test(ct);
     if(x.status>=400||!x.status||mismatch||/\.(glb|gltf)$/i.test(info.url)){
      rec('XHR_RESULT',{url:info.url,method:info.method,status:x.status,
       type:ct,mismatchHtmlForAsset:mismatch,
       ms:Math.round(performance.now()-info.at)});
     }
    }catch(e){rec('XHR_OBSERVE_ERROR',{message:clean(e)})}
   });
  }
  return send.apply(this,arguments);
 };
}
try{
 if(PerformanceObserver.supportedEntryTypes?.includes('resource')){
  new PerformanceObserver(function(l){
   l.getEntries().forEach(function(e){
    if(e.responseStatus>=400)rec('HTTP_RESOURCE_FAILURE',
      {url:path(e.name),status:e.responseStatus,ms:Math.round(e.duration)});
   });
  }).observe({type:'resource',buffered:true});
 }
}catch(e){rec('PERFORMANCE_OBSERVER_FAILED',{error:clean(e)})}
function download(){
 inspect();
 var state=dom();
 rec('USER_EXPORTED_REPORT',{state:state});
 var result={label:'HIGHFLY CLEAN UNIFIED LIFECYCLE LOG',version:1,
  createdAt:new Date().toISOString(),durationMs:Math.round(performance.now()-started),
  userAgent:navigator.userAgent,counts:counts,dropped:dropped,finalState:state,
  eventCount:events.length,events:events.slice()};
 var blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});
 var u=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=u;a.download='HIGHFLY_CLEAN_COMPLETO_'+Date.now()+'.json';
 a.style.display='none';document.body.appendChild(a);a.click();a.remove();
 setTimeout(function(){URL.revokeObjectURL(u)},2000);
}
window.__HF_CLEAN_UNIFIED__={events:events,counts:counts,snapshot:function(){
 return {counts:counts,state:dom(),events:events.slice(),dropped:dropped};},download:download};
function mount(){
 if(!document.body||document.getElementById('hf-clean-unified-log-control'))return;
 var host=document.createElement('div');host.id='hf-clean-unified-log-control';
 host.style.cssText='position:fixed;z-index:2147483645;right:9px;bottom:9px;'+
 'background:#0e1730;color:#fff;border:1px solid #62d6ff;border-radius:9px;'+
 'padding:6px;display:flex;align-items:center;gap:7px;font:12px system-ui;';
 var desc=document.createElement('span');desc.textContent='HIGHFLY LOG COMPLETO';
 var btn=document.createElement('button');btn.type='button';
 btn.textContent='DESCARGAR LOG';
 btn.style.cssText='color:#fff;background:#4b2cb4;border:1px solid #a988ff;'+
  'border-radius:6px;padding:8px 9px;font:700 12px system-ui;cursor:pointer;';
 btn.addEventListener('click',download);
 host.append(desc,btn);document.body.appendChild(host);
 rec('LOGGER_CONTROL_READY',dom());
 inspect();
 var monitor=new MutationObserver(function(){if(monitor.__timer)return;
  monitor.__timer=setTimeout(function(){monitor.__timer=null;inspect()},200);
 });
 monitor.observe(document.body,{subtree:true,attributes:true,childList:true,characterData:true,
  attributeFilter:['hidden','class','style','data-mode']});
}
rec('TRACE_STARTED',{pathname:location.pathname,ready:document.readyState});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
else mount();
window.addEventListener('load',function(){rec('WINDOW_LOADED',dom());inspect()},{once:true});
[1000,3000,10000,30000].forEach(function(ms){
 setTimeout(function(){rec('CHECKPOINT_'+ms,dom());inspect()},ms);
});
setInterval(function(){inspect()},10000);
})();
</script>"""

def validate():
 if not STAGE.is_dir() or STAGE.is_symlink() or not STAGE.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('UNIFIED_LOG_INVALID_PRIVATE_STAGE')
 if not DIST.is_dir() or DIST.is_symlink() or not DIST.resolve().is_relative_to(STAGE.resolve()):
  raise RuntimeError('UNIFIED_LOG_PRIVATE_BUILD_NOT_FOUND')
 if INDEX.is_symlink() or not INDEX.is_file():raise RuntimeError('UNIFIED_LOG_INDEX_NOT_FOUND')
 return INDEX.read_text('utf8')

def plan():
 original=validate()
 if MARK in original:return original,original,True
 if BACKUP.exists() or BACKUP.is_symlink():raise RuntimeError('UNIFIED_LOG_BACKUP_COLLISION')
 if original.count('<head>')!=1 or original.count('</head>')!=1:
  raise RuntimeError('UNIFIED_LOG_HTML_HEAD_UNEXPECTED')
 if 'offline-select' not in original or 'main-' not in original:
  raise RuntimeError('UNIFIED_LOG_NOT_THE_EXPECTED_PRIVATE_GAME')
 updated=original
 found=[]
 for tag in OLD_IDS:
  pat=r'<script\b[^>]*\bid=["\']'+tag+r'["\'][^>]*>[\s\S]*?</script>'
  updated,n=re.subn(pat,'',updated,count=1,flags=re.I)
  if n>1:raise RuntimeError('UNIFIED_LOG_OLD_LOG_AMBIGUOUS')
  found.append((tag,n))
 updated=re.sub(r'<!--\s*HIGHFLY_CLEAN_BOOTLOG_V1\s*-->','',updated)
 updated=re.sub(r'<!--\s*HIGHFLY_CLEAN_BROWSER_ESM_V1\s*-->','',updated)
 updated=updated.replace('<head>','<head>\n'+SCRIPT+'\n',1)
 if updated.count(MARK)!=1:raise RuntimeError('UNIFIED_LOG_INJECTION_INVALID')
 if any(x in updated for x in OLD_IDS):raise RuntimeError('UNIFIED_LOG_OLD_BUTTON_STILL_PRESENT')
 return original,updated,False

def apply():
 original,updated,already=plan()
 if already:
  print('[HIGHFLY UNIFIED] ALREADY_INSTALLED');return
 BACKUP.write_text(original,'utf8')
 if BACKUP.read_text('utf8')!=original:raise RuntimeError('UNIFIED_LOG_BACKUP_FAILED')
 if INDEX.read_text('utf8')!=original:raise RuntimeError('UNIFIED_LOG_CONCURRENT_INDEX_CHANGE')
 INDEX.write_text(updated,'utf8')
 print('[HIGHFLY UNIFIED] ONE LOGGER INSTALLED IN PRIVATE 4181 BUNDLE; previous buttons removed.')
 print('[HIGHFLY UNIFIED] Reload 4181; use single DESCARGAR LOG even if the 707 assets fail.')
 print('[HIGHFLY UNIFIED] Original source, media and saves untouched.')

def remove():
 current=validate()
 if MARK not in current or not BACKUP.is_file() or BACKUP.is_symlink():
  raise RuntimeError('UNIFIED_LOG_NO_BACKUP')
 old=BACKUP.read_text('utf8')
 if INDEX.read_text('utf8')!=current:raise RuntimeError('UNIFIED_LOG_CHANGED')
 # Recreate expected patched state from the backup for safe restoration.
 # During removal MARK is present, so compare via a temporary pure operation.
 saved_backup=BACKUP
 # Avoid loss from external edits: require exactly one injected script.
 if current.count(MARK)!=1 or '<script id="hf-clean-unified-lifecycle-logger">' not in current:
  raise RuntimeError('UNIFIED_LOG_DRIFT')
 script_rx=r'<script id="hf-clean-unified-lifecycle-logger">[\s\S]*?</script>'
 if len(re.findall(script_rx,current))!=1:
  raise RuntimeError('UNIFIED_LOG_SCRIPT_DRIFT')
 rebuilt=current.replace(SCRIPT,'')
 if not rebuilt or rebuilt==current:
  raise RuntimeError('UNIFIED_LOG_INJECTION_DRIFT')
 # The backup is byte-for-byte original, so guard by checking only generated
 # regions changed before restore.
 legacy=old
 for tag in OLD_IDS:
  legacy=re.sub(r'<script\b[^>]*\bid=["\']'+tag+r'["\'][^>]*>[\s\S]*?</script>','',legacy,count=1,flags=re.I)
 legacy=re.sub(r'<!--\s*HIGHFLY_CLEAN_BOOTLOG_V1\s*-->','',legacy)
 legacy=re.sub(r'<!--\s*HIGHFLY_CLEAN_BROWSER_ESM_V1\s*-->','',legacy)
 legacy=legacy.replace('<head>','<head>\n'+SCRIPT+'\n',1)
 if current!=legacy:raise RuntimeError('UNIFIED_LOG_USER_HTML_CHANGED')
 INDEX.write_text(old,'utf8');BACKUP.unlink()
 print('[HIGHFLY UNIFIED] BUNDLE INDEX RESTORED FROM EXACT BACKUP.')

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument('--apply',action='store_true')
 mode.add_argument('--remove',action='store_true')
 args=parser.parse_args()
 if args.apply:apply()
 else:remove()
