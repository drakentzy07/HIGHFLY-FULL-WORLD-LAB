#!/usr/bin/env python3
"""HIGHFLY P45B — original offline Hunter branding + original vector splash.

Scoped to the independently staged game. Preserves offline P41 save,
original class/sim abilities, existing working skin swatches, NPC classes.
Rebrands the *presentation*, NOT claiming finished universal combat/editor.
The 2D splash art is entirely original SVG geometry and wordmark.
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p45-branding"
HTML="index.html"
SCRIPT="public/highfly_p45_branding.js"
ART="public/highfly-origin-splash.svg"
MARK="HIGHFLY_P45_BRANDING"
SVG="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img">
<title>HIGHFLY ORIGIN — portal al mundo</title>
<defs>
<radialGradient id="bg"><stop stop-color="#152b4c"/><stop offset=".65" stop-color="#070e20"/><stop offset="1" stop-color="#030711"/></radialGradient>
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#4be4ff"/><stop offset=".55" stop-color="#5b74f4"/><stop offset="1" stop-color="#c464fa"/></linearGradient>
<filter id="glow"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<g opacity=".5" fill="none" stroke="url(#rim)">
<ellipse cx="800" cy="450" rx="520" ry="328" stroke-width="2"/>
<ellipse cx="800" cy="450" rx="447" ry="292" stroke-width="3"/>
<ellipse cx="800" cy="450" rx="362" ry="240" stroke-width="5"/>
<ellipse cx="800" cy="450" rx="265" ry="185" stroke-width="7" filter="url(#glow)"/>
</g>
<path d="M800 188 930 308 843 335 800 385 751 335 670 308Z" fill="url(#rim)" opacity=".9"/>
<path d="m650 515 150-145 150 145-150-55Z" fill="none" stroke="url(#rim)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
<path d="m740 550 60-88 60 88-60-25Z" fill="#081627" stroke="#8ceaff" stroke-width="7"/>
<text x="800" y="640" font-family="Arial,Helvetica,sans-serif" text-anchor="middle" font-size="95" letter-spacing="13" font-weight="bold" fill="#f4faff">HIGHFLY</text>
<text x="800" y="706" font-family="Arial,Helvetica,sans-serif" text-anchor="middle" font-size="36" letter-spacing="23" fill="#68d8f5">ORIGIN</text>
<text x="800" y="767" font-family="Arial,Helvetica,sans-serif" text-anchor="middle" font-size="21" letter-spacing="5" fill="#b8c8e9">TU MUNDO · TU CAZADOR · TU HISTORIA</text>
</svg>
"""
CSS="""
<!-- HIGHFLY_P45_BRANDING: independent intro & loading identity -->
<style id="highfly-p45-brand-css">
#loading-screen {
 background: #06101f url('/highfly-origin-splash.svg') center center / cover no-repeat !important;
}
#loading-screen::before, #loading-screen::after {
 background-image:none !important;
}
#loading-screen .ls-logo { display:none !important; }
#offline-select .auth-title {letter-spacing:.14em;color:#b9e9ff;}
#offline-select .mini-class[data-class="warrior"] {
 font-size:0 !important;min-width:128px !important;
}
#offline-select .mini-class[data-class="warrior"]::after {
 content:'CAZADOR UNIVERSAL';font-size:12px;color:#d8faff;
}
#offline-select .mini-class[data-class]:not([data-class="warrior"]) {
 display:none !important;
}
#offline-select #offline-skin-row {
 display:flex !important; flex-wrap:wrap;align-items:center;
 justify-content:center;gap:8px;padding:9px 0;
}
#offline-select #offline-class-details {display:none !important}
#highfly-p45-hunter-info {
 border:1px solid #4a93bc;background:rgba(8,21,44,.92);
 padding:15px;color:#def6ff;border-radius:12px;
 font:14px/1.6 Arial,sans-serif;max-width:350px;
 margin:10px auto 0;
}
#highfly-p45-hunter-info h3 {margin:0 0 7px;color:#76dbff;letter-spacing:.12em}
#highfly-p45-hunter-info p {margin:5px 0}
#highfly-p45-hunter-info small {color:#a2bbd3}
</style>
<script defer src="/highfly_p45_branding.js"></script>
"""
JS="""
// HIGHFLY_P45_BRANDING: presentation only. The original skin-row click
// handlers continue to select the actual character rig/portrait for preview.
(function(){
 'use strict';
 function mount(){
  const root=document.querySelector('#offline-select');
  if(!root)return;
  const existing=document.getElementById('highfly-p45-hunter-info');
  if(!existing){
   const details=root.querySelector('#offline-class-details');
   if(!details)return;
   const panel=document.createElement('section');
   panel.id='highfly-p45-hunter-info';
   panel.innerHTML='<h3>CAZADOR UNIVERSAL</h3>'+
    '<p>Un solo personaje para tu aventura. La apariencia no define tus habilidades.</p>'+
    '<p>El combate HIGHFLY y la obtención de habilidades están en desarrollo; '+
    'esta prueba conserva las reglas RPG actuales.</p>'+
    '<small>Elegí una apariencia entre las skins disponibles. '+
    'Se mantienen el nombre, el equipo y tu partida offline.</small>';
   details.after(panel);
  }
  const row=root.querySelector('#offline-skin-row');
  if(row&&!document.getElementById('highfly-p45-skin-label')){
   const t=document.createElement('div');
   t.id='highfly-p45-skin-label';
   t.textContent='APARIENCIA · ELEGÍ TU SKIN';
   t.style.cssText='text-align:center;letter-spacing:1px;color:#7edafb;font:12px Arial;margin-top:6px';
   row.before(t);
  }
  root.setAttribute('aria-label','Editor de Cazador Universal');
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);
 else mount();
})();
"""
def patch_html(s):
 if MARK in s:raise RuntimeError("P45B_ALREADY_APPLIED")
 if s.count("</head>")!=1:raise RuntimeError("P45B_HEAD_ANCHOR_DRIFT")
 return s.replace("</head>",CSS+"\n</head>",1)
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 h=STAGE/HTML
 before=h.read_text(encoding="utf8")
 updated=patch_html(before)
 for rel in (SCRIPT,ART):
  dest=STAGE/rel
  if dest.exists() or dest.is_symlink():raise RuntimeError("P45B_FILE_ALREADY_EXISTS "+rel)
 if apply:
  backup=OUT/"backups"/HTML
  if backup.exists() or backup.is_symlink():raise RuntimeError("P45B_BACKUP_EXISTS")
  backup.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(h,backup)
  if hashlib.sha256(h.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
   raise RuntimeError("P45B_BACKUP_HASH_MISMATCH")
  for rel,content in ((SCRIPT,JS),(ART,SVG)):
   dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open("x",encoding="utf8") as fh:fh.write(content)
  h.write_text(updated,encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 r={"phase":"P45B_HIGHFLY_SPLASH_HUNTER_INTRO","mode":"APPLY" if apply else "DRY_RUN",
    "originalSplashVector":True,"legacyLoadingLogoHidden":True,
    "hunterLabelAndDescription":True,"existingSkinSelectorPreserved":True,
    "universalSkillsImplemented":False,"fullCharacterEditorImplemented":False,
    "npcSkillsSaveUnchanged":True,"browserVerified":False}
 (OUT/"P45B_REPORT.json").write_text(json.dumps(r,indent=2)+"\n")
 print("[HIGHFLY] P45B BRAND: "+json.dumps(r))
 return r
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
