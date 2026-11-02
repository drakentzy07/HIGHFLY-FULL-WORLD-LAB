#!/usr/bin/env node
// HIGHFLY CLEAN 0.44.7 — real browser ESM module-graph diagnosis on Codespaces.
// Disposable Playwright context, DOES NOT mutate source, save files or assets.
// Requires running Vite localhost:4180. Diagnoses the reason main.ts cannot
// initialize nine-class OFFLINE menu. Reports failing request, Vite overlay,
// JS module import error and HTML/MIME mismatches even for HTTP 200.
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const LAB=path.join(ROOT,'.workspace','highfly-origin-clean-0447');
const REPORT=path.join(ROOT,'.workspace','reports','highfly-clean-0447','MODULE_GRAPH_BROWSER_DIAG.json');
const PORT=Number.parseInt(process.env.HF_CLEAN_PORT||'4180',10);
const URL_BASE='http://127.0.0.1:'+PORT+'/';
const started=Date.now();
const events=[], failed=[], broken=[], observed=[];
const limited=(arr,data,max=160)=>{if(arr.length<max)arr.push(data)};
const brief=(v,n=1100)=>String(v?.stack||v?.message||v).slice(0,n);
function address(uri){
 try{const u=new URL(uri,URL_BASE);return u.pathname;}catch{return '[invalid-url]';}
}
const report={phase:'HF_CLEAN_ORIGINAL_MODULE_LINK_DIAGNOSTIC',
 target:URL_BASE,sourceChanged:false,gameStateChanged:false,
 browserContext:'disposable',sourceVersion:'claudecraft-0.44.7',port:PORT,
 startedUtc:new Date().toISOString(),browserVerified:false};
let browser;
try{
 if(!existsSync(path.join(LAB,'src','main.ts')))throw new Error('CLEAN_0447_LAB_MISSING');
 const requireLab=createRequire(path.join(LAB,'package.json'));
 const {chromium}=requireLab('playwright');
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:1280,height:720},locale:'es-AR',
   serviceWorkers:'block'});
 const page=await context.newPage();
 page.on('pageerror',e=>limited(events,{type:'PAGE_ERROR',message:brief(e,1500)}));
 page.on('console',m=>{
  if(m.type()==='error'||m.type()==='warning')limited(events,{type:'CONSOLE_'+m.type(),
   message:m.text().slice(0,1500)});
 });
 page.on('requestfailed',r=>limited(failed,{url:address(r.url()),method:r.method(),
  error:r.failure()?.errorText||'unknown'}));
 page.on('response',async r=>{
  const name=address(r.url()),status=r.status();
  const type=r.headers()['content-type']||'';
  const isModule=/\.(?:ts|tsx|js|mjs)(?:\?|$)/.test(name)||name.startsWith('/@id/');
  if(isModule&&observed.length<40)observed.push({url:name,status,type});
  const mismatch=isModule && r.ok() && /text\/html/i.test(type);
  if(status>=400||mismatch){
   const detail={url:name,status,type,mismatchHtmlForJs:mismatch};
   if(status>=400||mismatch){
    try{detail.responseExcerpt=(await r.text()).slice(0,1200)
      .replace(/https?:\/\/[^\s"']+/g,'[URL]');}catch{}
   }
   limited(broken,detail);
  }
 });
 try{
  await page.goto(URL_BASE,{waitUntil:'domcontentloaded',timeout:45000});
 }catch(e){report.navigationError=brief(e);}
 await page.waitForTimeout(2500);
 report.bootState=await page.evaluate(()=>{
  const server=document.getElementById('server-select');
  const option=document.getElementById('server-opt-offline');
  const vite=document.querySelector('vite-error-overlay');
  const offline=document.getElementById('offline-select');
  return {readyState:document.readyState,
   selectedMode:server?.dataset?.mode??null,
   optionExists:!!option,optionHidden:option?.hasAttribute('hidden')??null,
   creatorClasses:offline?.querySelectorAll('.mini-class[data-class]')?.length??0,
   viteErrorOverlay:vite?.shadowRoot?.textContent?.slice(0,2600)||null,
   viteErrorHtml:vite?.shadowRoot?.querySelector('.message-body')?.textContent?.slice(0,2600)||null};
 });
 // Reattempt the ORIGINAL module in disposable browser. If the original
 // failed during linking, this surfaces exact missing import/stack. If it
 // succeeds, it can initialize the game in disposable context only.
 report.explicitModuleImport=await page.evaluate(async()=>{
  try{await import('/src/main.ts');return {ok:true};}
  catch(e){return {ok:false,name:String(e?.name||''),message:String(e?.message||e),
    stack:String(e?.stack||'').slice(0,3000)};}
 });
 await page.waitForTimeout(1200);
 report.afterImport=await page.evaluate(()=>({
  mode:document.getElementById('server-select')?.dataset.mode??null,
  viteOverlay:document.querySelector('vite-error-overlay')?.shadowRoot?.textContent?.slice(0,1500)||null,
  offlineOptionHidden:document.getElementById('server-opt-offline')?.hasAttribute('hidden')??null
 }));
 report.browserVerified=true;
 await context.close();
}catch(e){
 report.probeError=brief(e,1800);
}finally{
 if(browser)try{await browser.close();}catch{}
}
report.elapsedMs=Date.now()-started;
report.pageErrors=events;
report.requestFailures=failed;
report.invalidHttpAndJsResponses=broken;
report.firstObservedModules=observed;
mkdirSync(path.dirname(REPORT),{recursive:true});
writeFileSync(REPORT,JSON.stringify(report,null,2)+'\n','utf8');
console.log('[HF CLEAN MODULE] '+JSON.stringify({
  browserVerified:report.browserVerified,
  selectedRealm:report.bootState?.selectedMode??null,
  optionExists:report.bootState?.optionExists??null,
  optionHidden:report.bootState?.optionHidden??null,
  import:report.explicitModuleImport,
  errors:events.slice(0,10),requestsFailed:failed.slice(0,10),
  badModuleResponses:broken.slice(0,10),
  viteError:report.bootState?.viteErrorOverlay?.slice(0,1300),
  probeError:report.probeError,
  report:REPORT
},null,2));
if(report.probeError||report.explicitModuleImport?.ok===false||broken.length||failed.length)
 process.exitCode=1;
