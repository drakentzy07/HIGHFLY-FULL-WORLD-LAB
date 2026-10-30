#!/usr/bin/env python3
"""HIGHFLY P7b: find ACTUAL KayKit Medieval Hexagon building files in any model format.

Previous P7 looked only for .glb and returned 0. This inspection enumerates
FBX, OBJ, glTF and GLB without converting or copying assets into either game.
No claim of license approval or that FBX is immediately browser-playable.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
KAYKIT = ROOT / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
PACK = "KayKit Medieval Hexagon Pack 1.0.1"
REPORT = ROOT / ".workspace/reports/highfly-p7b"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
SUFFIXES = {".glb", ".gltf", ".fbx", ".obj"}
ORDER = {".glb":0, ".gltf":1, ".fbx":2, ".obj":3}
RX = re.compile(r"makeBuilding\(\s*'([^']+)'\s*,\s*'(/models/[^']+\.glb)'")
PALETTES = ("blue", "green", "red", "yellow", "purple", "orange", "neutral", "brown", "white", "black")
BUILDING_KEYS = ("townhall", "workshop", "tavern", "church", "home_a", "home_b", "market")


def source_kind(model: str) -> str:
    stem = Path(model).stem.lower()
    return stem.removeprefix("hexb_").removeprefix("hex_")


def building_variant(path: Path) -> tuple[str, str] | None:
    stem = path.stem.lower()
    if not stem.startswith("building_"):
        return None
    for building in sorted(BUILDING_KEYS, key=len, reverse=True):
        prefix = "building_" + building
        if stem == prefix:
            return building, "default"
        if not stem.startswith(prefix + "_"):
            continue
        palette = stem[len(prefix)+1:]
        if palette in PALETTES:
            return building, palette
    return None


def check_environment(stage: Path, original: Path, library: Path, report: Path) -> None:
    private = (ROOT / ".workspace").resolve()
    for path in (stage, original, library, report):
        if not path.resolve().is_relative_to(private):
            raise RuntimeError("REFUSING_OUTSIDE_PRIVATE_WORKSPACE: " + str(path))
    manifest = stage / "HIGHFLY_STAGE_STATUS.json"
    if not manifest.is_file():
        raise RuntimeError("HIGHFLY_STAGE_NOT_FOUND")
    state = json.loads(manifest.read_text(encoding="utf8"))
    if state.get("sourceCommit") != PIN or state.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("HIGHFLY_STAGE_NOT_PINNED")
    if not (original / ".git").is_dir():
        raise RuntimeError("REFERENCE_GIT_MISSING")
    sha = subprocess.check_output(["git", "-C", str(original), "rev-parse", "HEAD"], text=True).strip()
    if sha != PIN:
        raise RuntimeError("REFERENCE_NOT_PINNED")
    scene = stage / "src/sim/eastbrook_layout.ts"
    reference = original / "src/sim/eastbrook_layout.ts"
    if scene.read_bytes() != reference.read_bytes():
        raise RuntimeError("EASTBROOK_STAGE_LAYOUT_NOT_IDENTICAL_TO_REFERENCE")


def audit(stage: Path=STAGE, original: Path=ORIGINAL, library: Path=KAYKIT,
          report: Path=REPORT) -> dict:
    check_environment(stage, original, library, report)
    contents = (stage / "src/sim/eastbrook_layout.ts").read_text(encoding="utf8")
    original_buildings = [
        {"id": match.group(1), "originalModel": match.group(2),
         "buildingType": source_kind(match.group(2))}
        for match in RX.finditer(contents)
    ]
    if len(original_buildings) != 11:
        raise RuntimeError("EXPECTED_11_EASTBROOK_BUILDINGS_GOT_"+str(len(original_buildings)))
    pack_root = library / PACK
    if not pack_root.is_dir() or pack_root.is_symlink():
        raise RuntimeError("MEDIEVAL_HEXAGON_NOT_EXTRACTED")
    by_type: dict[str,list[dict]] = {}
    formats = Counter()
    all_models = []
    for path in pack_root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("SYMLINK_IN_PACK: "+str(path))
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        if path.stat().st_size == 0:
            continue
        formats[path.suffix.lower()] += 1
        all_models.append(path.relative_to(library).as_posix())
        variant = building_variant(path)
        if variant is None:
            continue
        kind, color = variant
        suffix = path.suffix.lower()
        by_type.setdefault(kind, []).append({
            "relativePath": path.relative_to(library).as_posix(),
            "modelType": kind,
            "color": color,
            "format": suffix,
            "sizeBytes": path.stat().st_size,
            "directGlbCandidate": suffix == ".glb",
            "requiresConversion": suffix in (".fbx", ".obj"),
            "requiresDependencyPackaging": suffix == ".gltf",
            "visualCompatibilityVerified": False,
            "licenseFileVerified": False,
        })
    for entries in by_type.values():
        entries.sort(key=lambda x:(ORDER[x["format"]],x["color"],x["relativePath"]))
    matches=[]
    for building in original_buildings:
        model_kind=building["buildingType"]
        options=by_type.get(model_kind,[])
        matches.append({
            **building, "sourceFilesFound":len(options),
            "previewCandidates":options[:15],
            "formats":dict(Counter(x["format"] for x in options)),
            "decision":"NEEDS_SCALE_GEOMETRY_RIGHTS_REVIEW" if options else "NO_MATCH_IN_SELECTED_FORMATS",
            "preserve":["id","position","rotation","footprint","npcAnchors","interiorLinks","questReferences"],
        })
    n=sum(row["sourceFilesFound"]>0 for row in matches)
    result={
        "project":"HIGHFLY ORIGIN","phase":"P7B_MULTIFORMAT_BUILDINGS",
        "originalVersion":"0.44.7","originalWorldUnchanged":True,"highflyWorldUnchanged":True,
        "filesCopiedToGame":0,"placements":len(matches),
        "placementsWithCandidate":n,"candidateBuildingTypes":sorted(by_type),
        "sourceModelFiles":len(all_models),"sourceFormats":dict(formats),
        "buildingSourceFilesByType":{key:len(val) for key,val in sorted(by_type.items())},
        "buildings":matches,
        "sampleModelNames":all_models[:25],
        "limitations":["An FBX/OBJ model must be converted before loading with the existing GLTFLoader.",
                       "A .gltf file may require external .bin/textures; only .glb is a single GLB file.",
                       "Names and file sizes do not prove scale, mesh quality or license.",
                       "No world models, NPCs, quests, loot, movement or saves were changed."],
    }
    report.mkdir(parents=True,exist_ok=True)
    (report / "EASTBROOK_KAYKIT_MULTIFORMAT_P7B.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lines=[
        "# HIGHFLY P7b - Eastbrook x KayKit building exports", "",
        "Read-only. Source candidates are not imported, transformed or release-cleared.", "",
        f"- Eastbrook building placements: {len(matches)}",
        f"- Placements with candidate files: {n}",
        f"- Total model files in extracted pack: {len(all_models)}",
        f"- Available formats: {dict(formats)}", "",
        "| Original building ID | Type | Source candidates | Formats |",
        "|---|---|---:|---|",
    ]
    for b in matches:
        lines.append(f"| {b['id']} | {b['buildingType']} | {b['sourceFilesFound']} | {b['formats']} |")
    lines.extend(["", "## Next integration action", "Use GLB if present; otherwise convert selected owned FBX/OBJ (or package glTF dependencies), verify dimensions + real geometry before changing visuals; preserve world IDs, collision and NPC anchors.", ""])
    (report / "EASTBROOK_KAYKIT_MULTIFORMAT_P7B.md").write_text("\n".join(lines),encoding="utf8")
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage",type=Path,default=STAGE)
    parser.add_argument("--reference",type=Path,default=ORIGINAL)
    parser.add_argument("--kaykit",type=Path,default=KAYKIT)
    parser.add_argument("--report",type=Path,default=REPORT)
    args=parser.parse_args()
    result=audit(args.stage,args.reference,args.kaykit,args.report)
    print("[HIGHFLY] P7B WORLD BUILDINGS: "+json.dumps({
        "eastbrookPlacements":result["placements"],
        "placementsWithCandidate":result["placementsWithCandidate"],
        "modelFilesByFormat":result["sourceFormats"],
        "matchedModelTypes":result["buildingSourceFilesByType"],
        "filesCopiedToGame":0,
    },ensure_ascii=False))
    print("[HIGHFLY] P7B PRIVATE REPORT: "+str(args.report/"EASTBROOK_KAYKIT_MULTIFORMAT_P7B.md"))
    print("[HIGHFLY] Eastbrook and ClaudeCraft untouched. Models require visual/rights verification.")


if __name__=="__main__":
    main()
