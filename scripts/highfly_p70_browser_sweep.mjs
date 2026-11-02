#!/usr/bin/env node
/* HIGHFLY P70 full private browser sweep. New isolated browser context;
 * captures ALL page errors, GLB HTTP statuses, console errors, and snapshots.
 * Does not change game sources, binaries, browser saves, or existing user tabs.
 * Example: node scripts/highfly_p70_browser_sweep.mjs --mobile
 */
import {existsSync,mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const LAB=path.join(ROOT,'.workspace/highfly-p69-restore-lab');
const REPORT_DIR=path.join(ROOT,'.workspace/reports/highfly-world7/p70-sweep');
const MOBILE=process.argv.includes('--mobile');
const NO_CREATE=process.argv.includes('--no-create');
const URL_BASE='http://127.0.0.1:4176/';
const URL_TEST=URL_BASE+'?hf_p69_boot=1&hf_p70_diag=1';
const waitMs=Number.parseInt(process.env.HF_P70_SWEEP_MS||'14000',10);
const events=[],steps=[];
const MAX=30000;
let dropped=0;
const emit=(type,data)=>{const row={at:new Date().toISOString(),type,data};if(events.length<MAX)events.push(row);else dropped++;};
const safeError=e=>String(e?.stack||e?.message||e).slice(0,1800);
const summarize=(snap)=>({selectedRealm:snap?.selectedRealm,creator:snap?.creator,preview:snap?.preview,classes:snap?.classes?.length,visibleClasses:snap?.classes?.filter(x=>x.width>0).length,loading:snap?.loading});
const report={
  name:'HIGHFLY P70 COMPLETE BROWSER SWEEP',version:1,
  timestamp:new Date().toISOString(),
  viewport:MOBILE?'915x412 S23 landscape simulation':'1365x768 desktop',
  url:URL_TEST,notes:[
    'Separate incognito-like context: existing user game saves not touched',
    'A working DEV server at port 4176 is required',
    'Result is browser evidence; no license proof comes from model name',
    'No source or model modifications happen in this sweep'
  ]
};
let browser=null;
async function inspect(page,name){
  const obj=await page.evaluate(()=>{
    function elem(id){
      const e=document.getElementById(id);
      if(!e)return {exists:false};
      const s=getComputedStyle(e),r=e.getBoundingClientRect();
      const parents=[];
      for(let n=e.parentElement;n&&parents.length<9;n=n.parentElement){
        const cs=getComputedStyle(n);
        if(cs.display==='none'||cs.visibility==='hidden'||n.hidden){
          parents.push({tag:n.tagName,id:n.id,hidden:n.hidden,display:cs.display,visibility:cs.visibility});
        }
      }
      return {exists:true,width:Math.round(r.width),height:Math.round(r.height),
        display:s.display,visibility:s.visibility,hidden:e.hidden,
        blockedByAncestors:parents};
    }
    const creator=document.getElementById('offline-select');
    const preview=document.getElementById('offline-preview-container');
    const classes=creator?[...creator.querySelectorAll('.mini-class[data-class]')].map(x=>{
      const r=x.getBoundingClientRect();
      return {key:x.dataset.class,width:Math.round(r.width),height:Math.round(r.height),
        display:getComputedStyle(x).display};
    }):[];
    return {
      href:location.pathname+location.search,readyState:document.readyState,
      start:elem('start-screen'),server:elem('server-select'),
      selectedRealm:document.getElementById('server-select')?.dataset.mode||null,
      creator:elem('offline-select'),preview:elem('offline-preview-container'),
      classes,
      previewCanvas:preview?.querySelectorAll('canvas').length||0,
      previewChildren:preview?.children.length||0,
      nativeCanvasCount:document.querySelectorAll('canvas').length,
      worldLoading:elem('loading-screen'),
      loadStatus:document.getElementById('ls-status')?.textContent?.slice(0,250)||'',
      progress:document.getElementById('ls-fill')?.style.width||'',
      documentWidth:document.documentElement.scrollWidth,
      viewport:[innerWidth,innerHeight],
      firstErrorText:document.body?.innerText?.match(/(?:ASSET LOAD FAILED|missing file|module failed|ERR_)[^\n]{0,280}/i)?.[0]||''
    };
  });
  steps.push({name,state:obj});
  console.log('[P70]',name,JSON.stringify(summarize(obj)));
  return obj;
}
async function shot(page,name){
  const file=path.join(REPORT_DIR,name+(MOBILE?'_mobile':'_desktop')+'.png');
  try{await page.screenshot({path:file,fullPage:false,timeout:12000});report.screenshots.push(file);}
  catch(e){emit('SCREENSHOT_FAILED',{step:name,error:safeError(e)});}
}
async function clickIfVisible(page,selector,name){
  const item=page.locator(selector).first();
  if(await item.count() && await item.isVisible().catch(()=>false)){
    try{await item.click({timeout:3500});steps.push({action:name,status:'clicked'});return true;}
    catch(e){steps.push({action:name,status:'failed',error:safeError(e)});}
  }else{steps.push({action:name,status:'not-visible'});}
  return false;
}
async function main(){
  mkdirSync(REPORT_DIR,{recursive:true});
  const t0=Date.now();
  try{
    const index=path.join(LAB,'index.html');
    if(!existsSync(index))throw new Error('P70_LAB_INDEX_MISSING');
    const requireLab=createRequire(path.join(LAB,'package.json'));
    const {chromium}=requireLab('playwright');
    browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
    const context=await browser.newContext(MOBILE?{
      viewport:{width:915,height:412},deviceScaleFactor:2,isMobile:true,hasTouch:true,locale:'es-AR',
      serviceWorkers:'block'
    }:{viewport:{width:1365,height:768},deviceScaleFactor:1,locale:'es-AR',serviceWorkers:'block'});
    const page=await context.newPage();
    page.on('console',m=>{
      if(['error','warning'].includes(m.type()))emit('CONSOLE_'+m.type().toUpperCase(),m.text().slice(0,2200));
    });
    page.on('pageerror',e=>emit('PAGE_ERROR',safeError(e)));
    page.on('crash',()=>emit('PAGE_CRASH','Chromium page crashed'));
    page.on('requestfailed',r=>emit('REQUEST_FAILED',{url:r.url(),method:r.method(),error:r.failure()?.errorText||'unknown'}));
    page.on('response',r=>{
      const url=r.url().split('?')[0];
      const status=r.status();
      if(status>=400 || /\.(glb|gltf)(?:$|#)/i.test(url)){
        const headers=r.headers();
        emit('HTTP_RESPONSE',{url,status,mime:headers['content-type']||'',size:headers['content-length']||'', 
          invalidGlbHtml:/\.glb$/i.test(url)&&/text\/html/i.test(headers['content-type']||'')});
      }
    });
    page.on('dialog',async d=>{emit('BROWSER_DIALOG',{type:d.type(),message:d.message().slice(0,450)});await d.dismiss();});
    const initial=await page.goto(URL_TEST,{waitUntil:'domcontentloaded',timeout:40000});
    report.httpInitial=initial?.status();
    await page.waitForTimeout(2400);
    await inspect(page,'A01_initial_entry');
    await shot(page,'A01_initial_entry');
    await clickIfVisible(page,'#btn-play','B02_start');
    await page.waitForTimeout(1000);
    await inspect(page,'B02_after_start');
    const realm=await page.evaluate(()=>document.getElementById('server-select')?.dataset.mode||'');
    if(realm!=='offline'){
      await clickIfVisible(page,'#server-select-trigger','C03_open_realm');
      await clickIfVisible(page,'#server-opt-offline','C03_select_offline');
    }
    await page.waitForTimeout(1800);
    await inspect(page,'C03_realm_selection');
    await shot(page,'C03_realm_selection');
    const current=await page.evaluate(()=>{
      const e=document.getElementById('offline-select');
      return !!e && getComputedStyle(e).display!=='none' && !e.hidden;
    });
    if(current){
      await shot(page,'D04_native_creator');
      await inspect(page,'D04_native_creator');
      // Choose one original class to test native preview; never replace a GLB.
      if(!NO_CREATE){
        await clickIfVisible(page,'#offline-select .mini-class[data-class="warrior"]','D04_warrior');
        const input=page.locator('#char-name');
        if(await input.count()&&await input.isVisible().catch(()=>false)){
          try{await input.fill('P70_Diagnostico');steps.push({action:'D04_fill_name',status:'filled'});}
          catch(e){emit('UI_ACTION_FAILED',{name:'fill_name',error:safeError(e)});}
        }
        await page.waitForTimeout(2000);
        await inspect(page,'D05_preview_after_selection');
        await shot(page,'D05_preview_after_selection');
        await clickIfVisible(page,'#btn-start-offline','E06_enter_world');
      }
    }
    if(!Number.isFinite(waitMs)||waitMs<1000||waitMs>90000)throw new Error('HF_P70_SWEEP_MS must be 1000..90000');
    await page.waitForTimeout(waitMs);
    await inspect(page,'F07_after_world_loading');
    await shot(page,'F07_after_world_loading');
    try { report.clientExport=await page.evaluate(()=>window.__HIGHFLY_P70_TRACE__?.export?.()||null); }
    catch(e) { emit('CLIENT_EXPORT_FAILED',safeError(e)); }
    await context.close();
  }catch(e){report.error=safeError(e);emit('SWEEP_ERROR',safeError(e));}
  finally{
    if(browser)await browser.close().catch(()=>{});
    report.seconds=+(Date.now()-t0).toFixed(0)/1000;
    report.steps=steps;report.events=events;report.dropped=dropped;
    const counts={};for(const e of events)counts[e.type]=(counts[e.type]||0)+1;
    report.counts=counts;
    const out=path.join(REPORT_DIR,'P70_BROWSER_SWEEP_'+(MOBILE?'MOBILE':'DESKTOP')+'.json');
    writeFileSync(out,JSON.stringify(report,null,2)+'\n');
    console.log('[P70 SWEEP] Report:',out);
    console.log('[P70 SWEEP] Event counts:',JSON.stringify(counts));
    console.log('[P70 SWEEP] Errors from browser:',report.error||'none (this does NOT prove gameplay works)');
  }
}
await main();
