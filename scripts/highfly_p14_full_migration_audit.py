#!/usr/bin/env python3
"""HIGHFLY P14 — complete migration inventory for original v0.44.7 -> private HIGHFLY.

Read-only, comprehensive at filesystem level: code presence/change, public
media by category, explicit code references, RPG integrity and exact matching
owned KayKit assets. Dynamic asset paths and copyright cannot be definitively
audited via filenames. The output is a migration checklist, NOT a license
clearance or proof of playable runtime.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ARCHIVE = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
REPORT = ROOT / ".workspace/reports/highfly-p14"
CODE_FOLDERS = ("src", "server", "data")
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
                 ".svelte", ".css", ".html", ".json", ".scss", ".wasm"}
EXPECTED_MODIFICATIONS = {
    "src/main.ts": "HIGHFLY: offline character preview",
    "src/render/characters/manifest.ts": "HIGHFLY: KayKit player/skeleton visual mapping",
    "src/render/characters/assets.ts": "HIGHFLY: KayKit-only initial character preload",
    "src/render/assets/loader.ts": "HIGHFLY: possible private fail-fast retry modification",
}
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p5_world_readiness as p5
import highfly_p6_rpg_and_world_packs as p6
import highfly_p12_world_kaykit_batch as p12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def code_inventory(original: Path, stage: Path) -> dict:
    exact, changed, missing, oversized = [], [], [], []
    for folder in CODE_FOLDERS:
        base = original / folder
        if not base.is_dir():
            continue
        for old in sorted(base.rglob("*")):
            if old.is_symlink():
                raise RuntimeError("SYMLINK_IN_REFERENCE_SOURCE: " + str(old))
            if not old.is_file() or old.suffix.lower() not in CODE_SUFFIXES:
                continue
            relative = old.relative_to(original).as_posix()
            copy = stage / relative
            if old.stat().st_size > 15_000_000:
                oversized.append(relative)
            if not copy.is_file() or copy.is_symlink():
                missing.append(relative)
            elif sha256(old) == sha256(copy):
                exact.append(relative)
            else:
                changed.append(relative)
    intentional = [p for p in changed if p in EXPECTED_MODIFICATIONS]
    unexpected = [p for p in changed if p not in EXPECTED_MODIFICATIONS]
    return {
        "sourceCodeCompared": len(exact) + len(changed) + len(missing),
        "identicalCodeFiles": len(exact),
        "modifiedCodeFiles": len(changed),
        "expectedModifiedCodeFiles": intentional,
        "unexpectedModifiedCodeFiles": unexpected,
        "missingCodeFiles": missing,
        "oversizedCodeFiles": oversized,
        "note": "A file being byte-identical does not prove it works at runtime, and a changed file is reviewed rather than automatically treated as a regression.",
    }


def category(path: str) -> str:
    parts = path.split("/")
    if parts[0] == "models" and len(parts) >= 3:
        return "/".join(parts[:2])
    return parts[0]


def media_inventory(original: Path, stage: Path, literals: set[str]) -> dict:
    original_files = p5.files_under(original / "public")
    stage_files = p5.files_under(stage / "public")
    missing = original_files - stage_files
    unfulfilled_literals = literals - stage_files
    categories = {}
    for cat in sorted(set(map(category, original_files)) | set(map(category, stage_files))):
        orig = sorted(x for x in original_files if category(x) == cat)
        present = sorted(x for x in stage_files if category(x) == cat)
        absent = sorted(x for x in missing if category(x) == cat)
        unfulfilled = sorted(x for x in unfulfilled_literals if category(x) == cat)
        categories[cat] = {
            "referenceFiles": len(orig), "highflyFiles": len(present),
            "sourceSamePathStillMissing": len(absent),
            "literalRefsNotInHighfly": len(unfulfilled),
            "missingExamples": absent[:18],
            "referenceExamples": unfulfilled[:18],
        }
    return {
        "referenceFiles": len(original_files),
        "independentFiles": len(stage_files),
        "missingSamePath": len(missing),
        "literalReferencesUnresolved": len(unfulfilled_literals),
        "literalReferencesAlsoAbsentInReference": len(unfulfilled_literals - original_files),
        "byCategory": categories,
        "important": "Original media filenames are NOT a list of legally approved assets and missing same-path does not always imply missing scene visuals. Dynamic URLs are not fully captured.",
    }


def priority(assets: dict, code: dict, match: dict) -> list[dict]:
    categories = assets["byCategory"]
    def folder_count(folder):
        return categories.get(folder, {}).get("sourceSamePathStillMissing", 0)
    return [
        {"order": 1, "area": "WORLD_STARTUP_AND_TERRAIN",
         "sourceMissing": sum(folder_count(s) for s in ("models/biome", "models/terrain", "textures")),
         "next": "Resolve terrain/ground, main town structure, walls, roads and boot-critical props with rights-reviewed replacements; verify GLB geometry/materials and collisions."},
        {"order": 2, "area": "PLAYER_NPCS_AND_ENEMIES",
         "sourceMissing": sum(folder_count(s) for s in ("models/chars", "models/creatures")),
         "next": "Fix KayKit Hunter rendered in creator AND spawn; map original NPC and monster IDs to owned rigged models + correct clips. No monster logic removed."},
        {"order": 3, "area": "DUNGEONS_AND_INTERIORS",
         "sourceMissing": folder_count("models/dungeon"),
         "next": "Map KayKit Dungeon/Halloween/furniture replacements, defer truly distant modules instead of requiring them all before town entry."},
        {"order": 4, "area": "INVENTORY_LOOT_EQUIPMENT",
         "sourceMissing": sum(folder_count(s) for s in ("ui", "icons", "models/items")),
         "next": "Preserve item IDs, stacking, corpses, inventory UI and equip logic while replacing icons, weapons and armor visuals."},
        {"order": 5, "area": "AUDIO_UI_LOCALIZATION",
         "sourceMissing": sum(folder_count(s) for s in ("audio", "sounds", "music", "images")),
         "next": "Replace unsupported visual/audio assets, update startup branding and Spanish UI; do not copy original licensed graphics."},
    ]


def audit(original: Path=ORIGINAL, stage: Path=STAGE, archive: Path=ARCHIVE,
          out: Path=REPORT) -> dict:
    private = (ROOT / ".workspace").resolve()
    for item in (original, stage, archive, out):
        if not item.resolve().is_relative_to(private):
            raise RuntimeError("PRIVATE_WORKSPACE_REQUIRED")
    p12.validate(original, stage, archive, out)
    integrity = p6.module_integrity(original, stage)
    code = code_inventory(original, stage)
    literal_refs, scanned = p5.scan_code_media(stage)
    assets = media_inventory(original, stage, literal_refs)
    with zipfile.ZipFile(archive) as zipdata:
        index = p12.index_models(p12.zip_members(zipdata))
    mapping = p12.source_manifest(original, stage, index)
    result = {
        "project": "HIGHFLY ORIGIN", "phase": "P14_FULL_WORLD_MIGRATION_AUDIT",
        "sourceCommit": p12.PIN, "readOnly": True, "originalMediaCopied": False,
        "gameplayVerified": False, "licenseClearedForRelease": False,
        "coreRpgCodeIdentical": all(x["status"] == "IDENTICAL_SOURCE_CODE" for x in integrity.values()),
        "rpgSystems": integrity,
        "code": code,
        "media": assets,
        "codeFilesScannedForMediaRefs": scanned,
        "ownedKayKitWorld": {
            "exactMatchModelsReadyToImport": len(mapping["exactMatches"]),
            "modelMatchingStatuses": mapping["statuses"],
            "firstExactModels": mapping["exactMatches"][:40],
            "needsManualMatchExamples": [x for x in mapping["items"] if x["status"] != "EXACT_SOURCE_NAME"][:100],
        },
        "priorities": priority(assets, code, mapping),
        "releaseBlockers": [
            "Runtime world preload still not passed",
            "Character model not verified in creator or actual player spawn",
            "Unreplaced media and dynamic asset paths",
            "Incomplete per-file provenance and licensing inventory",
            "Combat, loot, inventory, NPCs, quests, saves not yet end-to-end tested",
            "Android horizontal controls/quality not tested",
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "MIGRATION_AUDIT_P14.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    text = [
        "# HIGHFLY P14 — Auditoría completa de migración", "",
        "**Solo lectura.** Juego original intacto; recursos sin licencia verificada NO publicados.", "",
        f"- Código comparado: **{code['sourceCodeCompared']}** archivos",
        f"- Idénticos: **{code['identicalCodeFiles']}**",
        f"- Modificados previstos: **{len(code['expectedModifiedCodeFiles'])}**",
        f"- Modificados inesperados: **{len(code['unexpectedModifiedCodeFiles'])}**",
        f"- No copiados en HIGHFLY: **{len(code['missingCodeFiles'])}**",
        f"- Módulos RPG críticos idénticos: **{result['coreRpgCodeIdentical']}**",
        f"- Recursos públicos en referencia: **{assets['referenceFiles']}**",
        f"- Recursos públicos en HIGHFLY: **{assets['independentFiles']}**",
        f"- Rutas originales todavía ausentes: **{assets['missingSamePath']}**",
        f"- Referencias literales pendientes: **{assets['literalReferencesUnresolved']}**",
        f"- Modelos de mundo con equivalencia exacta KayKit por importar: **{len(mapping['exactMatches'])}**",
        f"- Modelos de mundo sin equivalencia directa/ambiguos: **{mapping['statuses']}**", "",
        "## Recursos por familia", "",
        "| Familia | Original | HIGHFLY | Rutas fuente ausentes | Referencias literales pendientes |",
        "|---|---:|---:|---:|---:|",
    ]
    for cat, row in sorted(assets["byCategory"].items(),
                           key=lambda kv: kv[1]["literalRefsNotInHighfly"], reverse=True):
        text.append(f"| {cat} | {row['referenceFiles']} | {row['highflyFiles']} | "
                    f"{row['sourceSamePathStillMissing']} | {row['literalRefsNotInHighfly']} |")
    text.extend(["", "## Código faltante o cambiado inesperadamente", ""])
    text.extend("- FALTA: " + s for s in code["missingCodeFiles"][:150])
    text.extend("- CAMBIO NO DECLARADO: " + s for s in code["unexpectedModifiedCodeFiles"][:150])
    text.extend(["", "## Plan de integración por bloques", ""])
    for entry in result["priorities"]:
        text.append(f"{entry['order']}. **{entry['area']}** — {entry['next']}")
    text.extend(["", "## Criterio de aceptación", "",
                 "Cada recurso debe tener modelo/URL, procedencia, licencia verificada, escala y compatibilidad visual. "
                 "Se debe validar jugabilidad real, no solo Vite exit 0. "
                 "No eliminar NPC, monstruos, loot ni otros sistemas para acelerar una pantalla de carga.",
                 "", "## Limitaciones", "",
                 "El escaneo estático no ve todos los URL generados, chunks ni contenido remoto; "
                 "la auditoría jurídica requiere licencia/procedencia de cada pack o archivo. "
                 "El reporte clasifica lo observado, no sustituye QA ni revisión jurídica.", ""])
    (out / "MIGRATION_AUDIT_P14.md").write_text("\n".join(text), encoding="utf8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=REPORT)
    args = parser.parse_args()
    r = audit(out=args.out)
    print("[HIGHFLY] P14 FULL MIGRATION AUDIT: " + json.dumps({
        "rpgSystemsIntact": r["coreRpgCodeIdentical"],
        "sourceCodeCompared": r["code"]["sourceCodeCompared"],
        "missingSourceCodeFiles": len(r["code"]["missingCodeFiles"]),
        "unexpectedCodeChanges": len(r["code"]["unexpectedModifiedCodeFiles"]),
        "publicMediaReference": r["media"]["referenceFiles"],
        "publicMediaHighfly": r["media"]["independentFiles"],
        "unresolvedLiteralReferences": r["media"]["literalReferencesUnresolved"],
        "remainingKayKitExactModelMatches": r["ownedKayKitWorld"]["exactMatchModelsReadyToImport"],
        "gameplayVerified": False,
        "gameFilesModified": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] P14 PRIVATE AUDIT: " + str(args.out / "MIGRATION_AUDIT_P14.md"))
    print("[HIGHFLY] NO SOURCE OR MEDIA COPIED. RELEASE LOCKED.")
    if not r["coreRpgCodeIdentical"]:
        raise SystemExit("HIGHFLY_P14_CRITICAL_RPG_CODE_DIFFERENCE")
if __name__ == "__main__":
    main()
