#!/usr/bin/env python3
"""P64 Entry V2: one stylesheet and one progress reader, no new presentation layers.

Replaces ONLY the P64 Entry existing CSS/JS in the private stage after SHA checks.
Preserves native login and its nine classes, P41 saves, World, P48 controls, P63
combat, P64 assets. No HTML, TypeScript, GLB, gameplay or localStorage mutation.
An immutable backup is made before any modification. P9 build and rollback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_world7_p64_entry_cleanup as p64entry

WORK=ROOT/".workspace"
STAGE=p9.STAGE
ENTRY_STATUS=WORK/"reports/highfly-world7/p64-entry-clean/P64_ENTRY_STATUS.json"
OUT=WORK/"reports/highfly-world7/p64-entry-v2"
STATUS_NAME="P64_ENTRY_V2_STATUS.json"
CSS_REL=p64entry.CSS_FILE
JS_REL=p64entry.JS_FILE
HTML_REL=p64entry.HTML

OLD_BG="""/* Keep the same HIGHFLY splash across the start screen and real loading.
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
"""

NEW_BG="""/* P64 V2 — ROOT CAUSE: official splash PNG includes photographed/fixed UI.
   Never draw those fake buttons/bars behind the native loading curtain.
   Keep portal art on start, and mask its bottom embedded UI with an opaque
   gradient. Real start buttons/character editor remain DOM controls. */
#start-screen.hf-p46-entry{
  background-color:#090719!important;
  background-image:
    linear-gradient(to top, #090719 0%,#090719 30%,
      rgba(9,7,25,.99) 36%,rgba(9,7,25,.85) 45%,
      rgba(9,7,25,0) 64%),
    url('/highfly/official/highfly_splash.png')!important;
  background-position:center center!important;background-size:cover!important;
}
/* The real loader ALWAYS has one clean background. Not a screenshot of a UI. */
body #loading-screen.visible {
  position:fixed!important;inset:0!important;
  width:100vw!important;height:100dvh!important;
  z-index:2147483200!important;
  box-sizing:border-box!important;overflow:hidden!important;
  margin:0!important;padding:0!important;
  display:flex!important;flex-direction:column!important;
  justify-content:center!important;align-items:center!important;
  background-color:#080c20!important;
  background-image:
    radial-gradient(ellipse 55% 75% at 50% 35%,rgba(117,53,204,.39),transparent 70%),
    linear-gradient(130deg,#081021,#120d2c 55%,#071020)!important;
  background-position:center!important;background-size:cover!important;
}
/* Native Word of ClaudeCraft loader has its own logo element; avoid duplication. */
body #loading-screen .ls-logo{display:none!important}
body #loading-screen.visible::before{
  content:"HIGHFLY"!important;position:absolute!important;
  display:block!important;inset:16% 0 auto!important;
  width:100%!important;height:auto!important;z-index:1!important;
  border:0!important;box-shadow:none!important;pointer-events:none!important;
  color:#f6ebff!important;letter-spacing:.19em!important;text-align:center!important;
  font:900 clamp(28px,5.5vw,54px)/1.2 system-ui,sans-serif!important;
  text-shadow:0 0 17px rgba(181,101,244,.85)!important;
  background:none!important;
}
body #loading-screen::after{
  content:none!important;display:none!important;background-image:none!important;
}
body:has(#loading-screen.visible) #start-screen,
body:has(#loading-screen.visible) #highfly-p46-landing{
  visibility:hidden!important;pointer-events:none!important;
}
"""
OLD_JS="""     const label='Progreso del motor: '+pct+' · '+elapsed+' s'+
       (stalled?' · Sin avance visible desde hace '+Math.round((now-lastChange)/1000)+' s':'');"""
NEW_JS="""     const label='Progreso del motor: '+pct+' · '+elapsed+' s'+
       (stalled?' · Sin avance visible desde hace '+Math.round((now-lastChange)/1000)+' s':'')+
       (runtimeFailure?' · Error detectado: '+runtimeFailure:'');"""
BEFORE_JS="""   let activeAt=0,lastChange=0,lastWidth='';
   let lastLabel='';"""
AFTER_JS="""   let activeAt=0,lastChange=0,lastWidth='';
   let lastLabel='';
   let runtimeFailure='';
   // Observes runtime errors while the curtain is active. A build-green result
   // says nothing about WebGL, resource loading or actual browser startup.
   window.addEventListener('error',function(e){
     if(loader.classList.contains('visible')&&e.message){
       runtimeFailure=String(e.message).slice(0,90);
       update();
     }
   });
   window.addEventListener('unhandledrejection',function(e){
     if(loader.classList.contains('visible')){
       runtimeFailure=String(e.reason&&e.reason.message||e.reason||'Promise rechazada').slice(0,90);
       update();
     }
   });"""

def replace_exact(s,old,new,label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError("ENTRY_V2_TEMPLATE_DRIFT_"+label+"_"+str(count))
    return s.replace(old,new,1)

NEW_CSS=replace_exact(p64entry.CSS,OLD_BG,NEW_BG,"CSS_BACKGROUND")
NEW_JS=replace_exact(
    replace_exact(p64entry.JS,BEFORE_JS,AFTER_JS,"JS_ERROR_LISTENER"),
    OLD_JS,NEW_JS,"JS_PROGRESS_TEXT"
)
# Hard source assertions are limited to the authored template in the public repo.
# Actual stage content is verified by SHA256 from P64_ENTRY_STATUS.json.

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()
def safe(path:Path,root:Path):
    return not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
def read(path:Path,root:Path)->bytes:
    if not safe(path,root) or not path.is_file():
        raise RuntimeError("ENTRY_V2_FILE_MISSING_OR_UNSAFE_"+str(path))
    return path.read_bytes()

def preflight(*,stage:Path=STAGE,work:Path=WORK,out:Path=OUT,
              entry_status:Path=ENTRY_STATUS):
    for path in (stage,out,entry_status):
        if not safe(path,work):
            raise RuntimeError("ENTRY_V2_UNSAFE_PATH_"+str(path))
    if not stage.is_dir():
        raise RuntimeError("ENTRY_V2_NO_PRIVATE_STAGE")
    if out.exists():
        status_file=out/STATUS_NAME
        if not status_file.is_file():
            raise RuntimeError("ENTRY_V2_EXISTING_BACKUP_REVIEW_REQUIRED")
        result=json.loads(read(status_file,out))
        if result.get("mode")!="BUILD_GREEN_BROWSER_PENDING":
            raise RuntimeError("ENTRY_V2_BAD_EXISTING_STATUS")
        for name,expected in result.get("sourceSha256",{}).items():
            if sha(read(stage/name,stage))!=expected:
                raise RuntimeError("ENTRY_V2_EXISTING_STAGE_DRIFT_"+name)
        if len(result.get("sourceSha256",{}))!=2:
            raise RuntimeError("ENTRY_V2_INCOMPLETE_STATUS")
        return {"already":True,"result":result}
    status=json.loads(read(entry_status,work))
    if status.get("mode")!="BUILD_GREEN_BROWSER_PENDING":
        raise RuntimeError("ENTRY_V2_PREVIOUS_ENTRY_NOT_GREEN")
    old_files={}
    for rel in (CSS_REL,JS_REL):
        data=read(stage/rel,stage)
        if sha(data)!=status.get("assets",{}).get(rel):
            raise RuntimeError("ENTRY_V2_STAGE_DRIFT_"+rel)
        old_files[rel]=data
    if old_files[CSS_REL]!=p64entry.CSS.encode() or old_files[JS_REL]!=p64entry.JS.encode():
        raise RuntimeError("ENTRY_V2_CSS_JS_DIFFER_FROM_VERIFIED_SOURCE")
    if sha(read(stage/HTML_REL,stage))!=status.get("htmlSha256"):
        raise RuntimeError("ENTRY_V2_HTML_HAS_CHANGED_DO_NOT_TOUCH")
    if "highfly_splash.png" not in NEW_CSS or "highfly_splash.png" in NEW_BG.split("body #loading-screen.visible")[1]:
        raise RuntimeError("ENTRY_V2_LOADER_BACKGROUND_REINTRODUCES_EMBEDDED_UI")
    return {"already":False,"original":old_files}

def run(apply=False, *,stage=STAGE,work=WORK,out=OUT,
        entry_status=ENTRY_STATUS,build=None,check_p9=True):
    if check_p9:p9.preflight(p9.ORIGINAL,stage,p9.REPORT)
    state=preflight(stage=stage,work=work,out=out,entry_status=entry_status)
    if state["already"]:return state["result"]
    result={
        "phase":"HIGHFLY_WORLD7_P64_ENTRY_V2_NO_DUPLICATE_UI",
        "mode":"DRY_RUN",
        "filesChanged":[CSS_REL,JS_REL],
        "indexHtmlChanged":False,
        "classesSaveRpgChanged":False,
        "imageFilesModified":False,
        "loadingImageWithBakedButtonsUsed":False,
        "originalNativeProgressReused":True,
        "browserGameplayVerified":False,
    }
    if not apply:return result
    out.mkdir(parents=True,exist_ok=False)
    backups=out/"backups"
    backups.mkdir(parents=True,exist_ok=False)
    for rel,data in state["original"].items():
        dst=backups/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("xb") as f:f.write(data)
        if dst.read_bytes()!=data:
            raise RuntimeError("ENTRY_V2_BACKUP_NOT_VERIFIED_"+rel)
    try:
        for rel,data in ((CSS_REL,NEW_CSS.encode()),(JS_REL,NEW_JS.encode())):
            target=stage/rel
            if read(target,stage)!=state["original"][rel]:
                raise RuntimeError("ENTRY_V2_CONCURRENT_MODIFICATION_"+rel)
            target.write_bytes(data)
        report=(build or p9.smoke)()
        if report.get("exitCode")!=0:
            raise RuntimeError("ENTRY_V2_PRIVATE_BUILD_FAILED")
        result["mode"]="BUILD_GREEN_BROWSER_PENDING"
        result["sourceSha256"]={
            rel:sha(read(stage/rel,stage)) for rel in (CSS_REL,JS_REL)
        }
        (out/STATUS_NAME).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
        return result
    except BaseException:
        for rel,data in state["original"].items():
            (stage/rel).write_bytes(data)
        print("[HIGHFLY P64 ENTRY V2] RED: previous CSS/JS restored, original stage intact",
              file=sys.stderr)
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    print("[HIGHFLY P64 ENTRY V2] "+json.dumps(run(args.apply),indent=2,ensure_ascii=False))
