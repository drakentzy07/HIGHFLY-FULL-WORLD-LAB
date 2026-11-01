#!/usr/bin/env python3
"""P51 ONE-SHOT: audit HIGHFLY P50 stage + reversible Eastbrook monument probe.

Runs without ripgrep. A single invocation reports all known defects with
concrete source lines and produces a compact TXT + full JSON.
--apply adds ONLY an opt-in ?hf_probe_monument=hide visibility test, builds
private P9, and rolls back on failure. It does not remove any world entity,
touch sim/quests, alter player saves, or redistribute private KayKit models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
REPORT_DIR = ROOT / ".workspace/reports/highfly-p51"
TOWN_FILE = STAGE / "src/render/eastbrook_town.ts"
MARK = "HIGHFLY_P51_MONUMENT_VISUAL_PROBE"
ANCHOR = """  const monumentBody = buildRealmBuilderMonumentBody(monumentTemplate.raw, monumentSeat);
  group.add(monumentBody.group);
  const monumentFx = buildRealmBuilderMonumentFx(monumentSeat);
  group.add(monumentFx.group);"""
REPLACEMENT = ANCHOR + """
  // HIGHFLY_P51_MONUMENT_VISUAL_PROBE: local, reversible browser experiment.
  // Add ?hf_probe_monument=hide to hide the 24-unit monument body and effects.
  // This changes ONLY rendering, not its quest, entity or collision definition.
  if (new URLSearchParams(window.location.search).get('hf_probe_monument') === 'hide') {
    monumentBody.group.scale.setScalar(0);
    monumentFx.group.scale.setScalar(0);
    console.warn('[HIGHFLY P51] MONUMENTO OCULTO SOLO EN ESTA URL', {
      x: monumentSeat.x, z: monumentSeat.z, originalHeight: monumentSeat.nativeHeight,
    });
  }"""

TOPICS = {
  "01_PANTALLAS_Y_CAPAS": [
    r"highfly[-_]p4[567890]", r"highfly[-_]p50",
    r"highfly_loading_bg", r"ls-progress", r"ls-tip",
    r"mode-select", r"highfly_enter_world_bg", r"highfly_splash",
  ],
  "02_LOG_Y_BADGE_P35": [
    r"HIGHFLY\s*P35", r"NPC/BOLSA", r"HIGHFLY\s*LOG",
    r"highfly[-_]log", r"fallos\s*[·\-]", r"DESCARGAR",
  ],
  "03_EDITOR_DE_PERSONAJE": [
    r"offline-appearance", r"offline-skin-row",
    r"CREATION_SKIN_PRESETS", r"modularAppearance",
    r"appearance_customizer", r"bodyGender",
  ],
  "04_JOYSTICK_GIRO_Y_FURY": [
    r"BACKPEDAL_MULT", r"autorun", r"touchDashUntil",
    r"mobile-dodge", r"furyDashing", r"highflyAirJumps",
    r"mobile-action-ring", r"mobile-action-attack",
  ],
  "05_JABALIES_Y_MONSTRUOS": [
    r"mob_boar", r"WILD_BOAR", r"wild_boar\.glb",
    r"mob_wolf", r"wolf\.glb", r"mob_spider",
  ],
  "06_EASTBROOK_BLOQUE_GIGANTE": [
    r"eastbrookRealmBuilderMonumentFxBody",
    r"buildRealmBuilderMonumentBody", r"eastbrookTownMicroOpaqueBatch",
    r"eastbrook_grand_armoury", r"highflyP45CheckBuilding",
    r"eastbrook.*placeholder", r"EASTBROOK_LAYOUT\.buildings",
  ],
  "07_NATACION_Y_BARCOS": [
    r"swimPitch", r"swimBlend", r"underwater",
    r"rowboat\.glb", r"ship.*\.glb", r"boat.*\.glb",
    r"shipMonument", r"harbor",
  ],
  "08_BOLSA_LOOT_Y_MISIONES": [
    r"highfly/p47-icons", r"mother_of_pearl", r"ps_lustrous_pearl",
    r"ui/items", r"lootIcon", r"mobile-interact",
    r"coach_prompt", r"tutorial",
  ],
  "09_FULLSCREEN_ANDROID": [
    r"requestFullscreen", r"fullscreen", r"manifest\.webmanifest",
    r"screen\.orientation", r"mobile-touch", r"safe-area-inset",
  ],
}
COMPILED = {
    name: re.compile("|".join(f"(?:{pattern})" for pattern in parts), re.I)
    for name, parts in TOPICS.items()
}
EXTENSIONS = {".ts", ".tsx", ".js", ".mjs", ".css", ".html", ".json"}
ASSETS = [
    "public/models/creatures/wolf.glb",
    "public/models/creatures/wild_boar.glb",
    "public/models/props/eastbrook_grand_armoury.glb",
    "public/highfly/official/highfly_splash.png",
    "public/highfly/official/highfly_enter_world_bg.png",
    "public/highfly/official/highfly_loading_bg.png",
    "public/highfly/p47.css",
    "public/highfly/p48.css",
    "public/highfly/p50_shell.css",
]

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def patch(source: str) -> str:
    if MARK in source:
        raise RuntimeError("P51_ALREADY_APPLIED")
    count = source.count(ANCHOR)
    if count != 1:
        raise RuntimeError(f"P51_EASTBROOK_MONUMENT_ANCHOR_DRIFT count={count}")
    return source.replace(ANCHOR, REPLACEMENT, 1)

def walk_sources():
    for base in (STAGE/"src", STAGE/"public", STAGE/"index.html"):
        if base.is_file():
            yield base
        elif base.is_dir():
            for path in base.rglob("*"):
                if path.is_file() and not path.is_symlink() and path.suffix.lower() in EXTENSIONS:
                    yield path

def inspect_sources() -> tuple[int, dict]:
    counts = defaultdict(int)
    source_files = defaultdict(set)
    examples = defaultdict(list)
    scanned = 0
    for path in walk_sources():
        try:
            if path.stat().st_size > 1_200_000:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        scanned += 1
        rel = str(path.relative_to(STAGE))
        for number, line in enumerate(lines, 1):
            for topic, pattern in COMPILED.items():
                if not pattern.search(line):
                    continue
                counts[topic] += 1
                source_files[topic].add(rel)
                if len(examples[topic]) < 24:
                    examples[topic].append({
                        "file": rel, "line": number,
                        "text": line.strip()[:190]
                    })
    result = {
        topic: {
            "occurrences": counts[topic],
            "files": sorted(source_files[topic])[:35],
            "examples": examples[topic],
        }
        for topic in TOPICS
    }
    return scanned, result

def private_kaykit_matches() -> dict:
    candidates = [
        ROOT/".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip",
        ROOT/".workspace/private-imports/KIT_COMPLETO.zip",
    ]
    matches = []
    checked = []
    for path in candidates:
        if not path.is_file() or path.is_symlink():
            continue
        checked.append(str(path.relative_to(ROOT)))
        try:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if re.search(r"(?i)(boar|wild.?pig|pig|hog|jabal)", name):
                        if len(matches) < 35:
                            matches.append(name[:190])
        except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
            return {"checked": checked, "matches": matches, "archiveError": str(exc)}
    return {
        "checked": checked, "matches": matches,
        "note": "Solo lectura de nombres; no se extrajo ni publico contenido privado."
    }

def validate_stage():
    p9.preflight(p9.ORIGINAL, STAGE, p9.REPORT)
    if not TOWN_FILE.is_file() or TOWN_FILE.is_symlink():
        raise RuntimeError("P51_STAGE_TOWN_MISSING")
    html = (STAGE/"index.html").read_text(encoding="utf-8")
    if "HIGHFLY_P50_SHELL_CLEANUP" not in html:
        raise RuntimeError("P51_REQUIRES_APPLIED_P50")
    return TOWN_FILE.read_text(encoding="utf-8")

def snapshot_report(apply: bool) -> dict:
    scanned, topics = inspect_sources()
    assets = {
        rel: {
            "exists": (STAGE/rel).is_file(),
            "bytes": (STAGE/rel).stat().st_size if (STAGE/rel).is_file() else None,
        } for rel in ASSETS
    }
    saved_p50 = ROOT/".workspace/reports/highfly-p50/P50_STATUS.json"
    p50 = {}
    if saved_p50.is_file():
        try: p50 = json.loads(saved_p50.read_text(encoding="utf-8"))
        except (OSError, ValueError): pass
    return {
        "phase": "HIGHFLY_P51_ALL_IN_ONE_AUDIT_AND_VISUAL_PROBE",
        "mode": "APPLY_PROBE" if apply else "AUDIT_ONLY",
        "scannedSourceFiles": scanned,
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "alreadyP50Built": p50.get("mode") == "BUILD_GREEN_NOT_BROWSER_VERIFIED",
        "sourceAssetAvailability": assets,
        "privateKayKitBoarFilenames": private_kaykit_matches(),
        "suspiciousRootFromP50": {
            "name": "eastbrookRealmBuilderMonumentFxBody",
            "measured": [13.8, 24.0, 14.6],
            "x": -14.8, "z": -102,
            "hypothesis": "Could account for giant geometry; NOT confirmed",
            "testUrl": "?hf_probe_monument=hide",
            "diagnosticsUrl": "?hf_audit_eastbrook=1&hf_probe_monument=hide",
        },
        "topics": topics,
        "originalWorldAndSavesChanged": False,
        "boarModelFixed": False,
        "furyFullCombatCompleted": False,
        "browserVerified": False,
    }

def save_report(report: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR/"P51_FULL_AUDIT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    lines = [
        "HIGHFLY P51 — AUDITORIA INTEGRAL (SIN RG)",
        f"Modo: {report['mode']} | archivos: {report['scannedSourceFiles']}",
        f"Modelo jabalí disponible: {report['sourceAssetAvailability']['public/models/creatures/wild_boar.glb']['exists']}",
        f"KayKit ZIP boar/pig filenames: {len(report['privateKayKitBoarFilenames']['matches'])}",
        "EASTBROOK: sospechoso eastbrookRealmBuilderMonumentFxBody "
        "(13.8×24×14.6, x=-14.8,z=-102), sin confirmación.",
        "Probar ?hf_probe_monument=hide y comparar en la MISMA zona.",
        "",
    ]
    for topic, info in report["topics"].items():
        lines.append(f"=== {topic}: {info['occurrences']} coincidencias ===")
        for item in info["examples"][:9]:
            lines.append(f"{item['file']}:{item['line']} {item['text'][:130]}")
        lines.append("")
    report_text = "\n".join(lines) + "\n"
    (REPORT_DIR/"P51_RESUMEN.txt").write_text(report_text, encoding="utf-8")
    print(report_text[:9500])
    print("REPORTE:", REPORT_DIR/"P51_RESUMEN.txt")
    print("DETALLE JSON:", REPORT_DIR/"P51_FULL_AUDIT.json")
    print("NO se extrajo contenido KayKit, ni se editaron partidas.")

def run(apply=False):
    source = validate_stage()
    next_town = patch(source)
    audit = snapshot_report(apply)
    if not apply:
        save_report(audit)
        return audit
    backup = REPORT_DIR/"backups/src/render/eastbrook_town.ts"
    if backup.exists() or backup.is_symlink():
        raise RuntimeError("P51_BACKUP_ALREADY_EXISTS")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOWN_FILE, backup)
    if file_hash(TOWN_FILE) != file_hash(backup):
        raise RuntimeError("P51_BACKUP_CHECKSUM_FAILED")
    try:
        if TOWN_FILE.read_text(encoding="utf-8") != source:
            raise RuntimeError("P51_CONCURRENT_STAGE_EDIT")
        TOWN_FILE.write_text(next_town, encoding="utf-8")
        subprocess.run(
            [sys.executable, str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
            cwd=ROOT, check=True,
        )
    except BaseException:
        shutil.copy2(backup, TOWN_FILE)
        print("[HIGHFLY] P51 ROLLBACK a P50 aplicado", file=sys.stderr)
        raise
    audit["mode"] = "BUILD_GREEN_NOT_BROWSER_VERIFIED"
    save_report(audit)
    return audit

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--apply", action="store_true",
                     help="Compila solamente el interruptor experimental del monumento")
    args = cli.parse_args()
    run(args.apply)
