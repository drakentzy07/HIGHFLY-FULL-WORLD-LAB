#!/usr/bin/env node
// HIGHFLY P43 diagnostic: inspect live localhost:4175 in an isolated browser.
// Read-only on game sources; NEVER touch active P64 or user save data.
import { createRequire } from 'node:module';
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const LAB=path.join(ROOT,'.workspace','highfly-p43-restore-lab');
const URL='http://127.0.0.1:4175/';
const REPORT=path.join(ROOT,'.workspace','reports','highfly-world7','P43_LIVE_ENTRY_DIAGNOSTIC.json');
const report={
  phase:'P43_LIVE_ENTRY_DIAGNOSTIC', target:URL,
  activeP64Modified:false, offlineSavesModified:false,
  mobileBrowserVerified:false
};
function statString(p,needle){
  try{return readFileSync(p,'utf8').includes(needle);}
  catch(e){return 'READ_ERROR: '+String(e);}
}
function brief(e){return String(e).slice(0,600);}
async function request(part){
  try{
    const res=await fetch(URL+part,{signal:AbortSignal.timeout(20000),redirect:'follow',
      headers:{'Cache-Control':'no-cache'}});
    const body=await res.text();
    const type=res.headers.get('content-type')||'';
    return {status:res.status,url:res.url,type,body};
  }catch(e){return {status:0,error:brief(e),url:URL+part,body:''};}
}
const INDEX=path.join(LAB,'index.html');
const MAIN=path.join(LAB,'src','main.ts');
report.disk={
  labExists:existsSync(LAB),
  p43HtmlMark:statString(INDEX,'HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES'),
  p43CssRescue:statString(INDEX,'p43-css-rescue'),
  p43FullscreenScript:statString(INDEX,'highfly_p43_native_fullscreen.js'),
  nativeOfflineHtml:statString(INDEX,'id="server-opt-offline"'),
  p43MainMark:statString(MAIN,'HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES'),
  mainOfflineDefault:statString(MAIN,"applyServerMode(offlineAvailable ? 'offline' : 'online')"),
};
const home=await request('');
const main=await request('src/main.ts');
const fullscreen=await request('highfly_p43_native_fullscreen.js');
report.http={
  home:{status:home.status,url:home.url,type:home.type,servedP43Marker:home.body.includes('HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES'),
    hasOfflineNode:home.body.includes('id="server-opt-offline"'),
    hasModuleEntry:home.body.includes('src="/src/main.ts"'),
    hasFullscreenScript:home.body.includes('highfly_p43_native_fullscreen.js')},
  main:{status:main.status,url:main.url,type:main.type,containsPatchedDefault:main.body.includes("applyServerMode(offlineAvailable ? 'offline' : 'online')"),
    containsP43Marker:main.body.includes('HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES'),
    containsOfflineAvailable:main.body.includes('offlineAvailable'),
    preview:main.status!==200?main.body.slice(0,450):''},
  fullscreen:{status:fullscreen.status,type:fullscreen.type}
};
try {
  const requireFromLab=createRequire(path.join(LAB,'package.json'));
  const {chromium}=requireFromLab('playwright');
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  try{
    const page=await browser.newPage({
      viewport:{width:915,height:412},deviceScaleFactor:2,
      isMobile:true,hasTouch:true,locale:'es-AR'
    });
    let errors=[],failed=[],badResponses=[];
    page.on('pageerror',e=>errors.push(brief(e.stack||e)));
    page.on('console',m=>{if(m.type()==='error')errors.push('CONSOLE '+m.text().slice(0,350));});
    page.on('requestfailed',q=>{if(failed.length<25)failed.push(q.url().slice(0,200)+' '+q.failure()?.errorText);});
    page.on('response',res=>{if(res.status()>=400 && badResponses.length<25)badResponses.push({status:res.status(),url:res.url().slice(0,210)});});
    await page.goto(URL,{waitUntil:'domcontentloaded',timeout:30000});
    try {
      await page.waitForFunction(() =>
        document.getElementById('server-select')?.dataset.mode==='offline',
        {timeout:12000});
    } catch { await page.waitForTimeout(1000); }
    const inspect=()=>page.evaluate(()=>{
      const ids=['start-screen','btn-play','server-select','server-select-trigger',
        'server-select-value','server-select-menu','server-opt-online','server-opt-offline',
        'btn-offline','offline-select','hf-p43-fullscreen-btn'];
      const obj={url:location.href,title:document.title,readyState:document.readyState};
      for(const id of ids){
        const e=document.getElementById(id);
        if(!e){obj[id]={exists:false};continue;}
        const style=getComputedStyle(e);
        const rect=e.getBoundingClientRect();
        obj[id]={exists:true,hiddenAttr:e.hasAttribute('hidden'),display:style.display,
          visibility:style.visibility,size:[Math.round(rect.width),Math.round(rect.height)],
          text:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,135),
          mode:e.getAttribute('data-mode')||null};
      }
      return obj;
    });
    report.mobile=await inspect();
    const button=page.locator('#server-select-trigger');
    if(await button.count()){
      try{
        await button.click({timeout:3000});
        report.mobileAfterTap=await inspect();
        const offline=page.locator('#server-opt-offline');
        if(await offline.count() && await offline.isVisible()){
          await offline.click({timeout:3000});
          report.mobileAfterChooseOffline=await inspect();
        }
      }catch(e){report.mobileMenuError=brief(e);}
    }
    report.browserErrors=errors.slice(0,20);
    report.failedRequests=failed;
    report.badResponses=badResponses;
    report.offlineAutomaticallySelected=report.mobile?.['server-select']?.mode==='offline';
    report.offlineOptionHidden=report.mobile?.['server-opt-offline']?.hiddenAttr;
    report.nativeMainLikelyBooted=report.offlineAutomaticallySelected===true;
    report.diagnosisHint=report.offlineAutomaticallySelected
      ? 'Offline selected in the browser; if Android still shows Online, compare browser URL/cache/proxy.'
      : 'Offline not selected: inspect browserErrors, failedRequests, badResponses, and mobile selector state.';
    report.mobileBrowserVerified=true;
    await page.close();
  }finally{await browser.close();}
}catch(e){report.browserProbeError=brief(e);}
mkdirSync(path.dirname(REPORT),{recursive:true});
writeFileSync(REPORT,JSON.stringify(report,null,2)+'\n');
console.log('[HIGHFLY P43 LIVE DIAGNOSTIC]\n'+JSON.stringify(report,null,2));
console.log('REPORT_PATH='+REPORT);
if(report.http.home.status!==200||!report.http.home.servedP43Marker)process.exitCode=2;
