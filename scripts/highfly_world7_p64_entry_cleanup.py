#!/usr/bin/env python3
"""WORLD7 P64 entry cleanup: retire obsolete class-hiding presentation and expose REAL progress.

Only index.html and two new presentation files are affected; keep original native
login/offline editor/loader, P41 save, FURY P48 sim and world assets untouched.
No reapplication of P65-P71. Dry-run by default, exact SHA guard against
verified P64 rollback, immutable backup, private Vite rebuild and rollback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9

WORK=ROOT/".workspace"
STAGE=p9.STAGE
P64_STATUS=WORK/"reports/highfly-world7/p64-clean-recovery/P64_CLEAN_STATUS.json"
OUT=WORK/"reports/highfly-world7/p64-entry-clean"
HTML="index.html"
CSS_FILE="public/highfly/p64_entry_clean.css"
JS_FILE="public/highfly/p64_entry_progress.js"
STATUS_FILE="P64_ENTRY_STATUS.json"
BACKUP="snapshot/index.html"
MARK="HIGHFLY_P64_ENTRY_CLEAN_20261102"
CSS=r"""/* HIGHFLY_P64_ENTRY_CLEAN_20261102
   A single entry/loading presentation. Preserve native controls, no fake loading. */
/* Native touch controls must NEVER float over splash or while loader is visible.
   P48 had positioned dodge independently with an enormous z-index. */
body:not(.game-active) #mobile-controls,
body:not(.game-active) #mobile-action-ring,
body:not(.game-active) #mobile-dodge,
body.start-screen-open #mobile-controls,
body.start-screen-open #mobile-action-ring,
body.start-screen-open #mobile-dodge,
body:has(#loading-screen.visible) #mobile-controls,
body:has(#loading-screen.visible) #mobile-action-ring,
body:has(#loading-screen.visible) #mobile-dodge{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
}
/* Keep the same HIGHFLY splash across the start screen and real loading.
   P46 intro remains the original landing CTA; no duplicate replacement button. */
#start-screen.hf-p46-entry,
#loading-screen{
  background-color:#090719!important;
  background-image:url('/highfly/official/highfly_splash.png')!important;
  background-position:center center!important;
  background-size:cover!important;
}
#loading-screen::before,
#loading-screen::after{
  content:none!important;display:none!important;background-image:none!important;
}
/* The original engine owns #ls-fill and changes its width.
   This is only a legible skin and does not simulate completion. */
body #loading-screen .ls-progress{
  position:fixed!important;inset:auto auto max(3dvh,env(safe-area-inset-bottom)) 50%!important;
  transform:translateX(-50%)!important;box-sizing:border-box!important;
  z-index:1500!important;display:flex!important;flex-direction:column!important;
  align-items:stretch!important;justify-content:center!important;
  gap:7px!important;width:min(760px,91vw)!important;height:auto!important;
  min-height:98px!important;max-height:none!important;
  padding:11px 18px!important;overflow:hidden!important;
  border:1px solid #ab80e7!important;border-radius:13px!important;
  background:linear-gradient(130deg,rgba(9,8,25,.94),rgba(35,15,55,.92))!important;
  box-shadow:0 8px 25px rgba(0,0,0,.6),0 0 13px rgba(128,70,218,.34)!important;
}
body #loading-screen #ls-status{
  position:static!important;inset:auto!important;order:0!important;
  transform:none!important;display:block!important;width:100%!important;
  height:auto!important;min-height:17px!important;max-height:none!important;
  margin:0!important;padding:0!important;border:0!important;background:none!important;
  white-space:normal!important;text-align:center!important;
  font:700 clamp(12px,1.8vw,16px)/1.3 system-ui,sans-serif!important;
  color:#f9efff!important;text-shadow:0 1px 5px #000!important;
}
body #loading-screen .ls-bar{
  position:relative!important;order:1!important;inset:auto!important;
  display:block!important;box-sizing:border-box!important;
  width:100%!important;height:13px!important;min-height:13px!important;
  margin:0!important;padding:0!important;
  overflow:hidden!important;border:1px solid #c2a2fa!important;
  border-radius:20px!important;background:#17102d!important;
  box-shadow:none!important;
}
body #loading-screen #ls-fill{
  display:block!important;height:100%!important;max-width:100%!important;
  border-radius:20px!important;
  background:linear-gradient(90deg,#7e43de,#d07dff,#76ddff)!important;
}
body #loading-screen #ls-tip{display:none!important}
body #loading-screen #ls-slow-hint{display:none!important}
body #loading-screen #hf-entry-progress-detail{
  display:block!important;order:2!important;
  min-height:15px!important;margin:0!important;
  font:600 clamp(11px,1.4vw,13px)/1.3 system-ui,sans-serif!important;
  color:#e5d8ff!important;text-align:center!important;
  background:none!important;white-space:normal!important;pointer-events:none!important;
}
/* The 9 native class cards, descriptions and appearance editor are authored
   by ClaudeCraft. No class is hidden or renamed by HIGHFLY here. */
@media(max-height:450px) and (orientation:landscape){
 body #loading-screen .ls-progress{
  min-height:72px!important;padding:6px 12px!important;gap:5px!important;
  bottom:max(2dvh,env(safe-area-inset-bottom))!important;
 }
 body #loading-screen .ls-bar{height:10px!important;min-height:10px!important}
}
"""
JS=r"""// HIGHFLY_P64_ENTRY_CLEAN_20261102 — observational native loader readout.
// Never set ls-fill width; never force load completion or modify the Sim.
(function(){
 'use strict';
 function boot(){
   const loader=document.getElementById('loading-screen');
   const fill=document.getElementById('ls-fill');
   const panel=loader&&loader.querySelector('.ls-progress');
   if(!loader||!fill||!panel)return;
   if(document.getElementById('hf-entry-progress-detail'))return;
   const text=document.createElement('div');
   text.id='hf-entry-progress-detail';
   text.setAttribute('role','status');
   text.setAttribute('aria-live','off');
   panel.appendChild(text);
   let activeAt=0,lastChange=0,lastWidth='';
   let lastLabel='';
   function update(){
     if(!loader.classList.contains('visible')){
       activeAt=0;lastChange=0;lastWidth='';lastLabel='';
       text.textContent='';
       return;
     }
     const now=Date.now();
     if(!activeAt){activeAt=now;lastChange=now;}
     const width=fill.style.width.trim();
     if(width!==lastWidth){lastWidth=width;lastChange=now;}
     const pct=/^\d+(?:\.\d+)?%$/.test(width)?width:'sin dato';
     const stalled=now-lastChange>=15000;
     const elapsed=Math.round((now-activeAt)/1000);
     const label='Progreso del motor: '+pct+' · '+elapsed+' s'+
       (stalled?' · Sin avance visible desde hace '+Math.round((now-lastChange)/1000)+' s':'');
     if(label!==lastLabel){text.textContent=label;lastLabel=label;}
   }
   update();
   const observer=new MutationObserver(update);
   observer.observe(fill,{attributes:true,attributeFilter:['style']});
   observer.observe(loader,{attributes:true,attributeFilter:['class']});
   const tick=setInterval(update,1000);
   window.addEventListener('pagehide',()=>{clearInterval(tick);observer.disconnect();},{once:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
 else boot();
})();
"""

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def safe(p:Path,root:Path):
    return not p.is_symlink() and p.resolve().is_relative_to(root.resolve())

def read(p:Path,root:Path)->bytes:
    if not safe(p,root) or not p.is_file():
        raise RuntimeError("ENTRY_MISSING_OR_UNSAFE_"+str(p))
    return p.read_bytes()

def remove_style(s:str, id_:str)->str:
    # P45 style was already removed by an older entry rebuild in real P64.
    # Remove when present, but never require an historical layer to still exist.
    expression=r'<style\s+id=["\']'+re.escape(id_)+r'["\']\s*>.*?</style>\s*'
    occurrences=len(re.findall(expression,s,flags=re.I|re.S))
    if occurrences>1:
        raise RuntimeError("ENTRY_DUPLICATE_STYLE_"+id_)
    if occurrences==0:
        if re.search(r'<style[^>]*id=["\']'+re.escape(id_),s,flags=re.I):
            raise RuntimeError("ENTRY_MALFORMED_STYLE_"+id_)
        return s
    return re.sub(expression,'',s,count=1,flags=re.I|re.S)

def remove_exact(s:str,needle:str,label:str)->str:
    # Historical P45/P47 links may be absent in P64's verified HTML.
    occurrences=s.count(needle)
    if occurrences>1:
        raise RuntimeError("ENTRY_DUPLICATE_LINK_"+label)
    return s.replace(needle,"",1) if occurrences==1 else s

def transform(s:str)->str:
    if MARK in s:raise RuntimeError("ENTRY_ALREADY_APPLIED")
    if "HIGHFLY_P46_OFFICIAL_IDENTITY" not in s:
        raise RuntimeError("ENTRY_EXPECTED_P46_PRESENTATION")
    if "HIGHFLY_P48_FURY_MOBILE" not in s:
        raise RuntimeError("ENTRY_EXPECTED_P48_STAGE")
    # Remove only presentation rules, NOT P41 saves, character creation,
    # original login callbacks, game assets or any original gameplay code.
    s=remove_style(s,"highfly-p42-hunter-styles")
    s=remove_style(s,"highfly-p45-brand-css")
    for href,label in (
        ('<script defer src="/highfly_p42_hunter.js"></script>',"P42_SINGLE_CLASS_JS"),
        ('<script defer src="/highfly_p45_branding.js"></script>',"P45_SINGLE_CLASS_JS"),
        ('<link rel="stylesheet" href="/highfly/p47.css" />',"P47_CONFLICTING_CSS"),
        ('<script defer src="/highfly/p47.js"></script>',"P47_CREATOR_REWRITE_JS"),
    ):
        s=remove_exact(s,href,label)
    if s.count("</head>")!=1:raise RuntimeError("ENTRY_HTML_HEAD_DRIFT")
    s=s.replace("</head>",
      '<!-- '+MARK+': consolidated presentation; native loading unchanged -->\n'
      '<link rel="stylesheet" href="/highfly/p64_entry_clean.css" />\n'
      '<script defer src="/highfly/p64_entry_progress.js"></script>\n'
      '</head>',1)
    return s

def plan(*,repo:Path=ROOT,stage:Path=STAGE,out:Path=OUT,p64:Path=P64_STATUS)->dict:
    work=repo/".workspace"
    for label,p in (("STAGE",stage),("OUT",out),("P64",p64)):
        if not safe(p,work):raise RuntimeError("ENTRY_UNSAFE_"+label)
    if not stage.is_dir():raise RuntimeError("ENTRY_STAGE_MISSING")
    status=json.loads(read(p64,work))
    if status.get("mode")!="BUILD_GREEN_BROWSER_PENDING":
        raise RuntimeError("ENTRY_P64_NOT_BUILD_GREEN")
    if out.exists():
        previous=out/STATUS_FILE
        if previous.is_file():
            saved=json.loads(read(previous,out))
            if saved.get("mode")!="BUILD_GREEN_BROWSER_PENDING":
                raise RuntimeError("ENTRY_PREVIOUS_STATUS_NOT_GREEN")
            if sha(read(stage/HTML,stage))!=saved.get("htmlSha256"):
                raise RuntimeError("ENTRY_PREVIOUS_HTML_DRIFT")
            for rel in (CSS_FILE,JS_FILE):
                if sha(read(stage/rel,stage))!=saved.get("assets",{}).get(rel):
                    raise RuntimeError("ENTRY_PREVIOUS_PRESENTATION_DRIFT")
            return {"already":True,"status":saved}
        raise RuntimeError("ENTRY_REPORT_EXISTS_WITHOUT_STATUS_REVIEW")
    original=read(stage/HTML,stage)
    if sha(original)!=status.get("sourceSha256",{}).get(HTML):
        raise RuntimeError("ENTRY_P64_HTML_CHANGED_SINCE_CLEAN_BUILD")
    for rel in (CSS_FILE,JS_FILE):
        p=stage/rel
        if p.exists() or p.is_symlink():raise RuntimeError("ENTRY_ASSET_ALREADY_EXISTS_"+rel)
        if not safe(p,stage):raise RuntimeError("ENTRY_UNSAFE_ASSET_"+rel)
    image=stage/"public/highfly/official/highfly_splash.png"
    if not image.is_file() or not safe(image,stage) or image.stat().st_size<10000:
        raise RuntimeError("ENTRY_ORIGINAL_SPLASH_MISSING")
    updated=transform(original.decode("utf8")).encode("utf8")
    return {"already":False,"original":original,"updated":updated,"imageBytes":image.stat().st_size}

def run(apply=False, *,repo=ROOT,stage=STAGE,out=OUT,p64=P64_STATUS,build=None,check_p9=True):
    if check_p9:p9.preflight(p9.ORIGINAL,stage,p9.REPORT)
    state=plan(repo=repo,stage=stage,out=out,p64=p64)
    if state["already"]:return state["status"]
    result={
      "phase":"WORLD7_P64_ENTRY_CONSOLIDATION",
      "mode":"DRY_RUN",
      "P64Retained":True,
      "nativeClassDataChanged":False,
      "offlineSaveChanged":False,
      "originalWorldChanged":False,
      "gameplayInputChanged":False,
      "oldHunterOnlyPresentationDisabled":True,
      "oldP47LootFallbackNotLoaded":True,
      "stagedP48MovementPreserved":True,
      "progressReadout":"NATIVE_LS_FILL_STYLE_WIDTH_ONLY",
      "gameplayBrowserVerified":False,
    }
    if not apply:return result
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/BACKUP
    snapshot.parent.mkdir(parents=True,exist_ok=False)
    with snapshot.open("xb") as f:f.write(state["original"])
    if sha(snapshot.read_bytes())!=sha(state["original"]):
        raise RuntimeError("ENTRY_BACKUP_INTEGRITY")
    affected=[HTML,CSS_FILE,JS_FILE]
    try:
        if read(stage/HTML,stage)!=state["original"]:
            raise RuntimeError("ENTRY_CONCURRENT_MAIN_CHANGE")
        (stage/HTML).write_bytes(state["updated"])
        for rel,content in ((CSS_FILE,CSS),(JS_FILE,JS)):
            f=stage/rel;f.parent.mkdir(parents=True,exist_ok=True)
            with f.open("xb") as target:target.write(content.encode("utf8"))
        smoke=(build if build is not None else p9.smoke)()
        if smoke.get("exitCode")!=0:
            raise RuntimeError("ENTRY_VITE_BUILD_RED")
        result["mode"]="BUILD_GREEN_BROWSER_PENDING"
        result["htmlSha256"]=sha(read(stage/HTML,stage))
        result["assets"]={rel:sha(read(stage/rel,stage)) for rel in (CSS_FILE,JS_FILE)}
        (out/STATUS_FILE).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
        return result
    except BaseException:
        (stage/HTML).write_bytes(state["original"])
        for rel in (CSS_FILE,JS_FILE):
            f=stage/rel
            if f.exists() and not f.is_symlink() and safe(f,stage):f.unlink()
        print("[HIGHFLY P64 ENTRY] RED: restored original P64 HTML. No game files touched.",
              file=sys.stderr)
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    print("[HIGHFLY P64 ENTRY] "+json.dumps(run(args.apply),indent=2,ensure_ascii=False))
