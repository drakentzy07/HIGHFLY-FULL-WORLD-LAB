#!/usr/bin/env python3
"""HIGHFLY P6: verify RPG systems preserved + index owned KayKit world packs.

READ-ONLY on ClaudeCraft, HIGHFLY and ZIP. Reports go to ignored .workspace.
The check compares exact source bytes of critical RPG modules, so a green
result proves presence/equality of code, NOT runtime behavior or asset rights.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
HIGHFLY = ROOT / ".workspace/highfly-origin-stage-p0"
ARCHIVE = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
OUT = ROOT / ".workspace/reports/highfly-p6"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"

# Only stable existing v0.44.7 modules; DO NOT require unchanged render manifest
# because P4 deliberately extended the independent renderer mapping.
MODULES = {
    "motor_y_datos": ["src/sim/sim.ts", "src/sim/data.ts"],
    "inventario": ["src/sim/items.ts", "src/sim/inventory_sort.ts"],
    "loot_cadaveres": ["src/sim/corpse_loot_state.ts", "src/sim/loot/enemy_quality.ts"],
    "armas_armaduras_y_equipamiento": ["src/sim/equipment_rules.ts", "src/sim/loadout_gear.ts"],
    "monstruos_vida_y_muerte": ["src/sim/mob/lifecycle.ts"],
    "misiones_y_recompensas": ["src/sim/quests/quest_credit.ts", "src/sim/world_quests.ts"],
    "mapa_eastbrook": ["src/sim/eastbrook_layout.ts"],
}
WORLD_PACKS = (
    ("construcciones", "KayKit Medieval Hexagon Pack 1.0.1"),
    ("vegetacion_y_biomas", "KayKit Forest Nature Pack 1.0"),
    ("mazmorras", "KayKit Dungeon Pack 1.1"),
    ("interiores", "KayKit Furniture Bits 1.0"),
    ("armas_y_loot", "KayKit Fantasy Weapons Bits 1.0"),
    ("objetos_interactivos", "KayKit RPG Tools Bits 1.0"),
    ("personajes_y_npc", "KayKit Adventurers 2.0"),
    ("esqueletos", "KayKit Skeletons 1.1"),
    ("animaciones", "KayKit Character Animations 1.1"),
)
MODEL_EXTS = {".glb", ".gltf", ".fbx", ".obj", ".blend"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def module_integrity(reference: Path, stage: Path) -> dict:
    result = {}
    for group, paths in MODULES.items():
        rows = []
        for relative in paths:
            source, copy = reference / relative, stage / relative
            present = source.is_file() and copy.is_file() and not source.is_symlink() and not copy.is_symlink()
            equal = present and digest(source) == digest(copy)
            rows.append({"path": relative, "presentBoth": present, "identicalBytes": equal})
        result[group] = {"status": "IDENTICAL_SOURCE_CODE" if all(r["identicalBytes"] for r in rows) else "REVIEW_NEEDED",
                         "files": rows}
    return result


def archive_index(archive: Path) -> dict:
    if not archive.is_file() or archive.is_symlink():
        raise RuntimeError("KAYKIT_COMPLETE_ZIP_NOT_FOUND")
    counts = {}
    samples = {}
    with zipfile.ZipFile(archive) as z:
        files = [i for i in z.infolist() if not i.is_dir()]
        if len(files) > 80000:
            raise RuntimeError("UNEXPECTED_ZIP_MEMBER_COUNT")
        for category, pack in WORLD_PACKS:
            selected = [i for i in files if pack in i.filename.split("/")]
            models = [i for i in selected if Path(i.filename).suffix.lower() in MODEL_EXTS]
            counts[category] = {
                "pack": pack,
                "files": len(selected),
                "modelFormatFiles": len(models),
                "uncompressedBytes": sum(i.file_size for i in selected),
                "presentInZip": bool(selected),
            }
            samples[category] = [i.filename for i in models[:12]]
        directory_names = {
            segment for item in files for segment in item.filename.split("/")
            if segment.startswith("KayKit ")
        }
    return {"worldPacks": counts, "modelExamples": samples,
            "namedPackFolders": sorted(directory_names), "archiveTotalFiles": len(files)}


def eastbrook_models(reference: Path) -> dict:
    text = (reference / "src/sim/eastbrook_layout.ts").read_text(encoding="utf8")
    matches = re.findall(r"makeBuilding\(\s*'([^']+)'\s*,\s*'(/models/[^']+\.glb)'", text)
    return {"buildingPlacements": len(matches), "models": [
        {"buildingId": identifier, "originalModelPath": filename,
         "replacementStatus": "UNDECIDED_REQUIRE_VISUAL_AND_LICENSE_CHECK"}
        for identifier, filename in matches
    ]}


def audit(reference: Path = REFERENCE, stage: Path = HIGHFLY,
          archive: Path = ARCHIVE, output: Path = OUT) -> dict:
    private = (ROOT / ".workspace").resolve()
    for path in (reference, stage, archive, output):
        if not path.resolve().is_relative_to(private):
            raise RuntimeError("PRIVATE_WORKSPACE_REQUIRED: " + str(path))
    if not (reference / ".git").is_dir():
        raise RuntimeError("CLAUDECRAFT_REFERENCE_MISSING")
    commit = subprocess.check_output(
        ["git", "-C", str(reference), "rev-parse", "HEAD"], text=True).strip()
    if commit != PIN:
        raise RuntimeError("REFERENCE_COMMIT_MISMATCH")
    status = stage / "HIGHFLY_STAGE_STATUS.json"
    if not status.is_file():
        raise RuntimeError("HIGHFLY_STAGE_MISSING")
    info = json.loads(status.read_text(encoding="utf8"))
    if info.get("sourceCommit") != PIN or info.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("UNEXPECTED_HIGHFLY_STAGE")
    integrity = module_integrity(reference, stage)
    core_intact = all(v["status"] == "IDENTICAL_SOURCE_CODE" for v in integrity.values())
    packs = archive_index(archive)
    buildings = eastbrook_models(reference)
    p4 = stage / "src/render/characters/manifest.ts"
    p4_bridge = p4.is_file() and "HIGHFLY_P4_VISUAL_BRIDGE_START" in p4.read_text(encoding="utf8")
    report = {
        "project": "HIGHFLY ORIGIN", "phase": "P6_RPG_PRESERVATION_AND_WORLD_PACK_INVENTORY",
        "reference": "World of ClaudeCraft v0.44.7", "sourceCommit": PIN,
        "coreRpgCodeIdentical": core_intact, "p4VisualBridgePresent": p4_bridge,
        "systems": integrity, "kaykit": packs, "eastbrook": buildings,
        "licenseStatus": "PER_FILE_VERIFICATION_REQUIRED_NOT_CLEARED_FOR_RELEASE",
        "runtimeStatus": "NOT_YET_VERIFIED_IN_HIGHFLY_INDEPENDENT",
        "readOnlyForGamesAndUserZip": True,
        "next": "Extract Medieval Hexagon privately (only if not already extracted); compare structures by visual, bounds, licensing and IDs. Keep ALL mechanics and other monster types intact.",
    }
    if not output.is_dir():
        output.mkdir(parents=True, exist_ok=True)
    (output / "RPG_AND_WORLD_P6.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    rows = [
        "# HIGHFLY P6 — RPG preservation and KayKit world packs", "",
        f"- v0.44.7 code modules identical: **{'YES' if core_intact else 'NO — investigate differences'}**",
        f"- P4 visual bridge in HIGHFLY: **{'YES' if p4_bridge else 'NO'}**",
        "- Gameplay independently tested: **NO**",
        "- Assets licensed for release: **NOT YET**", "",
        "## RPG systems preserved (byte-for-byte)",
        *(f"- {name}: {value['status']} ({len(value['files'])} files)" for name, value in integrity.items()),
        "", f"## Eastbrook: {buildings['buildingPlacements']} documented building placements",
        *(f"- {x['buildingId']}: {x['originalModelPath']}" for x in buildings["models"]),
        "", "## Owned KayKit pack availability in ZIP",
        *(f"- {key}: {v['pack']} — {v['files']} files, {v['modelFormatFiles']} model-format files"
          for key, v in packs["worldPacks"].items()),
        "", "Private index only. Do not copy original media wholesale or deploy the reference game.", ""
    ]
    (output / "RPG_AND_WORLD_P6.md").write_text("\n".join(rows), encoding="utf8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--stage", type=Path, default=HIGHFLY)
    parser.add_argument("--zip", type=Path, default=ARCHIVE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    r = audit(args.reference, args.stage, args.zip, args.out)
    print("[HIGHFLY] P6 RPG PRESERVATION: " + json.dumps({
        "coreRpgCodeIdentical": r["coreRpgCodeIdentical"],
        "p4VisualBridgePresent": r["p4VisualBridgePresent"],
        "rpgSystemGroups": len(r["systems"]),
        "eastbrookBuildings": r["eastbrook"]["buildingPlacements"],
        "worldPacksInZip": sum(x["presentInZip"] for x in r["kaykit"]["worldPacks"].values()),
        "originalReferenceChanged": False,
        "gameplayReady": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] P6 PRIVATE REPORT: " + str(args.out / "RPG_AND_WORLD_P6.md"))
    if not r["coreRpgCodeIdentical"] or not r["p4VisualBridgePresent"]:
        raise SystemExit("HIGHFLY_P6_REVIEW_REQUIRED — do NOT proceed with asset import")
    print("[HIGHFLY] P6 CORE PRESERVATION OK. NO GAME FILES CHANGED.")


if __name__ == "__main__":
    main()
