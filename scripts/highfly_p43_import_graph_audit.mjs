#!/usr/bin/env node
/**
 * HIGHFLY P43: find the FIRST actual broken Vite ESM import.
 *
 * Browser module-script <script type="module" src="/src/main.ts"> may fire
 * a load error even when GET /src/main.ts is 200: one of its imports can be
 * missing (404/500), non-JS (login/auth HTML), or not resolvable.
 *
 * This tool follows static import/export + literal import() dependencies using
 * the TypeScript syntax parser already installed in the private lab.
 * Read-only, no browser launch, no package installs, no active P64 changes.
 */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const WORK=path.join(ROOT,'.workspace');
const LAB=path.join(WORK,'highfly-p43-restore-lab');
const ORIGINAL=path.join(WORK,'claudecraft-v0.44.7');
const REPORT=path.join(WORK,'reports','highfly-world7','P43_IMPORT_GRAPH_FAILURES.json');
const BASE='http://127.0.0.1:4175';
const MAX_MODULES=900, MAX_FAILURES=12, BATCH=12;
const out={
  phase:'P43_ESM_IMPORT_GRAPH',
  target:BASE+'/src/main.ts',
  sourceRoot:LAB,
  readOnly:true, activeP64Modified:false, browserVerified:false,
  note:'Checks served ESM dependency URLs, not runtime behavior or browser linking.'
};

if(!existsSync(path.join(LAB,'src','main.ts'))){
  throw new Error('P43_ISOLATED_STAGE_NOT_FOUND');
}
const req=createRequire(path.join(LAB,'package.json'));
let ts;
try{ts=req('typescript');}
catch(e){throw new Error('TYPESCRIPT_PARSER_NOT_INSTALLED_IN_P43_NODE_MODULES: '+String(e));}

function readImports(source,relativeURL){
  const sf=ts.createSourceFile(relativeURL,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);
  const specs=new Set();
  function check(node){
    let value;
    if(ts.isImportDeclaration(node)||ts.isExportDeclaration(node)){
      if(node.moduleSpecifier&&ts.isStringLiteralLike(node.moduleSpecifier))value=node.moduleSpecifier.text;
    }else if(ts.isCallExpression(node)&&node.expression.kind===ts.SyntaxKind.ImportKeyword){
      const first=node.arguments[0];
      if(first&&ts.isStringLiteralLike(first))value=first.text;
    }
    if(value)specs.add(value);
    ts.forEachChild(node,check);
  }
  check(sf);
  return [...specs];
}

function resolveImport(base,spec){
  if(!spec.startsWith('.')&&!spec.startsWith('/')&&!spec.startsWith('http'))return null;
  let result;
  try{result=new URL(spec,base);}
  catch{return null;}
  if(result.origin!==BASE)return null;
  if(result.pathname.startsWith('/@fs/') || result.pathname.includes('..'))return null;
  return result.href;
}

function fileHint(href){
  let url;
  try{url=new URL(href);}catch{return null;}
  if(!url.pathname.startsWith('/src/'))return null;
  let rel;
  try{rel=decodeURIComponent(url.pathname.slice(1));}catch{return null;}
  if(rel.split('/').some(x=>x==='..'))return null;
  const stage=path.join(LAB,rel);
  const original=path.join(ORIGINAL,rel);
  return {relative:rel,inLab:existsSync(stage),inOriginal:existsSync(original)};
}

const queue=[{url:BASE+'/src/main.ts',parent:'index.html'}];
const discovered=new Set([queue[0].url]);
const checked=new Set();
const failures=[];
let edges=0,skipped=0,jsCount=0;
function addFailure(item,kind,extra){
  if(failures.length>=MAX_FAILURES)return;
  failures.push({kind,url:item.url.replace(BASE,''),importedBy:item.parent.replace(BASE,''),
    originalSourceHint:fileHint(item.url),...extra});
}

async function visit(item){
  let response,raw='',contentType='';
  try{
    response=await fetch(item.url,{
      signal:AbortSignal.timeout(12000),
      redirect:'follow',headers:{accept:'text/javascript, text/css;q=0.5, */*;q=0.1'}
    });
    contentType=response.headers.get('content-type')||'';
    raw=await response.text();
  }catch(e){
    addFailure(item,'NETWORK_OR_TRANSFORM_TIMEOUT',{error:String(e).slice(0,450)});
    return;
  }
  checked.add(item.url);
  if(!response.ok){
    addFailure(item,'HTTP_'+response.status,{
      contentType,redirected:response.redirected,
      responseURL:response.url.replace(BASE,''),
      excerpt:raw.slice(0,950)});
    return;
  }
  if(response.redirected&&new URL(response.url).origin!==BASE){
    addFailure(item,'AUTH_OR_REDIRECT',{responseURL:response.url,contentType});return;
  }
  if(/^\s*<(?:!doctype html|html)\b/i.test(raw)||(/html/.test(contentType)&&item.url.endsWith('.ts'))){
    addFailure(item,'HTML_INSTEAD_OF_MODULE',{contentType,
      responseURL:response.url,excerpt:raw.slice(0,350)});
    return;
  }
  if(!/javascript|ecmascript|typescript/i.test(contentType)){
    // Vite CSS direct resource was not meant to be parsed as ESM.
    if(/text\/css/.test(contentType))return;
    addFailure(item,'WRONG_MODULE_MIME',{contentType,excerpt:raw.slice(0,220)});return;
  }
  jsCount++;
  for(const spec of readImports(raw,item.url)){
    edges++;
    const target=resolveImport(item.url,spec);
    if(!target){skipped++;continue;}
    if(discovered.has(target))continue;
    discovered.add(target);
    queue.push({url:target,parent:item.url});
  }
}
while(queue.length&&checked.size<MAX_MODULES&&failures.length<MAX_FAILURES){
  const group=queue.splice(0,Math.min(BATCH,MAX_MODULES-checked.size));
  await Promise.all(group.map(visit));
}
out.summary={visited:checked.size,discovered:discovered.size,staticEdges:edges,
  skippedNonLocalOrBare:skipped,validJavascriptModules:jsCount,
  pending:queue.length,stoppedAtLimit:checked.size>=MAX_MODULES,
  failureCount:failures.length};
out.failures=failures;
out.nextAction=failures.length
 ? 'Inspect the FIRST error and its importedBy path; restore verified missing MIT source into P43 only.'
 : queue.length?'Increase MAX_MODULES only if needed.':'No network/MIME failures in crawled static imports; inspect ESM export binding/runtime.';
mkdirSync(path.dirname(REPORT),{recursive:true});
writeFileSync(REPORT,JSON.stringify(out,null,2)+'\n');
console.log('[HIGHFLY P43 IMPORT GRAPH]\n'+JSON.stringify(out,null,2));
console.log('REPORT_PATH='+REPORT);
if(failures.length)process.exitCode=2;
