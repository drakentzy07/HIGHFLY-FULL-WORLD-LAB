#!/usr/bin/env python3
"""HIGHFLY P16: rebuild missing CC0 KayKit world assets from pinned source specs,
fix first-party Knight preview attachments, produce runtime-blocker inventory.

Only writes into ignored private HIGHFLY stage. P12 does all GLB conversion and
ZIP safety checks. No upstream media copied, no RPG simulation altered, no
public release and no unverified claim that entering the world works.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ARCHIVE = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
OUT = ROOT / ".workspace/reports/highfly-p16"
SPECS = (
    "scripts/assets/specs/drakelands_castle.json",
    "scripts/assets/specs/gale_harbor.json",
    "scripts/assets/specs/dungeon.json",
)
PACK_DUNGEON = "KayKit Dungeon Pack 1.1"
PACK_HALLOWEEN = "KayKit Halloween Bits 1.0"
PACK_HEXAGON = "KayKit Medieval Hexagon Pack 1.0.1"
P16_MARK = "HIGHFLY_P16_NO_ORIGINAL_WEAPON_DEPENDENCIES"
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12

def source_pack(src: str) -> str:
    if "Medieval Hexagon Pack" in src:
        return PACK_HEXAGON
    if "Halloween-Bits" in src or "Halloween Bits" in src:
        return PACK_HALLOWEEN
    if "Dungeon-Remastered" in src or "Dungeon Remastered" in src:
        return PACK_DUNGEON
    return ""

def source_suffix(src: str) -> str:
    if "/Assets/gltf/" not in src:
        return ""
    tail = src.split("/Assets/gltf/", 1)[1]
    if tail.endswith(".gltf.glb"):
        tail = tail[:-4]
    if not tail.lower().endswith(".gltf"):
        return ""
    parts = PurePosixPath(tail)
    if parts.is_absolute() or ".." in parts.parts or not parts.parts:
        return ""
    return tail

def build_zip_index(table: dict) -> dict:
    indexed = {}
    for member in table:
        p = PurePosixPath(member)
        if p.suffix.lower() != ".gltf":
            continue
        pack = next((x for x in p.parts if x in (PACK_DUNGEON, PACK_HALLOWEEN, PACK_HEXAGON)), "")
        if not pack:
            continue
        if "/Assets/gltf/" not in member:
            continue
        tail = member.split("/Assets/gltf/", 1)[1].lower()
        indexed.setdefault((pack, tail), []).append(member)
    return indexed

def inventory(original: Path, stage: Path, table: dict) -> dict:
    exact = build_zip_index(table)
    fallback = p12.index_models(table)
    results = []
    seen = set()
    counts = Counter()
    for spec in SPECS:
        file = original / spec
        if not file.is_file() or file.is_symlink():
            raise RuntimeError("MISSING_PINNED_KAYKIT_SPEC: " + spec)
        data = json.loads(file.read_text(encoding="utf8"))
        if not isinstance(data.get("items"), list):
            raise RuntimeError("INVALID_KAYKIT_SOURCE_SPEC: " + spec)
        for record in data["items"]:
            dest = str(record.get("out", ""))
            rel = PurePosixPath(dest)
            if (len(rel.parts) != 3 or rel.parts[0] != "models" or
                    rel.parts[1] not in ("biome", "dungeon") or
                    rel.suffix != ".glb" or ".." in rel.parts or
                    "\\" in dest or dest in seen):
                # Duplicate destinations may be legitimate across original specs:
                # choose the first only, with an audit note.
                if dest in seen:
                    counts["duplicate_spec_output"] += 1
                    continue
                raise RuntimeError("UNEXPECTED_KAYKIT_SPEC_OUTPUT: " + spec + ": " + dest)
            seen.add(dest)
            target = stage / "public" / dest
            if target.is_symlink():
                raise RuntimeError("UNSAFE_P16_TARGET_SYMLINK: " + dest)
            if target.is_file():
                counts["already_present"] += 1
                continue
            src = str(record.get("src", ""))
            pack = source_pack(src)
            suffix = source_suffix(src)
            if not pack or not suffix:
                counts["unsupported_source_spec"] += 1
                results.append({"target": dest, "spec": spec, "source": src,
                                "status": "UNSUPPORTED_KAYKIT_SOURCE_SPEC"})
                continue
            found = exact.get((pack, suffix.lower()), [])
            how = "EXACT_SOURCE_SPEC_PATH"
            if not found:
                found = fallback.get((pack, PurePosixPath(suffix).stem.lower()), [])
                how = "UNIQUE_SOURCE_SPEC_STEM"
            if len(found) == 1:
                counts[how] += 1
                results.append({"target": dest, "spec": spec, "sourcePack": pack,
                                "sourceZipMember": found[0], "status": how})
            else:
                status = "MISSING_IN_OWNED_KAYKIT_V7" if not found else "AMBIGUOUS_KAYKIT_SOURCE"
                counts[status] += 1
                results.append({"target": dest, "spec": spec,
                                "sourcePack": pack, "expectedGlTF": suffix,
                                "status": status, "alternatives": found[:10]})
    choices = [r for r in results if r["status"] in
               ("EXACT_SOURCE_SPEC_PATH", "UNIQUE_SOURCE_SPEC_STEM")]
    return {"candidates": choices, "unmatched": [r for r in results
            if r["status"] not in ("EXACT_SOURCE_SPEC_PATH", "UNIQUE_SOURCE_SPEC_STEM")],
            "counts": dict(counts)}

def preview_patches(stage: Path) -> list[tuple[Path, str, str]]:
    manifest = stage / "src/render/characters/manifest.ts"
    main = stage / "src/main.ts"
    media = stage / "src/render/assets/media.ts"
    if not all(p.is_file() and not p.is_symlink() for p in (manifest, main, media)):
        raise RuntimeError("P16_PRIVATE_CHARACTER_OR_MEDIA_SOURCE_MISSING")
    before_manifest = manifest.read_text(encoding="utf8")
    before_main = main.read_text(encoding="utf8")
    before_media = media.read_text(encoding="utf8")
    if "HIGHFLY_P4_VISUAL_BRIDGE_START" not in before_manifest or "HIGHFLY_P13_OWNED_KNIGHT_PREVIEW" not in before_main:
        raise RuntimeError("P16_P4_OR_P13_CHARACTER_BRIDGE_REQUIRED")
    old = "  const heroBase = VISUALS.player_warrior;\n  if (heroBase) VISUALS.player_warrior = {\n    ...heroBase,\n"
    new = (old +
        "    // " + P16_MARK + ": temporary owned Knight without old weapon GLBs.\n"
        "    show: [],\n"
        "    attach: [],\n"
        "    weaponSlots: [],\n"
        "    offhandSlot: undefined,\n")
    if P16_MARK not in before_manifest:
        if before_manifest.count(old) != 1:
            raise RuntimeError("P16_HERO_VISUAL_ANCHOR_MISSING")
        after_manifest = before_manifest.replace(old, new, 1)
    else:
        after_manifest = before_manifest
    old_main = "    characterPreview.setClass('warrior');\n    return;\n"
    new_main = "    characterPreview.setClass('warrior', null, null); // P16 no unavailable legacy starter weapon\n    return;\n"
    if new_main in before_main:
        after_main = before_main
    elif before_main.count(old_main) == 1:
        after_main = before_main.replace(old_main, new_main, 1)
    else:
        raise RuntimeError("P16_PREVIEW_START_WEAPON_ANCHOR_MISSING")
    # The pinned upstream manifest.generated.ts resolves production GLBs to
    # /media/<OLD_SHA>.glb. P15 only stages our own KayKit under /models/...,
    # so keeping the old manifest makes valid owned GLBs still 404. Only the
    # private HIGHFLY Vite build bypasses the legacy manifest.
    media_before = "  if (import.meta.env.DEV) return `/${logical}`;"
    media_after = (
        "  // HIGHFLY_P16_OWNED_MEDIA_PATHS: use stage-owned Vite public/ media.\n"
        "  if (import.meta.env.VITE_HIGHFLY_P4 === '1') return `/${logical}`;\n"
        + media_before
    )
    if "HIGHFLY_P16_OWNED_MEDIA_PATHS" in before_media:
        after_media = before_media
    elif before_media.count(media_before) == 1:
        after_media = before_media.replace(media_before, media_after, 1)
    else:
        raise RuntimeError("P16_LEGACY_MEDIA_MANIFEST_ROUTING_ANCHOR_MISSING")
    return [(manifest, before_manifest, after_manifest),
            (main, before_main, after_main),
            (media, before_media, after_media)]

def runtime_missing(stage: Path) -> dict:
    base = stage / "public"
    assets = set()
    # Collect hardcoded boot resources and scene references. This is diagnostic,
    # not a complete dynamic URL graph.
    for name in ("src/render/props.ts", "src/render/dungeon.ts",
                 "src/render/eastbrook_town.ts"):
        text = (stage / name).read_text(encoding="utf8", errors="replace")
        assets.update(re.findall(r"""['"`](/?models/(?:biome|dungeon)/[a-zA-Z0-9_.-]+\.glb)['"`]""", text))
    missing = sorted(s.lstrip("/") for s in assets
                     if not (base / s.lstrip("/")).is_file())
    return {"literalWorldModelReferencesScanned": len(assets),
            "worldModelReferencesStillMissing": len(missing),
            "firstMissing": missing[:120]}

def run(apply: bool, build: bool) -> dict:
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    p12.validate(ORIGINAL, STAGE, ARCHIVE, OUT)
    with zipfile.ZipFile(ARCHIVE, "r") as z:
        table = p12.zip_members(z)
    plan = inventory(ORIGINAL, STAGE, table)
    patches = preview_patches(STAGE)
    results = []
    OUT.mkdir(parents=True, exist_ok=True)
    if apply:
        matches = plan["candidates"]
        for offset in range(0, len(matches), p12.MAX_IMPORTS):
            batch = matches[offset:offset + p12.MAX_IMPORTS]
            installed = p12.import_batch(ORIGINAL, STAGE, OUT, ARCHIVE, batch)
            results.extend(installed)
            print("[HIGHFLY] P16 SPEC KAYKIT BATCH: " + str(len(installed)) +
                  " installed; cumulative=" + str(len(results)), flush=True)
        for file, before, after in patches:
            if file.read_text(encoding="utf8") != before:
                raise RuntimeError("P16_CONCURRENT_VISUAL_SOURCE_CHANGE: " + str(file))
            if after != before:
                backup = OUT / (file.name + ".before_p16")
                if not backup.exists():
                    backup.write_text(before, encoding="utf8")
                file.write_text(after, encoding="utf8")
    diagnosis = runtime_missing(STAGE)
    result = {"phase": "P16_KAYKIT_ORIGINAL_SPEC_RECONSTRUCTION",
              "source": "pinned MIT JSON conversion specs + user-owned KayKit V7",
              "sourceSpecs": list(SPECS),
              "specAssetMatchCounts": plan["counts"],
              "modelConversionsInstalled": len(results),
              "ownedModelFiles": results,
              "unresolvedSpecModels": plan["unmatched"],
              "runtimeMissing": diagnosis,
              "previewPatched": apply and any(old != new for _, old, new in patches),
              "allModelsPresent": diagnosis["worldModelReferencesStillMissing"] == 0,
              "gameplayVerified": False, "publicReleaseApproved": False,
              "originalMediaCopied": False, "simChanged": False}
    if apply and build:
        result["buildExitCode"] = p9.smoke()["exitCode"]
    (OUT / "P16_SPEC_KAYKIT_REPAIR.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P16 WORLD REPAIR: " + json.dumps({
        "specsRead": len(SPECS), "matchesPendingAtStart": len(plan["candidates"]),
        "addedOwnedModels": len(results),
        "specUnmatched": len(plan["unmatched"]),
        "worldModelRefsStillMissing": diagnosis["worldModelReferencesStillMissing"],
        "buildExitCode": result.get("buildExitCode"),
        "gameplayVerified": False}, ensure_ascii=False))
    print("[HIGHFLY] P16 PRIVATE REPORT: " + str(OUT / "P16_SPEC_KAYKIT_REPAIR.json"))
    if result.get("buildExitCode") not in (None, 0):
        raise SystemExit("P16_BUILD_BLOCKED_LOG_IN_P9_REPORT")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    a = parser.parse_args()
    run(a.apply, not a.no_build)

if __name__ == "__main__":
    main()
