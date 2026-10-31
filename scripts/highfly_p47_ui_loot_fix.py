#!/usr/bin/env python3
"""HIGHFLY P47 — repair real P46 UI and missing bag art.

No imaginary P47 phase, no new fake character genders/classes and no tutorial
skip. Uses the actual existing appearance_customizer (body male/female, face,
hair) and keeps native Play and Loading progress handlers. No save module edits.
Private stage only; backup + rollback if Vite build fails.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p47"
MARK="HIGHFLY_P47_UI_LOOT_REAL_EDITOR"
CSS_PATH="public/highfly/p47.css"
JS_PATH="public/highfly/p47.js"
ORIGINAL_HTML="index.html"
CSS=r"""
/* HIGHFLY_P47_UI_LOOT_REAL_EDITOR — override only the broken P46 presentation.
 * Never modify the loading bar widths, engine counters or underlying sim. */
:root {--hf-p47-night:#090716;--hf-p47-gold:#f5c88e;--hf-p47-magenta:#d863ec}
#start-screen.hf-p46-entry {
 background-image:url('/highfly/official/highfly_enter_world_bg.png')!important;
 background-position:center center!important;
 background-size:cover!important;
}
#start-screen.hf-p46-entry #homepage-views-container,
#start-screen.hf-p46-entry #hero-view {
 position:static!important;inset:auto!important;transform:none!important;
 display:contents!important;background:transparent!important;
 border:0!important;box-shadow:none!important;min-height:0!important;
 height:auto!important;padding:0!important;margin:0!important;
}
#start-screen.hf-p46-entry #mode-select {
 position:fixed!important;left:50%!important;top:auto!important;
 right:auto!important;bottom:5.5dvh!important;
 transform:translateX(-50%)!important;
 width:min(480px,88vw)!important;height:auto!important;min-height:0!important;
 max-height:none!important;overflow:visible!important;margin:0!important;
 padding:0!important;background:transparent!important;
 border:0!important;border-radius:0!important;box-shadow:none!important;
 z-index:55!important;display:flex!important;flex-direction:column!important;
 align-items:center!important;gap:9px!important;
}
#start-screen.hf-p46-entry #mode-select .website-card-heading {
 display:block!important;background:#100920b0!important;border-radius:18px!important;
 padding:7px 18px!important;backdrop-filter:blur(3px)!important;
 border:1px solid #a968dc66!important;
 text-shadow:0 2px 9px #09020f!important;
}
#start-screen.hf-p46-entry #mode-select .website-card-heading::after {
 font:700 clamp(12px,1.8vw,18px)/1.2 Georgia,serif!important;
 letter-spacing:.09em!important;white-space:normal!important;
}
#start-screen.hf-p46-entry #mode-select .play-console {
 display:block!important;position:static!important;transform:none!important;
 width:100%!important;max-width:100%!important;padding:0!important;
 border:0!important;background:transparent!important;box-shadow:none!important;
}
#start-screen.hf-p46-entry #mode-select #btn-play {
 display:block!important;width:100%!important;min-height:54px!important;
 border:2px solid var(--hf-p47-gold)!important;
 box-shadow:0 0 20px #b231f6a0,inset 0 0 13px #ad38ef8a!important;
 background:linear-gradient(100deg,#1b0928df,#4b1b7aee,#1b0928df)!important;
 border-radius:12px!important;
}
#start-screen.hf-p46-entry #highfly-p46-local-notice {
 font:12px/1.3 Arial,sans-serif!important;color:#f1dfff!important;
 padding:4px 12px!important;background:#0c0620a8!important;
 border-radius:16px!important;text-align:center!important;
}
#start-screen.hf-p46-entry .view-section:not(#hero-view),
#start-screen.hf-p46-entry .website-story,
#start-screen.hf-p46-entry .website-entry-card::before,
#start-screen.hf-p46-entry .website-entry-card::after {
 background:none!important;box-shadow:none!important;
}
#offline-select {
 position:relative!important;inset:auto!important;transform:none!important;
 display:block!important;width:min(1140px,95vw)!important;
 height:min(640px,88dvh)!important;max-height:88dvh!important;
 overflow-y:auto!important;overscroll-behavior:contain!important;
 padding:clamp(12px,2vw,22px)!important;
 background:linear-gradient(142deg,#09091bf8,#160b31f7)!important;
 border:1px solid #9c67dc!important;border-radius:16px!important;
 box-shadow:0 9px 35px #0009!important;box-sizing:border-box!important;
}
#offline-select .auth-title {
 margin:0 0 9px!important;text-align:center!important;
 color:#f3d5ff!important;font:700 clamp(20px,2.3vw,28px)/1.3 Georgia,serif!important;
 letter-spacing:.08em!important;
}
#offline-select .charselect-layout {
 display:grid!important;grid-template-columns:minmax(325px,1.05fr) minmax(280px,.95fr)!important;
 align-items:start!important;gap:clamp(12px,2vw,24px)!important;
 position:relative!important;overflow:visible!important;
}
#offline-select .charselect-col-left,
#offline-select .charselect-col-right,
#offline-select .char-create {
 display:flex!important;flex-direction:column!important;gap:9px!important;
 width:auto!important;min-width:0!important;max-width:none!important;
 position:relative!important;inset:auto!important;transform:none!important;
}
#offline-select .charselect-col-left{order:1!important}
#offline-select .charselect-col-right{order:2!important;align-items:center!important}
#offline-select .char-create .char-input-group,
#offline-select #char-name {
 max-width:100%!important;box-sizing:border-box!important;
}
#offline-select .mini-class-row {
 order:1!important;margin:0!important;align-self:flex-start!important;
}
#offline-select .mini-class[data-class="warrior"] {
 font-size:0!important;margin:0!important;min-width:0!important;
 padding:10px 18px!important;border:1px solid #c480ee!important;
}
#offline-select .mini-class[data-class="warrior"]::after {
 content:"CAZADOR UNIVERSAL" !important;font:700 12px Arial,sans-serif!important;
}
#offline-select #offline-appearance {
 order:2!important;position:relative!important;inset:auto!important;
 display:block!important;visibility:visible!important;opacity:1!important;
 overflow:auto!important;max-height:min(45dvh,355px)!important;
 width:100%!important;padding:5px 7px!important;box-sizing:border-box!important;
 border:1px solid #604a9b!important;border-radius:10px!important;
 background:#080c20c4!important;
}
#offline-select #offline-appearance:empty {display:none!important}
#offline-select #offline-appearance .ac-tabs {display:flex!important;flex-wrap:wrap!important}
#offline-select #offline-appearance .ac-seg {display:flex!important;flex-wrap:wrap!important}
#offline-select #offline-skin-row:empty,
#offline-select #highfly-p45-skin-label {display:none!important}
#offline-select #offline-preview-container {
 position:relative!important;inset:auto!important;transform:none!important;
 width:100%!important;min-height:260px!important;height:min(49dvh,400px)!important;
 margin:0!important;overflow:visible!important;
}
#offline-select #highfly-p45-hunter-info,
#offline-select #offline-class-details {
 display:none!important;
}
#offline-select #highfly-p47-info {
 position:relative!important;display:block!important;box-sizing:border-box!important;
 width:100%!important;margin:6px 0 0!important;padding:10px 14px!important;
 border:1px solid #7651a0!important;border-radius:10px!important;
 background:#120e27e0!important;color:#ebe0ff!important;
 font:13px/1.5 Arial,sans-serif!important;
}
#offline-select #highfly-p47-info strong {color:#dfadff;letter-spacing:.07em}
#offline-select .auth-actions {
 order:3!important;position:relative!important;display:flex!important;
 gap:8px!important;flex-wrap:wrap!important;width:100%!important;
 margin-top:8px!important;
}
#offline-select .auth-actions button {
 flex:1 1 160px!important;min-width:0!important;max-width:none!important;
 min-height:49px!important;
}
#loading-screen {
 background-image:url('/highfly/official/highfly_loading_bg.png')!important;
 background-position:center center!important;background-size:cover!important;
}
#loading-screen .ls-progress {
 position:absolute!important;left:50%!important;right:auto!important;
 bottom:6.8dvh!important;top:auto!important;transform:translateX(-50%)!important;
 display:flex!important;flex-direction:column!important;gap:7px!important;
 width:min(920px,76vw)!important;min-height:0!important;
 margin:0!important;padding:0!important;
 border:0!important;border-radius:0!important;
 background:transparent!important;box-shadow:none!important;
 backdrop-filter:none!important;overflow:visible!important;
}
#loading-screen .ls-progress::before,
#loading-screen .ls-progress::after {display:none!important}
#loading-screen #ls-status {
 order:0!important;text-align:center!important;
 color:#fff4fb!important;text-shadow:0 2px 12px #000,0 0 16px #ad50f8!important;
 font:700 clamp(15px,2.2vw,26px)/1.15 Georgia,serif!important;
 margin:0!important;background:none!important;
}
#loading-screen .ls-bar {
 order:1!important;height:18px!important;width:100%!important;
 margin:0!important;border:2px solid #efc384!important;
 border-radius:20px!important;background:#0a061cc4!important;
 box-shadow:0 0 14px #c460fbaa!important;overflow:hidden!important;
}
#loading-screen #ls-fill {
 height:100%!important;background:linear-gradient(90deg,#6621cb,#bd4aff,#efadf7)!important;
 box-shadow:0 0 18px #d760ff!important;transition:width .14s linear!important;
}
#loading-screen #ls-tip {
 order:2!important;display:block!important;max-width:100%!important;
 text-align:center!important;color:#f8e8ff!important;
 text-shadow:0 2px 8px #000!important;
 background:#08051a88!important;border:1px solid #b46dcd55!important;
 border-radius:10px!important;padding:7px 12px!important;
 font:12px/1.35 Arial,sans-serif!important;min-height:0!important;
}
#loading-screen #ls-slow-hint {
 order:3!important;background:transparent!important;text-align:center!important;
}
@media (max-width:850px) and (orientation:landscape) {
 #offline-select{width:98vw!important;height:92dvh!important;max-height:92dvh!important;
  padding:8px 12px!important}
 #offline-select .charselect-layout{
  grid-template-columns:minmax(210px,1fr) minmax(190px,1fr)!important;gap:9px!important
 }
 #offline-select #offline-preview-container{height:45dvh!important;min-height:180px!important}
 #offline-select #offline-appearance{max-height:38dvh!important}
 #offline-select #highfly-p47-info{font-size:11px!important;padding:7px 9px!important}
 #loading-screen .ls-progress{width:84vw!important;bottom:5.2dvh!important}
}
"""
JS=r"""
// HIGHFLY_P47_UI_LOOT_REAL_EDITOR: attach only to existing native controls.
// Never substitute a fake gender/skin editor or tamper with save keys.
(function(){
 'use strict';
 const ID='highfly-p47-info';
 function arrangeCreator(){
  const root=document.getElementById('offline-select');
  if(!root)return;
  const title=root.querySelector('.auth-title');
  if(title){
   title.removeAttribute('data-i18n');
   title.textContent='CREAR TU CAZADOR';
  }
  const appearance=root.querySelector('#offline-appearance');
  const charCreate=root.querySelector('.char-create');
  const classes=root.querySelector('.mini-class-row');
  if(appearance && charCreate && appearance.parentElement!==charCreate){
   if(classes && classes.parentElement===charCreate)classes.after(appearance);
   else charCreate.append(appearance);
  }
  const previewCol=root.querySelector('.charselect-col-right');
  if(previewCol && !document.getElementById(ID)){
   const info=document.createElement('div');info.id=ID;
   const emphasis=document.createElement('strong');
   emphasis.textContent='CAZADOR UNIVERSAL';
   const description=document.createElement('div');
   description.textContent='Elegí tu nombre y personalizá cuerpo, rostro, cabello y estilo desde el editor. Tus habilidades dependerán de tu aventura.';
   info.append(emphasis,description);
   previewCol.append(info);
  }
 }
 function lootIconFor(img){
  if(!(img instanceof HTMLImageElement) || img.dataset.highflyP47Icon)return;
  let source;
  try {source=new URL(img.currentSrc||img.src,location.href).pathname.toLowerCase();}
  catch(_){return;}
  // Only the RPG UI inventory/quest icon family; keep legitimate donor models
  // and all valid icons unchanged. The capture listener only sees image errors.
  if(!/(?:\/ui\/(?:items|inventory|skills|icons)\/|\/highfly-icons\/)/.test(source))
   return;
  const name=source.split('/').pop()||'';
  let type='material';
  if(/pearl|perla|gem|crystal|ruby|sapphire|ore|stone/.test(name))type='gem';
  else if(/sword|axe|dagger|blade|bow|weapon/.test(name))type='sword';
  else if(/helm|chest|armor|armour|tunic|robe|boots|shield/.test(name))type='armor';
  else if(/potion|flask|elixir|heal|mana|food/.test(name))type='potion';
  else if(/quest|letter|scroll|map|recipe|book/.test(name))type='scroll';
  else if(/ring|amulet|necklace|earring/.test(name))type='ring';
  else if(/loot|chest|cache|coin|gold/.test(name))type='loot';
  img.dataset.highflyP47Icon='1';
  img.src='/highfly/p47-icons/'+type+'.svg';
 }
 document.addEventListener('error',e=>lootIconFor(e.target),true);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',arrangeCreator);
 else arrangeCreator();
 const editor=document.getElementById('offline-select');
 if(editor){
  // The original editor is often mounted AFTER the home splash. Reorder once
  // it actually arrives. Never recreate or duplicate its control event handlers.
  let done=false;
  const observer=new MutationObserver(()=>{
   if(!done && editor.querySelector('#offline-appearance .ac-tabs')){
    done=true;arrangeCreator();observer.disconnect();
   }
  });
  observer.observe(editor,{childList:true,subtree:true});
  window.addEventListener('pagehide',()=>observer.disconnect(),{once:true});
 }
})();
"""
DRAW={
 "material":('<path d="m24 60 17-29 37-4-10 44-34 13Z" fill="#64c9bc" stroke="#d7fff8" stroke-width="5"/><path d="m40 35 12 36m10-43-7 46" stroke="#1f807d" stroke-width="4"/>',"#55c7a8"),
 "gem":('<path d="M23 30 41 12h20l19 18-9 44-21 16-21-16Z" fill="#ac7def" stroke="#ffe4ff" stroke-width="5"/><path d="m23 30 27 60 30-60M41 12l9 78 11-78" stroke="#f9e8ff" stroke-width="3"/>',"#b478ec"),
 "sword":('<path d="m71 9 18 14-33 42-16-13Z" fill="#b7edff" stroke="#fff" stroke-width="4"/><path d="m27 50 31 25M40 63 18 89" stroke="#eaba6d" stroke-width="9" stroke-linecap="round"/>',"#67bfff"),
 "armor":('<path d="m20 18 18-9 12 12 12-12 18 9 12 22-14 10-6 40H28l-6-40-14-10Z" fill="#5899ba" stroke="#f5e3bf" stroke-width="5"/><path d="m49 23 1 58M28 53h45" stroke="#1c4775" stroke-width="6"/>',"#89baff"),
 "potion":('<path d="M39 11h22v15l13 15-2 37q-22 20-44 0l-2-37 13-15Z" fill="#b751cd" stroke="#ffe4ff" stroke-width="5"/><path d="M30 53q20-15 42 0v20q-22 23-42 0Z" fill="#e777f7"/><path d="M38 12h24" stroke="#eac987" stroke-width="8"/>',"#ef7ff3"),
 "scroll":('<path d="M24 22h47v58H24Z" fill="#e5c595" stroke="#fff1d8" stroke-width="5"/><path d="M25 22q-16-3-16 9v47q7 11 16 2m46-58q17-3 17 9v47q-7 10-17 2" fill="#9f7550" stroke="#f0daae" stroke-width="4"/><path d="M34 40h27M34 50h27M34 60h19" stroke="#845b41" stroke-width="4"/>',"#f0ca86"),
 "ring":('<ellipse cx="50" cy="65" rx="25" ry="17" fill="none" stroke="#f3c56a" stroke-width="12"/><path d="M50 8 76 38 50 60 24 38Z" fill="#c5a0f9" stroke="white" stroke-width="5"/>',"#e8bd73"),
 "loot":('<path d="M14 38h72v48H14Z" fill="#7354ae" stroke="#fbdc8a" stroke-width="5"/><path d="M14 38q0-26 36-26t36 26Z" fill="#b57936" stroke="#ffdfa1" stroke-width="5"/><path d="M42 38h16v32H42Z" fill="#ffe7a0"/>',"#ddaa68")
}
def svg(shape,color):
 return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
         '<rect x="1" y="1" width="98" height="98" rx="13" fill="#10162d" stroke="'+color+'" stroke-width="3"/>'
         +shape+'</svg>\n')
def patched_html(s):
 if MARK in s:raise RuntimeError("P47_ALREADY_APPLIED")
 if s.count("</head>")!=1:raise RuntimeError("P47_HEAD_ANCHOR_COUNT")
 if "HIGHFLY_P46_OFFICIAL_IDENTITY" not in s:raise RuntimeError("P47_P46_NOT_APPLIED")
 return s.replace("</head>",
  '<!-- '+MARK+': coherent UI layout and missing-image fallback. -->\n'
  '<link rel="stylesheet" href="/highfly/p47.css" />\n'
  '<script defer src="/highfly/p47.js"></script>\n</head>',1)
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 html=STAGE/"index.html"
 if not html.is_file() or html.is_symlink():raise RuntimeError("P47_MISSING_STAGE_HTML")
 original=html.read_text(encoding="utf8")
 updated=patched_html(original)
 created=[STAGE/CSS_PATH,STAGE/JS_PATH]+[
  STAGE/"public/highfly/p47-icons"/(name+".svg") for name in DRAW]
 if any(x.exists() or x.is_symlink() for x in created):
  raise RuntimeError("P47_OUTPUT_EXISTS (already installed or partial)")
 status={"phase":"HIGHFLY_P47_CREATOR_ENTRY_LOADING_LOOT_FIX","mode":"DRY_RUN",
  "p46ArtReused":True,"realNativeGenderEditorPreserved":True,
  "skinPresetFaked":False,"loadingEngineProgressUnchanged":True,
  "missingBagArtFallbackKinds":len(DRAW),
  "saveUntouched":True,"tutorialUntouched":True,
  "androidTested":False,"browserVerified":False}
 if not apply:
  print("[HIGHFLY] P47: "+json.dumps(status,ensure_ascii=False));return status
 backup=OUT/"backup/index.html"
 if backup.exists() or backup.is_symlink():raise RuntimeError("P47_BACKUP_EXISTS")
 backup.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(html,backup)
 if hashlib.sha256(html.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
  raise RuntimeError("P47_BACKUP_INTEGRITY_FAIL")
 try:
  for target,text in [(STAGE/CSS_PATH,CSS),(STAGE/JS_PATH,JS)]+[
    (STAGE/"public/highfly/p47-icons"/(name+".svg"),svg(*part)) for name,part in DRAW.items()]:
   target.parent.mkdir(parents=True,exist_ok=True)
   with target.open("x",encoding="utf8") as f:f.write(text)
  html.write_text(updated,encoding="utf8")
  subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
    cwd=str(ROOT),check=True)
 except BaseException:
  if backup.is_file():
   html.write_bytes(backup.read_bytes())
  for target in created:
   if target.is_file() and not target.is_symlink():target.unlink()
  print("[HIGHFLY] P47: ROLLBACK to P46, check build log",file=sys.stderr)
  raise
 OUT.mkdir(parents=True,exist_ok=True)
 status["mode"]="BUILD_GREEN_NOT_BROWSER_VERIFIED"
 (OUT/"P47_STATUS.json").write_text(json.dumps(status,indent=2,ensure_ascii=False)+"\n")
 print("[HIGHFLY] P47: "+json.dumps(status,ensure_ascii=False))
 return status
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
