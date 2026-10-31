#!/usr/bin/env python3
"""HIGHFLY P25 — actual upstream src->out provenance versus local owned libraries.

READ-ONLY AUDIT. Pinned ClaudeCraft 0.44.7 conversion specifications are the
authority for which raw file generated each runtime URL. The runtime captures
are evidence of which URLs the browser actually requested. A pack name in
CREDITS.md alone is NOT proof that the corresponding file is installed.

KayKit models: ONLY user's private KayKit Complete SOURCE archive.
Others: optional archives/extracted packs in private-imports/external-cc0-packs,
plus individually-proven original third-party CC0 media already imported in P21.
The catalog never copies original project-only media nor alters the RPG.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21
import highfly_p22_owned_asset_rebuilder as p22
import highfly_p23_real_kaykit_upgrade as p23

ORIGINAL=p9.ORIGINAL
STAGE=p9.STAGE
PRIVATE_ROOT=ROOT/".workspace/private-imports"
KAYKIT=p12.ZIP
OTHER_PACKS=PRIVATE_ROOT/"external-cc0-packs"
REPORT=ROOT/".workspace/reports/highfly-p25"
RUNTIME_314=ROOT/"reports/highfly_p20_runtime_missing_paths.json"
RUNTIME_266=ROOT/"reports/highfly_p21_fresh_missing_266.json"
ALLOWED_EXT={".gltf",".glb",".fbx",".obj",".blend"}
MAX_EXTRA_ARCHIVES=50
MAX_EXTRA_FILES=90000
MAX_ARCHIVE_LIST=70000
MAX_SPEC_FILES=500

# These are a *provenance classification*, not a license shortcut.
# The source converter spec and CREDITS.md must both corroborate CC0.
PROVIDER_RE=re.compile(
    r"(quaternius|poly_pirate|poly_medieval|kenney|kaykit|ambientcg|polyhaven|poly_haven|loafbrr)",
    re.IGNORECASE)
PREFIXES=[
    ("KayKit","kaykit"),
    ("Quaternius","quaternius"),
    ("Quaternius","poly_pirate"),
    ("Quaternius","poly_medieval"),
    ("Kenney","kenney"),
    ("ambientCG","ambientcg"),
    ("Poly Haven","polyhaven"),
    ("Poly Haven","poly_haven"),
    ("loafbrr","loafbrr"),
]
SOURCE_PROVIDERS={
    "KayKit":"Kay Lousberg",
    "Quaternius":"Quaternius",
    "Kenney":"Kenney",
    "ambientCG":"ambientCG",
    "Poly Haven":"Poly Haven",
    "loafbrr":"loafbrr",
}

def provider(src:str)->str:
    s=src.replace("\\","/").casefold()
    for label,keyword in PREFIXES:
        if ("/"+keyword) in s or s.startswith(keyword):
            return label
    return "UNATTRIBUTED_OR_PROJECT_ART"

def credited(reference:Path)->dict:
    lines=(reference/"CREDITS.md").read_text(encoding="utf8").splitlines()
    evidence={}
    for title,author in SOURCE_PROVIDERS.items():
        evidence[title]=any(
            line.startswith("|") and author.casefold() in line.split("|")[2].casefold()
            and re.search(r"\|\s*CC0 1\.0\s*\|\s*Yes\s*\|",line)
            for line in lines if len(line.split("|"))>4)
    return evidence

def outspec_index(reference:Path)->dict[str,list[dict]]:
    root=reference/"scripts/assets/specs"
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("P25_SOURCE_SPECS_ABSENT")
    specs=sorted(root.rglob("*.json"))
    if len(specs)>MAX_SPEC_FILES:
        raise RuntimeError("P25_UNEXPECTED_SPEC_VOLUME")
    by_out=defaultdict(list)
    for path in specs:
        if path.is_symlink() or path.stat().st_size>3_000_000:continue
        try:doc=json.loads(path.read_text(encoding="utf8"))
        except (ValueError,UnicodeError):continue
        if not isinstance(doc,dict):continue
        for item in doc.get("items",[]):
            if not isinstance(item,dict):continue
            src=item.get("src");out=item.get("out")
            if not isinstance(src,str) or not isinstance(out,str):
                continue
            output="/"+out.lstrip("/")
            if not p21.safe_asset_path(output):
                # Texture/HDR/VFX outputs outside the captured runtime paths
                # are still part of upstream inventory; no string traversal.
                if not re.fullmatch(r"/[A-Za-z0-9_.\/-]+",output) or ".." in PurePosixPath(output).parts:
                    continue
            by_out[output].append({
                "upstreamSpec":str(path.relative_to(reference)),
                "exactRawSource":src,"sourceProvider":provider(src),
                "converterType":item.get("type","static"),
                "explicitSourceName":PurePosixPath(src).name,
            })
    return dict(by_out)

def source_stem(src:str)->str:
    name=PurePosixPath(src.replace("\\","/")).name
    while Path(name).suffix.lower() in ALLOWED_EXT and Path(name).suffix:
        name=Path(name).stem
    return re.sub(r"[^a-z0-9]+","_",name.casefold()).strip("_")

def from_capture(path:Path,expect:int)->list[str]:
    obj=json.loads(path.read_text(encoding="utf8"))
    arr=obj.get("paths")
    if obj.get("pathCount")!=expect or not isinstance(arr,list) or len(arr)!=expect or len(arr)!=len(set(arr)):
        raise RuntimeError("P25_RUNTIME_CAPTURE_MISMATCH: "+str(path))
    if not all(p21.safe_asset_path(x) for x in arr):
        raise RuntimeError("P25_UNSAFE_CAPTURE")
    return arr

def source_candidate_index(root:Path, zip_archive:Path)->tuple[dict,int,dict]:
    """Index exact file stems only. Never unpack or download asset archives."""
    index=defaultdict(list)
    counts=Counter()
    paths_seen=0
    def add(path:str,source:str,claimed:str):
        nonlocal paths_seen
        p=PurePosixPath(path)
        if p.suffix.lower() not in ALLOWED_EXT:return
        if paths_seen>=MAX_EXTRA_FILES:raise RuntimeError("P25_TOO_MANY_LOCAL_MODELS")
        if not source_stem(p.name):return
        paths_seen+=1
        index[source_stem(p.name)].append({"file":path,"location":source,"providerHint":claimed})
        counts[claimed]+=1

    if not zip_archive.is_file() or zip_archive.is_symlink():
        raise RuntimeError("P25_USER_OWNED_COMPLETE_SOURCE_ZIP_MISSING")
    with zipfile.ZipFile(zip_archive) as z:
        members=p12.zip_members(z)
        for name in members:
            # Only genuine KayKit component packs inside source V7, no archive
            # wrapper, non-KayKit folders, old free/demo/lite.
            parts=PurePosixPath(name).parts
            if len(parts)<4:continue
            pack=next((x for x in parts[:-3] if x.casefold().startswith("kaykit ")
                       and "complete" not in x.casefold()
                       and "collection" not in x.casefold()
                       and not re.search(r"(^|[ _-])(free|demo|lite|old|legacy)([ _-]|$)",x,re.I)),None)
            if pack and parts[-3].lower()=="assets" and parts[-2].lower() in ("gltf","glb","fbx","obj"):
                add(name,"KAYKIT_COMPLETE_SOURCE_V7", "KayKit")
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise RuntimeError("P25_EXTERNAL_ARCHIVES_DIR_UNSAFE")
        files=sorted(root.rglob("*"))
        archives=[x for x in files if x.is_file() and x.suffix.lower()==".zip"]
        if len(archives)>MAX_EXTRA_ARCHIVES:
            raise RuntimeError("P25_TOO_MANY_EXTERNAL_ARCHIVES")
        for path in files:
            if path.is_symlink() or not path.is_file():continue
            if path.suffix.lower() in ALLOWED_EXT:
                rel=path.relative_to(root).as_posix()
                prov=provider(rel)
                # NEVER use external KayKit as source. V7 is exclusive.
                if prov!="KayKit":add(rel,str(path.parent),prov)
        for archive in archives:
            try:
                with zipfile.ZipFile(archive) as z:
                    if len(z.infolist())>MAX_ARCHIVE_LIST:continue
                    for m in z.infolist():
                        if (m.is_dir() or m.file_size>p12.MAX_SOURCE_BYTES or
                            not p23.safe_zip_name(m.filename)):continue
                        hint=provider(str(archive.name)+"/"+m.filename)
                        if hint!="KayKit":
                            add(m.filename,str(archive.relative_to(root)),hint)
            except (OSError,zipfile.BadZipFile):
                counts["UNREADABLE_EXTERNAL_ARCHIVE"]+=1
    return dict(index),paths_seen,dict(counts)

def match_sources(row:list[dict], target:str,index:dict,credits:dict)->dict:
    if not row:
        return {"match":"NO_UPSTREAM_CONVERSION_SPEC",
                "matched":[], "targetProvider":"UNKNOWN"}
    sources=sorted({(x["exactRawSource"],x["sourceProvider"]) for x in row})
    providers={p for _,p in sources}
    title=next(iter(providers)) if len(providers)==1 else "MULTIPLE_UPSTREAM_PROVIDERS"
    if title not in SOURCE_PROVIDERS or not credits.get(title,False):
        return {"match":"PROJECT_ART_OR_LICENSE_REVIEW",
                "matched":[],"targetProvider":title}
    available=[]
    for src,prov in sources:
        stem=source_stem(src)
        pool=index.get(stem,[])
        allowed_location=("KAYKIT_COMPLETE_SOURCE_V7" if prov=="KayKit" else None)
        for item in pool:
            if (prov=="KayKit" and item["location"]!=allowed_location or
                prov!="KayKit" and (item["location"]=="KAYKIT_COMPLETE_SOURCE_V7" or
                                     item["providerHint"] not in (prov,"UNATTRIBUTED_OR_PROJECT_ART"))):
                continue
            available.append({**item,"upstreamRaw":src})
    if not available:
        return {"match":"NEEDS_LOCAL_PACK_SOURCE",
                "matched":[],"targetProvider":title}
    return {"match":"LOCAL_EXACT_SOURCE_BASENAME_CANDIDATE_REVIEW",
            "matched":available[:12],"targetProvider":title}

def audit(archive:Path=KAYKIT,external:Path=OTHER_PACKS):
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    if not archive.resolve().is_relative_to(PRIVATE_ROOT.resolve()):
        raise RuntimeError("P25_LIBRARY_MUST_BE_PRIVATE")
    if not external.resolve().is_relative_to(PRIVATE_ROOT.resolve()):
        raise RuntimeError("P25_EXTERNAL_LIBRARY_MUST_BE_PRIVATE")
    user_314=from_capture(RUNTIME_314,314)
    user_266=from_capture(RUNTIME_266,266)
    if not set(user_266).issubset(user_314):
        raise RuntimeError("P25_RUNTIME_CAPTURES_INCONSISTENT")
    specs=outspec_index(ORIGINAL)
    credits=credited(ORIGINAL)
    library,model_count,source_counts=source_candidate_index(external,archive)
    p22_doc=json.loads(p23.P22_REPORT.read_text(encoding="utf8"))
    p22_temps={x["path"]:x["sha256"] for x in p22_doc.get("installed",[])
               if x.get("generation")=="ORIGINAL_PROCEDURAL_FIRST_PASS"}
    p21_doc=json.loads(p23.P21_REPORT.read_text(encoding="utf8"))
    p21_imports={x["path"]:x for x in p21_doc.get("installed",[])}
    rows=[]
    for url in user_314:
        mapped=specs.get(url,[])
        match=match_sources(mapped,url,library,credits)
        stage=STAGE/"public"/url.lstrip("/")
        valid=stage.is_file() and not stage.is_symlink() and p21.check_binary(stage,url)
        if url in p22_temps and valid and p12.digest(stage)==p22_temps[url]:
            state="P22_TEMP_PROCEDURAL"
        elif url in p21_imports and valid and p12.digest(stage)==p21_imports[url]["sha256"]:
            state="P21_CC0_PROVEN_"+p21_imports[url]["provenance"]
        elif valid:
            state="STAGED_MEDIA_OTHER_OR_REPLACED"
        else:
            state="MISSING_OR_INVALID_IN_STAGE"
        rows.append({"runtimeUrl":url,
             "requestedAgainAfterP21":url in user_266,
             "currentStageState":state,
             "modelOrImage":PurePosixPath(url).suffix.lower(),
             "upstreamSpecPaths":[x["upstreamSpec"] for x in mapped],
             "upstreamRawSources":[x["exactRawSource"] for x in mapped],
             "upstreamProviders":sorted({x["sourceProvider"] for x in mapped}),
             **match})
    status=Counter(r["match"] for r in rows)
    states=Counter(r["currentStageState"].split("P21_CC0_PROVEN_")[0] if "P21_CC0_PROVEN_" in r["currentStageState"]
                   else r["currentStageState"] for r in rows)
    providers=Counter(r["targetProvider"] for r in rows)
    p22_matches=Counter(r["match"] for r in rows if r["currentStageState"]=="P22_TEMP_PROCEDURAL")
    spec_all=Counter()
    for items in specs.values():
        if items:
            for provider_name in {x["sourceProvider"] for x in items}:
                spec_all[provider_name]+=1
    report={
        "phase":"HIGHFLY_P25_SOURCE_FIRST_PACK_AUDIT",
        "readOnly":True,
        "licenseDocumentationChecked":credits,
        "sourcePolicy":"KayKit SOURCE V7 only; other providers CC0 verified individually; no project-only import",
        "capturedOriginal":314,"capturedAfterP21":266,
        "runtimeUrlsWithConversionSpecs":sum(bool(r["upstreamSpecPaths"]) for r in rows),
        "exactSourceIdentifierCandidatesInLocalLibrary":status.get("LOCAL_EXACT_SOURCE_BASENAME_CANDIDATE_REVIEW",0),
        "originalSpecOutputCount":len(specs),
        "originalSpecByProvider":dict(spec_all),
        "localIndexedModels":model_count,
        "localLibraryByProviderHint":source_counts,
        "localNonKaykitSearchDir":str(external),
        "presentInStage":dict(states),
        "runtimeTargetProviderCounts":dict(providers),
        "sourceMatchStatus":dict(status),
        "p22TemporarySourceMatchStatus":dict(p22_matches),
        "createdAtUtc":datetime.now(timezone.utc).isoformat(),
        "warning":"This is an inventory and source-name matching audit, NOT proof of exact mesh equivalence, animation compatibility, license at download, or gameplay completion.",
        "rows":rows,
    }
    REPORT.mkdir(parents=True,exist_ok=True)
    output=REPORT/"P25_SOURCE_FIRST_314_AND_249.json"
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    csv_file=REPORT/"P25_RUNTIME_SOURCE_MATRIX.csv"
    with csv_file.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=[
            "runtimeUrl","requestedAgainAfterP21","currentStageState",
            "targetProvider","match","upstreamSpecPaths","upstreamRawSources",
            "matchedLocalFiles"])
        writer.writeheader()
        for item in rows:
            writer.writerow({k:(",".join(v) if isinstance(v,list) else v)
                             for k,v in {
                "runtimeUrl":item["runtimeUrl"],
                "requestedAgainAfterP21":str(item["requestedAgainAfterP21"]),
                "currentStageState":item["currentStageState"],
                "targetProvider":item["targetProvider"],
                "match":item["match"],
                "upstreamSpecPaths":item["upstreamSpecPaths"],
                "upstreamRawSources":item["upstreamRawSources"],
                "matchedLocalFiles":[x["file"] for x in item["matched"]]
                }.items()})
    print("[HIGHFLY] P25 AUDIT: "+json.dumps({
        "runtimePaths":314,"tempModels":len(p22_temps),
        "specOutputPaths":len(specs),
        "runtimeWithSourceSpec":report["runtimeUrlsWithConversionSpecs"],
        "exactSourceNameCandidatesLocally":report["exactSourceIdentifierCandidatesInLocalLibrary"],
        "localIndexedModels":model_count,
        "matchedByProvider":dict(providers),
        "matchStatus":dict(status),
        "tempModelSourceMatches":dict(p22_matches)
        },ensure_ascii=False))
    print("[HIGHFLY] P25 JSON: "+str(output))
    print("[HIGHFLY] P25 CSV: "+str(csv_file))
    print("[HIGHFLY] P25 SELECTED SOURCE EXAMPLES:")
    for item in rows:
        if item["upstreamRawSources"] and len(item["runtimeUrl"])<95:
            print("  "+item["runtimeUrl"]+" <- "+item["upstreamRawSources"][0]
                  +" ["+item["match"]+"]")
            if sum(1 for x in rows[:rows.index(item)+1] if x["upstreamRawSources"])>=12:break
    return report

if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--external-dir",type=Path,default=OTHER_PACKS)
    options=args.parse_args()
    audit(external=options.external_dir)
