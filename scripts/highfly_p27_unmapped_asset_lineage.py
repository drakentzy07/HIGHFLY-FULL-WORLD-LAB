#!/usr/bin/env python3
"""HIGHFLY P27: trace 249 provisional GLBs to their real source/builder lineage.

Unlike P25, this scans the actual pinned ClaudeCraft source-generation scripts
for evidence of the models which were NEVER in 'scripts/assets/specs/*.json'.
A prefix or filename resemblance IS NOT a license grant. Only exact conversion
spec + documented provider license can authorize an automated import.
No binary copies, builds, RPG modifications, or network downloads.

Writes a per-resource JSON + CSV action list, including which geometries remain
temporary AFTER any P23/P26 apply, and exact source-generation references.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv
import json
from pathlib import Path,PurePosixPath
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21
import highfly_p23_real_kaykit_upgrade as p23
import highfly_p25_source_first_asset_audit as p25

ORIGINAL=p9.ORIGINAL
STAGE=p9.STAGE
REPORT=ROOT/".workspace/reports/highfly-p27"
SCAN_ROOTS=("scripts/assets","scripts/asset_pipeline","src")
SUFFIXES={".mjs",".js",".ts",".tsx",".py",".json"}
MAX_SOURCE_FILES=14000
MAX_FILE_BYTES=1_200_000
MAX_EVIDENCE_PER_MODEL=8

# Heuristic builder families ARE LEADS, NEVER provenance/rights proof.
BUILD_FAMILY_HINTS={
    "/models/dungeon/ignivar_prop_":("scripts/assets/build_ignivar_props.mjs",),
    "/models/drakelands_kit/":("scripts/assets/build_drakelands_kit.mjs",),
    "/models/props/fenbridge_":("scripts/assets/fenbridge_town",),
    "/models/props/eastbrook_":("scripts/assets/eastbrook_town",),
    "/models/props/farm_":("scripts/assets/farm_props",),
    "/models/props/wickharbor_":("scripts/assets/wickharbor_harbor","scripts/assets/wickharbor_wharf"),
    "/models/props/hoard_":("scripts/assets/hoard_mobs","scripts/assets/hoard_bosses"),
    "/models/props/streetlamp_":("scripts/assets/build_veiled_hollow_props.mjs",
                                 "scripts/assets/build_willowfen_props.mjs"),
    "/models/props/wyro_":("scripts/assets/wyrmwatch_harbor",),
    "/models/props/willowfen_":("scripts/assets/build_willowfen_props.mjs",),
    "/models/props/palmreach_":("scripts/assets/build_palmreach_props.mjs",),
    "/models/props/evergarden_":("scripts/assets/evergarden_maze",),
}

def safe_text_sources(root:Path):
    seen=0
    for rel in SCAN_ROOTS:
        base=root/rel
        if not base.is_dir() or base.is_symlink():
            continue
        for file in sorted(base.rglob("*")):
            if not file.is_file() or file.is_symlink() or file.suffix.lower() not in SUFFIXES:
                continue
            if file.stat().st_size>MAX_FILE_BYTES:
                continue
            seen+=1
            if seen>MAX_SOURCE_FILES:
                raise RuntimeError("P27_TOO_MANY_SOURCE_FILES")
            yield file

def credited_lines(reference:Path):
    file=reference/"CREDITS.md"
    if not file.is_file() or file.is_symlink():
        raise RuntimeError("P27_CREDITS_MISSING")
    rows=[]
    for i,line in enumerate(file.read_text(encoding="utf-8").splitlines(),start=1):
        if line.startswith("|") and len(line.split("|"))>=5:
            cols=[p.strip() for p in line.split("|")[1:-1]]
            rows.append((i,line,cols))
    return rows

def license_evidence(path:str,credits:list):
    name=PurePosixPath(path).stem.casefold()
    target=PurePosixPath(path).name.casefold()
    # Exact full output filename or sufficiently distinctive model stem.
    # Broad family mentions are not used for license classification.
    evidence=[]
    for line_num,line,cols in credits:
        lo=line.casefold()
        if target in lo or (len(name)>=12 and re.search(
            r"(?<![a-z0-9_])"+re.escape(name)+r"(?![a-z0-9_])",lo)):
            license_name=cols[3] if len(cols)>3 else "UNKNOWN"
            usage=cols[4] if len(cols)>4 else "UNKNOWN"
            evidence.append({"line":line_num,"licenseClaim":license_name,
                            "reuseClaim":usage,"sourceLine":line[:460]})
    return evidence[:MAX_EVIDENCE_PER_MODEL]

def script_lineage(reference:Path,urls:list[str]):
    stems={PurePosixPath(x).stem.casefold():x for x in urls}
    # Stems that are too short risk misleading matches against ordinary code.
    stems={name:url for name,url in stems.items() if len(name)>=7}
    if not stems:
        return {},0
    names=list(stems)
    pattern=re.compile(r"(?<![A-Za-z0-9_])("+ "|".join(
        re.escape(x) for x in sorted(names,key=len,reverse=True))+r")(?![A-Za-z0-9_])",re.I)
    evidence=defaultdict(list)
    scanned=0
    for file in safe_text_sources(reference):
        scanned+=1
        rel=file.relative_to(reference).as_posix()
        try:
            with file.open("r",encoding="utf-8",errors="replace") as stream:
                for number,line in enumerate(stream,start=1):
                    if len(line)>16000:continue
                    hits={m.group(1).casefold() for m in pattern.finditer(line)}
                    for hit in hits:
                        url=stems[hit]
                        if len(evidence[url])>=MAX_EVIDENCE_PER_MODEL:
                            continue
                        kind=("ASSET_BUILD_SCRIPT_EXACT_IDENTIFIER" if rel.startswith("scripts/assets/")
                              else "GAME_CODE_REFERENCE_EXACT_IDENTIFIER")
                        evidence[url].append({"file":rel,"line":number,
                            "kind":kind,"excerpt":line.strip()[:280]})
        except OSError:
            continue
    return dict(evidence),scanned

def family_candidates(path:str,reference:Path):
    options=[]
    for prefix,candidates in BUILD_FAMILY_HINTS.items():
        if path.startswith(prefix):
            for candidate in candidates:
                if (reference/candidate).exists():
                    options.append(candidate)
    return list(dict.fromkeys(options))

def inspect():
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    p22=p23.p22_provisional_source()
    specs=p25.outspec_index(ORIGINAL)
    paths=sorted(p22)
    evidence,scanned=script_lineage(ORIGINAL,paths)
    credits=credited_lines(ORIGINAL)
    rows=[]
    for url in paths:
        stage=STAGE/"public"/url.lstrip("/")
        valid=stage.is_file() and not stage.is_symlink() and p21.check_binary(stage,url)
        unchanged=valid and p12.digest(stage)==p22[url] and p23.is_p22_file(stage,p22[url])
        docs=license_evidence(url,credits)
        script_refs=evidence.get(url,[])
        source_spec=specs.get(url,[])
        actual_builder=[x for x in script_refs if x["kind"]=="ASSET_BUILD_SCRIPT_EXACT_IDENTIFIER"]
        if source_spec:
            kind="UPSTREAM_EXACT_SRC_OUT_SPEC"
        elif actual_builder:
            kind="SOURCE_GENERATOR_EXACT_IDENTIFIER_FOUND"
        elif script_refs:
            kind="REFERENCED_IN_GAME_SOURCE_ONLY"
        elif family_candidates(url,ORIGINAL):
            kind="FAMILY_BUILDER_CANDIDATE_REVIEW"
        else:
            kind="UNTRACED_NEEDS_MANUAL_INSPECTION"
        # A direct reference/filename is not a universal reuse permission.
        # Treat all these rows as NEEDS_RIGHTS_REVIEW, unless P26/P23 separately
        # validated a third-party SOURCE, and leave gameplay contracts untouched.
        rows.append({
            "path":url,
            "currentStage":("P22_TEMP_PROCEDURAL" if unchanged else
                            "REPLACED_POST_P22" if valid else "MISSING_INVALID"),
            "lineageClass":kind,
            "sourceConversionSpecs":[{"spec":x["upstreamSpec"],
                        "rawSource":x["exactRawSource"],
                        "provider":x["sourceProvider"]} for x in source_spec],
            "exactScriptReferences":script_refs,
            "possibleBuilderFamilies":family_candidates(url,ORIGINAL),
            "creditsExactMentions":docs,
            "licensingStatus":"REQUIRES_SOURCE_SPEC_OR_EXPLICIT_ASSET_LICENSE_REVIEW",
            "recommendedNextAction":(
                "KEEP_REPLACED_ASSET_VERIFY_VISUALLY" if valid and not unchanged else
                "REVIEW_UPSTREAM_SPEC_AND_USE_P26_OR_P23" if source_spec else
                "TRACE_BUILDER_SOURCE_AND_LICENSE_THEN_FIND_REAL_PACK_EQUIVALENT"
                if actual_builder else
                "SEARCH_SAFE_PACK_EQUIVALENT_AND_VERIFY_SCENE_CONTRACT")
        })
    groups=Counter(x["lineageClass"] for x in rows)
    stage_state=Counter(x["currentStage"] for x in rows)
    prefix_counts=Counter("/".join(PurePosixPath(x["path"]).parts[1:3]) for x in rows)
    report={
        "phase":"HIGHFLY_P27_SOURCE_GENERATOR_LINEAGE_249",
        "readOnly":True,
        "sourcePin":p9.SHA,
        "runtimeProvisionalUniverse":len(rows),
        "sourceFilesScanned":scanned,
        "currentStageState":dict(stage_state),
        "lineageClasses":dict(groups),
        "byModelFolder":dict(prefix_counts),
        "sourcePolicy":"Preserve verified CC0/MIT; only user-owned KayKit SOURCE V7; never treat builder mention as grant of rights",
        "proofPolicy":"Exact conversion spec and verified pack license, not basename resemblance or family inference",
        "gameplayModified":False,
        "artReplaced":False,
        "timestampUtc":datetime.now(timezone.utc).isoformat(),
        "models":rows
    }
    REPORT.mkdir(parents=True,exist_ok=True)
    outfile=REPORT/"P27_249_ORIGIN_TRACE.json"
    outfile.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    csvfile=REPORT/"P27_249_ORIGIN_MATRIX.csv"
    with csvfile.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=[
            "path","currentStage","lineageClass","licensingStatus",
            "scriptReferences","possibleBuilderFamilies","creditsExactMentions",
            "recommendedNextAction"])
        writer.writeheader()
        for x in rows:
            writer.writerow({
                "path":x["path"],"currentStage":x["currentStage"],
                "lineageClass":x["lineageClass"],"licensingStatus":x["licensingStatus"],
                "scriptReferences":"; ".join(y["file"]+":"+str(y["line"]) for y in x["exactScriptReferences"]),
                "possibleBuilderFamilies":"; ".join(x["possibleBuilderFamilies"]),
                "creditsExactMentions":"; ".join(str(y["line"])+" "+y["licenseClaim"] for y in x["creditsExactMentions"]),
                "recommendedNextAction":x["recommendedNextAction"]})
    print("[HIGHFLY] P27 AUDIT: "+json.dumps({
        "provisionalsOriginally":len(rows),
        "sourceCodeFilesScanned":scanned,
        "stillTemporary":stage_state.get("P22_TEMP_PROCEDURAL",0),
        "replacedWithRealModels":stage_state.get("REPLACED_POST_P22",0),
        "lineage":dict(groups),
        "licenseClaimsNotAutomaticallyAccepted":True},ensure_ascii=False))
    print("[HIGHFLY] P27 JSON: "+str(outfile))
    print("[HIGHFLY] P27 CSV: "+str(csvfile))
    return report

if __name__=="__main__":
    inspect()
