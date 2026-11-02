#!/usr/bin/env python3
"""HIGHFLY CLEAN — rebuild v0.44.7 native player bodies from OWNED KayKit SOURCE V7.

Correct upstream recipe: scripts/assets/specs/characters_v2.json says KayKit
Adventurers 2.0 bodies carry ZERO animations. ClaudeCraft's pinned MIT
scripts/assets/build_assets.mjs merges 6 Rig_Medium donor GLBs and renames the
clips. A bare gltf-transform copy is NOT equivalent. This script runs that
verified pipeline, with --output-root set to a private TEMP dir.
Only the NEW clean lab can receive outputs. No model name guessing.
Dry-run is read only; --apply [--only knight] builds verified matching models.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p12_world_kaykit_batch as p12
import highfly_p23_real_kaykit_upgrade as p23

WORK=ROOT/".workspace"
SOURCE=WORK/"claudecraft-v0.44.7"
LAB=WORK/"highfly-origin-clean-0447"
ZIP=WORK/"private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
SPEC=SOURCE/"scripts/assets/specs/characters_v2.json"
PIPELINE=SOURCE/"scripts/assets/build_assets.mjs"
REPORT_DIR=WORK/"reports/highfly-clean-0447"
PIN="493c35a108cef6c8aa290e8793107b1cd117886e"
ALLOWED={"knight","mage","barbarian","rogue","rogue_hooded","druid","ranger","paladin"}
MAX_ZIP_FILE=60_000_000
MAX_ITEMS=12

def digest(file):
 h=hashlib.sha256()
 with file.open("rb") as stream:
  for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def parse_glb(file):
 try:
  if not file.is_file():return {"valid":False,"reason":"MISSING"}
  with file.open("rb") as fp:
   head=fp.read(20)
   if len(head)!=20 or head[:4]!=b"glTF":
    return {"valid":False,"reason":"NOT_GLB2"}
   magic,version,total=struct.unpack("<4sII",head[:12])
   json_length=struct.unpack("<I",head[12:16])[0]
   if version!=2 or total!=file.stat().st_size or head[16:20]!=b"JSON" or json_length>12_000_000:
    return {"valid":False,"reason":"BAD_HEADER"}
   d=json.loads(fp.read(json_length).decode("utf8"))
  clips=[x.get("name","") for x in d.get("animations",[])]
  skinned=sum("skin" in n for n in d.get("nodes",[]))
  return {"valid":True,"meshes":len(d.get("meshes",[])),
   "skins":len(d.get("skins",[])),"nodesWithSkin":skinned,
   "animations":len(clips),"clipNames":clips[:90],"scenes":len(d.get("scenes",[]))}
 except (OSError,ValueError,UnicodeDecodeError,struct.error) as e:
  return {"valid":False,"reason":str(e)[:120]}

def safe_pack(member):
 if not p23.safe_zip_name(member):return False
 parts=PurePosixPath(member).parts
 return len(parts)>=5 and any(
  p.casefold().startswith("kaykit ") and
  not any(w in p.casefold() for w in ("complete","collection","free","demo","legacy"))
  for p in parts[:-3])

def match_exact_member(table,spec_source,kind):
 # Match the exact ending of the original pinned conversion recipe; the user's
 # ZIP may have a different wrapper directory. NEVER trust that wrapper.
 rel=PurePosixPath(spec_source)
 if rel.suffix.lower() not in {".glb",".gltf"}:return [],"UNSUPPORTED_SPEC_INPUT"
 tail=tuple(p.casefold() for p in rel.parts[-3:])
 hits=[]
 for member,info in table.items():
  p=PurePosixPath(member)
  if not safe_pack(member) or info.file_size>MAX_ZIP_FILE:continue
  if tuple(a.casefold() for a in p.parts[-3:])!=tail:continue
  parents=" ".join(x.casefold() for x in p.parts[:-3])
  if kind=="body":
   if ("adventurers" not in parents and "paladin" not in parents):continue
   if "paladin" in tail[-1] and "paladin" not in parents:continue
   if "paladin" not in tail[-1] and "adventurers" not in parents:continue
  elif kind=="donor":
   if "character animations" not in parents:continue
  hits.append(member)
 return hits,None

def preflight():
 for folder in (WORK,SOURCE,LAB,WORK/"private-imports"):
  if folder.is_symlink() or not folder.is_dir() or not folder.resolve().is_relative_to(WORK.resolve()):
   raise RuntimeError("CLEAN_ANIMS_UNSAFE_OR_MISSING_DIR "+str(folder))
 for file in (ZIP,SPEC,PIPELINE,LAB/"index.html",LAB/"src/main.ts"):
  if file.is_symlink() or not file.is_file():
   raise RuntimeError("CLEAN_ANIMS_REQUIRED_SOURCE_MISSING "+str(file))
 sha=subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],text=True).strip()
 if sha!=PIN:raise RuntimeError("CLEAN_ANIMS_PINNED_REFERENCE_CHANGED")
 if not (SOURCE/"node_modules/@gltf-transform/functions").is_dir():
  raise RuntimeError("CLEAN_ANIMS_TRANSFORM_DEPENDENCIES_MISSING")
 spec=json.loads(SPEC.read_text("utf8"))
 defaults=spec.get("defaults",{})
 if len(spec.get("items",[]))!=8 or len(defaults.get("addClipsFrom",[]))!=6:
  raise RuntimeError("CLEAN_ANIMS_SPEC_VERSION_UNEXPECTED")
 if not defaults.get("renameClips") or not defaults.get("keepClips"):
  raise RuntimeError("CLEAN_ANIMS_ORIGINAL_ANIMATION_RECIPE_MISSING")
 for item in spec["items"]:
  out=item.get("out","")
  if not re.fullmatch(r"models/chars/players/[a-z_]+\.glb",out):
   raise RuntimeError("CLEAN_ANIMS_UNEXPECTED_OUTPUT_PATH")
  if Path(out).stem not in ALLOWED:
   raise RuntimeError("CLEAN_ANIMS_UNEXPECTED_OUTPUT_CLASS")
 return spec

def assess():
 spec=preflight()
 with zipfile.ZipFile(ZIP) as z:
  table=p12.zip_members(z)
  donors={}
  donor_errors={}
  for source in spec["defaults"]["addClipsFrom"]:
   hits,problem=match_exact_member(table,source,"donor")
   if len(hits)==1:donors[source]=hits[0]
   else:donor_errors[source]={"reason":problem or ("AMBIGUOUS" if hits else "ABSENT"),
     "candidates":hits[:8]}
  entries=[]
  for item in spec["items"]:
   target=item["out"]
   stem=Path(target).stem
   destination=LAB/"public"/target
   if destination.exists() or destination.is_symlink():
    stat=parse_glb(destination)
    # Presence alone is not proof: preserve it, don't overwrite.
    entries.append({"target":target,"stem":stem,"status":"ALREADY_PRESENT_REVIEW",
      "glb":{k:v for k,v in stat.items() if k!="clipNames"}})
    continue
   hits,problem=match_exact_member(table,item["src"],"body")
   if len(hits)!=1:
    entries.append({"target":target,"stem":stem,
      "status":"SOURCE_AMBIGUOUS" if hits else "SOURCE_NOT_IN_OWNED_V7",
      "expected":item["src"],"candidates":hits[:8]})
    continue
   if donor_errors:
    entries.append({"target":target,"stem":stem,"status":"ANIMATION_LIBRARIES_MISSING",
     "sourceMember":hits[0],"missingDonors":list(donor_errors)})
    continue
   entries.append({"target":target,"stem":stem,"status":"READY",
    "sourceMember":hits[0],
    "donorCount":len(donors)})
 return spec,entries,donors,donor_errors

def extract_member(z,table,member,folder):
 # Source GLB: exact file copy to private TEMP; glTF: validated pack-scoped
 # external dependencies via the pre-existing P12 safe extractor.
 if member.casefold().endswith(".gltf"):
  return p12.unpack_selected(z,table,member,folder)
 dest=folder/"input.glb"
 dest.parent.mkdir(parents=True,exist_ok=True)
 with z.open(table[member]) as src,dest.open("xb") as out:
  shutil.copyfileobj(src,out)
 if not p12.glb_valid(dest):
  raise RuntimeError("CLEAN_ANIMS_OWNED_INPUT_INVALID_GLB "+member)
 return dest

def build(only=None):
 spec,entries,donors,donor_errors=assess()
 chosen=[r for r in entries if r["status"]=="READY" and (only is None or r["stem"]==only)]
 outcomes=[]
 with zipfile.ZipFile(ZIP) as z:
  table=p12.zip_members(z)
  with tempfile.TemporaryDirectory(prefix="hf-clean-animated-",dir=WORK) as td:
   tmp=Path(td)
   extracted_donors={}
   if chosen:
    for i,(source,member) in enumerate(donors.items()):
     extracted_donors[source]=extract_member(z,table,member,tmp/"donors"/str(i))
   for idx,row in enumerate(chosen):
    body=extract_member(z,table,row["sourceMember"],tmp/"bodies"/str(idx))
    out=tmp/"outputs"/str(idx)
    recipe=tmp/("recipe-"+str(idx)+".json")
    defaults={**spec["defaults"],
      "addClipsFrom":[str(extracted_donors[x]) for x in spec["defaults"]["addClipsFrom"]]}
    item=next(x for x in spec["items"] if x["out"]==row["target"])
    recipe.write_text(json.dumps({"defaults":defaults,
     "items":[{**item,"src":str(body)}]}),encoding="utf8")
    command=["node",str(PIPELINE),str(recipe),"--output-root",str(out)]
    run=subprocess.run(command,cwd=SOURCE,encoding="utf8",capture_output=True,timeout=240)
    built=out/row["target"]
    if run.returncode:
     outcomes.append({"path":row["target"],"status":"CONVERSION_FAILED",
      "stderr":run.stderr[-1200:],"stdout":run.stdout[-900:]})
     continue
    meta=parse_glb(built)
    clipnames=set(meta.get("clipNames",[]))
    if not meta["valid"] or meta["meshes"]<1 or meta["skins"]<1 or meta["nodesWithSkin"]<1:
     outcomes.append({"path":row["target"],"status":"OUTPUT_NO_VALID_SKIN",
      "metadata":meta})
     continue
    required={"Idle","Walking_A","Running_A"}
    if not required.issubset(clipnames) or meta["animations"]<8:
     outcomes.append({"path":row["target"],"status":"OUTPUT_ANIMATION_CONTRACT_MISSING",
      "metadata":meta})
     continue
    dest=LAB/"public"/row["target"]
    if dest.exists() or dest.is_symlink():
     outcomes.append({"path":row["target"],"status":"CONCURRENT_DESTINATION_EXISTS"})
     continue
    dest.parent.mkdir(parents=True,exist_ok=True)
    built_hash=digest(built)
    with dest.open("xb") as outf,built.open("rb") as inf:
     shutil.copyfileobj(inf,outf)
    if digest(dest)!=built_hash:
     dest.unlink(missing_ok=True)
     raise RuntimeError("CLEAN_ANIMS_OUTPUT_HASH_CHANGED "+row["target"])
    outcomes.append({"path":row["target"],"status":"INSTALLED",
     "modelSha256":built_hash,"originalSourceMember":row["sourceMember"],
     "animationSourceMembers":list(donors.values()),"metadata":meta})
 name="ANIMATED_KAYKIT_"+(only or "ALL")+"_RESULT.json"
 report=REPORT_DIR/name
 if report.exists() or report.is_symlink():
  raise RuntimeError("CLEAN_ANIMS_REPORT_ALREADY_EXISTS")
 REPORT_DIR.mkdir(parents=True,exist_ok=True)
 report.write_text(json.dumps({"phase":"CLEAN_NATIVE_NINE_CLASS_ANIMATED_CHARACTERS",
   "createdUtc":datetime.now(timezone.utc).isoformat(),
   "mode":"APPLY","nativeSpec":"scripts/assets/specs/characters_v2.json",
   "pipeline":"scripts/assets/build_assets.mjs",
   "pinnedOriginalSourceUntouched":True,"allMediaUserOwnedSourceV7":True,
   "donorCount":len(donors),"donorIssues":donor_errors,
   "outputs":outcomes,"otherStagesModified":False,
   "gameplayVerified":False},indent=2,ensure_ascii=False)+"\n","utf8")
 print("[CLEAN ANIMATED] "+json.dumps({
  "ready":len(chosen),"installed":sum(x["status"]=="INSTALLED" for x in outcomes),
  "results":[{"path":x["path"],"status":x["status"]} for x in outcomes],
  "report":str(report),"sourceModified":False,"browserVerified":False
 },indent=2,ensure_ascii=False))
 return outcomes

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 p.add_argument("--only",choices=sorted(ALLOWED))
 args=p.parse_args()
 if args.apply:
  build(args.only);return
 spec,rows,donors,problems=assess()
 print("[CLEAN ANIMATED PREFLIGHT] "+json.dumps({
  "origin":"Original ClaudeCraft 0.44.7 MIT build_assets.mjs + exact character_v2.json",
  "ownedArchive":str(ZIP),"donorsFound":len(donors),"donorsNeeded":6,
  "donorIssues":problems,"models":rows,
  "mode":"DRY_RUN","codeEdited":False
 },indent=2,ensure_ascii=False))

if __name__=="__main__":main()
