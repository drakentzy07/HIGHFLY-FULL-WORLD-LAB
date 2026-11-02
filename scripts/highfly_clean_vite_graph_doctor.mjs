#!/usr/bin/env node
// HIGHFLY CLEAN — scan the ACTUAL Vite-transformed STATIC ESM imports via HTTP.
// Browser-free: Codespaces Chromium headless can die before rendering. This
// catches first HTML-fallback, 404, 500, Vite transform error or wrong MIME.
// Static graph only (dynamic imports ignored), pure read-only, no browser,
// no game source/save/asset changes. Example: node scripts/highfly_clean_vite_graph_doctor.mjs
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const LAB=path.join(ROOT,'.workspace','highfly-origin-clean-0447');
const REPORT=path.join(ROOT,'.workspace','reports','highfly-clean-0447','VITE_STATIC_MODULE_GRAPH.json');
const PORT=Number(process.env.HF_CLEAN_PORT||4180);
const LIMIT=Number(process.env.HF_CLEAN_GRAPH_LIMIT||750);
const CONCURRENCY=Number(process.env.HF_CLEAN_GRAPH_WORKERS||6);
if(!Number.isInteger(PORT)||PORT<1024||PORT>65535||!Number.isInteger(LIMIT)||LIMIT<10||LIMIT>4000||
   !Number.isInteger(CONCURRENCY)||CONCURRENCY<1||CONCURRENCY>16) throw Error('INVALID_GRAPH_CONFIG');
const ORIGIN='http://127.0.0.1:'+PORT;
const makeUrl=value=>new URL(value,ORIGIN+'/');
const req=createRequire(path.join(LAB,'package.json'));
let parse,lexerName;
try{
  const lexer=req('es-module-lexer');
  await lexer.init;
  parse=lexer.parse; lexerName='es-module-lexer';
}catch(e){
  lexerName='static-import-regex-fallback';
  parse=(js)=>{
    // Conservative fallback; misses complex imports, so report coverage.
    const imports=[];
    const rx=/(?:^|\n)\s*(?:import|export)\s+(?:[\s\S]{0,350}?\s+from\s*)?(['"])([^'"\r\n]+)\1/gm;
    for(const m of js.matchAll(rx))imports.push({n:m[2],d:-1});
    return [imports,[]];
  };
}
const start=Date.now();
const failures=[],results=[],seen=new Set(),queue=['/src/main.ts'],edges=[];
let peakQueue=1;
function cleanPath(input){
  const u=makeUrl(input);
  if(u.origin!==ORIGIN)throw Error('REJECTED_REMOTE_MODULE');
  return u.pathname+u.search;
}
async function get(module){
  const url=makeUrl(module);
  const ctl=new AbortController();
  const timer=setTimeout(()=>ctl.abort(),20000);
  try{
    const r=await fetch(url,{cache:'no-store',redirect:'follow',signal:ctl.signal,
      headers:{'Accept':'*/*'}});
    const ct=r.headers.get('content-type')||'';
    const snippet=await r.text();
    const returned=new URL(r.url);
    const html=/text\/html/i.test(ct)||/^\s*(?:<!doctype html|<html)\b/i.test(snippet.slice(0,180));
    const js=/javascript|typescript|ecmascript/i.test(ct);
    if(returned.origin!==ORIGIN)return {path:module,status:r.status,contentType:ct,
      failed:'REDIRECTED_TO_EXTERNAL',final:returned.origin+returned.pathname};
    if(!r.ok||html||!js){
      return {path:module,status:r.status,contentType:ct,
        failed:html?'RECEIVED_HTML_INSTEAD_OF_JAVASCRIPT':!r.ok?'HTTP_ERROR':'WRONG_JS_CONTENT_TYPE',
        responseExcerpt:snippet.slice(0,1400).replace(/https?:\/\/[^\s'"<>]+/g,'[URL]')};
    }
    const [imports]=parse(snippet);
    const children=[];
    for(const item of imports){
      if(item.d!==-1||!item.n||!item.n.startsWith('/')&&!item.n.startsWith('.'))continue;
      try{
        const dest=new URL(item.n,url);
        if(dest.origin!==ORIGIN)continue;
        // CSS imported as a module (without ?direct) is valid JS in Vite.
        // Ignore image files and assets, which import via ?url and don't link further.
        const p=dest.pathname+dest.search;
        children.push(p);
      }catch{}
    }
    return {path:module,status:r.status,contentType:ct,importCount:imports.length,
      children:[...new Set(children)],contentBytes:snippet.length};
  }catch(e){return {path:module,failed:e.name==='AbortError'?'TIMEOUT':'NETWORK_ERROR',
      error:String(e?.message||e).slice(0,400)}}
  finally{clearTimeout(timer)}
}
function fail(f){
 return !!f.failed;
}
async function scan(){
 while(queue.length&&seen.size<LIMIT&&failures.length<18){
   const batch=[];
   while(queue.length&&batch.length<CONCURRENCY&&seen.size<LIMIT){
     const u=cleanPath(queue.shift());
     if(seen.has(u))continue;
     seen.add(u);batch.push(u);
   }
   const found=await Promise.all(batch.map(get));
   for(const item of found){
     if(fail(item)){failures.push(item);continue;}
     results.push({path:item.path,status:item.status,contentType:item.contentType,
       importCount:item.importCount,contentBytes:item.contentBytes});
     for(const c of item.children){
       if(edges.length<6000)edges.push({parent:item.path,child:c});
       if(!seen.has(c)&&!queue.includes(c))queue.push(c);
     }
   }
   peakQueue=Math.max(peakQueue,queue.length);
   if(seen.size%120<CONCURRENCY)process.stdout.write('[VITE ESM] scanned '+seen.size+' modules; pending '+queue.length+'; failures '+failures.length+'\n');
 }
}
if(!existsSync(path.join(LAB,'src','main.ts')))throw Error('CLEAN_LAB_MAIN_MISSING');
await scan();
const parents=new Map();
for(const e of edges){if(!parents.has(e.child))parents.set(e.child,e.parent);}
const trace=target=>{
 const chain=[target], visited=new Set(chain);
 while(parents.has(chain[0]) && chain.length<20){
  const p=parents.get(chain[0]);if(visited.has(p))break;
  chain.unshift(p);visited.add(p);
 }
 return chain;
};
for(const f of failures)f.importChain=trace(f.path);
const report={task:'HIGHFLY CLEAN / original v0.44.7 / static module imports',
  atUtc:new Date().toISOString(),source:'Vite HTTP transformed modules via localhost',
  parser:lexerName,port:PORT,limit:LIMIT,checked:seen.size,
  queueUnexplored:queue.length,peakQueue,elapsedMs:Date.now()-start,
  errors:failures,modules:results.slice(0,240),edges:edges.slice(0,1000),
  originalSourceModified:false,modelAssetsModified:false,offlineSavesModified:false,
  notes:['Only static ESM imports; dynamic routes may still fail later.',
   'HTTP 200 main.ts alone does not prove its transitively imported modules load.',
   'No zero-error playable-world claim until real browser entry is tested.']};
mkdirSync(path.dirname(REPORT),{recursive:true});
writeFileSync(REPORT,JSON.stringify(report,null,2)+'\n','utf8');
console.log('\n[HIGHFLY CLEAN ESM RESULT]',JSON.stringify({
  moduleCount:seen.size,remaining:queue.length,parser:lexerName,
  firstFailures:failures.slice(0,16),elapsedMs:report.elapsedMs,
  report:REPORT},null,2));
if(failures.length||queue.length)process.exitCode=1;
