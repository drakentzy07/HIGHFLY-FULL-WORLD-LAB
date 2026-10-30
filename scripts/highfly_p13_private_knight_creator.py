#!/usr/bin/env python3
"""HIGHFLY P13: render P4 owned Knight in PRIVATE offline character preview.

ClaudeCraft's creation UI uses its modular WOC body before default VISUALS;
P11 changed boot preloads, not the modular preview call. In the independent
HIGHFLY build only, force previewClassBody to use setClass('warrior'), which
P4 maps to the owned KayKit Knight. Hide the unusable original modular editor
during this temporary preview, without altering creation/gameplay mechanics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
REPORT = ROOT / ".workspace/reports/highfly-p13"
MARKER = "HIGHFLY_P13_OWNED_KNIGHT_PREVIEW"
BEFORE = """function previewClassBody(cls: PlayerClass): void {
  if (!characterPreview) return;
  const look = modularLookForClass(cls);"""
AFTER = """function previewClassBody(cls: PlayerClass): void {
  if (!characterPreview) return;
  // HIGHFLY_P13_OWNED_KNIGHT_PREVIEW: PRIVATE visual bridge only.
  // The Sim still uses the original warrior mechanics during this test.
  if (import.meta.env.VITE_HIGHFLY_P4 === '1') {
    characterPreview.setClass('warrior');
    return;
  }
  const look = modularLookForClass(cls);"""
EDITOR_BEFORE = """  const existing = appearanceUis.get(panelId);
  if (!modularLookForClass(cls)) {"""
EDITOR_AFTER = """  const existing = appearanceUis.get(panelId);
  // HIGHFLY_P13_OWNED_KNIGHT_PREVIEW: the old modular bodies are absent
  // in the PRIVATE independent build. Keep original editor code below.
  if (import.meta.env.VITE_HIGHFLY_P4 === '1') {
    existing?.destroy();
    appearanceUis.delete(panelId);
    forgetAppearancePanel(panelId);
    host.hidden = true;
    return;
  }
  if (!modularLookForClass(cls)) {"""
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9


def plan(stage: Path = STAGE) -> dict:
    if not stage.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("PRIVATE_STAGE_REQUIRED")
    main = stage / "src/main.ts"
    if not main.is_file() or main.is_symlink():
        raise RuntimeError("HIGHFLY_MAIN_SOURCE_MISSING")
    original = main.read_text(encoding="utf8")
    if AFTER in original and EDITOR_AFTER in original:
        return {"source": original, "updated": original, "main": main}
    if original.count(BEFORE) != 1 or original.count(EDITOR_BEFORE) != 1:
        raise RuntimeError("HIGHFLY_P13_CREATOR_SOURCE_SIGNATURE_MISMATCH")
    if MARKER in original:
        raise RuntimeError("HIGHFLY_P13_PARTIAL_PATCH_DETECTED")
    revised = original.replace(BEFORE, AFTER, 1).replace(EDITOR_BEFORE, EDITOR_AFTER, 1)
    if revised.count(MARKER) != 2:
        raise RuntimeError("HIGHFLY_P13_MARKER_COUNT_UNEXPECTED")
    return {"source": original, "updated": revised, "main": main}


def apply(stage: Path = STAGE, report: Path = REPORT) -> dict:
    if not report.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("PRIVATE_REPORT_REQUIRED")
    p9.preflight(p9.ORIGINAL, stage, p9.REPORT)
    data = plan(stage)
    if data["main"].read_text(encoding="utf8") != data["source"]:
        raise RuntimeError("CREATOR_CHANGED_DURING_PATCH")
    report.mkdir(parents=True, exist_ok=True)
    if data["updated"] != data["source"]:
        backup = report / "MAIN_BEFORE_P13.ts"
        if not backup.exists():
            backup.write_text(data["source"], encoding="utf8")
        data["main"].write_text(data["updated"], encoding="utf8")
    result = {
        "phase": "P13_PRIVATE_KAYKIT_CREATOR_PREVIEW",
        "changed": data["updated"] != data["source"],
        "visualMapping": "P4_VISUALS.player_warrior_TO_KAYKIT_KNIGHT",
        "legacyAppearanceEditor": "hidden in private preview; source preserved",
        "characterClassSimulation": "WARRIOR_UNTIL_HUNTER_UNIVERSAL_MIGRATION",
        "maleFemaleEditorDone": False,
        "gameplayVerified": False,
        "originalCodeChanged": False,
        "rpgSimulationChanged": False,
        "mediaCopiedFromClaudeCraft": False,
        "releaseApproved": False,
    }
    (report / "KAYKIT_CREATOR_P13.json").write_text(json.dumps(
        result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        result = apply()
    else:
        state = plan()
        result = {"changedIfApplied": state["source"] != state["updated"]}
    print("[HIGHFLY] P13 PRIVATE CREATOR: " + json.dumps(result, ensure_ascii=False))
    print("[HIGHFLY] P13 does not fix world missing models or implement Hunter Universal yet.")


if __name__ == "__main__":
    main()
