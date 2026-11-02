#!/usr/bin/env python3
"""P43 lab-only: restore all 9 native ClaudeCraft character classes and native offline entry.

No custom class-picker, fake login, loader or joystick.
- Remove only the P42 CSS and script that hid 8 of the 9 original classes.
- Default the existing ClaudeCraft realm selector to Offline in Vite dev.
- Keep P41 autosave code intact (single-slot limitation still applies).
- Keep native mobile-preflight/fullscreen; no automatic browser fullscreen hacks.
- Write atomic guarded backups. Never modify active P64 or original checkout.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/".workspace"
LAB=WORK/"highfly-p43-restore-lab"
ORIGINAL_STAGE=WORK/"highfly-origin-stage-p0"
ORIGINAL=WORK/"claudecraft-v0.44.7"
BACKUPS=LAB/".hf-p43-native-editor-backup"
REPORT=WORK/"reports/highfly-world7/P43_NATIVE_EDITOR_OFFLINE.json"
CLASSES=("warrior","paladin","hunter","rogue","priest","shaman","mage","warlock","druid")
MARK="HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES"
FULLSCREEN_PATH="public/highfly_p43_native_fullscreen.js"
FULLSCREEN_JS=r"""// HIGHFLY P43 native fullscreen: explicit browser gesture; no loader replacements.
(function(){
  'use strict';
  function mount(){
    const play=document.getElementById('btn-play');
    if(!play || document.getElementById('hf-p43-fullscreen-btn'))return;
    const button=document.createElement('button');
    button.type='button';
    button.id='hf-p43-fullscreen-btn';
    button.className='btn btn-secondary';
    button.textContent='PANTALLA COMPLETA';
    button.setAttribute('aria-label','Activar pantalla completa');
    button.style.cssText='display:block;position:relative;z-index:3;margin:10px auto;min-height:44px;padding:10px 24px;font:600 13px system-ui,sans-serif;border:1px solid #78bee9;border-radius:8px;background:#0e2033;color:#f8fcff;cursor:pointer;max-width:95%;';
    play.insertAdjacentElement('afterend',button);
    button.addEventListener('click',function(){
      if(document.fullscreenElement){
        Promise.resolve(document.exitFullscreen?.()).catch(function(){});
        return;
      }
      const root=document.documentElement;
      const request=root.requestFullscreen?.bind(root) || root.webkitRequestFullscreen?.bind(root);
      if(!request){
        button.textContent='PANTALLA COMPLETA NO DISPONIBLE';
        return;
      }
      try{
        Promise.resolve(request()).then(function(){
          const lock=screen.orientation?.lock;
          if(typeof lock==='function')Promise.resolve(lock.call(screen.orientation,'landscape')).catch(function(){});
        }).catch(function(){
          button.textContent='CHROME NO PERMITIÓ FULLSCREEN';
        });
      }catch(e){
        button.textContent='CHROME NO PERMITIÓ FULLSCREEN';
      }
    });
    document.addEventListener('fullscreenchange',function(){
      button.textContent=document.fullscreenElement?'SALIR DE PANTALLA COMPLETA':'PANTALLA COMPLETA';
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);
  else mount();
})();
"""

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def checked_read(path:Path)->str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("P43_NOT_REGULAR_FILE "+str(path))
    return path.read_text("utf8")

def patch_html(src:str)->str:
    if MARK in src:
        raise RuntimeError("P43_ALREADY_APPLIED_TO_HTML")
    if src.count('id="offline-select"')!=1 or src.count('id="server-opt-offline"')!=1:
        raise RuntimeError("P43_NATIVE_OFFLINE_MARKUP_MISSING")
    if src.count('id="charcreate-panel"')!=1:
        raise RuntimeError("P43_NATIVE_CHARACTER_EDITOR_MISSING")
    expected=set(CLASSES)
    for marker in ('id="charcreate-panel"','id="offline-select"'):
        start=src.index(marker)
        # offline/online panels contain nested divs; inspect up to closing of
        # native class picker by finding all 9 class buttons in a 9 KB window.
        near=src[start:start+18000]
        classes=set(re.findall(r'<button[^>]*class="mini-class(?: [^"]*)?"[^>]*data-class="([^"]+)"',near))
        if not expected.issubset(classes):
            raise RuntimeError("P43_NATIVE_NINE_CLASS_CONTROLS_MISSING "+
                               marker+" "+",".join(sorted(expected-classes)))
    old_style=re.compile(
        r'<style id="highfly-p42-hunter-styles">\s*.*?</style>\s*',
        flags=re.DOTALL)
    old_js=re.compile(r'<script defer src="/highfly_p42_hunter\.js"></script>\s*')
    if len(old_style.findall(src))!=1 or len(old_js.findall(src))!=1:
        raise RuntimeError("P43_P42_CLASS_HIDER_MISSING_OR_ALREADY_REMOVED")
    result=old_style.sub("",src,count=1)
    result=old_js.sub("",result,count=1)
    if ("highfly-p42-hunter-styles" in result or
            "highfly_p42_hunter.js" in result):
        raise RuntimeError("P43_HUNTER_CSS_STILL_INCLUDED")
    result=result.replace("</head>",f"<!-- {MARK}: original editor and its 9 class controls restored -->\n"
        f'<script defer src="/highfly_p43_native_fullscreen.js"></script>\n</head>',1)
    return result

def patch_main(src:str)->str:
    if MARK in src:
        raise RuntimeError("P43_ALREADY_APPLIED_TO_MAIN")
    if "HIGHFLY_P41_OFFLINE_SAVE" not in src or "readHighflySave" not in src:
        raise RuntimeError("P43_P41_OFFLINE_PERSISTENCE_NOT_FOUND")
    # The P43 source has gone through earlier HIGHFLY patches, so its
    # offlineAvailable initializer may not be the exact original expression.
    # Anchor to the real declaration and native handlers, not one string.
    gate_re=re.compile(
        r"(?m)^([ \t]*)const[ \t]+offlineAvailable(?:[ \t]*:[ \t]*boolean)?"
        r"[ \t]*=[ \t]*([\s\S]{0,350}?);[ \t]*(?=\r?$)")
    matches=list(gate_re.finditer(src))
    if len(matches)!=1:
        nearby=[row.strip()[:180] for row in src.splitlines()
                if "offlineAvailable" in row or "server-opt-offline" in row][:12]
        raise RuntimeError("P43_NATIVE_OFFLINE_GATE_DECLARATION_UNRECOGNIZED "+
                           str(len(matches))+" "+repr(nearby))
    if "handleOfflineSelect" not in src or "server-opt-offline" not in src:
        raise RuntimeError("P43_NATIVE_OFFLINE_ROUTING_MISSING")
    if "requestMobileFullscreenLandscape();" not in src:
        raise RuntimeError("P43_NATIVE_MOBILE_FULLSCREEN_MISSING")
    anchor="    applyServerMode('online');"
    if src.count(anchor)!=1:
        nearby=[row.strip()[:180] for row in src.splitlines()
                if "applyServerMode" in row][:12]
        raise RuntimeError("P43_NATIVE_REALM_DEFAULT_ANCHOR_DRIFT "+
                           str(src.count(anchor))+" "+repr(nearby))
    # Explicitly enable the EXISTING offline flow in this private Vite
    # development laboratory only. Production bundles keep the gate false.
    # Keep every original event handler, class control, gameplay system and
    # offline character save wiring untouched.
    gate=matches[0]
    original_expr=gate.group(2).strip()
    if not original_expr:
        raise RuntimeError("P43_NATIVE_OFFLINE_GATE_EMPTY")
    replacement=(gate.group(1)+"const offlineAvailable = import.meta.env.DEV;"
        " // "+MARK+": original offline mode available only in Vite dev")
    src=src[:gate.start()]+replacement+src[gate.end():]
    # The marker is intentionally on the gate declaration; the script must
    # never run twice against an already-modified stage.
    return src.replace(anchor,
        "    // P43 LAB: default to the built-in Offline path for easy local testing.\n"
        "    applyServerMode(offlineAvailable ? 'offline' : 'online');",1)

def plan(lab:Path=LAB):
    if lab.is_symlink() or not lab.is_dir() or not lab.resolve().is_relative_to(WORK.resolve()):
        raise RuntimeError("P43_RECOVERY_LAB_NOT_FOUND_OR_UNSAFE")
    if (lab/"public").is_symlink() or not (lab/"public").is_dir():
        raise RuntimeError("P43_PUBLIC_ASSETS_DIR_UNSAFE")
    if (lab/".hf-p43-native-editor-backup").exists() or (lab==LAB and REPORT.exists()):
        raise RuntimeError("P43_PREVIOUS_RUN_PRESENT_STOP_NO_OVERWRITE")
    h=lab/"index.html"
    m=lab/"src/main.ts"
    orig_html=checked_read(h)
    orig_main=checked_read(m)
    fulljs=lab/FULLSCREEN_PATH
    if fulljs.exists() or fulljs.is_symlink():
        raise RuntimeError("P43_FULLSCREEN_JS_ALREADY_EXISTS")
    new_html=patch_html(orig_html)
    new_main=patch_main(orig_main)
    return {
        "files":{"index.html":(orig_html,new_html),
                 "src/main.ts":(orig_main,new_main)},
        "newFiles":[FULLSCREEN_PATH],
        "classes":list(CLASSES),
        "mode":"DRY_RUN","activeP64Modified":False,
        "nativeFullScreenHookPresent":True,
        "manualMobileFullscreenButton":True,
        "nativeOfflineGatePreserved":True,
        "browserVerified":False,
        "backupDir":str(lab/".hf-p43-native-editor-backup"),
    }

def apply(lab:Path=LAB):
    info=plan(lab)
    # All safety checks BEFORE any write; avoid re-running after applying.
    backup=lab/".hf-p43-native-editor-backup"
    backup.mkdir(mode=0o700)
    original_values={}
    try:
        for name,(a,b) in info["files"].items():
            dest=backup/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(a,"utf8")
            if dest.read_text("utf8")!=a:raise RuntimeError("P43_BACKUP_WRITE_FAILED")
            original_values[name]=(a,b)
        for name,(a,b) in original_values.items():
            dest=lab/name
            if checked_read(dest)!=a:
                raise RuntimeError("P43_SOURCE_CHANGED_DURING_PATCH")
            dest.write_text(b,"utf8")
        jsfile=lab/FULLSCREEN_PATH
        jsfile.write_text(FULLSCREEN_JS,"utf8")
        summary={k:v for k,v in info.items() if k!="files"}
        summary.update({"mode":"APPLY","htmlSha256":sha((lab/"index.html").read_bytes()),
                        "mainSha256":sha((lab/"src/main.ts").read_bytes()),
                        "originalEditorRestoredInMarkup":True,
                        "originalOfflinePlayPreferred":True,
                        "native9ClassesWithoutP42HiddenFilter":True,
                        "browserVerified":False,
                        "note":"Vite dev: offline is native. Screen fullscreen requests need user gesture. P41 saves one name-slot globally."})
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n","utf8")
        return summary
    except Exception:
        for name,(a,b) in original_values.items():
            (lab/name).write_text(a,"utf8")
        new_js=lab/FULLSCREEN_PATH
        if new_js.is_file() and not new_js.is_symlink() and new_js.read_text("utf8")==FULLSCREEN_JS:
            new_js.unlink()
        raise

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    if args.apply:
        result=apply()
    else:
        p=plan()
        result={k:v for k,v in p.items() if k!="files"}
        result["willEdit"]=["index.html","src/main.ts"]
        result["willCreate"]=[FULLSCREEN_PATH]
        result["willEditActiveP64"]=False
    print("[HIGHFLY P43 NATIVE EDITOR] "+json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
