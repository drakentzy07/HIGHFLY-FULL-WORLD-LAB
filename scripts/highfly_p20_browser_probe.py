#!/usr/bin/env python3
"""HIGHFLY P20: install/remove a TEMPORARY, private-only browser asset probe.

Injects one external script into the independent stage's index/play pages.
It observes asset fetch/load failures and offers a JSON download; it does NOT
change renderers, loaders, game rules, assets or error handling policy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
REPORT = ROOT / ".workspace/reports/highfly-p20"
SOURCE_JS = ROOT / "scripts/highfly_p20_browser_asset_probe.js"
TARGET = "public/highfly-private-p20/asset-probe.js"
MARKUP = '<script src="/highfly-private-p20/asset-probe.js" data-highfly-p20="asset-log"></script>'
HTML_FILES = ("index.html", "play.html")

sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9


def inject_html(html: str) -> str:
    count = html.count(MARKUP)
    if count == 1:
        return html
    if count != 0 or "data-highfly-p20" in html or "highfly-private-p20" in html:
        raise RuntimeError("P20_UNKNOWN_EXISTING_PROBE_FRAGMENT")
    head = re.search(r"<head(?:\s[^>]*)?>", html, flags=re.IGNORECASE)
    if head is None:
        raise RuntimeError("P20_NO_HTML_HEAD")
    offset = head.end()
    return html[:offset] + "\n  " + MARKUP + html[offset:]


def remove_html(html: str) -> str:
    if html.count(MARKUP) > 1:
        raise RuntimeError("P20_DUPLICATE_INJECTION")
    return html.replace("\n  " + MARKUP, "").replace(MARKUP, "")


def verify_stage(stage: Path, source_js: Path) -> dict:
    if not source_js.is_file() or source_js.is_symlink():
        raise RuntimeError("P20_PROBE_SOURCE_UNAVAILABLE")
    source = source_js.read_bytes()
    if b"__HIGHFLY_P20_PROBE__" not in source:
        raise RuntimeError("P20_JS_PROBE_SIGNATURE_MISSING")
    node_check = subprocess.run(["node", "--check", str(source_js)],
                                text=True, capture_output=True, timeout=15)
    if node_check.returncode:
        raise RuntimeError("P20_BROWSER_SCRIPT_SYNTAX_INVALID: " + node_check.stderr[-600:])
    target = stage / TARGET
    if target.is_symlink() or target.is_dir():
        raise RuntimeError("P20_TARGET_UNSAFE")
    if target.is_file() and target.read_bytes() != source:
        raise RuntimeError("P20_EXISTING_PROBE_CONTENT_CONFLICT")
    html_updates = []
    for relative in HTML_FILES:
        file = stage / relative
        if not file.is_file() or file.is_symlink():
            raise RuntimeError("P20_PRIVATE_ENTRY_NOT_FOUND: " + relative)
        text = file.read_text(encoding="utf8")
        html_updates.append((file, text, inject_html(text)))
    return {"source": source, "target": target, "pages": html_updates}


def execute(mode: str, build: bool) -> dict:
    # Existing P9 guard checks pinned 0.44.7 ref and protected RPG simulation.
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    state = verify_stage(STAGE, SOURCE_JS)
    REPORT.mkdir(parents=True, exist_ok=True)
    altered = []
    if mode == "APPLY":
        target = state["target"]
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE_JS, target)
        for page, old, new in state["pages"]:
            if old != new:
                backup = REPORT / (page.name + ".before_p20")
                if not backup.exists():
                    backup.write_text(old, encoding="utf8")
                if page.read_text(encoding="utf8") != old:
                    raise RuntimeError("P20_CONCURRENT_HTML_EDIT: " + str(page))
                page.write_text(new, encoding="utf8")
                altered.append(page.name)
    elif mode == "REMOVE":
        for relative in HTML_FILES:
            page = STAGE / relative
            old = page.read_text(encoding="utf8")
            new = remove_html(old)
            if new != old:
                page.write_text(new, encoding="utf8")
                altered.append(page.name)
        if state["target"].is_file():
            state["target"].unlink()
    else:
        altered = [page.name for page, old, new in state["pages"] if old != new]
    result = {
        "phase": "P20_TEMPORARY_PRIVATE_BROWSER_ASSET_PROBE",
        "mode": mode,
        "candidatePages": list(HTML_FILES),
        "affectedOrWouldAffectPages": altered,
        "scriptSha256": hashlib.sha256(state["source"]).hexdigest(),
        "privateOnly": True,
        "protectedSimulationChanged": False,
        "assetFilesChanged": False,
        "licensePolicyChanged": False,
        "gameplayVerified": False,
        "publicReleaseApproved": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "exportedReportName": "HIGHFLY_P20_BROWSER_ASSET_LOG.json",
    }
    if mode in ("APPLY", "REMOVE") and build:
        result["buildExitCode"] = p9.smoke()["exitCode"]
    path = REPORT / "P20_PROBE_STATE.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[HIGHFLY] P20 " + mode + ": " + json.dumps({
        "pages": altered, "buildExitCode": result.get("buildExitCode"),
        "privateOnly": True, "gameplayVerified": False,
    }, ensure_ascii=False))
    print("[HIGHFLY] P20 STATE: " + str(path))
    print("[HIGHFLY] PROBE: press 'HIGHFLY LOG · DESCARGAR' in browser after Enter World.")
    print("[HIGHFLY] REMOVAL: python3 scripts/highfly_p20_browser_probe.py --remove")
    if result.get("buildExitCode") not in (None, 0):
        raise SystemExit("P20_BUILD_FAILED_REVIEW_P9_LOG")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--remove", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    mode = "APPLY" if args.apply else "REMOVE" if args.remove else "DRY_RUN"
    execute(mode, not args.no_build)


if __name__ == "__main__":
    main()
