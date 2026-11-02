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
import argparse,hashlib,json,os
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
 if REPORT.exists() or REPORT.is_symlink():
  raise RuntimeError("CLEAN_OWNED_RECEIPT_ALREADY_EXISTS")
 executable=ORIGINAL/"node_modules/.bin/gltf-transform"
 if not executable.is_file():raise RuntimeError("CLEAN_OWNED_CONVERTER_MISSING")
 if not (LAB/"public/models").is_dir():raise RuntimeError("CLEAN_OWNED_MODELS_DIR_MISSING")
 return executable

def plan():
 preflight()
 found=[];blocked=[]
 with zipfile.ZipFile(ARCHIVE) as z:
  _,catalog=p23.zip_index(z)
 for target,stem in {**BODIES,**WEAPONS}.items():
  if (LAB/"public"/target).is_file():
   found.append({"path":target,"state":"ALREADY_PRESENT"})
   continue
  options=catalog.get(stem,[])
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
     source=p12.unpack_selected(z,table,row["member"],work/("src"+str(i)))
     built=work/("model"+str(i)+".glb")
     p=subprocess.run([str(executable),"copy",str(source),str(built)],
      cwd=ORIGINAL,encoding="utf8",capture_output=True,timeout=120)
     if p.returncode:
      raise RuntimeError("CLEAN_OWNED_CONVERSION_FAILED "+row["path"]+" "+p.stderr[-350:])
     if not p21.check_binary(built,row["path"]):
      raise RuntimeError("CLEAN_OWNED_GLB_BINARY_INVALID "+row["path"])
     meta=glb_metadata(built)
     if not meta["valid"] or meta["meshes"]<1:
      raise RuntimeError("CLEAN_OWNED_GLB_NO_MESHES "+row["path"])
     if row["path"] in BODIES and (meta["skinnedMeshes"]<1 or meta["animations"]<1):
      raise RuntimeError("CLEAN_OWNED_CHARACTER_MISSING_SKIN_OR_ANIMATION "+row["path"])
     binaries.append((row,built,meta,sha(built)))
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
   "mode":"APPLY","installed":selected,"blocked":blocked,
   "nineClasses":[ "warrior","paladin","hunter","rogue","priest",
                    "shaman","mage","warlock","druid"],
   "npcLooksEdited":False,"gameCodeEdited":False,
   "rigRetargetConfirmed":False,"characterPreviewConfirmed":False,
   "license":"Source-owned KayKit V7; media stays in ignored private lab",
   "notes":"Missing donor animations / materials remain pending until explicitly checked"}
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
  print("[CLEAN OWNED SOURCE IMPORT] "+json.dumps({
   "installedModels":len(selected),"blocked":blocked,
   "existingModels":sum(r["state"]=="ALREADY_PRESENT" for r in ready),
   "report":str(REPORT),"browserVerified":False},ensure_ascii=False,indent=2))
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
