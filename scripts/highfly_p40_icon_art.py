#!/usr/bin/env python3
"""P40: restore 20 currently broken UI image paths with ORIGINAL SVG artwork.

No CraftPix, no unverified artwork, no private assets and no changes to the
underlying item/skill data. Provides visually distinct illustrated SVG icons
for exact P35 broken images, using DOM image-error fallback to preserve the
existing original .webp references. Can later replace SVGs with premium art.
"""
from __future__ import annotations
import argparse,json,shutil,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p40-icon-art"
MARK="HIGHFLY_P40_ICON_ART"
JS_PATH="public/highfly_p40_icons.js"
HTML="index.html"
# original drawings, not external asset copies. Multiple palettes and symbols.
ART={
 "ui/items/recruit_tunic.webp":("Túnica","vest","#36c9bb"),
 "ui/items/worn_sword.webp":("Espada","sword","#b6ddff"),
 "ui/items/eastbrook_buckler.webp":("Rodela","shield","#e7bb5c"),
 "ui/classes/warrior.webp":("Guerrero","sword","#e46c68"),
 "ui/classes/paladin.webp":("Paladín","shield","#ffd57e"),
 "ui/classes/hunter.webp":("Cazador","bow","#62df9b"),
 "ui/classes/rogue.webp":("Pícaro","dagger","#9ae182"),
 "ui/classes/priest.webp":("Sacerdote","star","#dfbdff"),
 "ui/classes/shaman.webp":("Chamán","spiral","#64dddf"),
 "ui/classes/mage.webp":("Mago","star","#6aabff"),
 "ui/classes/warlock.webp":("Brujo","flame","#d79bef"),
 "ui/classes/druid.webp":("Druida","leaf","#91d878"),
 "ui/currency/honor.webp":("Honor","medal","#f8d16d"),
 "ui/daily-rewards/treasure_chest.webp":("Recompensa","chest","#ddb76b"),
 "ui/procs/chronomancy-phoenix-v2.webp":("Fénix cronos","hourglass","#91c9ff"),
 "ui/procs/fire-phoenix-v2.webp":("Fénix fuego","flame","#ff9c45"),
 "ui/procs/frost-phoenix-v1.webp":("Fénix hielo","snow","#83e2ff"),
 "ui/skills/warrior/charge.webp":("Carga","bolt","#ffb86b"),
 "ui/skills/warrior/execute.webp":("Ejecutar","cross_swords","#f07d68"),
 "ui/skills/warrior/heroic_strike.webp":("Golpe heroico","star","#f7d367"),
}
SVG_SYMBOLS={
"vest":'<path d="M34 21 46 16l14 8 14-8 12 5 10 22-16 8v42H20V51L4 43l10-22 12 5Z" fill="url(#metal)" stroke="#eafff9" stroke-width="4"/><path d="M43 23 50 40 57 23M30 54h40M34 70h32" fill="none" stroke="#087e82" stroke-width="6"/>',
"sword":'<path d="m70 14 14 13-32 43-12-12Z" fill="url(#metal)" stroke="#e9fdff" stroke-width="4"/><path d="m32 53 29 26M37 63 18 85M16 82l7 8" fill="none" stroke="#e6bd66" stroke-width="8" stroke-linecap="round"/>',
"shield":'<path d="M50 8 86 22v29q0 29-36 44Q14 80 14 51V22Z" fill="url(#metal)" stroke="#ffdf8e" stroke-width="5"/><path d="M50 17v66M22 48h56" fill="none" stroke="#79511d" stroke-width="8"/><circle cx="50" cy="48" r="12" fill="#ffcc66" stroke="#fff3bb" stroke-width="3"/>',
"bow":'<path d="M23 13Q87 45 23 88M24 13 72 50 24 88" stroke="#d9ffb4" stroke-width="5" fill="none"/><path d="m17 62 71-17-15 12-8-8" fill="#edca84" stroke="#f9ebc5" stroke-width="3"/>',
"dagger":'<path d="M79 12 55 65 40 55Z" fill="url(#metal)" stroke="#ebf6ff" stroke-width="4"/><path d="m34 49 29 26m-25-9L19 88" stroke="#cfa26d" stroke-width="8" fill="none"/>',
"star":'<path d="m50 5 12 30 32 15-32 13-12 32-12-32L6 50l32-15Z" fill="url(#metal)" stroke="#fff8cb" stroke-width="5"/><circle cx="50" cy="50" r="13" fill="#fff2ca" opacity=".65"/>',
"spiral":'<path d="M47 10C8 14 8 83 49 86c48 3 49-67 6-70-34-2-40 46-11 52 24 5 29-27 9-30" fill="none" stroke="url(#metal)" stroke-width="9" stroke-linecap="round"/><circle cx="50" cy="50" r="8" fill="#fff"/>',
"flame":'<path d="M50 6C67 36 90 45 78 76c-14 32-58 25-58-8 0-25 22-37 21-54 18 16 4 34 9 41 9-13 9-27 0-49Z" fill="url(#metal)" stroke="#fff0b9" stroke-width="4"/><path d="M52 46C39 59 35 72 43 82c13 10 25 0 17-16Z" fill="#fff0bc"/>',
"leaf":'<path d="M90 11C38 11 10 29 13 60c3 35 50 38 63 0 6-20 9-38 14-49Z" fill="url(#metal)" stroke="#dfffba" stroke-width="4"/><path d="M22 87Q48 45 83 22M43 60 26 47M59 44l1-21" stroke="#215e35" stroke-width="5" fill="none"/>',
"medal":'<path d="M26 8h22l10 30-20 6ZM74 8H52L42 38l20 6Z" fill="#b65546" stroke="#ffcf72" stroke-width="3"/><circle cx="50" cy="58" r="33" fill="url(#metal)" stroke="#fff0b1" stroke-width="5"/><path d="m50 34 7 16 18 3-14 12 4 19-15-10-15 10 4-19-14-12 18-3Z" fill="#fff5be"/>',
"chest":'<path d="M12 42h76v43H12Z" fill="url(#metal)" stroke="#f9d87a" stroke-width="5"/><path d="M13 42Q12 13 50 13t37 29Z" fill="#96601f" stroke="#ffdf86" stroke-width="5"/><path d="M43 43h14v25H43Z" fill="#ffeb94" stroke="#fff6cb" stroke-width="3"/>',
"hourglass":'<path d="M23 11h54M23 90h54M30 13Q27 35 50 50 73 35 70 13M30 88Q27 65 50 50 73 65 70 88" fill="none" stroke="url(#metal)" stroke-width="7"/><path d="M35 24h30L50 42Zm0 56h30L50 64Z" fill="#fff1bf"/>',
"snow":'<path d="M50 7v86M15 27l70 46M15 73l70-46M50 7l-10 13m10-13 10 13M50 93l-10-13m10 13 10-13M15 27l18 2m-18-2 6 17M85 73l-18-2m18 2-6-17M15 73l18-2m-18 2 6-17M85 27l-18 2m18-2-6 17" fill="none" stroke="url(#metal)" stroke-width="5" stroke-linecap="round"/>',
"bolt":'<path d="M57 6 20 57h28l-5 37 39-58H54Z" fill="url(#metal)" stroke="#ffedbd" stroke-width="5"/>',
"cross_swords":'<path d="m10 12 38 40-9 9L8 33Zm80 0L52 52l9 9 31-28Z" fill="url(#metal)" stroke="#fff1bb" stroke-width="4"/><path d="m31 55 14 14M55 69l14-14M38 62 20 90m42-28 18 28" stroke="#dca46b" stroke-width="8" fill="none"/>',
}
def svg(label,shape,color):
 body=SVG_SYMBOLS[shape]
 # Text in <title> is known trusted static description.
 return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img">'
 f'<title>{label}</title><defs><radialGradient id="bg"><stop stop-color="#24495b"/>'
 f'<stop offset="1" stop-color="#080f22"/></radialGradient>'
 f'<linearGradient id="metal" x2="1" y2="1"><stop stop-color="#ffffff"/>'
 f'<stop offset=".38" stop-color="{color}"/><stop offset="1" stop-color="#335576"/></linearGradient></defs>'
 f'<rect x="1" y="1" width="98" height="98" rx="16" fill="url(#bg)" stroke="{color}" stroke-width="2"/>'
 f'<circle cx="50" cy="50" r="43" fill="none" stroke="{color}" opacity=".2" stroke-width="2"/>'
 f'<g>{body}</g></svg>\n')
JS="""
// HIGHFLY_P40_ICON_ART: replace known absent images with ORIGINAL authored
// vector icon art; no CraftPix or restricted upstream asset is copied.
(function(){
'use strict';
const art=Object.freeze({
"""
JS+= "\n".join(" '"+path+"':'/highfly-icons/"+path.replace("/","__").replace(".webp",".svg")+"'," for path in ART)
JS+="""
});
function fix(e){
 const img=e.target;if(!(img instanceof HTMLImageElement))return;
 if(img.dataset.highflyP40Applied)return;
 let path='';try{path=new URL(img.currentSrc||img.src,location.href).pathname.replace(/^\\/+/, '');}catch(_){return;}
 const fallback=art[path];if(!fallback)return;
 img.dataset.highflyP40Applied='1';
 img.src=fallback;
}
document.addEventListener('error',fix,true);
})();
"""
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 page=STAGE/"index.html"
 original=page.read_text(encoding="utf8")
 if MARK in original or (STAGE/JS_PATH).exists():
  raise RuntimeError("P40_ALREADY_APPLIED")
 if original.count("</head>")!=1:raise RuntimeError("P40_HTML_HEAD_DRIFT")
 new=original.replace("</head>",'<script defer src="/highfly_p40_icons.js"></script>\n</head>')
 assets={}
 for url,(label,shape,color) in ART.items():
  filename="public/highfly-icons/"+url.replace("/","__").replace(".webp",".svg")
  dest=STAGE/filename
  if dest.exists() or dest.is_symlink():raise RuntimeError("P40_ASSET_ALREADY_EXISTS "+filename)
  assets[filename]=svg(label,shape,color)
 if apply:
  backup=OUT/"backups/index.html"
  if backup.exists() or backup.is_symlink():raise RuntimeError("P40_BACKUP_EXISTS")
  backup.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(page,backup)
  if hashlib.sha256(page.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
   raise RuntimeError("P40_BACKUP_HASH_FAIL")
  for rel,text in assets.items():
   dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open("x",encoding="utf8") as f:f.write(text)
  script=STAGE/JS_PATH;script.write_text(JS,encoding="utf8")
  page.write_text(new,encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 status={"phase":"P40_ORIGINAL_ICONS","mode":"APPLY" if apply else "DRY_RUN",
         "icons":len(assets),"paths":list(ART),"copiedRestrictedArt":False,
         "browserIconDisplayVerified":False}
 (OUT/"P40_STATUS.json").write_text(json.dumps(status,indent=2,ensure_ascii=False)+"\n")
 print("[HIGHFLY] P40 ICONS: "+json.dumps({"mode":status["mode"],"icons":len(assets),
  "licensed":"Original HIGHFLY vector artwork, no external dependency"}))
 return status
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
