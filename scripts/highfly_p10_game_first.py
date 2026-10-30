#!/usr/bin/env python3
"""HIGHFLY P10: restore missing UI source files and focus the PRIVATE Vite build.

No gameplay code, original ClaudeCraft files, assets or public destinations are
changed. Admin/guide/wallet source is retained; those pages are only omitted
from the temporary build so we can get to the playable client faster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
REPORT = ROOT / ".workspace/reports/highfly-p10"
GAME_ENTRIES = {"main": "index.html", "play": "play.html", "editor": "editor.html"}
MAX_SOURCE_BYTES = 3_000_000
ENTRY_RX = re.compile(
    r"(?m)^[ \t]+(?P<key>[A-Za-z]\w*):[ \t]*fileURLToPath\(new URL\('(?P<page>[^']+\.html)',[ \t]*import\.meta\.url\)\),[ \t]*\r?\n"
)
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def private_only(*paths: Path) -> None:
    prefix = (ROOT / ".workspace").resolve()
    for path in paths:
        if not path.resolve().is_relative_to(prefix):
            raise RuntimeError("OUTSIDE_PRIVATE_WORKSPACE: " + str(path))


def plan(original: Path = ORIGINAL, stage: Path = STAGE, report: Path = REPORT) -> dict:
    private_only(original, stage, report)
    config = stage / "vite.config.ts"
    if not config.is_file() or config.is_symlink():
        raise RuntimeError("MISSING_STAGE_VITE_CONFIG")
    content = config.read_text(encoding="utf8")
    start = content.find("rollupOptions:")
    if start < 0:
        raise RuntimeError("ROLLUP_OPTIONS_NOT_FOUND")
    start = content.find("input:", start)
    end = content.find("output:", start)
    if start < 0 or end < start:
        raise RuntimeError("ROLLUP_INPUT_OR_OUTPUT_NOT_FOUND")
    section = content[start:end]
    entries = list(ENTRY_RX.finditer(section))
    if not entries:
        raise RuntimeError("NO_VITE_HTML_ENTRIES")
    existing = {e.group("key"): e.group("page") for e in entries}
    if len(existing) != len(entries):
        raise RuntimeError("DUPLICATE_VITE_ENTRY_KEYS")
    for key, page in GAME_ENTRIES.items():
        if existing.get(key) != page or not (stage / page).is_file():
            raise RuntimeError("GAME_ENTRY_MISSING: " + key + " " + page)
    for entry in entries:
        page = entry.group("page")
        if Path(page).is_absolute() or ".." in Path(page).parts:
            raise RuntimeError("UNSAFE_VITE_ENTRY: " + page)
    focused = ENTRY_RX.sub(
        lambda e: e.group(0) if e.group("key") in GAME_ENTRIES else "", section
    )
    revised = content[:start] + focused + content[end:]
    dropped = [e.group("page") for e in entries if e.group("key") not in GAME_ENTRIES]

    # Source code only. Never copy models, audio, original UI images or textures.
    missing = []
    for file in (original / "src").rglob("*.svelte"):
        if not file.is_file() or file.is_symlink() or file.stat().st_size > MAX_SOURCE_BYTES:
            raise RuntimeError("UNSAFE_OR_OVERSIZED_SVELTE_SOURCE: " + str(file))
        target = stage / file.relative_to(original)
        if target.is_symlink():
            raise RuntimeError("STAGE_SVELTE_SYMLINK: " + str(target))
        if not target.exists():
            missing.append((file, target))
        elif not target.is_file():
            raise RuntimeError("STAGE_SVELTE_CONFLICT: " + str(target))
    config_source, config_target = original / "svelte.config.js", stage / "svelte.config.js"
    if config_source.is_file() and not config_target.exists():
        if config_source.is_symlink() or config_source.stat().st_size > MAX_SOURCE_BYTES:
            raise RuntimeError("UNSAFE_SVELTE_CONFIG")
        missing.append((config_source, config_target))
    return {
        "config": config, "before": content, "after": revised,
        "removedFromBuildOnly": dropped,
        "keptGamePages": list(GAME_ENTRIES.values()), "missingSourceCode": missing,
    }


def apply(data: dict, report: Path = REPORT) -> dict:
    private_only(report)
    config = data["config"]
    if config.read_text(encoding="utf8") != data["before"]:
        raise RuntimeError("VITE_CONFIG_CHANGED_DURING_P10")
    for source, dest in data["missingSourceCode"]:
        private_only(source, dest)
        if dest.exists() or dest.is_symlink():
            raise RuntimeError("SOURCE_CREATED_CONCURRENTLY: " + str(dest))
    report.mkdir(parents=True, exist_ok=True)
    backup = report / "VITE_BEFORE_P10.ts"
    if not backup.exists():
        backup.write_text(data["before"], encoding="utf8")
    for source, dest in data["missingSourceCode"]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        if checksum(source) != checksum(dest):
            raise RuntimeError("SOURCE_COPY_FAILED: " + str(dest))
    if data["after"] != data["before"]:
        config.write_text(data["after"], encoding="utf8")
    result = {
        "phase": "P10_PRIVATE_GAME_FIRST",
        "sourceCommit": p9.SHA,
        "missingSourceComponentsRecovered": len(data["missingSourceCode"]),
        "buildOnlyPagesExcluded": data["removedFromBuildOnly"],
        "gameBuildPages": data["keptGamePages"],
        "referenceGameModified": False,
        "simulationModified": False,
        "originalMediaImported": False,
        "playableVerified": False,
        "publicReleaseApproved": False,
    }
    (report / "GAME_FIRST_P10.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    # Existing P9 verifies source pin, player bridge, seven imported GLBs and
    # source integrity of critical RPG subsystems.
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    data = plan()
    print("[HIGHFLY] P10 GAME-FIRST PLAN: " + json.dumps({
        "missingSvelteSourceFiles": len(data["missingSourceCode"]),
        "removedOnlyFromViteBuild": data["removedFromBuildOnly"],
        "preservedBuildEntries": data["keptGamePages"],
    }, ensure_ascii=False))
    if not args.apply:
        print("[HIGHFLY] P10 DRY RUN ONLY")
        return
    result = apply(data)
    print("[HIGHFLY] P10 GAME-FIRST APPLIED: " + json.dumps(result, ensure_ascii=False))
    print("[HIGHFLY] No original media copied, no game logic deleted, no public deployment.")


if __name__ == "__main__":
    main()
