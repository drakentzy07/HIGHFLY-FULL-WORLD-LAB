#!/usr/bin/env python3
"""HIGHFLY P17: READ-ONLY inventory of private-stage asset references.

The inventory includes quoted/static paths found in source and known P16
world references. Dynamic paths, network failures and corrupt GLBs require
separate browser/runtime verification. No asset is copied or changed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
P16 = ROOT / ".workspace/reports/highfly-p16/P16_SPEC_KAYKIT_REPAIR.json"
OUT = ROOT / ".workspace/reports/highfly-p17/P17_ASSET_INVENTORY.json"
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".html"}
ASSET_RE = re.compile(
    r"(?<![A-Za-z0-9_])/?((?:models|textures|vfx)/"
    r"[A-Za-z0-9_./-]+\.(?:glb|png|jpe?g|webp|ktx2|hdr|exr|svg|gif))"
    r"(?![A-Za-z0-9_.-])", re.IGNORECASE
)


def collect_source_refs(stage: Path) -> tuple[dict[str, list[str]], int]:
    refs: dict[str, set[str]] = defaultdict(set)
    candidates = list((stage / "src").rglob("*"))
    candidates.extend(stage / p for p in ("index.html", "play.html", "editor.html"))
    scanned = 0
    for file in candidates:
        if not file.is_file() or file.is_symlink() or file.suffix.lower() not in EXTENSIONS:
            continue
        if file.stat().st_size > 5_000_000:
            continue
        scanned += 1
        raw = file.read_text(encoding="utf8", errors="replace")
        for match in ASSET_RE.finditer(raw):
            rel = match.group(1)
            if ".." in Path(rel).parts:
                continue
            refs[rel].add(file.relative_to(stage).as_posix())
    return {k: sorted(v) for k, v in refs.items()}, scanned


def audit(stage: Path, p16: Path) -> dict:
    if not (stage / "src").is_dir() or not (stage / "public").is_dir():
        raise RuntimeError("P17_PRIVATE_STAGE_SOURCE_OR_PUBLIC_NOT_FOUND")
    refs, scanned = collect_source_refs(stage)
    from_p16 = []
    if p16.is_file():
        report = json.loads(p16.read_text(encoding="utf8"))
        from_p16 = report.get("runtimeMissing", {}).get("firstMissing", [])
        for rel in from_p16:
            if isinstance(rel, str) and rel.startswith(("models/", "textures/", "vfx/")):
                refs.setdefault(rel, ["P16_WORLD_AUDIT"])
    public = stage / "public"
    dist = stage / "dist"
    has_dist = dist.is_dir()
    # Case-only problems are relevant on Linux and can look like missing GLBs.
    present = {}
    for file in public.rglob("*"):
        if file.is_file():
            present.setdefault(file.relative_to(public).as_posix().lower(), []).append(
                file.relative_to(public).as_posix()
            )
    missing_public, missing_dist, case_only = [], [], []
    groups = Counter()
    for rel in sorted(refs):
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            continue
        candidate = public / rel
        if not candidate.is_file():
            groups["/".join(Path(rel).parts[:2])] += 1
            entry = {"path": rel, "referencedBy": refs[rel][:3]}
            alt = present.get(rel.lower(), [])
            if alt:
                entry["caseOnlyCandidates"] = alt[:5]
                case_only.append(entry)
            else:
                missing_public.append(entry)
        elif has_dist and not (dist / rel).is_file():
            missing_dist.append({"path": rel, "referencedBy": refs[rel][:3]})
    return {
        "phase": "P17_READ_ONLY_STATIC_ASSET_INVENTORY",
        "sourceFilesScanned": scanned,
        "staticAndP16PathsFound": len(refs),
        "p16MissingImportedForCoverage": len(from_p16),
        "distPresent": has_dist,
        "absentFromPublicCount": len(missing_public),
        "caseOnlyMismatchesCount": len(case_only),
        "presentInPublicButAbsentFromDistCount": len(missing_dist),
        "missingByCategory": dict(sorted(groups.items(), key=lambda x: (-x[1], x[0]))),
        "missingPublic": missing_public,
        "caseOnlyMismatches": case_only,
        "missingDist": missing_dist,
        "limitations": [
            "This is a source-text scan, not browser network capture.",
            "Dynamically constructed runtime URLs may not be included.",
            "Existence does not prove GLB, texture or VFX validity.",
            "Paths in comments or dead code may be counted.",
            "No files, simulation or visual assets were modified."
        ],
    }


def main() -> None:
    report = audit(STAGE, P16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P17 READ-ONLY ASSET INVENTORY")
    for name in ("sourceFilesScanned", "staticAndP16PathsFound", "absentFromPublicCount",
                 "caseOnlyMismatchesCount", "presentInPublicButAbsentFromDistCount"):
        print(f"  {name}: {report[name]}")
    print("[HIGHFLY] MISSING BY CATEGORY:")
    for category, count in report["missingByCategory"].items():
        print(f"  {category}: {count}")
    print("[HIGHFLY] FIRST 35 ABSENT FILES:")
    for item in report["missingPublic"][:35]:
        print("  " + item["path"])
    print("[HIGHFLY] CASE-ONLY MISMATCHES (FIRST 10):")
    for item in report["caseOnlyMismatches"][:10]:
        print("  " + item["path"] + " -> " + ", ".join(item["caseOnlyCandidates"]))
    print("[HIGHFLY] REPORT: " + str(OUT))
    print("[HIGHFLY] NO FILES COPIED, NO BUILD, NO DEPLOY.")


if __name__ == "__main__":
    main()
