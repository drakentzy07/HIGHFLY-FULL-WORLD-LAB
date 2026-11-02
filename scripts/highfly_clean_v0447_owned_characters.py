#!/usr/bin/env python3
"""Import exactly named CHARACTER/WEAPON GLBs from user's private KayKit SOURCE V7.

Acts ONLY on the NEW .workspace/highfly-origin-clean-0447 lab.
No media from ClaudeCraft, no geometric fallback, no generated game source.
Reject ambiguous stems, non-KayKit packs, non-skinned bodies and bad GLBs.
Default dry-run. --apply adds only missing, exact approved models to clean lab.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
import argparse,hashlib,json,os,re
from pathlib import Path
import shutil,struct,subprocess,sys,tempfile,zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p12_world_kaykit_batch as p12
import highfly_p23_real_kaykit_upgrade as p23
import highfly_p21_runtime_asset_recovery as p21

WORK=ROOT/".workspace"
ARCHIVE=WORK/"private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
ORIGINAL=WORK/"claudecraft-v0.44.7"
LAB=WORK/"highfly-origin-clean-0447"
REPORT=WORK/"reports/highfly-clean-0447/OWNED_KAYKIT_CHARACTERS.json"
REPAIR_REPORT=WORK/"reports/highfly-clean-0447/OWNED_KAYKIT_CHARACTERS_REPAIR.json"
# Character source is exact stem in the owned zip, not an arbitrary visual match.
# These 7 rigs are shared by the 9 native character classes in ClaudeCraft 0.44.7.
BODIES={
 "models/chars/players/knight.glb":"knight",
 "models/chars/players/mage.glb":"mage",
 "models/chars/players/rogue.glb":"rogue",
 "models/chars/players/barbarian.glb":"barbarian",
 "models/chars/players/paladin.glb":"paladin",
 "models/chars/players/ranger.glb":"ranger",
 "models/chars/players/druid.glb":"druid",
}
WEAPONS={
 "models/weapons/sword_1handed.glb":"sword_1handed",
 "models/weapons/sword_2handed.glb":"sword_2handed",
 "models/weapons/staff.glb":"staff",
 "models/weapons/wand.glb":"wand",
 "models/weapons/dagger.glb":"dagger",
 "models/weapons/axe_1handed.glb":"axe_1handed",
 "models/weapons/crossbow_2handed.glb":"crossbow_2handed",
}
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as stream:
  for part in iter(lambda:stream.read(1024*1024),b""):h.update(part)
 return h.hexdigest()

def glb_metadata(file):
 with file.open("rb") as f:
  head=f.read(20)
  if len(head)!=20:return {"valid":False}
  magic,version,length=struct.unpack("<4sII",head[:12])
  size=struct.unpack("<I",head[12:16])[0]
  if magic!=b"glTF" or version!=2 or length!=file.stat().st_size or head[16:20]!=b"JSON":
   return {"valid":False}
  if size>8_000_000:return {"valid":False}
  raw=f.read(size)
 doc=json.loads(raw.decode("utf8"))
 return {"valid":True,"skinnedMeshes":sum("skin" in node for node in doc.get("nodes",[])),
   "animations":len(doc.get("animations",[])),"meshes":len(doc.get("meshes",[])),
   "scenes":len(doc.get("scenes",[]))}

def preflight():
 for p in (LAB,ORIGINAL,WORK/"private-imports"):
  if p.is_symlink() or not p.is_dir() or not p.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError("CLEAN_OWNED_UNSAFE_DIR_"+str(p))
 if not ARCHIVE.is_file() or ARCHIVE.is_symlink():
  raise RuntimeError("CLEAN_OWNED_SOURCE_V7_ARCHIVE_MISSING")
 if not (LAB/"index.html").is_file() or not (LAB/"src/main.ts").is_file():
  raise RuntimeError("CLEAN_OWNED_NEW_LAB_NOT_PREPARED")
 if REPAIR_REPORT.exists() or REPAIR_REPORT.is_symlink():
  raise RuntimeError("CLEAN_OWNED_REPAIR_ALREADY_DONE_NO_OVERWRITE")
 if REPORT.is_symlink():
  raise RuntimeError("CLEAN_OWNED_ORIGINAL_RECEIPT_SYMLINK")
 executable=ORIGINAL/"node_modules/.bin/gltf-transform"
 if not executable.is_file():raise RuntimeError("CLEAN_OWNED_CONVERTER_MISSING")
 if not (LAB/"public/models").is_dir():raise RuntimeError("CLEAN_OWNED_MODELS_DIR_MISSING")
 return executable

def build_catalog(z):
 # ClaudeCraft changes output paths; SOURCE V7 character models are stored in
 # Characters/gltf/{Name}.glb while source weapons are in Assets/gltf/{name}.gltf.
 # Resolve by VERIFIED pack / asset type / exact canonical filename (casefold).
 table=p12.zip_members(z)
 _,weapons=p23.zip_index(z)
 bodies={}
 for member,info in table.items():
  if not p23.safe_zip_name(member) or info.file_size>65_000_000:continue
  p=Path(member)
  if p.suffix.casefold() not in (".glb",".gltf"):continue
  if len(p.parts)<4 or tuple(x.casefold() for x in p.parts[-3:-1])!=("characters","gltf"):
   continue
  packs=[part for part in p.parts[:-3]
   if part.casefold().startswith("kaykit ")
    and not re.search(r"complete|collection|free|demo|lite|legacy|old",part,re.I)]
  if not packs:continue
  data={"member":member,"pack":packs[-1],"stem":p.stem.casefold(),
   "source":"USER_OWNED_KAYKIT_COMPLETE_SOURCE_V7"}
  bodies.setdefault(p.stem.casefold(),[]).append(data)
 return bodies,weapons

def plan():
 preflight()
 found=[];blocked=[]
 with zipfile.ZipFile(ARCHIVE) as z:
  bodies,weapons=build_catalog(z)
 for target,stem in {**BODIES,**WEAPONS}.items():
  if (LAB/"public"/target).is_file():
   found.append({"path":target,"state":"ALREADY_PRESENT"})
   continue
  options=(bodies if target in BODIES else weapons).get(stem,[])
  if len(options)!=1:
   blocked.append({"path":target,"reason":"NO_UNIQUE_EXACT_SOURCE_V7",
     "stem":stem,"candidates":[x["member"] for x in options[:8]]})
   continue
  m=options[0]
  found.append({"path":target,"state":"READY","stem":stem,"member":m["member"],"pack":m["pack"]})
 return found,blocked

def apply():
 executable=preflight()
 ready,blocked=plan()
 selected=[x for x in ready if x["state"]=="READY"]
 created=[]
 try:
  with zipfile.ZipFile(ARCHIVE) as z:
   table=p12.zip_members(z)
   with tempfile.TemporaryDirectory(prefix="hf-owned-",dir=WORK) as temp:
    work=Path(temp)
    binaries=[]
    for i,row in enumerate(selected):
     try:
      member=row["member"]
      if member.casefold().endswith(".glb"):
       source=work/("source"+str(i)+".glb")
       with z.open(table[member]) as input_file,source.open("xb") as output_file:
        shutil.copyfileobj(input_file,output_file)
       if not p12.glb_valid(source):raise RuntimeError("INVALID_OWNED_SOURCE_GLB")
      else:
       source=p12.unpack_selected(z,table,member,work/("src"+str(i)))
      built=work/("model"+str(i)+".glb")
      p=subprocess.run([str(executable),"copy",str(source),str(built)],
       cwd=ORIGINAL,encoding="utf8",capture_output=True,timeout=120)
      if p.returncode:
       raise RuntimeError("CONVERSION_FAILED "+p.stderr[-180:])
      if not p21.check_binary(built,row["path"]):
       raise RuntimeError("BAD_GLB_BINARY")
      meta=glb_metadata(built)
      if not meta["valid"] or meta["meshes"]<1:
       raise RuntimeError("NO_MESHES")
      if row["path"] in BODIES and (meta["skinnedMeshes"]<1 or meta["animations"]<1):
       raise RuntimeError("CHARACTER_NO_SKIN_OR_ANIMATION")
      binaries.append((row,built,meta,sha(built)))
     except (RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as err:
      blocked.append({"path":row["path"],"reason":"EXACT_OWNED_MODEL_UNUSABLE",
        "detail":str(err)[:280]})
      continue
    for row,built,meta,hashval in binaries:
     dest=LAB/"public"/row["path"]
     if dest.exists() or dest.is_symlink():
      raise RuntimeError("CLEAN_OWNED_TARGET_ALREADY_EXISTS "+str(dest))
     dest.parent.mkdir(parents=True,exist_ok=True)
     with dest.open("xb") as f:
      with built.open("rb") as source:shutil.copyfileobj(source,f)
     created.append(dest)
     if sha(dest)!=hashval:raise RuntimeError("CLEAN_OWNED_SHA_MISMATCH "+row["path"])
     row["sha256"]=hashval;row["glb"]=meta
  result={
   "status":"OWNED_CHARACTER_IMPORT_DONE_BROWSER_UNVERIFIED",
   "capturedUtc":datetime.now(timezone.utc).isoformat(),
   "library":"PRIVATE_USER_OWNED_KAYKIT_COMPLETE_SOURCE_V7",
   "mode":"APPLY","installed":[row for row in selected if "sha256" in row],"blocked":blocked,
   "nineClasses":[ "warrior","paladin","hunter","rogue","priest",
                    "shaman","mage","warlock","druid"],
   "npcLooksEdited":False,"gameCodeEdited":False,
   "rigRetargetConfirmed":False,"characterPreviewConfirmed":False,
   "license":"Source-owned KayKit V7; media stays in ignored private lab",
   "notes":"Missing donor animations / materials remain pending until explicitly checked"}
  output_report=REPAIR_REPORT if REPORT.exists() else REPORT
  output_report.parent.mkdir(parents=True,exist_ok=True)
  if output_report.exists() or output_report.is_symlink():
   raise RuntimeError("CLEAN_OWNED_RECEIPT_EXISTS_NO_OVERWRITE")
  output_report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
  print("[CLEAN OWNED SOURCE IMPORT] "+json.dumps({
   "installedModels":sum("sha256" in row for row in selected),"blocked":blocked,
   "existingModels":sum(r["state"]=="ALREADY_PRESENT" for r in ready),
   "report":str(output_report),"browserVerified":False},ensure_ascii=False,indent=2))
 except BaseException:
  for f in created:
   if f.is_file() and not f.is_symlink():f.unlink()
  raise

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 args=p.parse_args()
 if args.apply:apply()
 else:
  ready,blocked=plan()
  print("[CLEAN OWNED PREFLIGHT] "+json.dumps({
   "ready":sum(r["state"]=="READY" for r in ready),
   "present":sum(r["state"]=="ALREADY_PRESENT" for r in ready),
   "blocked":blocked,"sourceArchive":str(ARCHIVE),
   "originalGameFilesEdited":False},ensure_ascii=False,indent=2))
