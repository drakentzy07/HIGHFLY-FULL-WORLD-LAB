#!/usr/bin/env python3
"""P44: wolf CC0 restoration + Madreperla icons + Eastbrook NPC visual variety.
Leaves P43 saves, combat, building geometry, quests, loot and player logic alone.
"""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE;ORIGINAL=p9.ORIGINAL
OUT=ROOT/".workspace/reports/highfly-p44"
MARK="HIGHFLY_P44_ORIGINAL_WOLF"
FILES=("src/render/characters/manifest.ts","src/render/characters/assets.ts",
       "src/render/assets/media.ts","src/main.ts","public/highfly_p40_icons.js")
ROLES={
 "cook_marlow":"barbarian","tanner_hesk":"barbarian",
 "weaver_ottilie":"druid","herbalist_yara":"druid",
 "alchemist_verane":"mage","apothecary_lin":"mage",
 "chronicler_saul":"mage","fisherman_brandt":"rogue",
 "scout_maren":"rogue","tinker_gizzel":"barbarian",
 "forgemistress_darva":"barbarian","brother_halven":"paladin",
 "marshal_redbrook":"knight","captain_thessaly":"knight",
 "huntsman_deral":"rogue","keeper_saelwyn":"mage",
}
ICONS={
 "ui/items/mother_of_pearl.webp":"mother_of_pearl.svg",
 "ui/items/ps_lustrous_pearl.webp":"lustrous_pearl.svg",
 "ui/items/ps_briny_lure.webp":"briny_lure.svg",
}
def h(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def once(s,old,new,why):
 n=s.count(old)
 if n!=1:raise RuntimeError("P44_ANCHOR_DRIFT "+why+" "+str(n))
 return s.replace(old,new,1)
def patch_wolf(s):
 for name in ("mob_wolf","form_ghost_wolf"):
  mm=list(re.finditer(r"(?ms)^  "+name+r": \{\n(.*?)^  \},",s))
  if len(mm)!=1:raise RuntimeError("P44_WOLF_DEFINITION_MISSING "+name)
  m=mm[0];body=m.group(1)
  if body.count("wolf_basic.glb")!=1 or body.count("clips: WOLF_BAKED")!=1:
   raise RuntimeError("P44_WOLF_DEFINITION_CHANGED "+name)
  body=body.replace("wolf_basic.glb","wolf.glb").replace(
    "clips: WOLF_BAKED","clips: animal(['Attack'])")
  if name=="mob_wolf":
   body=re.sub(r"(?m)^    authoredAtlas: true,[^\n]*\n","",body,count=1)
  body="    // "+MARK+": Quaternius original CC0, no Tripo model.\n"+body
  s=s[:m.start(1)]+body+s[m.end(1):]
 return s
def patch(x):
 if any(MARK in v for v in x.values()):raise RuntimeError("P44_ALREADY_APPLIED")
 a=patch_wolf(x[FILES[0]])
 anchor="  const npcBaseKey = NPC_KEYS[e.templateId] ?? 'npc_villager';"
 entries="\n".join("    "+json.dumps(k)+": "+json.dumps(v)+"," for k,v in ROLES.items())
 a=once(a,anchor,
   "  // HIGHFLY_P44_EASTBROOK_NPCS: individual roles, no change to interactions.\n"
   "  const highflyRole = ({\n"+entries+
   "\n  } as Record<string,string>)[e.templateId];\n"
   "  if (highflyRole) return 'highfly_npc_' + highflyRole;\n"+anchor,"npc-roles")
 b=once(x[FILES[1]],"export async function preloadHighflyCrabAssets(): Promise<void> {",
   "// "+MARK+": cache the original, source-verified CC0 creature.\n"
   "export async function preloadHighflyWolf(): Promise<void> {\n"
   "  try { await prepareCharacterUrl('models/creatures/wolf.glb'); }\n"
   "  catch (error) { console.warn('[HIGHFLY P44] wolf',error); }\n}\n"
   "export async function preloadHighflyCrabAssets(): Promise<void> {","wolf-loader")
 # P39B adds a second crab_ability_anims.glb row to the same set.
 # Anchor the SET DECLARATION, not an asset that appears more than once.
 # The P38 direct-public routing checks THIS set at runtime.
 c=once(x[FILES[2]],"const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([\n",
   "const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([\n"
   "  // "+MARK+": original Quaternius wolf, already provenance-checked.\n"
   "  'models/creatures/wolf.glb',\n","media-wolf-direct-cc0-set")
 d=once(x[FILES[3]],"  preloadHighflyCrabAssets,",
   "  preloadHighflyCrabAssets,\n  preloadHighflyWolf,","main-import")
 d=once(d,"  await preloadHighflyCrabAssets();",
   "  await preloadHighflyCrabAssets();\n"
   "  // "+MARK+"\n  await preloadHighflyWolf();","main-load")
 iconEntries="\n".join(" '"+k+"':'/highfly-icons/"+v+"'," for k,v in ICONS.items())
 e=once(x[FILES[4]],"const art=Object.freeze({",
   "const art=Object.freeze({\n  // "+MARK+" quest-specific illustrations\n"+iconEntries+"\n",
   "mother-of-pearl")
 return dict(zip(FILES,(a,b,c,d,e)))
def icon(name):
 shapes={
 "mother_of_pearl.svg":'<ellipse cx="50" cy="65" rx="25" ry="18" fill="none" stroke="#e8ba69" stroke-width="12"/><path d="M50 8 78 37 50 59 22 37Z" fill="#d5aff9" stroke="#fff" stroke-width="4"/>',
 "lustrous_pearl.svg":'<path d="M10 74Q35 19 50 25q30 7 40 49-40 24-80 0Z" fill="#d8a88b" stroke="#fff2cc" stroke-width="4"/><circle cx="50" cy="51" r="22" fill="#defcff" stroke="white" stroke-width="4"/>',
 "briny_lure.svg":'<path d="M32 17h36v54Q50 92 32 71Z" fill="#52baac" stroke="#e2fff9" stroke-width="5"/><circle cx="50" cy="48" r="12" fill="#f9df8d"/>'
 }
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="14" fill="#102237" stroke="#b3a0df" stroke-width="3"/>'+shapes[name]+'</svg>\n'
def provenance():
 spec=json.loads((ORIGINAL/"scripts/assets/specs/characters.json").read_text(encoding="utf8"))
 xs=[r.get("src") for r in spec["items"] if r.get("out")=="models/creatures/wolf.glb"]
 if xs!=["tmp/asset_src/quaternius_creatures/Wolf.glb"]:raise RuntimeError("P44_UNVERIFIED_WOLF_SOURCE")
 credits=(ORIGINAL/"CREDITS.md").read_text(encoding="utf8")
 if not any("Animated creatures (wolf" in line and "| CC0 1.0 | Yes |" in line for line in credits.splitlines()):
  raise RuntimeError("P44_UNVERIFIED_WOLF_LICENSE")
 a=ORIGINAL/"public/models/creatures/wolf.glb"
 b=STAGE/"public/models/creatures/wolf.glb"
 if not a.is_file() or a.is_symlink() or a.open("rb").read(4)!=b"glTF":raise RuntimeError("P44_ORIGINAL_WOLF_MISSING")
 if b.is_symlink() or (b.exists() and (not b.is_file() or h(a)!=h(b))):
  raise RuntimeError("P44_STAGE_WOLF_CONFLICT")
 return a,b
def eastbrook_audit():
 results=[]
 for name in p9.BUILDING_NAMES:
  file=STAGE/"public/models/biome"/name
  row={"model":name,"bytes":file.stat().st_size if file.is_file() else None}
  if file.is_file():
   try:
    with file.open("rb") as f:
     hd=f.read(20);magic,version,total,n,typ=struct.unpack("<4sIIII",hd)
     if magic==b"glTF" and typ==0x4e4f534a:
      j=json.loads(f.read(n));v=[]
      for mesh in j.get("meshes",[]):
       for primitive in mesh.get("primitives",[]):
        ix=primitive.get("attributes",{}).get("POSITION")
        if isinstance(ix,int) and ix<len(j.get("accessors",[])):
         obj=j["accessors"][ix]
         if "min" in obj and "max" in obj:v.append((obj["min"],obj["max"]))
      if v:row["rawMeshExtents"]=[round(max(x[1][i] for x in v)-min(x[0][i] for x in v),2) for i in range(3)]
   except (ValueError,IndexError,struct.error) as err:row["error"]=str(err)
  results.append(row)
 return results
def run(apply=False):
 p9.preflight(ORIGINAL,STAGE,p9.REPORT)
 wolf_source,wolf_stage=provenance()
 inputs={}
 for rel in FILES:
  file=STAGE/rel
  if not file.is_file() or file.is_symlink():raise RuntimeError("P44_MISSING_STAGE_SOURCE "+rel)
  inputs[rel]=file.read_text(encoding="utf8")
 outputs=patch(inputs)
 new=[STAGE/"public/highfly-icons"/name for name in ICONS.values()]
 if any(x.exists() or x.is_symlink() for x in new):raise RuntimeError("P44_ALREADY_HAS_ICONS")
 audit=eastbrook_audit()
 if apply:
  for rel in FILES:
   bak=OUT/"backups"/rel
   if bak.exists() or bak.is_symlink():raise RuntimeError("P44_BACKUP_EXISTS "+rel)
  for rel in FILES:
   source=STAGE/rel;backup=OUT/"backups"/rel
   backup.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source,backup)
   if h(source)!=h(backup):raise RuntimeError("P44_BAD_BACKUP "+rel)
  if not wolf_stage.exists():
   wolf_stage.parent.mkdir(parents=True,exist_ok=True)
   with wolf_source.open("rb") as s,wolf_stage.open("xb") as d:shutil.copyfileobj(s,d)
  if h(wolf_source)!=h(wolf_stage):raise RuntimeError("P44_BAD_WOLF_COPY")
  for name in ICONS.values():
   target=STAGE/"public/highfly-icons"/name;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open("x",encoding="utf8") as dest:dest.write(icon(name))
  for rel in FILES:
   src=STAGE/rel
   if src.read_text(encoding="utf8")!=inputs[rel]:raise RuntimeError("P44_CONCURRENT_EDIT "+rel)
   src.write_text(outputs[rel],encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 result={"phase":"P44_WORLD_VISUAL_FIX","mode":"APPLY" if apply else "DRY_RUN",
  "quaterniusWolfOriginal":"models/creatures/wolf.glb",
  "wolfSourceVerifiedCC0":True,"npcRoleOverrides":len(ROLES),
  "questIconsCreated":len(ICONS),"eastbrookBuildingMeshDiagnostics":audit,
  "giantBlockCauseKnown":False,"worldTransformsUnchanged":True,
  "rpgOrOfflineSaveChanged":False,"browserVerified":False,
  "timestampUtc":datetime.now(timezone.utc).isoformat()}
 (OUT/"P44_REPORT.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("[HIGHFLY] P44: "+json.dumps({k:v for k,v in result.items() if k!="eastbrookBuildingMeshDiagnostics"},ensure_ascii=False))
 print("[HIGHFLY] P44 EASTBROOK GLB BOUNDS: "+json.dumps(audit,ensure_ascii=False))
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
