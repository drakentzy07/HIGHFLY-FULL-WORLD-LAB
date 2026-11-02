#!/usr/bin/env python3
"""HIGHFLY P74: isolated advanced P72/P73 + exact-spec verified CC0 assets + 9 native classes.

No source/asset changes in any existing stage. No geometric placeholders.
No "with-project-only", CraftPix, or other unverified media. Old upstream KayKit
is excluded: use owned licensed KayKit pack separately, after its own audit.
Default dry-run; --apply commits a complete NEW lab atomically.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p21_runtime_asset_recovery as p21
import highfly_p25_source_first_asset_audit as p25
import highfly_p69_creator_native_layout as creator

WORK=ROOT/".workspace"
SOURCE=WORK/"highfly-p71b-no-drakenlab-lab"
STAGE=WORK/"highfly-origin-stage-p0"
ORIGINAL=WORK/"claudecraft-v0.44.7"
LAB=WORK/"highfly-p74-advanced-licensed-lab"
TEMP=WORK/".hf-p74-assemble-private"
REPORT=WORK/"reports/highfly-world7/P74_INTEGRAL_CC0_NINE_CLASSES.json"
P70=WORK/"reports/highfly-world7/P70_FULL_FORENSIC_AUDIT.json"
CLASSES=("warrior","paladin","hunter","rogue","priest","shaman","mage","warlock","druid")
ROOTS=("models","textures","vfx")
PROVIDERS={"Quaternius","Kenney","ambientCG","Poly Haven","loafbrr"}
MAX_TOTAL_BYTES=1_500_000_000
MAX_FILES=3500
MARK="HIGHFLY_P74_ADVANCED_CC0_NINE_CLASS_NATIVE"
STYLE_LINK='<link rel="stylesheet" href="/highfly/p74_nine_class_native.css" />'
DIAG_LINK='<script defer src="/highfly/p74_class_readout.js"></script>'
INSERT=f"<!-- {MARK}: ORIGINAL nine-class editor, owned/CC0 assets only -->\n{STYLE_LINK}\n{DIAG_LINK}\n"

EXTRA_CSS=r"""
/* P74: only the authentic native OFFLINE class controls. No fake selector.
   P46/P47 hunter styling had hidden the original .mini-class-row. */
body #offline-select:not([hidden]){
 visibility:visible!important;
}
body #offline-select .charselect-layout,
body #offline-select .char-create,
body #offline-select .charselect-col-left{
 visibility:visible!important;min-width:0!important;
}
body #offline-select .mini-class-row,
body #offline-select .char-create > .mini-class-row{
 display:grid!important;visibility:visible!important;opacity:1!important;
 grid-template-columns:repeat(3,minmax(0,1fr))!important;
 position:relative!important;inset:auto!important;
 width:100%!important;max-width:100%!important;height:auto!important;
 max-height:none!important;min-height:0!important;
 transform:none!important;overflow:visible!important;
 margin:8px 0!important;padding:0!important;gap:7px!important;
}
body #offline-select .mini-class-row .mini-class[data-class]{
 display:flex!important;visibility:visible!important;opacity:1!important;
 position:relative!important;inset:auto!important;transform:none!important;
 box-sizing:border-box!important;
 width:100%!important;min-width:0!important;max-width:100%!important;
 height:auto!important;min-height:39px!important;
 margin:0!important;padding:6px!important;
 font:700 12px/1.2 system-ui,sans-serif!important;
 align-items:center!important;justify-content:center!important;
 pointer-events:auto!important;cursor:pointer!important;
}
body #offline-select #offline-preview-container{
 display:block!important;position:relative!important;
 min-height:180px!important;overflow:hidden!important;
}
@media(max-height:490px) and (orientation:landscape){
 body #offline-select .mini-class-row .mini-class[data-class]{
  min-height:29px!important;font-size:10px!important;padding:3px!important;
 }
}
"""

JS_TEXT=r"""/* HIGHFLY P74 native class audit — read only. No fake models or buttons. */
(function(){
'use strict';
const required=['warrior','paladin','hunter','rogue','priest',
'shaman','mage','warlock','druid'];
const diag=new URLSearchParams(location.search).has('hf_p74_diag');
const state={classesPresent:[],classesVisible:[],previewCanvases:0,previewChildren:0,
creatorVisible:false,lastChecked:0};
window.__HIGHFLY_P74_CLASS_AUDIT__=state;
function check(){
const root=document.getElementById('offline-select');
const buttons=root?[...root.querySelectorAll('.mini-class[data-class]')]:[];
const visible=el=>{
const s=getComputedStyle(el),r=el.getBoundingClientRect();
return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
};
state.classesPresent=required.filter(id=>buttons.some(x=>x.dataset.class===id));
state.classesVisible=required.filter(id=>buttons.some(x=>x.dataset.class===id&&visible(x)));
const preview=document.getElementById('offline-preview-container');
state.previewChildren=preview?.children.length||0;
state.previewCanvases=preview?.querySelectorAll('canvas').length||0;
state.creatorVisible=!!root&&visible(root);
state.lastChecked=performance.now();
const el=document.getElementById('hf-p74-class-readout');
if(el){
el.style.display=state.creatorVisible?'block':'none';
el.textContent='P74 · clases nativas visibles '+state.classesVisible.length+'/9'+
' · preview 3D '+state.previewCanvases+' canvas';
}
}
function mount(){
if(!document.body)return;
if(diag){
const el=document.createElement('div');
el.id='hf-p74-class-readout';
el.style.cssText='position:fixed;z-index:2147483600;bottom:8px;right:8px;'+
'font:700 12px system-ui;color:#fff;background:#07172fe8;'+
'border:1px solid #55cbea;padding:7px 10px;border-radius:7px;pointer-events:none';
document.body.appendChild(el);
}
check();setInterval(check,1300);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
else mount();
})();
"""

def hashed(file:Path)->str:
 h=hashlib.sha256()
 with file.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def ensure(path:Path,root:Path,kind="file"):
 if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
  raise RuntimeError("P74_UNSAFE_PATH_"+str(path))
 if kind=="file" and not path.is_file():raise RuntimeError("P74_REQUIRED_FILE_MISSING_"+str(path))
 if kind=="dir" and not path.is_dir():raise RuntimeError("P74_REQUIRED_DIR_MISSING_"+str(path))

def make_proof_index():
 # The converter's exact src->out record plus the upstream CREDITS CC0 1.0
 # line must agree; filename resemblance never authorizes reuse.
 index=p25.outspec_index(ORIGINAL)
 credits=p25.credited(ORIGINAL)
 approved=[]
 blocked=Counter()
 source_evidence=[]
 for url,records in sorted(index.items()):
  parts=PurePosixPath(url.lstrip("/"))
  if (not p21.safe_asset_path(url) or parts.parts[0] not in ROOTS
      or parts.suffix.lower() not in {".glb",".png",".jpg",".jpeg",".webp"}):
   continue
  if (STAGE/"public"/str(parts)).is_file():continue
  src=ORIGINAL/"public"/str(parts)
  if not src.is_file() or src.is_symlink():
   blocked["ORIGINAL_BINARY_ABSENT"]+=1;continue
  sources={r.get("exactRawSource") for r in records}
  origins={r.get("sourceProvider") for r in records}
  if len(sources)!=1 or len(origins)!=1:
   blocked["AMBIGUOUS_CONVERSION_SPEC"]+=1;continue
  raw=next(iter(sources))
  provider=next(iter(origins))
  if (not isinstance(raw,str) or not raw.replace("\\","/").startswith("tmp/asset_src/")
      or provider not in PROVIDERS or not credits.get(provider,False)):
   blocked["PROJECT_ONLY_OR_LICENSE_UNVERIFIED_OR_OWNED_SOURCE_REQUIRED"]+=1
   continue
  if not p21.check_binary(src,url):
   blocked["BAD_BINARY"]+=1;continue
  approved.append({"url":url,"provider":provider,
   "sourceSpec":sorted({r["upstreamSpec"] for r in records}),
   "sourceDescription":raw,"bytes":src.stat().st_size,
   "sha256":hashed(src)})
  if len(approved)>MAX_FILES or sum(r["bytes"] for r in approved)>MAX_TOTAL_BYTES:
   raise RuntimeError("P74_CC0_IMPORT_TOO_LARGE_REQUIRE_VOLUME_REVIEW")
 return approved,blocked,len(index),credits

def original_issues():
 if not P70.is_file() or P70.is_symlink():return [],{"P70":"NOT_FOUND"}
 p70=json.loads(P70.read_text("utf8"))
 if p70.get("name")!="HIGHFLY_P70_FULL_P69_FORENSIC_AUDIT":
  raise RuntimeError("P74_P70_REPORT_UNKNOWN")
 rows=[]
 count=Counter()
 for r in p70.get("allResources",[]):
  url=r.get("url","")
  if not isinstance(url,str) or not url.startswith("/"):continue
  if r.get("p69",{}).get("state")=="EXISTS":continue
  count[PurePosixPath(url).suffix.lower()]+=1
  if len(rows)<10000:rows.append(url)
 return rows,dict(count)

def preflight():
 ensure(WORK,WORK,"dir")
 ensure(SOURCE,WORK,"dir")
 ensure(STAGE,WORK,"dir")
 ensure(ORIGINAL,WORK,"dir")
 ensure(SOURCE/"src",SOURCE,"dir")
 ensure(SOURCE/"public",SOURCE,"dir")
 ensure(SOURCE/"public/highfly",SOURCE,"dir")
 ensure(STAGE/"public",STAGE,"dir")
 for r in ROOTS:ensure(STAGE/"public"/r,STAGE,"dir")
 for f in ("index.html","src/main.ts","public/highfly/p73_clean_entry_loader.css",
           "public/highfly/p73_native_load_observer.js"):
  ensure(SOURCE/f,SOURCE)
 if any(x.exists() or x.is_symlink() for x in (LAB,TEMP,REPORT)):
  raise RuntimeError("P74_TARGET_ALREADY_EXISTS_STOP_NO_OVERWRITE")
 html=(SOURCE/"index.html").read_text("utf8")
 main=(SOURCE/"src/main.ts").read_text("utf8")
 if (html.count("</head>")!=1 or "HIGHFLY_P72_P71B_WITHOUT_DRAKENLAB" not in html
     or "HIGHFLY_P73_CLEAN_ENTRY_NATIVE_LOADER_ONLY" not in html):
  raise RuntimeError("P74_EXPECTED_P72_P73_ENTRY_MISSING")
 if "HIGHFLY_P69_FURY_CORE" not in main or "HIGHFLY_P41_OFFLINE_SAVE" not in main:
  raise RuntimeError("P74_FURY_OR_OFFLINE_SAVE_MISSING")
 if "HIGHFLY_WORLD7_P71_DRAKENLAB" in main or "drakenlab_p71" in main:
  raise RuntimeError("P74_DRAKENLAB_STILL_PRESENT")
 for cls in CLASSES:
  if not re.search(r'<button\b[^>]*data-class="'+cls+r'"',html):
   raise RuntimeError("P74_ORIGINAL_CLASS_BUTTON_MISSING_"+cls)
 for f in ("src/highfly/drakenlab_p71.ts","src/highfly/drakenlab_p71.css"):
  if (SOURCE/f).exists():raise RuntimeError("P74_DRAKENLAB_FILE_STILL_PRESENT_"+f)
 if not (STAGE/"node_modules/vite/bin/vite.js").is_file():
  raise RuntimeError("P74_VITE_NODE_MODULES_MISSING")
 # Vite config imports are sourced from exact original scripts. No copied source.
 if not (ORIGINAL/"scripts/browserslist_targets.mjs").is_file():
  raise RuntimeError("P74_VITE_CONFIG_HELPERS_MISSING")
 new_html=html.replace("</head>",INSERT+"</head>",1)
 approved,blocked,spec_count,credits=make_proof_index()
 issues,issue_types=original_issues()
 return {"html":new_html,"mainSha256":hashed(SOURCE/"src/main.ts"),
         "approved":approved,"blocked":blocked,"specCount":spec_count,
         "credits":credits,"missingRefs":issues,"missingTypes":issue_types}

def mirror_to_overlay(stage_root:Path,dest:Path):
 if not stage_root.is_dir() or stage_root.is_symlink():
  raise RuntimeError("P74_SOURCE_TREE_NOT_REGULAR")
 dest.mkdir(mode=0o700)
 for parent,dirs,files in os.walk(stage_root,followlinks=False):
  parent=Path(parent)
  relative=parent.relative_to(stage_root)
  target=dest/relative
  for d in list(dirs):
   if (parent/d).is_symlink():
    raise RuntimeError("P74_UNEXPECTED_NESTED_DIRECTORY_SYMLINK_"+str(parent/d))
   (target/d).mkdir(exist_ok=True)
  for f in files:
   file=parent/f
   if file.is_symlink() or not file.is_file():
    raise RuntimeError("P74_UNEXPECTED_NESTED_FILE_SYMLINK_"+str(file))
   (target/f).symlink_to(file)

def create(plan):
 # Build in a fresh private dir, atomically rename only after verification.
 TEMP.mkdir(mode=0o700)
 try:
  shutil.copytree(SOURCE/"src",TEMP/"src",symlinks=False)
  root_skips={"src","public","node_modules","scripts","dist",".git"}
  for item in SOURCE.iterdir():
   if item.name in root_skips or item.name.startswith(".hf-"):continue
   dest=TEMP/item.name
   if item.is_file() and not item.is_symlink() and item.stat().st_size<10_000_000:
    shutil.copy2(item,dest)
   elif item.is_dir() and not item.is_symlink() and item.name in ("server","shared","packages","vendor"):
    dest.symlink_to(item,target_is_directory=True)
  (TEMP/"scripts").symlink_to(ORIGINAL/"scripts",target_is_directory=True)
  (TEMP/"node_modules").symlink_to(STAGE/"node_modules",target_is_directory=True)
  (TEMP/"public").mkdir()
  for item in (SOURCE/"public").iterdir():
   if item.name in (*ROOTS,"highfly"):continue
   dest=TEMP/"public"/item.name
   if item.is_symlink():dest.symlink_to(item.resolve(),target_is_directory=item.is_dir())
   elif item.is_file():dest.symlink_to(item)
   elif item.is_dir():dest.symlink_to(item,target_is_directory=True)
  (TEMP/"public/highfly").mkdir()
  for item in (SOURCE/"public/highfly").iterdir():
   dest=TEMP/"public/highfly"/item.name
   if item.is_symlink():
    dest.symlink_to(item.resolve(),target_is_directory=item.is_dir())
   elif item.is_file():
    shutil.copy2(item,dest)
   elif item.is_dir():
    dest.symlink_to(item,target_is_directory=True)
  for root in ROOTS:
   mirror_to_overlay(STAGE/"public"/root,TEMP/"public"/root)
  restored=[]
  for row in plan["approved"]:
   rel=PurePosixPath(row["url"].lstrip("/"))
   source=ORIGINAL/"public"/str(rel)
   if hashed(source)!=row["sha256"] or not p21.check_binary(source,row["url"]):
    raise RuntimeError("P74_CC0_SOURCE_CHANGED_"+row["url"])
   target=TEMP/"public"/str(rel)
   target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() or target.is_symlink():
    raise RuntimeError("P74_WOULD_OVERWRITE_EXISTING_ASSET_"+row["url"])
   shutil.copy2(source,target)
   if hashed(target)!=row["sha256"]:
    raise RuntimeError("P74_COPIED_ASSET_HASH_CHANGED_"+row["url"])
   restored.append(row["url"])
  html=TEMP/"index.html"
  html.write_text(plan["html"],encoding="utf8")
  if hashed(TEMP/"src/main.ts")!=plan["mainSha256"]:
   raise RuntimeError("P74_MAIN_CHANGED_IN_COPY")
  style=TEMP/"public/highfly/p74_nine_class_native.css"
  diag=TEMP/"public/highfly/p74_class_readout.js"
  with style.open("x",encoding="utf8") as f:
   f.write(creator.CSS_TEXT+"\n"+EXTRA_CSS)
  with diag.open("x",encoding="utf8") as f:f.write(JS_TEXT)
  for item in ("scripts/browserslist_targets.mjs",
               "scripts/ci_balanced_sequencer.mjs",
               "scripts/i18n_modulepreload.mjs",
               "scripts/lib/diagnostics_capture_guard.mjs",
               "scripts/lib/vitest_fs_module_cache.mjs"):
   if not (TEMP/item).is_file():
    raise RuntimeError("P74_VITE_HELPER_LINK_BROKEN_"+item)
  if "HIGHFLY_P74_ADVANCED_CC0_NINE_CLASS_NATIVE" not in html.read_text("utf8"):
   raise RuntimeError("P74_UI_LINK_MISSING")
  counts=Counter(r["provider"] for r in plan["approved"])
  blocked=dict(plan["blocked"])
  approved_set=set(restored)
  remaining=[u for u in plan["missingRefs"] if
       u not in approved_set and not (STAGE/"public"/u.lstrip("/")).is_file()]
  report={"phase":"HIGHFLY_P74_LICENSED_CC0_NINE_NATIVE_CLASSES",
   "status":"STAGED_NOT_BROWSER_VERIFIED","created":datetime.now(timezone.utc).isoformat(),
   "scope":"NEW_PRIVATE_LAB_ONLY","newLab":str(LAB),"port":4179,
   "source":"P72 P71B recovery with P73 native loader retained",
   "DrakenLab":False,"FURYPreserved":True,
   "expectedNativeClasses":list(CLASSES),"classButtonsVerifiedInHTML":9,
   "nativeClassCSSRestored":True,"classButtonsVisuallyTested":False,
   "nativePreview3DVerified":False,"nativeWorldGameplayVerified":False,
   "sourceAssetProvenance":"exact original conversion spec + CREDITS CC0 1.0 Yes",
   "copyrightPolicy":"UNVERIFIED_OR_PROJECT_ONLY_NOT_COPIED; legacy upstream KayKit excluded",
   "cc0Imported":len(restored),"cc0Bytes":sum(r["bytes"] for r in plan["approved"]),
   "cc0ByProvider":dict(counts),"cc0Provenance":plan["approved"],
   "blockedSpecReasons":blocked,"upstreamSpecsIndexed":plan["specCount"],
   "creditedProviders":plan["credits"],
   "missingRefsAtP70":len(plan["missingRefs"]),
   "remainingMissingRefs":len(remaining),
   "remainingMissingExamples":remaining[:250],
   "remainingRefsRequireOwnedOrFurtherLicensedSource":remaining,
   "sourceFingerprintSha256":plan["mainSha256"],
   "P72_P69_P64_P43_SourceModified":False,
   "originalClaudeCraftSourceModified":False,
   "placeholderGeometryCreated":False,
   "notes":[
     "Build success is not proof of game readiness",
     "Models lacking proven upstream CC0 provenance were not copied",
     "Some legacy references can still return HTML and trigger 3D loader failures",
     "Final owned asset replacements require separately verified source pack"]
  }
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  if REPORT.exists() or REPORT.is_symlink():
   raise RuntimeError("P74_REPORT_CONCURRENT_CREATION")
  REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n","utf8")
  if LAB.exists() or LAB.is_symlink():raise RuntimeError("P74_LAB_RACE")
  TEMP.rename(LAB)
  print("[P74 CREATED] "+json.dumps({
   "lab":str(LAB),"port":4179,
   "restoredCC0":len(restored),"providers":dict(counts),
   "unresolvedP70References":len(remaining),
   "nativeClassesInHTML":9,"classCSSInstalled":True,
   "FURYPreserved":True,"DrakenLab":False,
   "browserVerified":False,
   "protectedOtherStagesChanged":False,"report":str(REPORT)
  },indent=2,ensure_ascii=False))
 except BaseException:
  if TEMP.is_dir() and not TEMP.is_symlink():
   shutil.rmtree(TEMP)
  raise

def cli():
 ap=argparse.ArgumentParser()
 ap.add_argument("--apply",action="store_true")
 args=ap.parse_args()
 plan=preflight()
 count=Counter(r["provider"] for r in plan["approved"])
 print("[P74 PREFLIGHT] "+json.dumps({
  "mode":"APPLY" if args.apply else "DRY_RUN",
  "newLab":str(LAB),"port":4179,
  "nativeClasses":list(CLASSES),"DrakenLab":False,
  "CC0Ready":len(plan["approved"]),
  "CC0Bytes":sum(r["bytes"] for r in plan["approved"]),
  "CC0Providers":dict(count),
  "blockedSpecs":dict(plan["blocked"]),
  "P70MissingRefs":len(plan["missingRefs"]),
  "noPriorStageChanges":True
 },ensure_ascii=False,indent=2))
 if args.apply:create(plan)

if __name__=="__main__":cli()
