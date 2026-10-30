#!/usr/bin/env python3
"""HIGHFLY P9B: remove obsolete missing PRIVATE pilot HTML entries from stage Vite input.

This repairs ONLY the ignored independent HIGHFLY Vite config. It keeps the
original v0.44.7 checkout, game source, RPG systems and media untouched.
It does NOT remove required game entries, publish a build or approve assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
REPORT = ROOT / ".workspace/reports/highfly-p9b"
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

# Match only a complete rollupOptions.input entry. Not used anywhere else.
ENTRY_RX = re.compile(
    r"(?m)^(?P<indent>[ \t]+)(?P<key>[A-Za-z]\w*):[ \t]*"
    r"fileURLToPath\(new URL\('(?P<page>[^']+\.html)',[ \t]*"
    r"import\.meta\.url\)\),[ \t]*(?P<end>\r?\n|$)"
)
VALID_GAME_PAGES = {
    "index.html", "admin.html", "play.html", "guide.html",
    "editor.html", "wallet-handoff.html",
}
PILOT_PREFIX = "highfly-"


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf8")).hexdigest()


def analyze(stage: Path) -> dict:
    private = (ROOT / ".workspace").resolve()
    if not stage.resolve().is_relative_to(private):
        raise RuntimeError("STAGE_MUST_BE_PRIVATE")
    vite = stage / "vite.config.ts"
    if vite.is_symlink() or not vite.is_file():
        raise RuntimeError("VITE_CONFIG_MISSING_OR_LINK")
    content = vite.read_text(encoding="utf8")
    start = content.find("rollupOptions:")
    if start < 0:
        raise RuntimeError("VITE_ROLLUP_INPUT_NOT_FOUND")
    start = content.find("input:", start)
    if start < 0:
        raise RuntimeError("VITE_INPUT_MAP_NOT_FOUND")
    end = content.find("output:", start)
    if end <= start:
        raise RuntimeError("VITE_OUTPUT_MAP_NOT_FOUND")
    section = content[start:end]
    matches = list(ENTRY_RX.finditer(section))
    if not 5 <= len(matches) <= 28:
        raise RuntimeError("UNEXPECTED_VITE_ENTRY_COUNT: " + str(len(matches)))
    before_pages = [m.group("page") for m in matches]
    if len(set(before_pages)) != len(before_pages):
        raise RuntimeError("DUPLICATE_VITE_PAGE_ENTRIES")
    if not VALID_GAME_PAGES.issubset(set(before_pages)):
        raise RuntimeError("EXPECTED_GAME_HTML_ENTRIES_NOT_FOUND")
    drop_pages = []
    missing_core = []
    for match in matches:
        page = match.group("page")
        if Path(page).is_absolute() or ".." in Path(page).parts:
            raise RuntimeError("UNSAFE_VITE_ENTRY: " + page)
        actual = stage / page
        if actual.is_file() and not actual.is_symlink():
            continue
        if page.startswith(PILOT_PREFIX) and page.endswith(".html"):
            drop_pages.append(page)
        else:
            missing_core.append(page)
    if missing_core:
        raise RuntimeError(
            "REQUIRED_GAME_ENTRY_MISSING: " + ", ".join(missing_core)
            + ". P9 must stage the original core HTML pages before P9B."
        )
    new_section = ENTRY_RX.sub(
        lambda m: "" if m.group("page") in drop_pages else m.group(0),
        section,
    )
    updated = content[:start] + new_section + content[end:]
    final_pages = [m.group("page") for m in ENTRY_RX.finditer(new_section)]
    if len(final_pages) + len(drop_pages) != len(before_pages):
        raise RuntimeError("UNEXPECTED_VITE_REPAIR_RESULT")
    if not VALID_GAME_PAGES.issubset(set(final_pages)):
        raise RuntimeError("VITE_GAME_PAGES_WOULD_BE_REMOVED")
    return {
        "file": vite, "original": content, "new": updated,
        "removedPilotEntries": drop_pages,
        "gameEntriesPreserved": sorted(VALID_GAME_PAGES),
        "remainingHtmlEntries": final_pages,
        "sourceConfigSha256": sha_text(content),
        "updatedConfigSha256": sha_text(updated),
    }


def repair(stage: Path = STAGE, report: Path = REPORT, *, apply: bool = False) -> dict:
    private = (ROOT / ".workspace").resolve()
    if not report.resolve().is_relative_to(private):
        raise RuntimeError("REPORT_MUST_BE_PRIVATE")
    data = analyze(stage)
    summary = {
        "project": "HIGHFLY ORIGIN",
        "phase": "P9B_VITE_MISSING_PRIVATE_PILOT_INPUT_FIX",
        "sourceCommit": p9.SHA,
        "removedPilotEntries": data["removedPilotEntries"],
        "gameEntriesPreserved": data["gameEntriesPreserved"],
        "remainingHtmlEntries": data["remainingHtmlEntries"],
        "sha256Before": data["sourceConfigSha256"],
        "sha256After": data["updatedConfigSha256"],
        "originalReferenceChanged": False,
        "gameplayFilesChanged": False,
        "mediaFilesChanged": False,
        "publishApproved": False,
        "applied": bool(apply),
    }
    if apply:
        report.mkdir(parents=True, exist_ok=True)
        before = report / "VITE_CONFIG_BEFORE_P9B.ts"
        if data["removedPilotEntries"] and not before.exists():
            before.write_text(data["original"], encoding="utf8")
        if data["file"].read_text(encoding="utf8") != data["original"]:
            raise RuntimeError("VITE_CONFIG_CHANGED_DURING_REPAIR")
        if data["new"] != data["original"]:
            data["file"].write_text(data["new"], encoding="utf8")
        (report / "VITE_INPUT_FIX_P9B.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply to private stage only")
    args = parser.parse_args()
    # Assert the same source/media boundary as the P9 build.
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    result = repair(apply=args.apply)
    print("[HIGHFLY] P9B VITE ENTRIES: " + json.dumps({
        "removedMissingPilotPages": result["removedPilotEntries"],
        "preservedGamePages": result["gameEntriesPreserved"],
        "applied": result["applied"],
        "originalReferenceChanged": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] P9B " + ("PRIVATE VITE INPUTS REPAIRED" if args.apply else "DRY RUN ONLY"))
    print("[HIGHFLY] ClaudeCraft original, Eastbrook, RPG systems and private media untouched.")


if __name__ == "__main__":
    main()
