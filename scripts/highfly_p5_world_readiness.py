#!/usr/bin/env python3
"""HIGHFLY P5 — read-only readiness audit for independent World of ClaudeCraft RPG.

The private .workspace/highfly-origin-stage-p0 is code-only, with selected owned
KayKit P4 models. This audits file presence and obvious literal media references,
WITHOUT copying unreviewed upstream assets or claiming a playable/releasable build.

All reports remain inside .workspace/ and are not committed to GitHub.
"""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "493c35a108cef6c8aa290e8793107b1cd117886e"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
KAYKIT_ZIP = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
REPORT_DIR = ROOT / ".workspace/reports/highfly-p5"

MEDIA_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?:models|textures|audio|sounds|sfx|music|icons|images|fonts|sprites|ui)"
    r"/[A-Za-z0-9_./() +@~-]+?\.(?:glb|gltf|bin|png|webp|jpg|jpeg|svg|ktx2|mp3|ogg|wav|woff2?|ttf|json)"
    r"(?=[^\w./-]|$)", re.I
)
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".html", ".json"}
MAX_SOURCE_FILE_SIZE = 8_000_000


def files_under(directory: Path) -> set[str]:
    """Collect regular files only, fail-closed on links so reports never follow them."""
    if not directory.is_dir():
        raise RuntimeError("MEDIA_DIRECTORY_MISSING: " + str(directory))
    result: set[str] = set()
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("SYMLINK_IN_MEDIA_DIRECTORY: " + str(path))
        if path.is_file():
            result.add(path.relative_to(directory).as_posix())
    return result


def quoted_media_literals(source: str) -> set[str]:
    """Diagnostic heuristic, not a full runtime dependency resolver."""
    return {match.group(0).removeprefix("/") for match in MEDIA_PATTERN.finditer(source)}


def verify(stage: Path, original: Path) -> dict:
    workspace = (ROOT / ".workspace").resolve()
    if not stage.resolve().is_relative_to(workspace):
        raise RuntimeError("STAGE_OUTSIDE_PRIVATE_WORKSPACE")
    if not original.resolve().is_relative_to(workspace):
        raise RuntimeError("ORIGINAL_OUTSIDE_PRIVATE_WORKSPACE")
    info_file = stage / "HIGHFLY_STAGE_STATUS.json"
    if not info_file.is_file():
        raise RuntimeError("P0_STAGE_MISSING")
    info = json.loads(info_file.read_text(encoding="utf8"))
    if info.get("sourceCommit") != SOURCE_SHA or info.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("INVALID_P0_STAGE_METADATA")
    if not (original / ".git").is_dir():
        raise RuntimeError("CLAUDECRAFT_REFERENCE_MISSING")
    commit = subprocess.check_output(
        ["git", "-C", str(original), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != SOURCE_SHA:
        raise RuntimeError("CLAUDECRAFT_REFERENCE_VERSION_CHANGED")
    manifest = stage / "src/render/characters/manifest.ts"
    if not manifest.is_file() or not (stage / "src/sim/eastbrook_layout.ts").is_file():
        raise RuntimeError("CORE_ENGINE_OR_WORLD_LAYOUT_MISSING")
    if "// HIGHFLY_P4_VISUAL_BRIDGE_START" not in manifest.read_text(encoding="utf8"):
        raise RuntimeError("P4_WORLD_BRIDGE_NOT_FOUND")
    return info


def scan_code_media(stage: Path) -> tuple[set[str], int]:
    found: set[str] = set()
    searched = 0
    directories = (stage / "src", stage / "data", stage / "server")
    for base in directories:
        if not base.is_dir():
            continue
        for file in base.rglob("*"):
            if file.is_symlink():
                raise RuntimeError("SYMLINK_IN_CODE_SOURCE: " + str(file))
            if not file.is_file() or file.suffix.lower() not in CODE_SUFFIXES:
                continue
            if file.stat().st_size > MAX_SOURCE_FILE_SIZE:
                continue
            searched += 1
            found.update(quoted_media_literals(file.read_text(encoding="utf8", errors="replace")))
    for name in ("index.html", "play.html", "editor.html", "vite.config.ts"):
        file = stage / name
        if file.is_file() and not file.is_symlink():
            searched += 1
            found.update(quoted_media_literals(file.read_text(encoding="utf8", errors="replace")))
    return found, searched


def audit(stage: Path = STAGE, original: Path = ORIGINAL, report_dir: Path = REPORT_DIR) -> dict:
    status = verify(stage, original)
    original_media = files_under(original / "public")
    staged_media = files_under(stage / "public")
    literals, scanned = scan_code_media(stage)
    missing = original_media - staged_media
    referenced_missing = sorted(literals - staged_media)
    missing_from_original = sorted(set(referenced_missing) - original_media)
    # Note: original "public" is not a license source or a required-asset manifest.
    # Dynamic import paths, generated manifests, indirect dependencies and build
    # outputs are invisible to this simple source-literal scan.
    extensions = dict(Counter(Path(s).suffix.lower() for s in missing).most_common(30))
    top_dirs = dict(Counter(s.split("/")[0] for s in missing).most_common(25))
    blockers = [
        "P0 public/ intentionally contains only individually staged HIGHFLY-owned media, not the source world's complete visual/audio resources.",
        "Original ClaudeCraft public/ resources must NOT be bulk-copied: licenses and provenance vary by exact file.",
        "Literal reference inventory is incomplete by design (computed paths, imports and generated assets need a runtime graph).",
        "P4 entity mappings are code-only and guarded by VITE_HIGHFLY_P4=1; the Hunter Universal and selection/sex editor are not implemented.",
        "No playable independent 3D build has been verified, nor any Android landscape test.",
    ]
    result = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P5_PRIVATE_INDEPENDENT_WORLD_READINESS_AUDIT",
        "sourceCommit": SOURCE_SHA,
        "noFilesCopiedOrAlteredInGames": True,
        "commercialRelease": "BLOCKED_UNTIL_INDIVIDUAL_RIGHTS_AND_QA",
        "stageCodeFilesAtCreation": status.get("stats", {}).get("codeFiles"),
        "referencePublicFileCount": len(original_media),
        "independentStagePublicFileCount": len(staged_media),
        "sameRelativePathMissing": len(missing),
        "obviousLiteralMediaReferences": len(literals),
        "stageCodeFilesScannedForLiterals": scanned,
        "referencedButNotInStage": len(referenced_missing),
        "referencedAndNotInOriginal": len(missing_from_original),
        "selectedMediaFiles": sorted(staged_media),
        "missingExtensions": extensions,
        "missingTopFolders": top_dirs,
        "mediaReferencesMissingFromStage": referenced_missing[:250],
        "unresolvedEvenInReference": missing_from_original[:80],
        "kaykitCompleteZipPresent": KAYKIT_ZIP.is_file(),
        "blockers": blockers,
        "nextBuildPlan": [
            "Resolve dependencies of Eastbrook and player creation while preserving original sim, quests, dialogue, loot and save IDs.",
            "Reintroduce only individually verified original/KayKit media or new replacements; maintain a by-file license and source manifest.",
            "Build a private independent HIGHFLY runtime, then verify player, NPC, enemy, loot, equipment and save loading.",
            "After the world passes, expand available Adventurers skins and male/female modular appearance options.",
            "Polish 360-degree movement, attacks in motion, air combos and horizontal S23 Ultra MOBA controls.",
        ],
    }
    if not report_dir.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("REPORT_OUTSIDE_PRIVATE_WORKSPACE")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "WORLD_READINESS_P5.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    lines = [
        "# HIGHFLY ORIGIN — P5 world readiness (private)",
        "",
        "Read-only report. Not a game build and not an automatic license approval.",
        "",
        f"- Original public media count: {len(original_media)}",
        f"- HIGHFLY staged public media count: {len(staged_media)}",
        f"- Same-path media absent from stage: {len(missing)}",
        f"- Source code media literals scanned: {len(literals)} in {scanned} files",
        f"- Literal media refs not present in HIGHFLY stage: {len(referenced_missing)}",
        f"- Own KayKit Complete ZIP available: {'yes' if result['kaykitCompleteZipPresent'] else 'no'}",
        "",
        "## Missing original asset types (not licenses)",
        *(f"- {kind or '[no extension]'}: {count}" for kind, count in extensions.items()),
        "",
        "## Actual blockers",
        *(f"- {b}" for b in blockers),
        "",
        "## Action plan",
        *(f"{i}. {text}" for i, text in enumerate(result["nextBuildPlan"], 1)),
        "",
    ]
    (report_dir / "WORLD_READINESS_P5.md").write_text("\n".join(lines), encoding="utf8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=STAGE)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--out", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = audit(args.stage, args.original, args.out)
    compact = {key: result[key] for key in (
        "referencePublicFileCount", "independentStagePublicFileCount",
        "sameRelativePathMissing", "obviousLiteralMediaReferences",
        "referencedButNotInStage", "kaykitCompleteZipPresent"
    )}
    print("[HIGHFLY] P5 WORLD READINESS: " + json.dumps(compact, ensure_ascii=False))
    print("[HIGHFLY] PRIVATE REPORT: " + str(args.out / "WORLD_READINESS_P5.md"))
    print("[HIGHFLY] NO MEDIA COPIED. NO BUILD PUBLISHED. CLAUDECRAFT REFERENCE UNCHANGED.")


if __name__ == "__main__":
    main()
