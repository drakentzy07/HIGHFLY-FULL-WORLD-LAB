#!/usr/bin/env python3
"""HIGHFLY P7: match Eastbrook's 11 existing building records against own KayKit GLBs.

Read-only to games/assets. Creates a private, non-authoritative candidate matrix
for visual/scale/license review. Does not change meshes, model URLs, collisions,
NPC anchors, gameplay or publishing configuration.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
LIBRARY = ROOT / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
PACK_NAME = "KayKit Medieval Hexagon Pack 1.0.1"
REPORT = ROOT / ".workspace/reports/highfly-p7"
SOURCE_COMMIT = "493c35a108cef6c8aa290e8793107b1cd117886e"
BUILDING_RX = re.compile(
    r"makeBuilding\(\s*'(?P<id>[^']+)'\s*,\s*'(?P<model>/models/[^']+\.glb)'",
    re.M,
)
BUILDING_SYNONYMS = {
    "townhall": ("townhall",), "workshop": ("workshop",),
    "tavern": ("tavern",), "church": ("church",),
    "market": ("market",), "home_a": ("home_a",),
    "home_b": ("home_b",),
}
MAX_GLB_FILES = 3000


def require_private(path: Path, prefix: Path) -> None:
    if not path.resolve().is_relative_to(prefix.resolve()):
        raise RuntimeError("PRIVATE_PATH_REQUIRED: " + str(path))


def source_key(model_url: str) -> str:
    stem = Path(model_url).stem.lower()
    for prefix in ("hexb_", "hex_"):
        if stem.startswith(prefix):
            return stem[len(prefix):]
    return stem


def glb_summary(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("INVALID_GLB_PATH: " + str(path))
    with path.open("rb") as f:
        header = f.read(20)
    size = path.stat().st_size
    if len(header) < 20 or header[:4] != b"glTF" or struct.unpack_from("<I", header, 4)[0] != 2:
        raise RuntimeError("INVALID_GLB2_HEADER: " + str(path))
    if struct.unpack_from("<I", header, 8)[0] != size or header[16:20] != b"JSON":
        raise RuntimeError("INVALID_GLB2_SIZE_OR_CHUNK: " + str(path))
    return {"bytes": size}


def eastbrook(stage: Path) -> list[dict]:
    layout = stage / "src/sim/eastbrook_layout.ts"
    if not layout.is_file():
        raise RuntimeError("EASTBROOK_LAYOUT_MISSING")
    return [{
        "id": m.group("id"),
        "originalAssetId": m.group("model"),
        "kind": source_key(m.group("model")),
    } for m in BUILDING_RX.finditer(layout.read_text(encoding="utf-8"))]


def candidates(pack: Path) -> dict[str, list[Path]]:
    if not pack.is_dir() or pack.is_symlink():
        raise RuntimeError("KAYKIT_MEDIEVAL_PACK_NOT_EXTRACTED")
    glbs = list(pack.rglob("*.glb"))
    if len(glbs) > MAX_GLB_FILES:
        raise RuntimeError("TOO_MANY_GLB_FILES")
    out: dict[str, list[Path]] = {}
    for file in glbs:
        if file.is_symlink():
            raise RuntimeError("SYMLINK_IN_KAYKIT_PACK: " + str(file))
        s = file.stem.lower()
        if not s.startswith("building_"):
            continue
        # For example "building_home_A_blue.glb" is "home_a", color "blue".
        for key in BUILDING_SYNONYMS:
            base = "building_" + key
            if s == base or s.startswith(base + "_"):
                # Avoid accidental "home_a" matching a different longer building name
                suffix = s[len(base):].lstrip("_")
                if suffix and suffix not in {"blue", "green", "red", "yellow", "purple",
                                               "orange", "neutral", "brown", "white", "black"}:
                    continue
                out.setdefault(key, []).append(file)
                break
    for entries in out.values():
        entries.sort(key=lambda f: ("/gltf/" not in f.as_posix().lower(), f.as_posix().lower()))
    return out


def audit(stage: Path = STAGE, original: Path = ORIGINAL, library: Path = LIBRARY,
          report: Path = REPORT) -> dict:
    private = ROOT / ".workspace"
    for path in (stage, original, library, report):
        require_private(path, private)
    status = stage / "HIGHFLY_STAGE_STATUS.json"
    if not status.is_file():
        raise RuntimeError("P0_PRIVATE_STAGE_MISSING")
    data = json.loads(status.read_text(encoding="utf-8"))
    if data.get("sourceCommit") != SOURCE_COMMIT or data.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("STAGE_SOURCE_OR_MEDIA_POLICY_MISMATCH")
    if not (original / ".git").is_dir():
        raise RuntimeError("REFERENCE_MISSING")
    sha = subprocess.check_output(
        ["git", "-C", str(original), "rev-parse", "HEAD"], text=True).strip()
    if sha != SOURCE_COMMIT:
        raise RuntimeError("REFERENCE_PIN_MISMATCH")
    building_list = eastbrook(stage)
    if len(building_list) != 11:
        raise RuntimeError("EASTBROOK_PLACEMENTS_CHANGED: expected 11, got " + str(len(building_list)))
    originals = (original / "src/sim/eastbrook_layout.ts").read_bytes()
    if (stage / "src/sim/eastbrook_layout.ts").read_bytes() != originals:
        raise RuntimeError("HIGHFLY_EASTBROOK_LAYOUT_CHANGED_UNEXPECTEDLY")
    pack = library / PACK_NAME
    pools = candidates(pack)
    found = set()
    matrix = []
    for b in building_list:
        items = []
        for key in BUILDING_SYNONYMS.get(b["kind"], (b["kind"],)):
            for f in pools.get(key, []):
                details = glb_summary(f)
                found.add(f)
                items.append({
                    "relativeToKayKitLibrary": f.relative_to(library).as_posix(),
                    "bytes": details["bytes"],
                    "formatHeaderValid": True,
                    "licenseApproved": False,
                    "visuallyVerified": False,
                })
        matrix.append({
            **b, "candidateCount": len(items), "candidates": items[:20],
            "decision": "PENDING_VISUAL_SCALE_COLLISION_RIGHTS_REVIEW",
            "preserve": ["buildingId", "position", "rotation", "footprint",
                         "collision", "npcAnchors", "questReferences", "interiorLinks"],
        })
    match_count = sum(bool(row["candidateCount"]) for row in matrix)
    result = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P7_PRIVATE_EASTBROOK_BUILDING_CANDIDATES",
        "referenceCommit": SOURCE_COMMIT,
        "stageWorldUnchanged": True,
        "originalGameUnchanged": True,
        "assetsCopiedIntoGame": 0,
        "buildings": matrix,
        "placements": len(matrix),
        "placementsWithCandidate": match_count,
        "uniqueCandidateGlbsChecked": len(found),
        "package": PACK_NAME,
        "note": "File-header + name match ONLY. Does not prove CC0 provenance, geometry compatibility, world-scale, collisions, entry points, interiors or working gameplay.",
    }
    report.mkdir(parents=True, exist_ok=True)
    (report / "EASTBROOK_KAYKIT_CANDIDATES_P7.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# HIGHFLY P7 — Eastbrook x KayKit Medieval Hexagon", "",
        "Inspection only. No world meshes or actors changed; no license approvals made.", "",
        f"- Original building placements: {len(matrix)}",
        f"- Buildings with candidate GLB: {match_count}",
        f"- Unique candidate GLBs checked: {len(found)}",
        "",
        "| Building ID | Original asset | KayKit candidate(s) | Status |",
        "|---|---|---:|---|",
    ]
    for row in matrix:
        md.append(
            f"| {row['id']} | {row['originalAssetId']} | {row['candidateCount']} | "
            "Review geometry, license, scale, interactions |"
        )
    md.extend(["", "The next decision requires a 3D comparison of candidates and technical mapping. "
                    "Never overwrite Eastbrook placements, NPC/quest anchors or collision information.",
                    "The pack was extracted privately; do not publish it or a game build until rights review.", ""])
    (report / "EASTBROOK_KAYKIT_CANDIDATES_P7.md").write_text(
        "\n".join(md), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=STAGE)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--library", type=Path, default=LIBRARY)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    result = audit(args.stage, args.original, args.library, args.report)
    print("[HIGHFLY] P7 EASTBROOK CANDIDATES: " + json.dumps({
        "placements": result["placements"],
        "withCandidates": result["placementsWithCandidate"],
        "uniqueGlbCandidates": result["uniqueCandidateGlbsChecked"],
        "gameFilesChanged": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] PRIVATE P7 REPORT: " + str(args.report / "EASTBROOK_KAYKIT_CANDIDATES_P7.md"))
    print("[HIGHFLY] No assets copied into HIGHFLY; models not yet verified visually or for release.")


if __name__ == "__main__":
    main()
