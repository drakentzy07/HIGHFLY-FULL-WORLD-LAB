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
    chunks=[]
    for marker in ('id="charcreate-panel"','id="offline-select"'):
        start=src.index(marker)
        end=src.find("</div>",start)
        # offline/online panels contain nested divs; inspect up to closing of
        # native class picker by finding all 9 class buttons in a 9 KB window.
        near=src[start:start+18000]
        classes=set(re.findall(r'<button[^>]*class="mini-class(?: [^"]*)?"[^>]*data-class="([^"]+)"',near))
        if not expected.issubset(classes):
            raise RuntimeError("P43_NATIVE_NINE_CLASS_CONTROLS_MISSING "+
                               marker+" "+",".join(sorted(expected-classes)))
        chunks.append(sorted(classes))
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
    result=result.replace("</head>",f"<!-- {MARK}: original editor and its 9 class controls restored -->\n</head>",1)
    return result

def patch_main(src:str)->str:
    if MARK in src:
        raise RuntimeError("P43_ALREADY_APPLIED_TO_MAIN")
    if "HIGHFLY_P41_OFFLINE_SAVE" not in src or "readHighflySave" not in src:
        raise RuntimeError("P43_P41_OFFLINE_PERSISTENCE_NOT_FOUND")
    if "isOfflineModeAvailable(import.meta.env.DEV)" not in src:
        raise RuntimeError("P43_NATIVE_OFFLINE_GATE_MISSING")
    if "requestMobileFullscreenLandscape();" not in src:
        raise RuntimeError("P43_NATIVE_MOBILE_FULLSCREEN_MISSING")
    anchor="    applyServerMode('online');"
    if src.count(anchor)!=1:
        raise RuntimeError("P43_NATIVE_REALM_DEFAULT_ANCHOR_DRIFT "+str(src.count(anchor)))
    # No bypass of isOfflineModeAvailable. Dev server route only; the existing
    # game still owns the dropdown, play button and offline character creation.
    return src.replace(anchor,
        "    // "+MARK+": choose existing dev-only offline destination first.\\n"
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
    new_html=patch_html(orig_html)
    new_main=patch_main(orig_main)
    return {
        "files":{"index.html":(orig_html,new_html),
                 "src/main.ts":(orig_main,new_main)},
        "classes":list(CLASSES),
        "mode":"DRY_RUN","activeP64Modified":False,
        "nativeFullScreenHookPresent":True,
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
        summary={k:v for k,v in info.items() if k!="files"}
        summary.update({"mode":"APPLY","htmlSha256":sha((lab/"index.html").read_bytes()),
                        "mainSha256":sha((lab/"src/main.ts").read_bytes()),
                        "originalEditorRestoredInMarkup":True,
                        "originalOfflinePlayPreferred":True,
                        "browserVerified":False,
                        "note":"Vite dev: offline is native. Screen fullscreen requests need user gesture. P41 saves one name-slot globally."})
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n","utf8")
        return summary
    except Exception:
        for name,(a,b) in original_values.items():
            (lab/name).write_text(a,"utf8")
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
        result["willEditActiveP64"]=False
    print("[HIGHFLY P43 NATIVE EDITOR] "+json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
