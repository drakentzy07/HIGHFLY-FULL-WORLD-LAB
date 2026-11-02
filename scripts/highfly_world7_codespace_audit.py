#!/usr/bin/env python3
"""HIGHFLY WORLD 7 P70 — read-only private-stage diagnostic for VS Codespaces.

Never changes gameplay, skin files, original source or licensed media.
Only writes JSON + Markdown into ignored .workspace/reports/highfly-world7/.
Findings are source/asset inspections, NOT proof of working in-game behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / ".workspace"
STAGE = WORKSPACE / "highfly-origin-stage-p0"
ORIGINAL = WORKSPACE / "claudecraft-v0.44.7"
OUT = WORKSPACE / "reports/highfly-world7"

SOURCE_PATHS = (
    "src/main.ts",
    "src/sim/types.ts",
    "src/sim/content/classes.ts",
    "src/sim/player_motion.ts",
    "src/sim/combat/auto_attack.ts",
    "src/sim/sim.ts",
    "src/game/input.ts",
    "src/game/mobile_controls.ts",
    "src/game/highfly_fury_skill_touch.ts",
    "src/render/characters/manifest.ts",
    "src/ui/hud.ts",
    "src/ui/hud/action_bar/mobile_action_ring_controller.ts",
    "index.html",
)
MARKERS = (
    "HIGHFLY_P13_OWNED_KNIGHT_PREVIEW",
    "HIGHFLY_P48_FURY_MOBILE",
    "HIGHFLY_P63_COMBAT_C1",
    "HIGHFLY_P65_MOBILE_COMBAT",
    "HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM",
    "HIGHFLY_P68_FURY_GOLDEN_RECOVERY",
    "HIGHFLY_P69_FURY_CORE",
)
ANCHORS = {
    "legacyPreviewWarrior": r"characterPreview\.setClass\(['\"]warrior['\"]\)",
    "legacyClassType": r"(?:type\s+PlayerClass|ALL_CLASSES|resourceType\s*:)",
    "legacyRage": r"\b(?:rage|Rage)\b",
    "groundedDash": r"inp\.dash[\s\S]{0,180}\bp\.onGround\b",
    "aimPositionGate": r"targetMode\s*!==\s*['\"]position['\"]",
    "manualAttackTap": r"highflyTapBasicAttack|queueHighflyTap",
    "secondJump": r"highflyAirJumps|secondJump",
    "offlineSave": r"HIGHFLY_P41_OFFLINE_SAVE",
}

def within(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())

def safe_regular(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and within(path, WORKSPACE)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_source(path: Path) -> dict:
    if not safe_regular(path):
        return {"status": "MISSING_OR_UNSAFE"}
    raw = path.read_bytes()
    try:
        source = raw.decode("utf8")
    except UnicodeDecodeError:
        return {"status": "NOT_UTF8", "sha256": digest(raw)}
    return {
        "status": "FOUND",
        "bytes": len(raw),
        "sha256": digest(raw),
        "markers": [m for m in MARKERS if m in source],
        "anchors": [k for k, pattern in ANCHORS.items()
                    if re.search(pattern, source, re.MULTILINE)],
        "legacyWarriorReferences": len(re.findall(r"\bwarrior\b", source)),
    }

def gltf_animations(path: Path) -> dict:
    """Read only the header/JSON chunk of a GLB or JSON glTF; never copy assets."""
    try:
        if path.stat().st_size > 200_000_000:
            return {"status": "SKIPPED_OVERSIZE"}
        if path.suffix.lower() == ".gltf":
            if path.stat().st_size > 8_000_000:
                return {"status": "SKIPPED_JSON_OVERSIZE"}
            doc = json.loads(path.read_text("utf8"))
        else:
            with path.open("rb") as stream:
                header = stream.read(12)
                if len(header) != 12:
                    return {"status": "INVALID_GLB"}
                magic, version, length = struct.unpack("<4sII", header)
                if magic != b"glTF" or version != 2 or length != path.stat().st_size:
                    return {"status": "INVALID_GLB_HEADER"}
                chunk_header = stream.read(8)
                if len(chunk_header) != 8:
                    return {"status": "INVALID_GLB_CHUNK"}
                chunk_len, chunk_type = struct.unpack("<II", chunk_header)
                if chunk_type != 0x4E4F534A or chunk_len > 8_000_000:
                    return {"status": "INVALID_GLB_JSON"}
                doc = json.loads(stream.read(chunk_len).decode("utf8"))
        animations = doc.get("animations", [])
        if not isinstance(animations, list):
            return {"status": "INVALID_ANIMATIONS"}
        names = [a.get("name") or "(unnamed)" for a in animations
                 if isinstance(a, dict)]
        return {"status": "PARSED", "animationCount": len(animations),
                "animationNames": names[:150], "namesTruncated": len(names) > 150,
                "skinningCount": len(doc.get("skins", []))}
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        return {"status": "PARSE_FAILED", "error": type(exc).__name__}

def run() -> dict:
    if STAGE.is_symlink() or (STAGE.exists() and not within(STAGE, WORKSPACE)):
        raise RuntimeError("UNSAFE_PRIVATE_STAGE")
    if OUT.is_symlink() or (OUT.exists() and not within(OUT, WORKSPACE)):
        raise RuntimeError("UNSAFE_PRIVATE_REPORT")
    stage_ready = STAGE.is_dir()
    files = {rel: read_source(STAGE / rel) if stage_ready
             else {"status": "STAGE_ABSENT"} for rel in SOURCE_PATHS}
    glb = []
    asset_root = STAGE / "public/models"
    ignored = 0
    if stage_ready and asset_root.is_dir() and not asset_root.is_symlink():
        for path in sorted(asset_root.rglob("*")):
            if path.suffix.lower() not in (".glb", ".gltf"):
                continue
            if not safe_regular(path):
                ignored += 1
                continue
            if len(glb) >= 400:
                ignored += 1
                continue
            glb.append({"file": str(path.relative_to(STAGE)),
                        **gltf_animations(path)})
    manifest_path = STAGE / "HIGHFLY_STAGE_STATUS.json"
    manifest = {}
    if safe_regular(manifest_path):
        try:
            obj = json.loads(manifest_path.read_text("utf8"))
            manifest = {k: obj.get(k) for k in (
                "sourceCommit", "originalPublicMediaCopied",
                "phase", "status") if k in obj}
        except (ValueError, UnicodeError):
            manifest = {"error": "INVALID_STAGE_MANIFEST"}
    by_marker = {m: sorted(p for p, v in files.items()
                          if m in v.get("markers", [])) for m in MARKERS}
    aim = files["src/game/highfly_fury_skill_touch.ts"]["status"] == "FOUND"
    main = files["src/main.ts"]
    blockers = []
    if not stage_ready:
        blockers.append("PRIVATE_STAGE_NOT_FOUND")
    if files["src/sim/types.ts"]["status"] != "FOUND":
        blockers.append("MISSING_SIM_TYPES")
    if files["src/render/characters/manifest.ts"]["status"] != "FOUND":
        blockers.append("MISSING_CHARACTER_MANIFEST")
    if files["src/main.ts"]["status"] != "FOUND":
        blockers.append("MISSING_MAIN")
    if not by_marker["HIGHFLY_P68_FURY_GOLDEN_RECOVERY"]:
        blockers.append("P68_NOT_DETECTED_IN_SCANNED_SOURCES")
    if not (aim and by_marker["HIGHFLY_P69_FURY_CORE"]):
        blockers.append("P69_NOT_CONFIRMED_IN_SCANNED_SOURCES")
    result = {
        "phase": "WORLD7_P70_STAGE_AUDIT", "readOnlyGameplay": True,
        "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
        "stagePath": str(STAGE), "originalPath": str(ORIGINAL),
        "privateStageFound": stage_ready,
        "referenceSourceFound": (ORIGINAL / ".git").is_dir(),
        "stageManifest": manifest, "files": files,
        "markers": by_marker,
        "modelAnimationHeaders": glb,
        "unscannedModelCount": ignored,
        "modelsWithAnimation": sum(
            1 for item in glb if item.get("animationCount", 0) > 0),
        "animationNamesAreUnverifiedForRuntime": True,
        "codeDoesNotProveMobileBehavior": True,
        "blockers": blockers,
    }
    return result

def write_report(report: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P70_CODESPACE_AUDIT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf8")
    rows = [
        "# HIGHFLY WORLD 7 / P70 — Codespace preflight",
        "",
        f"- Stage privado presente: **{report['privateStageFound']}**",
        f"- Referencia v0.44.7 presente: **{report['referenceSourceFound']}**",
        f"- GLB/glTF inspeccionados: **{len(report['modelAnimationHeaders'])}**",
        f"- Modelos con animaciones declaradas: **{report['modelsWithAnimation']}**",
        "- No hay cambios al juego. Los nombres de clips declarados no prueban "
        "que el rig activo los pueda reproducir.",
        "",
        "## Bloqueos y advertencias",
    ]
    rows += ["- " + x for x in report["blockers"]] or ["- Ningún bloqueo estático detectado (NO significa gameplay validado)"]
    rows += ["", "## Marcadores presentes en código privado"]
    for k, paths in report["markers"].items():
        rows.append(f"- {k}: " + (", ".join(paths) if paths else "NO DETECTADO"))
    rows += [
        "", "## Próximo paso",
        "Revisar resultados, reparar prerequisitos de P68/P69 sólo si faltan, "
        "y conectar un adaptador de Hunter Universal en stage privado "
        "con tests + backup/rollback. No sustituir tipos de clases a ciegas.",
        "",
        "Detalle privado completo: P70_CODESPACE_AUDIT.json",
    ]
    (OUT / "P70_CODESPACE_AUDIT.md").write_text("\n".join(rows) + "\n", "utf8")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--strict", action="store_true",
                     help="Exit nonzero when mandatory stage prereqs are missing")
    args = cli.parse_args()
    report = run()
    write_report(report)
    print("[HIGHFLY WORLD7] " + json.dumps({
        "privateStageFound": report["privateStageFound"],
        "glbScanned": len(report["modelAnimationHeaders"]),
        "animatedModels": report["modelsWithAnimation"],
        "markers": {k: bool(v) for k, v in report["markers"].items()},
        "blockers": report["blockers"],
        "report": str(OUT / "P70_CODESPACE_AUDIT.md"),
        "jsonReport": str(OUT / "P70_CODESPACE_AUDIT.json"),
        "gameplayModified": False,
        "browserTested": False,
    }, ensure_ascii=False, indent=2))
    if args.strict and report["blockers"]:
        raise SystemExit(2)
