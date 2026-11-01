#!/usr/bin/env python3
"""HIGHFLY P49 - READ-ONLY audit: no ripgrep, no stage edits or build.

Inspect EXACT staged source references for unwanted overlays, P46-P48 skins,
mobile input, Eastbrook building models, jabalíes/boars, loot and boats.
Writes only .workspace/reports/highfly-p49/P49_AUDIT.json.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse, json, re
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/".workspace/highfly-origin-stage-p0"
REPORT=ROOT/".workspace/reports/highfly-p49/P49_AUDIT.json"
EXTS={".ts",".tsx",".js",".mjs",".css",".html",".json"}
GROUPS={
 "OVERLAYS_DEBUG":[r"HIGHFLY\s*P35",r"NPC/BOLSA",r"HIGHFLY\s*LOG",r"highfly.?log",r"debug.?overlay",r"fallos",r"diagnostic"],
 "SPLASH_CREATOR_LOADING":[r"hf-p46-entry",r"mode-select",r"highfly-p46-landing",r"highfly_loading_bg",r"highfly_splash\.png",r"ls-progress",r"ls-tip",r"ls-fill",r"offline-appearance"],
 "MOBILE_FURY":[r"isMoveAutorunPush",r"setAutorun\(",r"mobile-dodge",r"BACKPEDAL_MULT",r"furyDashing",r"highflyAirJumps",r"mobile-action-attack",r"mobile-jump",r"mobile-interact",r"CLIMB_BODY_PITCH"],
 "EASTBROOK_GIANT":[r"EASTBROOK_LAYOUT\.buildings",r"buildKitBuilding\(",r"buildBuilding\(",r"highflyP45CheckBuilding",r"hexb_townhall",r"hexb_workshop",r"hexb_tavern",r"hex_church",r"eastbrook.*placeholder",r"eastbrook.*proxy"],
 "BOAR_WOLF":[r"mob_boar",r"WILD_BOAR",r"wild_boar\.glb",r"mob_wolf",r"wolf_basic\.glb",r"creatures/wolf\.glb"],
 "LOOT_ICONS":[r"highfly/p47-icons",r"highfly_p40_icons",r"ui/items/",r"mother_of_pearl",r"ps_lustrous_pearl",r"loot.*icon"],
 "WATER_BOATS":[r"swimPitch",r"advanceSwimPitch",r"buildHarbor",r"ship.*\.glb",r"boat.*\.glb",r"harbor.*\.glb"],
}
PATTERNS={k:re.compile("|".join("(?:"+pat+")" for pat in ps),re.I) for k,ps in GROUPS.items()}
ASSETS=[
 "public/highfly/official/highfly_splash.png",
 "public/highfly/official/highfly_enter_world_bg.png",
 "public/highfly/official/highfly_loading_bg.png",
 "public/models/creatures/wolf.glb",
 "public/models/creatures/wild_boar.glb",
 "public/highfly/p47.css",
 "public/highfly/p48.css",
]
def candidates():
 for base in (STAGE/"src",STAGE/"public",STAGE/"index.html"):
  if base.is_file():yield base
  elif base.is_dir():
   for f in base.rglob("*"):
    if f.is_file() and not f.is_symlink() and f.suffix.lower() in EXTS:yield f
def inspection():
 examples=defaultdict(list);counts=defaultdict(int);located=defaultdict(set);nfiles=0
 for f in candidates():
  try:
   if f.stat().st_size>1_500_000:continue
   lines=f.read_text(encoding="utf8").splitlines()
  except (OSError,UnicodeError):continue
  nfiles+=1;name=str(f.relative_to(STAGE))
  for line_number,line in enumerate(lines,1):
   for category,pat in PATTERNS.items():
    if pat.search(line):
     counts[category]+=1;located[category].add(name)
     if len(examples[category])<24:
      examples[category].append({"file":name,"line":line_number,"text":line.strip()[:190]})
 return nfiles,{cat:{"count":counts[cat],"files":sorted(located[cat])[:35],"examples":examples[cat]} for cat in GROUPS}
def has(rel,pattern):
 f=STAGE/rel
 return f.is_file() and pattern.lower() in f.read_text(encoding="utf8").lower()
def report():
 if not (STAGE/"index.html").is_file():
  raise RuntimeError("P49: falta index.html del stage; no se modifico nada")
 n,data=inspection()
 flags={
  "P46":has("index.html","HIGHFLY_P46_OFFICIAL_IDENTITY"),
  "P47":has("index.html","HIGHFLY_P47_UI_LOOT_REAL_EDITOR"),
  "P48":has("index.html","HIGHFLY_P48_FURY_MOBILE"),
  "realDash":has("src/sim/player_motion.ts","furyDashing"),
  "noJoystickAutorun":has("src/game/mobile_controls.ts","no autorun from joystick overshoot"),
 }
 files={a:{"exists":(STAGE/a).is_file(),"bytes":(STAGE/a).stat().st_size if (STAGE/a).is_file() else None} for a in ASSETS}
 geometry=[]
 saved=ROOT/".workspace/reports/highfly-p44/P44_REPORT.json"
 if saved.is_file():
  try:geometry=json.loads(saved.read_text(encoding="utf8")).get("eastbrookBuildingMeshDiagnostics",[])
  except (OSError,ValueError):pass
 output={"phase":"P49_READ_ONLY","scanned":n,"timeUtc":datetime.now(timezone.utc).isoformat(),"flags":flags,"assets":files,"p44BuildingBounds":geometry,"topics":data,"mutatedGame":False}
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print("[HIGHFLY P49] AUDITORIA SOLO LECTURA - no se modifico el juego")
 print("Archivos inspeccionados:",n)
 print("Estado:",json.dumps(flags))
 for name,status in files.items():print("ACTIVO" if status["exists"] else "FALTA",name)
 if geometry:print("Dimensiones GLB P44:",json.dumps(geometry,ensure_ascii=False)[:1500])
 for title,info in data.items():
  print("\n==",title,"(",info["count"],"referencias) ==")
  for row in info["examples"][:11]:
   print(row["file"]+":"+str(row["line"]),row["text"][:118])
 print("\nREPORTE COMPLETO:",REPORT)
 print("No aplica parches ni toca partidas, tutorial, modelos o compilacion.")
if __name__=="__main__":
 ap=argparse.ArgumentParser(description=__doc__)
 ap.parse_args()
 report()
