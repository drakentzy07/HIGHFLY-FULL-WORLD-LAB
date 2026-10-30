#!/usr/bin/env python3
"""HIGHFLY P8 — privately convert SEVEN owned KayKit glTF building sources to GLB.

Does not alter original ClaudeCraft, HIGHFLY's Eastbrook layout, simulation,
NPC, quests, loot, collisions, character systems, or save. Target paths are
the exact existing Eastbrook visual asset IDs in the ignored independent stage.
The model's visual compatibility and commercial license remain UNVERIFIED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import tempfile
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
PACK = ROOT / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1"
REPORT_DIR = ROOT / ".workspace/reports/highfly-p8"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
BUILDINGS = {
    "townhall": "hexb_townhall.glb",
    "workshop": "hexb_workshop.glb",
    "tavern": "hexb_tavern.glb",
    "church": "hex_church.glb",
    "home_a": "hexb_home_a.glb",
    "home_b": "hexb_home_b.glb",
    "market": "hexb_market.glb",
}
PALETTE = ("blue", "green", "red", "yellow", "purple", "orange", "neutral", "brown", "white", "black")
REPORT_NAME = "EASTBROOK_OWNED_BUILDINGS_P8.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def secure_path(path: Path) -> None:
    if not path.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("PRIVATE_WORKSPACE_REQUIRED: " + str(path))


def check_stage(reference: Path, stage: Path, pack: Path, report_dir: Path) -> None:
    for path in (reference, stage, pack, report_dir):
        secure_path(path)
    status_file = stage / "HIGHFLY_STAGE_STATUS.json"
    if not status_file.is_file():
        raise RuntimeError("MISSING_HIGHFLY_STAGE_P0")
    status = json.loads(status_file.read_text(encoding="utf8"))
    if status.get("sourceCommit") != PIN or status.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("UNEXPECTED_HIGHFLY_STAGE")
    if not (reference / ".git").is_dir():
        raise RuntimeError("MISSING_CLAUDECRAFT_REFERENCE")
    sha = subprocess.check_output(["git", "-C", str(reference), "rev-parse", "HEAD"], text=True).strip()
    if sha != PIN:
        raise RuntimeError("CLAUDECRAFT_SOURCE_COMMIT_MISMATCH")
    for relative in ("src/sim/eastbrook_layout.ts", "src/sim/items.ts",
                     "src/sim/corpse_loot_state.ts", "src/sim/mob/lifecycle.ts"):
        old, new = reference / relative, stage / relative
        if not old.is_file() or not new.is_file() or digest(old) != digest(new):
            raise RuntimeError("PROTECTED_RPG_CODE_DIFFERENCE: " + relative)
    if not pack.is_dir() or pack.is_symlink():
        raise RuntimeError("PRIVATE_KAYKIT_MEDIEVAL_HEXAGON_NOT_EXTRACTED")


def dependencies(file: Path, pack: Path) -> dict:
    """Check source glTF JSON and ensure all external URIs are local to owned pack."""
    if file.is_symlink() or not file.is_file() or file.suffix.lower() != ".gltf":
        raise RuntimeError("NOT_A_LOCAL_GLTF_FILE: " + str(file))
    document = json.loads(file.read_text(encoding="utf8"))
    if not isinstance(document.get("meshes"), list) or not document["meshes"]:
        raise RuntimeError("GLTF_HAS_NO_MESHES: " + str(file))
    names = []
    for section in ("buffers", "images"):
        for node in document.get(section, []):
            uri = node.get("uri")
            if not uri or uri.startswith("data:"):
                continue
            parsed = urlparse(uri)
            if parsed.scheme or parsed.netloc or uri.startswith(("/", "\\")) or "?" in uri or "#" in uri:
                raise RuntimeError("GLTF_DEPENDENCY_NOT_LOCAL: " + uri)
            dependency = (file.parent / unquote(uri)).resolve()
            if not dependency.is_relative_to(pack.resolve()):
                raise RuntimeError("GLTF_DEPENDENCY_OUTSIDE_KAYKIT_PACK: " + uri)
            if not dependency.is_file() or dependency.is_symlink():
                raise RuntimeError("GLTF_DEPENDENCY_MISSING_OR_LINK: " + str(dependency))
            names.append(dependency.relative_to(pack).as_posix())
    return {"meshCount": len(document["meshes"]), "externalDependencies": sorted(set(names))}


def find_source(pack: Path, kind: str) -> Path:
    # Keep selection deterministic. A blue palette is provisional, not a
    # design decision. No geometry is modified by this import.
    chosen = None
    gltfs = [p for p in pack.rglob("*.gltf") if p.stem.lower().startswith("building_")]
    for color in PALETTE:
        filename = f"building_{kind}_{color}"
        matches = sorted(p for p in gltfs if p.stem.lower() == filename)
        if matches:
            chosen = matches[0]
            break
    if chosen is None:
        matches = sorted(p for p in gltfs if p.stem.lower() == f"building_{kind}")
        chosen = matches[0] if matches else None
    if chosen is None:
        raise RuntimeError("NO_KAYKIT_GLTF_SOURCE_FOR_BUILDING: " + kind)
    if not chosen.resolve().is_relative_to(pack.resolve()) or chosen.is_symlink():
        raise RuntimeError("UNSAFE_KAYKIT_MODEL_SOURCE")
    return chosen


def inspect_glb(path: Path) -> dict:
    with path.open("rb") as fp:
        header = fp.read(20)
        if len(header) != 20 or header[:4] != b"glTF":
            raise RuntimeError("CONVERTED_GLB_INVALID_MAGIC")
        _, version, total, chunk, kind = struct.unpack("<4sIII4s", header)
        if version != 2 or kind != b"JSON" or total != path.stat().st_size:
            raise RuntimeError("CONVERTED_GLB_INVALID_HEADER")
        if chunk <= 0 or chunk > 12 * 1024 * 1024:
            raise RuntimeError("CONVERTED_GLB_UNEXPECTED_JSON_SIZE")
        document = json.loads(fp.read(chunk).decode("utf8").rstrip(" \x00"))
    if not document.get("meshes"):
        raise RuntimeError("CONVERTED_GLB_NO_RENDERABLE_MESHES")
    # Image buffers must be embedded in a GLB, not external linked file URIs.
    if any(row.get("uri") and not row["uri"].startswith("data:")
           for section in ("buffers", "images") for row in document.get(section, [])):
        raise RuntimeError("CONVERTED_GLB_STILL_HAS_EXTERNAL_LINKS")
    return {"bytes": path.stat().st_size, "meshes": len(document["meshes"]),
            "materials": len(document.get("materials", [])),
            "images": len(document.get("images", []))}


def converter_path(reference: Path) -> Path:
    result = reference / "node_modules/.bin/gltf-transform"
    if not result.is_file():
        raise RuntimeError(
            "GLTF_TRANSFORM_NOT_INSTALLED_IN_REFERENCE: run pnpm install --frozen-lockfile "
            "in the private reference checkout only after confirming the dependency setup.")
    return result


def convert(source: Path, destination: Path, executable: Path, cwd: Path) -> None:
    outcome = subprocess.run(
        [str(executable), "copy", str(source), str(destination)],
        cwd=str(cwd), capture_output=True, text=True, timeout=120, check=False)
    if outcome.returncode != 0:
        raise RuntimeError("GLTF_TRANSFORM_CONVERSION_FAILED: " + (outcome.stderr or outcome.stdout)[-2000:])
    inspect_glb(destination)


def plan(reference: Path=REFERENCE, stage: Path=STAGE, pack: Path=PACK,
         report_dir: Path=REPORT_DIR) -> list[dict]:
    check_stage(reference, stage, pack, report_dir)
    results = []
    targets = set()
    for kind, original_name in BUILDINGS.items():
        source = find_source(pack, kind)
        dep = dependencies(source, pack)
        target = stage / "public/models/biome" / original_name
        if target in targets:
            raise RuntimeError("DUPLICATE_BUILDING_TARGET")
        targets.add(target)
        results.append({
            "kind":kind, "source": source, "sourcePath":source.relative_to(pack).as_posix(),
            "sourceSha256":digest(source),
            "sourceMeshCount":dep["meshCount"],
            "externalDependencies":dep["externalDependencies"],
            "target": target, "publicUrl":"/models/biome/" + original_name,
            "palette":"blue-provisional" if source.stem.lower().endswith("_blue") else "alternate-provisional",
        })
    return results


def install(entries: list[dict], reference: Path, stage: Path, report_dir: Path) -> dict:
    secure_path(report_dir)
    previous = report_dir / REPORT_NAME
    old = json.loads(previous.read_text(encoding="utf8")) if previous.is_file() else None
    if old and old.get("sourceCommit") != PIN:
        raise RuntimeError("EXISTING_P8_REPORT_SOURCE_MISMATCH")
    for row in entries:
        target = row["target"]
        if target.is_symlink():
            raise RuntimeError("P8_SYMLINK_TARGET: " + str(target))
        if target.exists():
            old_row = next((item for item in old.get("buildings", []) if item["publicUrl"] == row["publicUrl"]), None) if old else None
            if not old_row or old_row.get("sourceSha256") != row["sourceSha256"] or old_row.get("glbSha256") != digest(target):
                raise RuntimeError("P8_EXISTING_TARGET_NOT_FROM_THIS_IMPORT: " + str(target))
    missing = [row for row in entries if not row["target"].exists()]
    exe = converter_path(reference) if missing else None
    staged = {}
    with tempfile.TemporaryDirectory(prefix="highfly-p8-conversion-", dir=str(report_dir.parent)) as tmp:
        for row in missing:
            destination = Path(tmp) / row["target"].name
            convert(row["source"], destination, exe, reference)
            staged[row["publicUrl"]] = destination
        # All conversions succeeded before the first output is copied.
        for row in missing:
            target = row["target"]
            if target.exists() or target.is_symlink():
                raise RuntimeError("P8_TARGET_CREATED_CONCURRENTLY: " + str(target))
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged[row["publicUrl"]], target)
    report = {
        "project":"HIGHFLY ORIGIN", "phase":"P8_PRIVATE_EASTBROOK_GLB_IMPORT",
        "sourceCommit":PIN,
        "licensedForCommercialRelease":False,
        "gameplayVerified":False,
        "noClaudeCraftMediaCopied":True,
        "sourceOfAssets":"User-owned private KayKit Complete V7 / Medieval Hexagon 1.0.1",
        "originalLayoutAltered":False, "originalReferenceAltered":False,
        "protectedRpgCodeAltered":False,
        "modelStyle":"BLUE provisional (subject to owner visual review)",
        "buildings":[{
            "kind":r["kind"], "source":r["sourcePath"],
            "sourceSha256":r["sourceSha256"], "palette":r["palette"],
            "sourceMeshes":r["sourceMeshCount"],
            "externalDependencies":r["externalDependencies"],
            "publicUrl":r["publicUrl"],
            "glbSha256":digest(r["target"]),
            "glb":inspect_glb(r["target"]),
            "status":"PRIVATE_MODEL_IMPORTED_REQUIRES_VISUAL_SCALING_AND_LICENSE_REVIEW",
        } for r in entries],
        "next":"Resolve remaining required world media; private build Eastbrook; visually verify appearance, window materials, doors and collision vs preserved footprints.",
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    previous.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--install",action="store_true")
    args=parser.parse_args()
    rows=plan()
    print("[HIGHFLY] P8 BUILDINGS PLAN: "+json.dumps({
        "sourceModels":len(rows),
        "models":[r["kind"] for r in rows],
        "sources":[r["sourcePath"] for r in rows],
        "externalDependencyCount":sum(len(r["externalDependencies"]) for r in rows),
        "targetGame":"INDEPENDENT_HIGHFLY_PRIVATE_STAGE",
    },ensure_ascii=False))
    if not args.install:
        print("[HIGHFLY] P8 DRY RUN ONLY; run --install to convert 7 owned models to private GLB.")
        return
    REPORT_DIR.mkdir(parents=True,exist_ok=True)
    report=install(rows,REFERENCE,STAGE,REPORT_DIR)
    print("[HIGHFLY] P8 PRIVATE BUILDINGS INSTALLED: "+json.dumps({
        "uniqueModels":len(report["buildings"]),
        "originalWorldUnchanged":True,
        "sourceCodeUnchanged":True,
        "commercialReleaseBlocked":True,
        "privateGameAssets":len(report["buildings"]),
    },ensure_ascii=False))
    print("[HIGHFLY] P8 PRIVATE REPORT: "+str(REPORT_DIR/REPORT_NAME))
    print("[HIGHFLY] NO GAME BUILD LAUNCHED, original ClaudeCraft and HIGHFLY world layout untouched.")


if __name__=="__main__":
    main()
