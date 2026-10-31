#!/usr/bin/env python3
"""P42: single playable Hunter presentation + Spanish default in private stage.

Does NOT delete original NPC/mob role data, restore nine classes, overwrite
modular models, or pretend to provide missing modular hairstyles and faces.
The 'warrior' class remains an INTERNAL compatibility implementation for the
only offline selectable Hunter. Reuse original MIT character editor later
when HIGHFLY legally-owned compatible modular library is prepared.
"""
from __future__ import annotations
import argparse,json,shutil,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p42-spanish-hunter"
FILES=("src/ui/i18n.ts","index.html")
JS_PATH="public/highfly_p42_hunter.js"
MARK="HIGHFLY_P42_SINGLE_HUNTER"
JS="""
// HIGHFLY_P42_SINGLE_HUNTER: UI only. Do not change internal RPG class enum.
// Existing P36/P38 world NPC roles and combat systems remain independent.
(function(){
'use strict';
function apply(){
 const root=document.querySelector('#offline-select');
 if(!root)return;
 const cards=[...root.querySelectorAll('.mini-class[data-class]')];
 for(const c of cards){
  if(c.getAttribute('data-class')!=='warrior'){
    c.setAttribute('hidden','');c.setAttribute('aria-hidden','true');
    c.style.setProperty('display','none','important');
  }else{
    c.setAttribute('aria-label','Cazador universal');
    c.setAttribute('title','Cazador universal - sin clases seleccionables');
    if(!c.hasAttribute('data-highfly-p42')){
      c.setAttribute('data-highfly-p42','1');
      for(const node of c.childNodes){
        if(node.nodeType===Node.TEXT_NODE &&
           /^(GUERRERO|WARRIOR)$/i.test((node.textContent||'').trim()))
           node.textContent='CAZADOR UNIVERSAL';
      }
    }
  }
 }
 const details=root.querySelector('#offline-class-details');
 if(details && !details.hasAttribute('data-highfly-p42')){
  details.setAttribute('data-highfly-p42','1');
  details.setAttribute('aria-label','Cazador universal');
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);
else apply();
const mo=new MutationObserver(()=>{
 const el=document.querySelector('#offline-select');
 if(el && !el.hasAttribute('data-highfly-p42-observed')){
  el.setAttribute('data-highfly-p42-observed','1');apply();
 }
});
mo.observe(document.documentElement,{childList:true,subtree:true});
})();
""".strip()+"\n"
STYLE="""
<style id="highfly-p42-hunter-styles">
/* HIGHFLY_P42_SINGLE_HUNTER. One selectable player; NPC classes untouched. */
#offline-select .mini-class[data-class]:not([data-class="warrior"]) {
  display:none !important;
}
#offline-select .mini-class[data-class="warrior"] {
  border-color:#5dc7eb !important;
}
</style>
<script defer src="/highfly_p42_hunter.js"></script>
"""
def replace_one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError("P42_ANCHOR_DRIFT "+label+" "+str(n))
 return s.replace(a,b,1)
def patch(data):
 if any(MARK in t for t in data.values()):raise RuntimeError("P42_ALREADY_APPLIED")
 loc=replace_one(data[FILES[0]],"let currentLanguage: SupportedLanguage = 'en';",
  "// "+MARK+": Spanish default; user preference and ?lang overrides kept.\n"
  "let currentLanguage: SupportedLanguage = 'es';","locale")
 html=replace_one(data[FILES[1]],"</head>",STYLE+"\n</head>","html")
 return {FILES[0]:loc,FILES[1]:html}
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 target=STAGE/JS_PATH
 if target.exists() or target.is_symlink():raise RuntimeError("P42_ALREADY_APPLIED_JS")
 inp={}
 for rel in FILES:
  f=STAGE/rel
  if not f.is_file() or f.is_symlink():raise RuntimeError("P42_FILE_MISSING "+rel)
  inp[rel]=f.read_text(encoding="utf8")
 out=patch(inp)
 if apply:
  for rel in FILES:
   b=OUT/"backups"/rel
   if b.exists() or b.is_symlink():raise RuntimeError("P42_BACKUP_EXISTS "+rel)
  for rel in FILES:
   src=STAGE/rel;b=OUT/"backups"/rel
   b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,b)
   if hashlib.sha256(src.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest():
    raise RuntimeError("P42_BACKUP_MISMATCH "+rel)
  for rel in FILES:
   if (STAGE/rel).read_text(encoding="utf8")!=inp[rel]:
    raise RuntimeError("P42_SOURCE_CHANGED "+rel)
   (STAGE/rel).write_text(out[rel],encoding="utf8")
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(JS,encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 s={"phase":"P42_SPANISH_SINGLE_HUNTER","mode":"APPLY" if apply else "DRY_RUN",
  "spanishDefault":True,"languagePreferenceOverridePreserved":True,
  "singleSelectableOfflineClass":True,"internalClass":"warrior",
  "npcsAndMobRolesChanged":False,"modularEditorFullyRestored":False,
  "browserVerified":False}
 (OUT/"P42_STATUS.json").write_text(json.dumps(s,indent=2)+"\n")
 print("[HIGHFLY] P42 HUNTER/ES: "+json.dumps(s))
 return s
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--apply",action="store_true")
 run(ap.parse_args().apply)
