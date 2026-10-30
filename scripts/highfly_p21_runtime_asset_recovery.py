#!/usr/bin/env python3
"""HIGHFLY P21: whole P20 runtime asset audit + conservative CC0 bulk repair.

Processes the complete 314-path browser failure capture. Unlike the old P17
source regex scan, these paths were ACTUALLY requested during world entry.

Only automatically imports from the pinned ClaudeCraft reference when an
exact output path is proven in an asset conversion spec with a source from
an explicitly credited CC0 third-party pack. No "with project only" media,
no random name matching, no overwrite, no edits to simulation/gameplay.
Validates both stage public/ AND final dist/ after build.

Dry-run by default. Writes only in ignored PRIVATE .workspace stage/reports.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12

REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
OUTPUT = ROOT / ".workspace/reports/highfly-p21"
MANIFEST = ROOT / "reports/highfly_p20_runtime_missing_paths.json"
VALID_SUFFIXES = {".glb", ".jpg", ".jpeg", ".png", ".webp"}
SOURCE_PREFIXES = {
    "CC0_QUATERNIUS": (
        "tmp/asset_src/quaternius", "tmp/asset_src/quaternius_",
    ),
    "CC0_KENNEY": ("tmp/asset_src/kenney/",),
    "CC0_KAYKIT": ("tmp/asset_src/kaykit/",),
    "CC0_AMBIENTCG": ("tmp/asset_src/ambientcg/",),
    "CC0_POLYHAVEN": ("tmp/asset_src/polyhaven/", "tmp/asset_src/poly_haven/"),
}
CREDIT_AUTHOR = {
    "CC0_QUATERNIUS": "Quaternius",
    "CC0_KENNEY": "Kenney",
    "CC0_KAYKIT": "Kay Lousberg",
    "CC0_AMBIENTCG": "ambientCG",
    "CC0_POLYHAVEN": "Poly Haven",
}
LIMIT = 500
MAX_FILE_SIZE = 100_000_000


def safe_asset_path(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 300:
        return False
    if not value.startswith(("/models/", "/textures/", "/vfx/")):
        return False
    p = PurePosixPath(value)
    return (len(p.parts) >= 3 and
            ".." not in p.parts and "\\" not in value and
            not any(x in (".", "") for x in p.parts) and
            p.suffix.lower() in VALID_SUFFIXES and
            re.fullmatch(r"/[A-Za-z0-9_./-]+", value) is not None)


def paths_from_capture(path: Path) -> list[str]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("P21_CAPTURE_MANIFEST_NOT_FOUND")
    obj = json.loads(path.read_text(encoding="utf8"))
    paths = obj.get("paths")
    if (obj.get("pathCount") != 314 or not isinstance(paths, list) or
            len(paths) != 314 or len(set(paths)) != 314 or
            not all(safe_asset_path(p) for p in paths)):
        raise RuntimeError("P21_P20_CAPTURE_NOT_EXPECTED_314_PATHS")
    return paths


def spec_license(source: str, credit: dict[str, bool]) -> str | None:
    source = source.replace("\\", "/")
    if source.startswith("/") or ".." in PurePosixPath(source).parts:
        return None
    for kind, prefixes in SOURCE_PREFIXES.items():
        if credit.get(kind) and source.lower().startswith(tuple(p.lower() for p in prefixes)):
            return kind
    # Some pinned conversion specs encode absolute paths that were redacted
    # in the open source mirror. Only the explicit 'Complete KayKit Collection'
    # declaration earns a KayKit classification; no generic .gltf matching.
    if credit.get("CC0_KAYKIT") and (
            "Complete KayKit Collection" in source and
            "/Assets/gltf/" in source and
            ("KayKit " in source or "KayKit-" in source)):
        return "CC0_KAYKIT"
    return None


def credits_state(reference: Path) -> dict[str, bool]:
    file = reference / "CREDITS.md"
    if not file.is_file() or file.is_symlink():
        raise RuntimeError("P21_REFERENCE_CREDITS_MISSING")
    lines = file.read_text(encoding="utf8").splitlines()
    state = {}
    for kind, author in CREDIT_AUTHOR.items():
        state[kind] = any(
            line.startswith("|") and f"| {author} |" in line and
            re.search(r"\|\s*CC0 1\.0\s*\|\s*Yes\s*\|", line)
            for line in lines
        )
    if not all(state.values()):
        raise RuntimeError("P21_THIRD_PARTY_CREDITS_NOT_VERIFIED: " + repr(state))
    return state


def build_spec_index(reference: Path, credit: dict[str, bool]) -> dict[str, list[dict]]:
    root = reference / "scripts/assets/specs"
    if not root.is_dir():
        raise RuntimeError("P21_PINNED_CONVERSION_SPECS_MISSING")
    index = defaultdict(list)
    files = sorted(root.rglob("*.json"))
    if len(files) > 500:
        raise RuntimeError("P21_TOO_MANY_SOURCE_SPECS")
    for file in files:
        if file.is_symlink() or file.stat().st_size > 3_000_000:
            continue
        try:
            data = json.loads(file.read_text(encoding="utf8"))
        except (ValueError, UnicodeError):
            continue
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            continue
        for record in data["items"]:
            if not isinstance(record, dict):
                continue
            raw_output = record.get("out")
            raw_source = record.get("src")
            if not isinstance(raw_output, str) or not isinstance(raw_source, str):
                continue
            output = "/" + raw_output.lstrip("/")
            if not safe_asset_path(output):
                continue
            license_tag = spec_license(raw_source, credit)
            index[output].append({
                "sourceSpec": file.relative_to(reference).as_posix(),
                "sourceDescription": raw_source,
                "provenance": license_tag or "UNVERIFIED_OR_PROJECT_ONLY",
            })
    return dict(index)


def check_binary(file: Path, expected: str) -> bool:
    if not file.is_file() or file.is_symlink() or not (8 <= file.stat().st_size <= MAX_FILE_SIZE):
        return False
    suffix = file.suffix.lower()
    if suffix == ".glb":
        return p12.glb_valid(file)
    with file.open("rb") as handle:
        header = handle.read(16)
    if suffix == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in (".jpg", ".jpeg"):
        return header.startswith(b"\xff\xd8\xff")
    if suffix == ".webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    return False


def classify(path: str, stage: Path, reference: Path,
             spec_index: dict[str, list[dict]]) -> dict:
    relative = path.lstrip("/")
    stage_file = stage / "public" / relative
    dist_file = stage / "dist" / relative
    original_file = reference / "public" / relative
    candidates = spec_index.get(path, [])
    evidence = [{k: v for k, v in c.items() if k != "sourceDescription"}
                for c in candidates[:8]]
    record = {"path": path, "sourcePublicExists": stage_file.is_file(),
              "distExists": dist_file.is_file(), "upstreamExists": original_file.is_file(),
              "sourceSpecs": evidence}
    if stage_file.is_symlink() or dist_file.is_symlink() or original_file.is_symlink():
        record["status"] = "REVIEW_UNSAFE_SYMLINK"
    elif stage_file.is_file():
        if not check_binary(stage_file, relative):
            record["status"] = "REVIEW_BAD_STAGE_BINARY"
        elif not dist_file.is_file():
            record["status"] = "STAGED_BUT_NOT_BUNDLED"
        elif not check_binary(dist_file, relative):
            record["status"] = "REVIEW_BAD_DIST_BINARY"
        elif p12.digest(stage_file) != p12.digest(dist_file):
            record["status"] = "REVIEW_DIST_HASH_MISMATCH"
        else:
            record["status"] = "STAGED_AND_BUNDLED_BUT_BROWSER_REPORTED_FAIL"
    elif original_file.is_file():
        provenance = {x["provenance"] for x in candidates}
        if len(candidates) == 1 and len(provenance) == 1 and next(iter(provenance)).startswith("CC0_") and check_binary(original_file, relative):
            record["status"] = "EXACT_CC0_IMPORT_READY"
            record["provenance"] = next(iter(provenance))
            record["sourceSha256"] = p12.digest(original_file)
            record["sourceBytes"] = original_file.stat().st_size
        elif candidates and len(provenance) == 1 and next(iter(provenance)).startswith("CC0_") and (
                len({c["sourceDescription"] for c in candidates}) == 1) and check_binary(original_file, relative):
            # Repeated entries referencing exactly the same third-party source
            # are acceptable, conflicting upstream descriptions are not.
            record["status"] = "EXACT_CC0_IMPORT_READY"
            record["provenance"] = next(iter(provenance))
            record["sourceSha256"] = p12.digest(original_file)
            record["sourceBytes"] = original_file.stat().st_size
        else:
            record["status"] = "LICENSE_OR_SPEC_REVIEW_REQUIRED"
    else:
        record["status"] = "NEEDS_OWNED_REPLACEMENT_OR_NEW_SOURCE"
    return record


def plan(reference: Path, stage: Path, manifest: Path) -> dict:
    paths = paths_from_capture(manifest)
    credits = credits_state(reference)
    index = build_spec_index(reference, credits)
    rows = [classify(path, stage, reference, index) for path in paths]
    counts = Counter(r["status"] for r in rows)
    by_cat = defaultdict(Counter)
    for row in rows:
        by_cat["/".join(PurePosixPath(row["path"]).parts[1:3])][row["status"]] += 1
    return {
        "capturedPaths": len(paths), "creditEvidence": credits,
        "specOutputPathsIndexed": len(index),
        "statusCounts": dict(sorted(counts.items())),
        "byCategory": {k: dict(v) for k, v in sorted(by_cat.items())},
        "items": rows,
    }


def install(reference: Path, stage: Path, rows: list[dict]) -> list[dict]:
    if len(rows) > LIMIT:
        raise RuntimeError("P21_CC0_IMPORT_LIMIT_EXCEEDED")
    # File hashes, exact spec provenance and source origin were verified by plan.
    # Validate every candidate again before modifying any target.
    for row in rows:
        relative = row["path"].lstrip("/")
        src = reference / "public" / relative
        target = stage / "public" / relative
        if (not row["status"] == "EXACT_CC0_IMPORT_READY" or
                not safe_asset_path(row["path"]) or
                target.exists() or target.is_symlink() or
                not check_binary(src, relative) or
                p12.digest(src) != row["sourceSha256"]):
            raise RuntimeError("P21_IMPORT_PRECHECK_FAILED: " + row["path"])
    installed = []
    for row in rows:
        relative = row["path"].lstrip("/")
        src = reference / "public" / relative
        target = stage / "public" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".p21-", dir=target.parent,
                                             delete=False) as opened:
                temp = Path(opened.name)
                with src.open("rb") as f:
                    shutil.copyfileobj(f, opened)
            if p12.digest(temp) != row["sourceSha256"] or target.exists():
                raise RuntimeError("P21_COPY_CHANGED_SOURCE_OR_DESTINATION")
            os.replace(temp, target)
            installed.append({"path": row["path"], "sha256": row["sourceSha256"],
                              "provenance": row["provenance"],
                              "specs": row["sourceSpecs"][:3]})
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return installed


def execute(apply: bool, build: bool) -> dict:
    p9.preflight(REFERENCE, STAGE, p9.REPORT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = plan(REFERENCE, STAGE, MANIFEST)
    picks = [row for row in before["items"] if row["status"] == "EXACT_CC0_IMPORT_READY"]
    installed = install(REFERENCE, STAGE, picks) if apply else []
    build_exit = None
    if apply and build:
        build_exit = p9.smoke()["exitCode"]
    after = plan(REFERENCE, STAGE, MANIFEST)
    unresolved_dist = [r["path"] for r in after["items"] if r["status"] == "STAGED_BUT_NOT_BUNDLED"]
    result = {
        "phase": "P21_COMPLETE_P20_RUNTIME_PROVENANCE_BULK_AUDIT",
        "mode": "APPLY" if apply else "DRY_RUN",
        "sourceCommit": p9.SHA,
        "captureDate": "2026-10-30T23:01:09.981Z",
        "capturedPaths": before["capturedPaths"],
        "licensedCandidates": len(picks),
        "installed": installed,
        "before": before,
        "after": {"statusCounts": after["statusCounts"],
                  "byCategory": after["byCategory"],
                  "items": after["items"]},
        "buildExitCode": build_exit,
        "bundlingAnomalies": unresolved_dist,
        "buildIsVerifiedForCapturedAssets": apply and not unresolved_dist,
        "rightsClearedForPublicRelease": False,
        "gameplayVerified": False,
        "originalGameChanged": False,
        "simulationChanged": False,
        "timeUtc": datetime.now(timezone.utc).isoformat(),
        "notes": [
            "License is decided per verified source spec + provider credits; not from filename alone.",
            "Source missing in reference does not mean missing from external CC0 provider.",
            "Original project-only custom art is not copied or replaced with random stand-ins.",
            "Browser failures captured before imports are historical, not proof of current errors.",
            "If STAGED_AND_BUNDLED_BUT_BROWSER_REPORTED_FAIL, investigate browser cache/service worker and runtime GLB validation.",
        ],
    }
    report_path = OUTPUT / "P21_RUNTIME_314_LICENSED_RECOVERY.json"
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P21 " + result["mode"] + ": " + json.dumps({
        "captured": result["capturedPaths"], "licensed": len(picks),
        "installed": len(installed), "buildExitCode": build_exit,
        "before": before["statusCounts"], "after": after["statusCounts"],
        "distMissingAfterBuild": len(unresolved_dist), "gameplayVerified": False,
    }, ensure_ascii=False), flush=True)
    print("[HIGHFLY] P21 REPORT: " + str(report_path))
    if unresolved_dist:
        print("[HIGHFLY] WARNING: PUBLIC FILES NOT PRESENT IN dist/. FIRST 20:")
        for s in unresolved_dist[:20]:
            print("  " + s)
    if result["buildExitCode"] not in (None, 0):
        raise SystemExit("P21_VITE_BUILD_FAILED")
    if apply and unresolved_dist:
        raise SystemExit("P21_DIST_ASSET_PACKAGING_NOT_FIXED")
    return result


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--apply", action="store_true")
    cli.add_argument("--no-build", action="store_true")
    args = cli.parse_args()
    execute(args.apply, not args.no_build)


if __name__ == "__main__":
    main()
