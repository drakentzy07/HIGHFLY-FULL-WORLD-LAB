#!/usr/bin/env python3
"""P71 static visual matrix: nine classes, no copyrighted media copied."""
from __future__ import annotations
import json
import re
from pathlib import Path
import highfly_world7_codespace_audit as p70

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
OUT = ROOT / ".workspace/reports/highfly-world7/p71"
CLASSES = ("warrior","paladin","hunter","rogue","priest","shaman","mage","warlock","druid")

def analyze(stage: Path=STAGE) -> dict:
    if (stage.is_symlink() or not stage.is_dir()
            or not stage.resolve().is_relative_to((ROOT / ".workspace").resolve())):
        raise RuntimeError("P71_VISUAL_STAGE_MISSING_OR_UNSAFE")
    manifest = stage / "src/render/characters/manifest.ts"
    if manifest.is_symlink() or not manifest.is_file():
        raise RuntimeError("P71_VISUAL_MANIFEST_MISSING")
    source = manifest.read_text("utf8")
    results = {}
    for cls in CLASSES:
        pattern = re.compile(
            r"^\s*player_" + cls
            + r":\s*swims\(\{\s*url:[^\n]*?/([a-zA-Z0-9_.-]+\.glb)",
            re.M)
        match = pattern.search(source)
        if not match:
            results[cls] = {"status": "MANIFEST_MODEL_NOT_RESOLVED", "runtimeVerified": False}
            continue
        relative = "models/chars/players/" + match.group(1)
        asset = stage / "public" / relative
        exists = (asset.is_file() and not asset.is_symlink()
                  and asset.resolve().is_relative_to(stage.resolve()))
        clips = p70.gltf_animations(asset) if exists else {"status": "FILE_MISSING"}
        results[cls] = {
            "declaredModel": relative,
            "filePresent": bool(exists),
            "declaredAnimations": clips.get("animationCount"),
            "animationSample": clips.get("animationNames", [])[:14],
            "parseStatus": clips.get("status"),
            "rigCompatibilityVerified": False,
            "redistributionVerified": False,
            "runtimeVerified": False,
            "note": "Base model; modular appearance or the P4 private bridge can override it.",
        }
    bridge = "const heroBase = VISUALS.player_warrior;" in source
    return {
        "phase": "WORLD7_P71_NINE_CLASS_VISUAL_MATRIX",
        "modelCount": len(results),
        "classes": results,
        "p4WarriorVisualBridgeDetected": bridge,
        "p4OwnedHeroPresent": (stage / "public/highfly-private-p4/hero.glb").is_file(),
        "modelLicense": "UNVERIFIED_PER_FILE_DO_NOT_SHIP_FROM_REPORT",
        "gameplayTested": False,
    }

def run() -> dict:
    result = analyze()
    if OUT.is_symlink() or not OUT.resolve().is_relative_to((ROOT / ".workspace").resolve()):
        raise RuntimeError("P71_UNSAFE_VISUAL_REPORT")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P71_VISUAL_MATRIX.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
    lines = [
        "# HIGHFLY WORLD7 P71: nueve clases y modelos",
        "",
        "Auditoria estatica: NO prueba rig, VFX, skin, gameplay ni licencia exacta de cada archivo.",
        "",
        "| Clase | Modelo declarado | Existe | Animaciones declaradas |",
        "|---|---|---|---|",
    ]
    for cls, row in result["classes"].items():
        lines.append("| "+cls+" | "+row.get("declaredModel","NO RESUELTO")+" | "+
                     ("SI" if row.get("filePresent") else "NO")+" | "+
                     str(row.get("declaredAnimations","—"))+" |")
    lines += [
        "", "Puente visual P4: "+str(result["p4WarriorVisualBridgeDetected"]),
        "Knight propio P4: "+str(result["p4OwnedHeroPresent"]),
        "", "Si un modelo falta, resolver con KayKit propio/CC0 auditado; no usar placeholders.",
    ]
    (OUT / "P71_VISUAL_MATRIX.md").write_text("\n".join(lines)+"\n","utf8")
    return {"visualModels":len(result["classes"]),
            "filesPresent":sum(bool(a.get("filePresent")) for a in result["classes"].values()),
            "report":str(OUT / "P71_VISUAL_MATRIX.md"), "gameplayTested":False}

if __name__ == "__main__":
    print("[WORLD7 P71 VISUAL MATRIX] "+json.dumps(run(),ensure_ascii=False))
