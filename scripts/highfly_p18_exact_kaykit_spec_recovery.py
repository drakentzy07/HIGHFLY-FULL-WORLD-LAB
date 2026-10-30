#!/usr/bin/env python3
"""HIGHFLY P18: conservative, licensed KayKit SPEC recovery for biome + garden.

Spec files are MIT *textual mapping data* from the pinned ClaudeCraft checkout;
model bytes are converted only from the user's private KayKit Complete V7 ZIP.
No original media is copied. No simulation changes. No public deployment.
Only exact source pack + exact relative glTF path matches auto-import.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p16_kaykit_spec_repair as p16

REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ARCHIVE = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
OUT = ROOT / ".workspace/reports/highfly-p18"
SPEC_PATHS = (
    "scripts/assets/specs/biome_packs.json",
    "scripts/assets/specs/garden_town.json",
)
ALLOWED_GROUPS = {"biome", "props"}
MAX_IMPORTS = 50


def eligible_target(value: str) -> bool:
    p = PurePosixPath(value)
    return (
        len(p.parts) == 3 and p.parts[0] == "models" and
        p.parts[1] in ALLOWED_GROUPS and p.suffix.lower() == ".glb" and
        not p.is_absolute() and ".." not in p.parts and
        "\\" not in value and not value.startswith("/")
    )


def inventory(reference: Path, stage: Path, table: dict) -> dict:
    exact_index = p16.build_zip_index(table)
    by_stem = p12.index_models(table)
    rows = []
    seen = set()
    counts = Counter()
    for spec in SPEC_PATHS:
        file = reference / spec
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 2_000_000:
            raise RuntimeError("P18_SPEC_UNAVAILABLE_OR_UNSAFE: " + spec)
        data = json.loads(file.read_text(encoding="utf8"))
        if not isinstance(data.get("items"), list):
            raise RuntimeError("P18_SPEC_ITEMS_INVALID: " + spec)
        for record in data["items"]:
            source = str(record.get("src", ""))
            pack = p16.source_pack(source)
            suffix = p16.source_suffix(source)
            # Other packs in biome_packs.json may require separate licensing.
            if not pack or not suffix:
                counts["skipped_non_supported_kit_source"] += 1
                continue
            dest = str(record.get("out", ""))
            if not eligible_target(dest):
                raise RuntimeError("P18_KAYKIT_SPEC_TARGET_UNSAFE: " + dest)
            if dest in seen:
                counts["duplicate_destination_in_new_specs"] += 1
                continue
            seen.add(dest)
            target = stage / "public" / dest
            if target.is_symlink() or target.is_dir():
                raise RuntimeError("P18_EXISTING_TARGET_UNSAFE: " + dest)
            row = {"target": dest, "spec": spec, "sourcePack": pack,
                   "specGltfPath": suffix}
            if target.is_file():
                row["status"] = "ALREADY_PRESENT"
            else:
                exact = exact_index.get((pack, suffix.lower()), [])
                if len(exact) == 1:
                    row["status"] = "EXACT_SOURCE_PATH"
                    row["sourceZipMember"] = exact[0]
                elif len(exact) > 1:
                    row["status"] = "DUPLICATE_SOURCE_PATH_REVIEW"
                    row["alternatives"] = exact[:8]
                else:
                    by_name = by_stem.get((pack, PurePosixPath(suffix).stem.lower()), [])
                    if len(by_name) == 1:
                        row["status"] = "UNIQUE_STEM_REVIEW_ONLY"
                        row["alternatives"] = by_name
                    else:
                        row["status"] = "NOT_FOUND_OR_AMBIGUOUS_REVIEW"
                        row["alternatives"] = by_name[:8]
            counts[row["status"]] += 1
            rows.append(row)
    return {"rows": rows, "statusCounts": dict(counts),
            "exactImportCandidates": [r for r in rows if r["status"] == "EXACT_SOURCE_PATH"]}


def install_exact(reference: Path, stage: Path, archive: Path, out: Path,
                  candidates: list[dict], table: dict) -> list[dict]:
    if len(candidates) > MAX_IMPORTS:
        raise RuntimeError("P18_BATCH_TOO_LARGE")
    for item in candidates:
        relative = item["target"]
        if not eligible_target(relative) or item["sourceZipMember"] not in table:
            raise RuntimeError("P18_INVALID_EXACT_IMPORT_INPUT")
        target = stage / "public" / relative
        if target.exists() or target.is_symlink():
            raise RuntimeError("P18_NO_OVERWRITE_POLICY: " + relative)
    converter = reference / "node_modules/.bin/gltf-transform"
    if not converter.is_file():
        raise RuntimeError("P18_CONVERTER_UNAVAILABLE")
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        with tempfile.TemporaryDirectory(prefix="p18-owned-kaykit-", dir=out) as tmp:
            workspace = Path(tmp)
            converted = []
            # Stage everything first: a failed conversion leaves public/ intact.
            for i, item in enumerate(candidates):
                source = p12.unpack_selected(z, table, item["sourceZipMember"],
                                              workspace / f"src-{i}")
                build = workspace / f"built-{i}.glb"
                attempt = subprocess.run(
                    [str(converter), "copy", str(source), str(build)],
                    cwd=str(reference), capture_output=True, text=True, timeout=120,
                    check=False,
                )
                if attempt.returncode != 0 or not p12.glb_valid(build):
                    raise RuntimeError("P18_GLB_CONVERSION_REJECTED: " +
                                       item["target"] + " " + attempt.stderr[-450:])
                converted.append((item, build))
            installed = []
            for item, build in converted:
                target = stage / "public" / item["target"]
                if target.exists() or target.is_symlink():
                    raise RuntimeError("P18_IMPORT_TARGET_CREATED_DURING_BUILD")
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(build, target)
                installed.append({
                    "target": item["target"], "sourcePack": item["sourcePack"],
                    "sourceZipMember": item["sourceZipMember"],
                    "sha256": p12.digest(target), "bytes": target.stat().st_size,
                    "license": "KayKit CC0 (owned ZIP)", "publicReleaseApproved": False,
                })
            return installed


def execute(apply: bool, build: bool) -> dict:
    # P9 protects the original sim and validates the pinned source.
    p9.preflight(REFERENCE, STAGE, p9.REPORT)
    p12.validate(REFERENCE, STAGE, ARCHIVE, OUT)
    with zipfile.ZipFile(ARCHIVE) as z:
        table = p12.zip_members(z)
    plan = inventory(REFERENCE, STAGE, table)
    before = p16.runtime_missing(STAGE)
    installed = []
    if apply and plan["exactImportCandidates"]:
        installed = install_exact(REFERENCE, STAGE, ARCHIVE, OUT,
                                  plan["exactImportCandidates"], table)
    after = p16.runtime_missing(STAGE)
    result = {
        "phase": "P18_GARDEN_BIOME_KAYKIT_SPEC_EXACT_RECOVERY",
        "specs": list(SPEC_PATHS),
        "statusCounts": plan["statusCounts"],
        "exactCandidatesFound": len(plan["exactImportCandidates"]),
        "imported": installed,
        "unresolved": [r for r in plan["rows"] if r["status"] not in
                       ("EXACT_SOURCE_PATH", "ALREADY_PRESENT")],
        "remainingP16ModelsBefore": before["worldModelReferencesStillMissing"],
        "remainingP16ModelsAfter": after["worldModelReferencesStillMissing"],
        "remainingP16Paths": after["firstMissing"],
        "sourceMediaCopied": False,
        "simulationModified": False,
        "gameplayVerified": False,
        "publicReleaseApproved": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "notes": [
            "This does not solve non-KayKit props, foliage, water textures or VFX.",
            "P16's scan is incomplete; browser verification is still required.",
            "Unique-stem and ambiguous matches are never imported automatically."
        ],
    }
    if apply and build:
        result["buildExitCode"] = p9.smoke()["exitCode"]
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / "P18_EXACT_KAYKIT_IMPORT.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf8")
    print("[HIGHFLY] P18 " + ("APPLY" if apply else "DRY-RUN") + ": " +
          json.dumps({
              "candidates": len(plan["exactImportCandidates"]),
              "installed": len(installed),
              "statuses": plan["statusCounts"],
              "remainingP16Models": after["worldModelReferencesStillMissing"],
              "buildExitCode": result.get("buildExitCode"),
              "gameplayVerified": False
          }, ensure_ascii=False), flush=True)
    print("[HIGHFLY] P18 REPORT: " + str(report_path))
    print("[HIGHFLY] NO UPSTREAM MEDIA COPIED. NO PUBLIC DEPLOY.")
    if result.get("buildExitCode") not in (None, 0):
        raise SystemExit("P18_BUILD_FAILED_SEE_P9_LOG")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    execute(args.apply, not args.no_build)


if __name__ == "__main__":
    main()
