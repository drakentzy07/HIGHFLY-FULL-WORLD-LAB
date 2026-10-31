#!/usr/bin/env python3
"""HIGHFLY P24 — Replace LEGACY KayKit GLBs from P21 with new SOURCE V7 assets.

KayKit used in HIGHFLY must originate ONLY from the user's full SOURCE V7 ZIP.
Other creators (Quaternius, Kenney, ambientCG, Poly Haven) remain allowed if
their independent CC0 provenance is verified. This script does not touch them.

NO blanket delete: an active legacy KayKit model is replaced only if the
new ZIP contains a single compatible source-name match. Unmatched old assets
are explicitly reported, not made into missing runtime URLs.

Dry-run first, --apply only after validated plan. Preserves original upstream
reference, RPG simulation, protected P8 world models, and owned archive.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21
import highfly_p23_real_kaykit_upgrade as p23

REFERENCE=p23.REFERENCE
STAGE=p23.STAGE
ARCHIVE=p23.ARCHIVE
OUTPUT=ROOT/".workspace/reports/highfly-p24"


def manifest(index:dict)->list[dict]:
    """Inventory explicitly hash-identified P21 KayKit imports, not unrelated assets."""
    previous=p23.legacy_kaykit_inventory()["items"]
    rows=[]
    for row in previous:
        if row["status"]=="EXACT_OLD_KAYKIT_PRESENT":
            candidate=p23.match_archive(row["path"],index)
            rows.append({**row,**candidate})
        else:
            rows.append({**row,"method":"ALREADY_CHANGED_OR_ABSENT"})
    return rows


def ready(rows:list[dict])->list[dict]:
    return [r for r in rows if r["status"]=="EXACT_OLD_KAYKIT_PRESENT"
            and r["method"]=="REPLACE_WITH_OWNED_KAYKIT"]


def target(row:dict)->Path:
    return STAGE/"public"/row["path"].lstrip("/")


def old_verified(row:dict)->bool:
    dst=target(row)
    return (dst.is_file() and not dst.is_symlink()
            and p21.check_binary(dst,row["path"])
            and p12.digest(dst)==row["sha256"])


def prepare_assets(z:zipfile.ZipFile,table:dict,rows:list[dict],work:Path)->list[tuple]:
    prepared=[]
    for i,row in enumerate(rows):
        if not old_verified(row):
            raise RuntimeError("P24_UNEXPECTED_LEGACY_SOURCE: "+row["path"])
        converted=work/("source-v7-"+str(i)+".glb")
        p23.convert_zip_asset(z,table,row["sourceZipMember"],converted,work/("gltf-"+str(i)))
        if not p21.check_binary(converted,row["path"]):
            raise RuntimeError("P24_BAD_USER_SOURCE_MODEL: "+row["path"])
        backup=work/("p21-original-"+str(i)+".glb")
        shutil.copyfile(target(row),backup)
        if p12.digest(backup)!=row["sha256"]:
            raise RuntimeError("P24_BACKUP_MISMATCH: "+row["path"])
        prepared.append((row,converted,backup,p12.digest(converted)))
    return prepared


def restore_stage(changed:list[tuple]):
    """Rollback EXACT original hash of every changed old KayKit stage model."""
    for row,original in reversed(changed):
        dst=target(row)
        if not original.is_file() or p12.digest(original)!=row["sha256"]:
            raise RuntimeError("P24_ROLLBACK_BACKUP_INVALID: "+row["path"])
        shutil.copyfile(original,dst)
        if p12.digest(dst)!=row["sha256"]:
            raise RuntimeError("P24_ROLLBACK_RESULT_INVALID: "+row["path"])


def apply_migration(z:zipfile.ZipFile,table:dict,rows:list[dict])->tuple[list[dict],int|None]:
    if len(rows)>300:raise RuntimeError("P24_TOO_MANY_LEGACY_MODELS")
    if not rows:return [],None
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p24-migration-",dir=OUTPUT) as workdir:
        prepared=prepare_assets(z,table,rows,Path(workdir))
        changed=[]
        try:
            # Conversions all passed before replacing any file.
            for row,converted,backup,hashnew in prepared:
                if not old_verified(row):
                    raise RuntimeError("P24_LEGACY_CHANGED_DURING_CONVERSION: "+row["path"])
                os.replace(converted,target(row))
                changed.append((row,backup))
            build=p9.smoke()["exitCode"]
            bad=[]
            for row,converted,backup,hashnew in prepared:
                dist=STAGE/"dist"/row["path"].lstrip("/")
                if (not p21.check_binary(dist,row["path"])
                    or p12.digest(target(row))!=hashnew
                    or p12.digest(dist)!=hashnew):
                    bad.append(row["path"])
            if build!=0 or bad:
                raise RuntimeError("P24_BUILD_OR_BUNDLE_FAILED: "+repr(bad[:7]))
        except BaseException:
            restore_stage(changed)
            if changed:
                result=p9.smoke()
                if result["exitCode"]!=0:
                    raise RuntimeError("P24_ROLLBACK_BUILD_FAILED_AFTER_RESTORING_STAGE")
            raise
        installed=[{"path":row["path"],
                    "sourceZipMember":row["sourceZipMember"],
                    "replacedLegacySha256":row["sha256"],
                    "sourceV7Sha256":hashnew}
                   for row,converted,backup,hashnew in prepared]
        return installed,build


def execute(apply:bool=False):
    p9.preflight(REFERENCE,STAGE,p9.REPORT)
    p12.validate(REFERENCE,STAGE,ARCHIVE,OUTPUT)
    with zipfile.ZipFile(ARCHIVE,"r") as z:
        table,index=p23.zip_index(z)
        source_packs=sorted({x["pack"] for items in index.values() for x in items})
        if len(source_packs)<2 or sum(map(len,index.values()))<10:
            raise RuntimeError("P24_NOT_A_FULL_USER_SOURCE_V7_ARCHIVE")
        rows=manifest(index)
        eligible=ready(rows)
        installed=[]
        build=None
        if apply:
            installed,build=apply_migration(z,table,eligible)
    changed={r["path"] for r in installed}
    remaining=[r for r in rows
               if r["status"]=="EXACT_OLD_KAYKIT_PRESENT" and r["path"] not in changed]
    report={
        "phase":"P24_REPLACE_OLDER_P21_KAYKIT_WITH_OWNED_COMPLETE_V7",
        "mode":"APPLY" if apply else "DRY_RUN",
        "capturedUtc":datetime.now(timezone.utc).isoformat(),
        "kaykitExclusiveArchive":str(ARCHIVE),
        "newSourcePackCount":len(source_packs),
        "newSourceModelsIndexed":sum(map(len,index.values())),
        "olderKaykitTracked":len(rows),
        "olderStillPresentBefore":sum(r["status"]=="EXACT_OLD_KAYKIT_PRESENT" for r in rows),
        "safeMatches":len(eligible),
        "replacedOldKaykit":len(installed),
        "oldKaykitRemaining":len(remaining),
        "untouchedNonKaykitCC0":True,
        "noOtherGameMediaDeleted":True,
        "rpgCodeChanged":False,
        "playableVerified":False,
        "buildExitCode":build,
        "installed":installed,
        "unresolved":remaining,
        "items":rows,
        "note":"Unmatched legacy KayKit assets remain until verified SOURCE V7 replacements can preserve world behavior. This never treats those as canonical source packs."
    }
    OUTPUT.mkdir(parents=True,exist_ok=True)
    dest=OUTPUT/"P24_SOURCE_V7_LEGACY_MIGRATION.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("[HIGHFLY] P24 "+report["mode"]+": "+json.dumps({
        "v7SourcePacks":report["newSourcePackCount"],
        "v7Models":report["newSourceModelsIndexed"],
        "oldKaykitTracked":report["olderKaykitTracked"],
        "safeMatches":report["safeMatches"],
        "replacedOldKaykit":report["replacedOldKaykit"],
        "oldKaykitRemaining":report["oldKaykitRemaining"],
        "nonKaykitCC0Preserved":True,
        "buildExitCode":build
    },ensure_ascii=False))
    print("[HIGHFLY] P24 REPORT: "+str(dest))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    execute(args.apply)
