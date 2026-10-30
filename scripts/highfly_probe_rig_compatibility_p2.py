#!/usr/bin/env python3
"""HIGHFLY KayKit v7 private rig/animation compatibility scan, no external libs.

Inspects GLB 2.0 JSON metadata ONLY; no model extraction or game modification.
Scores animation donors based on target-node-name intersection. A score is
DIAGNOSTIC, not proof that retargeted animation looks correct in Three.js.
Uses user-owned KayKit v7 local files in ignored .workspace.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
KAYKIT=ROOT/".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
REPORT=ROOT/".workspace/reports/kaykit-v7/RIG_COMPATIBILITY_P2.json"
MAX_JSON=32*1024*1024
MAX_MODELS=1000
PACKS=("KayKit Adventurers 2.0","KayKit Skeletons 1.1","KayKit Character Animations 1.1")
HERO="KayKit Adventurers 2.0/Characters/gltf/Knight.glb"
SKELETON="KayKit Skeletons 1.1/characters/gltf/Skeleton_Minion.glb"

def read_glb_json(filename: Path) -> dict:
    if not filename.is_file() or filename.is_symlink():
        raise FileNotFoundError("GLB absent or symlink: "+str(filename))
    with filename.open("rb") as f:
        header=f.read(12)
        if len(header)!=12:
            raise ValueError("Short GLB header")
        signature,version,total=struct.unpack("<4sII",header)
        if signature!=b"glTF" or version!=2 or total!=filename.stat().st_size:
            raise ValueError("Invalid GLB2 header, version or file size")
        chunk_header=f.read(8)
        if len(chunk_header)!=8:
            raise ValueError("GLB missing JSON chunk header")
        size,kind=struct.unpack("<I4s",chunk_header)
        if kind!=b"JSON" or size>MAX_JSON or size+20>total:
            raise ValueError("Invalid or oversized GLB JSON chunk")
        raw=f.read(size)
        if len(raw)!=size:
            raise ValueError("Truncated GLB JSON")
    result=json.loads(raw.decode("utf-8").rstrip(" \x00"))
    if not isinstance(result,dict):raise ValueError("GLB JSON is not object")
    return result

def model_info(source: Path,root:Path) -> dict:
    payload=read_glb_json(source)
    nodes=payload.get("nodes",[])
    def name(n):return n.get("name","") if isinstance(n,dict) else ""
    names=[name(node) for node in nodes]
    skins=payload.get("skins",[])
    joints={names[i] for skin in skins for i in skin.get("joints",[]) if isinstance(i,int) and 0<=i<len(names) and names[i]}
    animations=[]
    target_names=set()
    for animation in payload.get("animations",[]):
        targets=[]
        for channel in animation.get("channels",[]):
            target=channel.get("target",{})
            index=target.get("node")
            if isinstance(index,int) and 0<=index<len(names) and names[index]:
                targets.append(names[index])
                target_names.add(names[index])
        animations.append({"name":animation.get("name","(unnamed)"),
                           "channels":len(animation.get("channels",[])),
                           "namedTargets":len(set(targets))})
    return {"path":source.relative_to(root).as_posix(),"bytes":source.stat().st_size,
            "nodeCount":len(nodes),"skinCount":len(skins),"jointCount":len(joints),
            "jointNames":sorted(joints),"nodeNames":sorted(set(n for n in names if n)),
            "animationCount":len(animations),"animations":animations,
            "animationTargetNames":sorted(target_names)}

def coverage(donor:dict,target:dict)->dict:
    names=set(target["nodeNames"])
    wanted=set(donor["animationTargetNames"])
    common=wanted & names
    return {
        "donor":donor["path"],
        "animationCount":donor["animationCount"],
        "animationNames":[x["name"] for x in donor["animations"]],
        "animatedTargetNames":len(wanted),
        "matchingTargetNodes":len(common),
        "coveragePercent":round(100*len(common)/len(wanted),1) if wanted else 0,
        "missingTargets":sorted(wanted-names)[:24],
        "potentialBoneOverlap":len(set(donor["jointNames"]) & set(target["jointNames"])),
        "warning":"NAME_OVERLAP_ONLY_RENDER_AND_RETARGETING_NOT_VERIFIED",
    }

def scan(root:Path, report:Path)->dict:
    if not root.is_dir():raise FileNotFoundError("KayKit selected extraction missing at "+str(root))
    if not ".workspace/private-imports" in root.resolve().as_posix():
        raise ValueError("Only inspect private imported KayKit assets")
    sources=[]
    for pack in PACKS:
        pack_dir=root/pack
        if not pack_dir.is_dir():raise FileNotFoundError("Missing selected pack: "+str(pack_dir))
        sources.extend(sorted(pack_dir.rglob("*.glb")))
    if len(sources)>MAX_MODELS:raise ValueError("Too many .glb for bounded pilot scan")
    records=[]
    errors=[]
    for p in sources:
        try:records.append(model_info(p,root))
        except (ValueError,KeyError,UnicodeDecodeError, OSError) as exc:
            errors.append({"file":str(p.relative_to(root)),"error":str(exc)})
    bypath={r["path"]:r for r in records}
    targets={}
    for key,path in (("hero",HERO),("skeleton",SKELETON)):
        target=bypath.get(path)
        if not target:raise FileNotFoundError("Primary target not found as valid GLB: "+path)
        donors=[]
        for candidate in records:
            if candidate["path"]==path or candidate["animationCount"]==0:
                continue
            score=coverage(candidate,target)
            if score["matchingTargetNodes"]>0:
                donors.append(score)
        donors.sort(key=lambda d:(-d["coveragePercent"],-d["matchingTargetNodes"],-d["animationCount"],d["donor"]))
        targets[key]={
            "model":path,"skins":target["skinCount"],
            "joints":target["jointCount"],"embeddedClips":target["animationCount"],
            "topPotentialAnimationDonors":donors[:12],
        }
    summary={
        "project":"HIGHFLY ORIGIN","baseVersion":"ClaudeCraft v0.44.7",
        "status":"PRIVATE_DIAGNOSTIC_ONLY_DOES_NOT_CHANGE_GAME_OR_AUTHORIZE_SHIPPING",
        "filesInspected":len(sources),"validGlb":len(records),
        "invalidGlb":errors,
        "modelsWithEmbeddedAnimations":sum(r["animationCount"]>0 for r in records),
        "packStats":dict(sorted(Counter(r["path"].split("/")[0] for r in records).items())),
        "heroAndSkeleton":targets,
        "allModels":[{"path":r["path"],"skinCount":r["skinCount"],
                     "jointCount":r["jointCount"],"animationCount":r["animationCount"],
                     "animationNames":[a["name"] for a in r["animations"]][:40]} for r in records],
    }
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=KAYKIT)
    parser.add_argument("--report",type=Path,default=REPORT)
    args=parser.parse_args()
    r=scan(args.root,args.report)
    print("[HIGHFLY] PRIVATE RIG P2: "+json.dumps({
        "validGlb":r["validGlb"],
        "modelsWithAnimations":r["modelsWithEmbeddedAnimations"],
        "errors":len(r["invalidGlb"]),
        "models":{key:{"embeddedClips":value["embeddedClips"],
                       "rigBones":value["joints"],
                       "bestDonors":value["topPotentialAnimationDonors"][:4]}
                  for key,value in r["heroAndSkeleton"].items()},
        "report":str(args.report),
        },ensure_ascii=False))
    print("[HIGHFLY] No models modified or published. Name overlap != visually verified compatible rig.")
if __name__=="__main__":
    main()
