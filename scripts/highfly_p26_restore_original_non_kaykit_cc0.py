#!/usr/bin/env python3
"""HIGHFLY P26: restore exact originally built CC0 (NON-KayKit) 3D assets.

Source is pinned WOC v0.44.7 public GLB, ONLY when its exact src->out spec
points into a recognized CC0 raw asset provider, credits record CC0/Yes, and
the output URL identifies an unchanged P22 procedural stand-in.

Real KayKit models must come from USER-OWNED SOURCE V7 (P23/P24): excluded here.
With-the-project-only / restricted/project-generated WOC media excluded.
No changes to world layout, render code, game simulation, mobs or quests.
Read-only default; --apply creates hash-checked backups and validates dist.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime,timezone
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21
import highfly_p23_real_kaykit_upgrade as p23
import highfly_p25_source_first_asset_audit as p25

REFERENCE=p9.ORIGINAL
STAGE=p9.STAGE
OUTPUT=ROOT/".workspace/reports/highfly-p26"
ALLOWED={"Quaternius","Kenney","ambientCG","Poly Haven","loafbrr"}
MAX_ITEMS=249


def evaluate(output:str,specs:dict,credits:dict,expected_hash:str)->dict:
    row={"path":output,"oldP22Hash":expected_hash}
    if not p21.safe_asset_path(output) or PurePosixPath(output).suffix.lower()!=".glb":
        row["decision"]="INVALID_OR_NONGLB";return row
    stage=STAGE/"public"/output.lstrip("/")
    upstream=REFERENCE/"public"/output.lstrip("/")
    if not p23.is_p22_file(stage,expected_hash):
        row["decision"]="NO_LONGER_UNCHANGED_P22_PROVISIONAL";return row
    if not upstream.is_file() or upstream.is_symlink() or not p21.check_binary(upstream,output):
        row["decision"]="NO_VALID_ORIGINAL_BINARY";return row
    records=specs.get(output,[])
    sources={entry["exactRawSource"] for entry in records}
    provs={entry["sourceProvider"] for entry in records}
    if not records:
        row["decision"]="NO_EXACT_SOURCE_CONVERSION_SPEC";return row
    if len(sources)!=1 or len(provs)!=1:
        row["decision"]="MULTIPLE_OR_AMBIGUOUS_SOURCE_SPECS";return row
    raw=next(iter(sources))
    prov=next(iter(provs))
    row.update({"originalRawSource":raw,"sourceProvider":prov,
                "conversionSpecs":sorted({x["upstreamSpec"] for x in records})})
    if prov=="KayKit":
        row["decision"]="EXCLUDE_OLD_KAYKIT_USE_OWNED_V7";return row
    if prov not in ALLOWED:
        row["decision"]="RESTRICTED_OR_UNKNOWN_OR_PROJECT_ART";return row
    if not credits.get(prov,False):
        row["decision"]="CC0_CREDITS_MISSING";return row
    if not raw.replace("\\","/").startswith("tmp/asset_src/"):
        row["decision"]="SOURCE_OUTSIDE_VERIFIED_PACK_ROOT";return row
    # Source identity and compiled target are both exact. Never choose a
    # vaguely similar archive file; this reuses the known packaged WOC CC0
    # glb for its own original output URL.
    row.update({"decision":"EXACT_CC0_ORIGINAL_READY",
                "upstreamSha256":p12.digest(upstream),
                "upstreamBytes":upstream.stat().st_size})
    return row


def audit():
    p9.preflight(REFERENCE,STAGE,p9.REPORT)
    temp=p23.p22_provisional_source()
    if len(temp)!=249:raise RuntimeError("P26_P22_PROVISIONAL_249_REQUIRED")
    specs=p25.outspec_index(REFERENCE)
    credits=p25.credited(REFERENCE)
    return [evaluate(url,specs,credits,sha) for url,sha in sorted(temp.items())]


def restore(changed:list[tuple]):
    for row,backup in reversed(changed):
        target=STAGE/"public"/row["path"].lstrip("/")
        if not backup.is_file() or p12.digest(backup)!=row["oldP22Hash"]:
            raise RuntimeError("P26_ROLLBACK_BACKUP_HASH_MISMATCH: "+row["path"])
        shutil.copyfile(backup,target)
        if p12.digest(target)!=row["oldP22Hash"]:
            raise RuntimeError("P26_ROLLBACK_FAILED: "+row["path"])


def install(rows:list[dict])->tuple[list[dict],int|None]:
    selected=[x for x in rows if x["decision"]=="EXACT_CC0_ORIGINAL_READY"]
    if len(selected)>MAX_ITEMS:raise RuntimeError("P26_TOO_MANY_REPLACEMENTS")
    if not selected:return [],None
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p26-build-",dir=OUTPUT) as folder:
        tmp=Path(folder)
        prepared=[]
        for i,row in enumerate(selected):
            target=STAGE/"public"/row["path"].lstrip("/")
            upstream=REFERENCE/"public"/row["path"].lstrip("/")
            if not p23.is_p22_file(target,row["oldP22Hash"]):
                raise RuntimeError("P26_P22_CHANGED_BEFORE_IMPORT: "+row["path"])
            if not p21.check_binary(upstream,row["path"]) or p12.digest(upstream)!=row["upstreamSha256"]:
                raise RuntimeError("P26_CC0_SOURCE_CHANGED: "+row["path"])
            candidate=tmp/("original-"+str(i)+".glb")
            backup=tmp/("backup-"+str(i)+".glb")
            shutil.copyfile(upstream,candidate)
            shutil.copyfile(target,backup)
            if (not p21.check_binary(candidate,row["path"]) or
                p12.digest(candidate)!=row["upstreamSha256"] or
                p12.digest(backup)!=row["oldP22Hash"]):
                raise RuntimeError("P26_UNEXPECTED_CONTENT: "+row["path"])
            prepared.append((row,candidate,backup))
        changed=[]
        try:
            for row,candidate,backup in prepared:
                target=STAGE/"public"/row["path"].lstrip("/")
                if not p23.is_p22_file(target,row["oldP22Hash"]):
                    raise RuntimeError("P26_DEST_CHANGED_BEFORE_SWAP: "+row["path"])
                os.replace(candidate,target)
                changed.append((row,backup))
            build=p9.smoke()["exitCode"]
            incorrect=[]
            for row,_,_ in prepared:
                target=STAGE/"public"/row["path"].lstrip("/")
                dist=STAGE/"dist"/row["path"].lstrip("/")
                if (not p21.check_binary(target,row["path"]) or
                    not p21.check_binary(dist,row["path"]) or
                    p12.digest(target)!=row["upstreamSha256"] or
                    p12.digest(dist)!=row["upstreamSha256"]):
                    incorrect.append(row["path"])
            if build!=0 or incorrect:
                raise RuntimeError("P26_RESTORED_ORIGINAL_NOT_BUNDLED: "+str(incorrect[:10]))
        except BaseException:
            restore(changed)
            if changed and p9.smoke()["exitCode"]!=0:
                raise RuntimeError("P26_ROLLBACK_BUILD_FAILED")
            raise
    return [{"path":row["path"],
             "source":row["originalRawSource"],
             "provider":row["sourceProvider"],
             "hash":row["upstreamSha256"]} for row in selected],build


def run(apply:bool=False):
    rows=audit()
    counts=dict(Counter(x["decision"] for x in rows))
    installed=[]
    build=None
    if apply:installed,build=install(rows)
    report={"phase":"HIGHFLY_P26_SOURCE_FIRST_EXACT_CC0_NONKAYKIT_RESTORE",
            "mode":"APPLY" if apply else "DRY_RUN",
            "createdAtUtc":datetime.now(timezone.utc).isoformat(),
            "p22TemporaryUniverse":len(rows),
            "methods":counts,"installed":installed,"installedCount":len(installed),
            "buildExitCode":build,
            "noKayKitFreeMediaImported":True,
            "noProjectOnlyOrRestrictedAssetsImported":True,
            "protectedWorldLogicChanged":False,
            "playabilityVerified":False,"visualQualityVerified":False,
            "safeHashCheckedSwaps":True,
            "rows":rows}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    path=OUTPUT/"P26_EXACT_CC0_RESTORE.json"
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("[HIGHFLY] P26 "+report["mode"]+": "+json.dumps({
        "provisionalCandidates":len(rows),
        "exactCC0Recoverable":counts.get("EXACT_CC0_ORIGINAL_READY",0),
        "alreadyReplaced":counts.get("NO_LONGER_UNCHANGED_P22_PROVISIONAL",0),
        "otherStates":counts,
        "installed":len(installed),"buildExitCode":build,
        "gameplayVerified":False},ensure_ascii=False))
    print("[HIGHFLY] P26 REPORT: "+str(path))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    opts=parser.parse_args()
    run(opts.apply)
