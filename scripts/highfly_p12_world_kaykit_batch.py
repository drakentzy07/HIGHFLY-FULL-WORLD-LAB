#!/usr/bin/env python3
"""HIGHFLY P12: import exact-match owned KayKit glTFs for missing WORLD models.

Works only with the original user's PRIVATE KayKit ZIP and ignored HIGHFLY
stage. Never copies media from ClaudeCraft, never changes world placements,
AI, loot, quests, Sim, or source code. Exact conservative correspondences
only; absent/ambiguous model names remain unresolved for human review.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import struct
import subprocess
import tempfile
from urllib.parse import unquote, urlparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ZIP = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
REPORT = ROOT / ".workspace/reports/highfly-p12"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
ALLOWED_PACKS = {
    "KayKit Medieval Hexagon Pack 1.0.1",
    "KayKit Dungeon Pack 1.1",
    "KayKit Halloween Bits 1.0",
    "KayKit Forest Nature Pack 1.0",
    "KayKit Furniture Bits 1.0",
    "KayKit RPG Tools Bits 1.0",
    "KayKit Resource Bits 1.0",
}
ALLOWED_GROUPS = {"biome", "dungeon"}
MAX_ZIP_MEMBERS = 70000
MAX_SOURCE_BYTES = 40_000_000
MAX_GLB_BYTES = 65_000_000
MAX_IMPORTS = 120


def secure_private(p: Path) -> None:
    if not p.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("P12_PRIVATE_WORKSPACE_ONLY: " + str(p))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(original: Path, stage: Path, library_zip: Path, report: Path) -> None:
    for p in (original, stage, library_zip, report):
        secure_private(p)
    if not library_zip.is_file() or library_zip.is_symlink():
        raise RuntimeError("USER_OWNED_KAYKIT_ARCHIVE_MISSING")
    status = stage / "HIGHFLY_STAGE_STATUS.json"
    if not status.is_file():
        raise RuntimeError("P0_HIGHFLY_STAGE_MISSING")
    data = json.loads(status.read_text(encoding="utf8"))
    if data.get("sourceCommit") != PIN or data.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("P0_SOURCE_OR_MEDIA_POLICY_MISMATCH")
    if not (original / ".git").is_dir():
        raise RuntimeError("ORIGINAL_REFERENCE_NOT_FOUND")
    commit = subprocess.check_output(
        ["git", "-C", str(original), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != PIN:
        raise RuntimeError("ORIGINAL_REFERENCE_PIN_MISMATCH")
    for relative in ("src/sim/eastbrook_layout.ts", "src/sim/items.ts",
                     "src/sim/corpse_loot_state.ts", "src/sim/mob/lifecycle.ts"):
        a, b = original / relative, stage / relative
        if not a.is_file() or not b.is_file() or digest(a) != digest(b):
            raise RuntimeError("PROTECTED_RPG_CODE_MISMATCH: " + relative)


def zip_members(z: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    members = z.infolist()
    if len(members) > MAX_ZIP_MEMBERS:
        raise RuntimeError("ZIP_TOO_MANY_MEMBERS")
    table = {}
    for m in members:
        if m.is_dir():
            continue
        p = PurePosixPath(m.filename)
        if (p.is_absolute() or ".." in p.parts or
            "\\" in m.filename or not p.parts or
            len(m.filename) > 700 or m.file_size > MAX_SOURCE_BYTES):
            continue
        if ((m.external_attr >> 16) & 0o170000) == 0o120000:
            continue
        table[m.filename] = m
    return table


def index_models(table: dict) -> dict:
    by_pack_stem = defaultdict(list)
    for name in table:
        p = PurePosixPath(name)
        if p.suffix.lower() != ".gltf" or len(p.parts) < 4:
            continue
        pack = next((part for part in p.parts if part in ALLOWED_PACKS), None)
        if pack is None:
            continue
        by_pack_stem[(pack, p.stem.lower())].append(name)
    return by_pack_stem


def candidate_stems(original_stem: str, group: str) -> list[tuple[str, str]]:
    s = original_stem.lower()
    if group == "dungeon":
        return [(pack, s) for pack in ("KayKit Dungeon Pack 1.1",
            "KayKit Halloween Bits 1.0", "KayKit Furniture Bits 1.0")]
    if group == "biome":
        if s.startswith("hexb_") or s.startswith("hexr_"):
            color = "blue" if s.startswith("hexb_") else "red"
            base = s.split("_", 1)[1]
            return [("KayKit Medieval Hexagon Pack 1.0.1", "building_" + base + "_" + color),
                    ("KayKit Medieval Hexagon Pack 1.0.1", base + "_" + color)]
        if s.startswith("kcas_"):
            base = s[5:]
            return [("KayKit Medieval Hexagon Pack 1.0.1", base)]
        return [(pack, s) for pack in
                ("KayKit Medieval Hexagon Pack 1.0.1", "KayKit Forest Nature Pack 1.0",
                 "KayKit RPG Tools Bits 1.0", "KayKit Resource Bits 1.0")]
    return []


def match_asset(file: Path, reference_public: Path, index: dict) -> dict:
    rel = file.relative_to(reference_public)
    group = rel.parts[1]
    options = candidate_stems(file.stem, group)
    # One exact matching source in the first priority pack with a hit; if two
    # files in same pack share basename we DO NOT guess among them.
    for pack, stem in options:
        matches = index.get((pack, stem), [])
        if len(matches) == 1:
            return {"status": "EXACT_SOURCE_NAME", "sourceZipMember": matches[0],
                    "sourcePack": pack, "matchedStem": stem}
        if len(matches) > 1:
            return {"status": "AMBIGUOUS_SOURCE_NAMES",
                    "alternatives": sorted(matches)[:8]}
    return {"status": "NO_EXACT_KAYKIT_SOURCE"}


def source_manifest(reference: Path, stage: Path, index: dict) -> dict:
    original_public = reference / "public"
    stage_public = stage / "public"
    rows = []
    groups = Counter()
    for original in sorted((original_public / "models").rglob("*.glb")):
        if original.is_symlink():
            continue
        rel = original.relative_to(original_public)
        if len(rel.parts) < 3 or rel.parts[1] not in ALLOWED_GROUPS:
            continue
        dst = stage_public / rel
        if dst.is_file():
            continue
        matched = match_asset(original, original_public, index)
        groups[matched["status"]] += 1
        rows.append({"target": rel.as_posix(), **matched})
    matches = [r for r in rows if r["status"] == "EXACT_SOURCE_NAME"]
    return {"items": rows, "exactMatches": matches, "statuses": dict(groups)}


def safe_dependency(member: str, uri: str, table: dict) -> str:
    if uri.startswith("data:"):
        return ""
    parsed = urlparse(uri)
    if (not uri or uri.startswith(("/", "\\")) or parsed.scheme or parsed.netloc
            or parsed.query or parsed.fragment or "\\" in uri):
        raise RuntimeError("GLTF_EXTERNAL_DEPENDENCY_REJECTED: " + uri)
    normalized = posixpath.normpath(
        posixpath.join(posixpath.dirname(member), unquote(uri))
    )
    p = PurePosixPath(normalized)
    root_parts = PurePosixPath(member).parts[:2]  # owned collection root + exact pack
    if p.is_absolute() or ".." in p.parts or p.parts[:2] != root_parts:
        raise RuntimeError("GLTF_DEPENDENCY_OUTSIDE_SOURCE_PACK: " + uri)
    if normalized not in table:
        raise RuntimeError("GLTF_REQUIRED_DEPENDENCY_NOT_IN_ZIP: " + normalized)
    return normalized


def unpack_selected(z: zipfile.ZipFile, table: dict, member: str,
                    tmp: Path) -> Path:
    if member not in table:
        raise RuntimeError("UNEXPECTED_KAYKIT_ZIP_MEMBER")
    document = json.loads(z.read(table[member]).decode("utf8"))
    if not isinstance(document.get("meshes"), list) or not document["meshes"]:
        raise RuntimeError("MODEL_WITHOUT_MESHES: " + member)
    names = {member}
    for section in ("buffers", "images"):
        for item in document.get(section, []):
            uri = item.get("uri")
            if uri:
                dep = safe_dependency(member, uri, table)
                if dep:
                    names.add(dep)
    for name in names:
        out = tmp / name
        if not out.resolve().is_relative_to(tmp.resolve()):
            raise RuntimeError("ZIP_SLIP_BLOCKED")
        out.parent.mkdir(parents=True, exist_ok=True)
        with z.open(table[name]) as stream, out.open("wb") as output:
            shutil.copyfileobj(stream, output)
    return tmp / member


def glb_valid(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size > MAX_GLB_BYTES:
        return False
    with path.open("rb") as f:
        h = f.read(20)
    return (len(h) == 20 and h[:4] == b"glTF" and
            struct.unpack_from("<I", h, 4)[0] == 2 and
            struct.unpack_from("<I", h, 8)[0] == path.stat().st_size and
            h[16:20] == b"JSON")


def import_batch(reference: Path, stage: Path, report: Path,
                 archive: Path, chosen: list[dict]) -> list[dict]:
    # Check ALL targets before calling the converter, creating temp folders,
    # or writing any GLB. The earlier version checked per item inside the loop
    # and could run a converter before noticing a later output collision.
    # Fail closed on unexpected or duplicate paths.
    secure_private(reference)
    secure_private(stage)
    secure_private(report)
    secure_private(archive)
    seen = set()
    for item in chosen:
        relative = PurePosixPath(item["target"])
        if (relative.is_absolute() or ".." in relative.parts or
                len(relative.parts) < 3 or relative.parts[0] != "models" or
                relative.parts[1] not in ALLOWED_GROUPS or
                relative.suffix.lower() != ".glb" or
                "\\" in item["target"]):
            raise RuntimeError("INVALID_PRIVATE_MEDIA_TARGET: " + str(relative))
        if item["target"] in seen:
            raise RuntimeError("DUPLICATE_MEDIA_TARGET: " + item["target"])
        seen.add(item["target"])
        target = stage / "public" / item["target"]
        if target.exists() or target.is_symlink():
            raise RuntimeError("REFUSE_TO_OVERWRITE_EXISTING_MEDIA: " + str(target))
    executable = reference / "node_modules/.bin/gltf-transform"
    if not executable.is_file():
        raise RuntimeError("GLTF_TRANSFORM_TOOL_MISSING_IN_PRIVATE_REFERENCE")
    report.mkdir(parents=True, exist_ok=True)
    staged = []
    with zipfile.ZipFile(archive, "r") as z:
        table = zip_members(z)
        with tempfile.TemporaryDirectory(prefix="p12-assets-", dir=str(report)) as workspace:
            work = Path(workspace)
            for i, item in enumerate(chosen):
                target = stage / "public" / item["target"]
                if target.is_symlink() or target.exists():
                    raise RuntimeError("REFUSE_TO_OVERWRITE_EXISTING_MEDIA: " + str(target))
                source = unpack_selected(z, table, item["sourceZipMember"],
                                         work / ("source-" + str(i)))
                output = work / ("converted-" + str(i) + ".glb")
                process = subprocess.run(
                    [str(executable), "copy", str(source), str(output)],
                    cwd=str(reference), capture_output=True, text=True,
                    timeout=120, check=False)
                if process.returncode != 0 or not glb_valid(output):
                    raise RuntimeError("KAYKIT_GLB_CONVERSION_FAILED: " +
                                       item["target"] + " " + process.stderr[-900:])
                staged.append((item, output))
            # Only publish into PRIVATE stage after ALL conversions succeeded.
            result = []
            for item, output in staged:
                target = stage / "public" / item["target"]
                if target.exists() or target.is_symlink():
                    raise RuntimeError("MEDIA_DESTINATION_CREATED_DURING_IMPORT: " + str(target))
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(output, target)
                result.append({"target": item["target"],
                               "sourceZipMember": item["sourceZipMember"],
                               "sha256": digest(target),
                               "bytes": target.stat().st_size,
                               "rightsClearedForPublicRelease": False})
    return result


def main() -> None:
    arg = argparse.ArgumentParser()
    arg.add_argument("--apply", action="store_true")
    arg.add_argument("--limit", type=int, default=60)
    args = arg.parse_args()
    if not 1 <= args.limit <= MAX_IMPORTS:
        raise RuntimeError("INVALID_BATCH_SIZE")
    validate(REFERENCE, STAGE, ZIP, REPORT)
    with zipfile.ZipFile(ZIP) as z:
        index = index_models(zip_members(z))
    inventory = source_manifest(REFERENCE, STAGE, index)
    selected = inventory["exactMatches"][:args.limit]
    REPORT.mkdir(parents=True, exist_ok=True)
    report = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P12_BULK_EXACT_KAYKIT_WORLD_MODEL_IMPORT",
        "originalReferenceModified": False,
        "gameCodeModified": False,
        "simulationAndRpgCodeModified": False,
        "mediaFromClaudeCraftCopied": False,
        "licenseClearedForPublicRelease": False,
        "statusCounts": inventory["statuses"],
        "exactMatchesAvailable": len(inventory["exactMatches"]),
        "nextBatchMax": args.limit,
        "selectedForThisRun": selected,
        "firstUnresolved": [row for row in inventory["items"]
                           if row["status"] != "EXACT_SOURCE_NAME"][:50],
        "imported": [],
    }
    if args.apply:
        report["imported"] = import_batch(REFERENCE, STAGE, REPORT, ZIP, selected)
    (REPORT / "WORLD_KAYKIT_P12.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("[HIGHFLY] P12 WORLD KAYKIT BATCH: " + json.dumps({
        "availableExactMatches": report["exactMatchesAvailable"],
        "attempted": len(selected),
        "imported": len(report["imported"]),
        "unmatchedOrAmbiguous": sum(inventory["statuses"].get(k, 0)
             for k in ("NO_EXACT_KAYKIT_SOURCE", "AMBIGUOUS_SOURCE_NAMES")),
        "gameplayVerified": False,
        "originalMediaCopied": False,
        "originalSourceChanged": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] P12 PRIVATE REPORT: " + str(REPORT / "WORLD_KAYKIT_P12.json"))
    print("[HIGHFLY] NO MATCH = NO IMPORT. NOTHING PUBLISHED. RUN P9 BUILD AFTER IMPORT.")


if __name__ == "__main__":
    main()
