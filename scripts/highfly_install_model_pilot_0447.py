#!/usr/bin/env python3
"""Install KayKit v7 3D viewer into PRIVATE ClaudeCraft v0.44.7 checkout.

Only changes the GITIGNORED .workspace/claudecraft-v0.44.7 clone. Existing world
gameplay, NPCs, quests, character saves and player creation are NOT edited.
Media NEVER enters GitHub; build/preview port must remain PRIVATE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess

PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/".workspace/claudecraft-v0.44.7"
KAYKIT=ROOT/".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
PILOT="highfly-private-pilot"
MANIFEST_NAME="manifest.json"

def glb_valid(path:Path)->bool:
    if not path.is_file() or path.is_symlink():return False
    n=path.stat().st_size
    if n<20:return False
    with path.open("rb") as f:
        header=f.read(12)
    return header[:4]==b"glTF" and int.from_bytes(header[4:8],"little")==2 and int.from_bytes(header[8:12],"little")==n

def choose_model(pack: Path, role: str) -> Path:
    if not pack.is_dir():raise FileNotFoundError("KayKit pack missing: "+str(pack))
    found=[]
    for p in pack.rglob("*.glb"):
        if p.is_symlink() or any(x.is_symlink() for x in p.parents if x!=pack):
            continue
        name=p.stem.lower()
        parent=p.as_posix().lower()
        score=0
        if "/assets/gltf/" in parent: score+=20
        if "/animations/" in parent: score-=25
        if "/rig_medium/" in parent: score-=15
        if role=="hero":
            for hint,weight in (("knight",14),("barbarian",12),("ranger",10),("mage",8),("rogue",8)):
                if hint in name:score+=weight
        else:
            for hint,weight in (("skeleton_minion",15),("skeleton_warrior",13),("skeleton",8),("minion",5)):
                if hint in name:score+=weight
        if "_anim" in name or "movement" in name:score-=40
        if glb_valid(p):found.append((-score,p.as_posix().lower(),p))
    if not found:raise FileNotFoundError(f"No valid .glb found in {pack}; keep original files and inspect formats")
    found.sort()
    return found[0][2]

def donor_animation(pack: Path)->Path|None:
    matches=list(pack.glob("Animations/gltf/Rig_Medium/Rig_Medium_General.glb"))
    return matches[0] if matches and glb_valid(matches[0]) else None

def sha256(file:Path)->str:
    h=hashlib.sha256()
    with file.open("rb") as f:
        while (b:=f.read(1024*1024)):h.update(b)
    return h.hexdigest()

def put_unmodified(from_file:Path, to_file:Path)->None:
    to_file.parent.mkdir(parents=True,exist_ok=True)
    if to_file.exists():
        if to_file.is_symlink() or sha256(from_file)!=sha256(to_file):
            raise FileExistsError("Refusing to overwrite mismatched file: "+str(to_file))
        return
    shutil.copy2(from_file,to_file)

def plan(upstream:Path=UPSTREAM,kaykit:Path=KAYKIT)->dict:
    if not (upstream/".git").is_dir():raise FileNotFoundError("Original private v0.44.7 checkout missing")
    sha=subprocess.check_output(["git","-C",str(upstream),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise ValueError("Wrong upstream version: expected v0.44.7")
    if not str(upstream.resolve()).startswith(str((ROOT/".workspace").resolve())+"/"):
        raise ValueError("Expected ignored .workspace checkout")
    hero=choose_model(kaykit/"KayKit Adventurers 2.0","hero")
    skeleton=choose_model(kaykit/"KayKit Skeletons 1.1","skeleton")
    donor=donor_animation(kaykit/"KayKit Adventurers 2.0")
    models=[
        {"key":"hero","title":"Adventurer · "+hero.stem,"source":str(hero),"file":f"/{PILOT}/hero.glb",
         "sha256":sha256(hero),"donor":f"/{PILOT}/rig_medium_animations.glb" if donor else None},
        {"key":"skeleton","title":"Skeleton · "+skeleton.stem,"source":str(skeleton),
         "file":f"/{PILOT}/skeleton.glb","sha256":sha256(skeleton),"donor":None},
    ]
    return {"project":"HIGHFLY ORIGIN", "sourceCommit":PIN,
            "status":"PRIVATE_ONLY_NO_REDISTRIBUTION", "models":models,
            "donorSource":str(donor) if donor else None}

def install(preview:dict, upstream:Path=UPSTREAM)->None:
    # Fail-closed: exact Vite input line. Never touch source gameplay code.
    vite=upstream/"vite.config.ts"
    current=vite.read_text(encoding="utf8")
    target="        editor: fileURLToPath(new URL('editor.html', import.meta.url)),"
    replacement=target+"\n        highflyKaykit: fileURLToPath(new URL('highfly-kaykit-pilot.html', import.meta.url)),"
    if replacement not in current:
        if current.count(target)!=1:raise ValueError("UPSTREAM_VITE_CONFIG_CHANGED")
        current=current.replace(target,replacement,1)
    # Verify all destination files before changing anything.
    dests=[
        (ROOT/"pilot/highfly-kaykit-pilot.html",upstream/"highfly-kaykit-pilot.html"),
        (ROOT/"pilot/highfly_kaykit_pilot.ts",upstream/"src/highfly_kaykit_pilot.ts"),
    ]
    media=upstream/"public"/PILOT
    for model in preview["models"]:
        dests.append((Path(model["source"]),media/(model["key"]+".glb")))
    if preview["donorSource"]:
        dests.append((Path(preview["donorSource"]),media/"rig_medium_animations.glb"))
    for original,dest in dests:
        if not original.is_file() or original.is_symlink():raise FileNotFoundError("Missing source: "+str(original))
        if dest.exists() and (dest.is_symlink() or sha256(original)!=sha256(dest)):
            raise FileExistsError("Existing pilot file is different: "+str(dest))
    manifest=media/MANIFEST_NAME
    sanitized={
        "project":preview["project"],"sourceCommit":PIN,
        "status":"PRIVATE_ONLY_NO_REDISTRIBUTION",
        "models":[{k:v for k,v in model.items() if k!="source" and k!="sha256"}
                  for model in preview["models"]]}
    expected=json.dumps(sanitized,ensure_ascii=False,indent=2)+"\n"
    if manifest.exists() and manifest.read_text(encoding="utf8")!=expected:
        raise FileExistsError("Existing pilot manifest differs; refuse to overwrite")
    for original,dest in dests:
        put_unmodified(original,dest)
    media.mkdir(parents=True,exist_ok=True)
    if not manifest.exists():manifest.write_text(expected,encoding="utf8")
    if vite.read_text(encoding="utf8")!=current:
        vite.write_text(current,encoding="utf8")
    report=ROOT/".workspace/reports/kaykit-v7/PRIVATE_3D_PILOT.json"
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(preview,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("[HIGHFLY] v0.44.7 PRIVATE VISUAL PILOT INSTALLED")
    print("[HIGHFLY] Build in private terminal: bash scripts/start_preview_0447.sh")
    print("[HIGHFLY] View: /highfly-kaykit-pilot.html on private Codespaces port 4173")
    print("[HIGHFLY] Original gameplay and save data untouched. NOT commercial-release cleared.")

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--install",action="store_true",
                   help="Opt in to installation in gitignored PRIVATE upstream checkout")
    p.add_argument("--upstream",type=Path,default=UPSTREAM)
    p.add_argument("--kaykit",type=Path,default=KAYKIT)
    args=p.parse_args()
    result=plan(args.upstream,args.kaykit)
    print("[HIGHFLY] model selection from owner's KayKit Complete:",
          json.dumps({"models":result["models"],"donorFound":bool(result["donorSource"])},
          ensure_ascii=False,indent=2))
    if args.install:install(result,args.upstream)
    else:print("[HIGHFLY] INSPECTION ONLY. Add --install to create private visual pilot.")

if __name__=="__main__":main()
