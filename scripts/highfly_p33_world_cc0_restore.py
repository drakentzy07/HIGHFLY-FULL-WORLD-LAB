#!/usr/bin/env python3
"""P33: world-wide CC0 provenance bulk restoration + Hunter/NPC selector diagnostics.

Dry-run by default; --apply restores ONLY assets with an exact source->output
conversion spec and a CC0 provider confirmed in v0.44.7 credits. Preserves IDs,
all game/selector/renderer code, P8-owned buildings and non-provisional assets.
Does not redistribute private KayKit SOURCE V7, publish or start a server.
Missing/unsafe/unverified modular actor libraries are reported, never faked.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p21_runtime_asset_recovery as p21
import highfly_p23_real_kaykit_upgrade as p23

ORIGINAL = p9.ORIGINAL
STAGE = p9.STAGE
OUT = ROOT / ".workspace/reports/highfly-p33-reuse-world"
P30 = ROOT / ".workspace/reports/highfly-p30-master/P30_ALL_MEDIA_AND_USAGE.csv"
PROTECTED = {"models/biome/" + x for x in p9.BUILDING_NAMES}
ACTORS = (
    "models/chars/modular/warrior_modular.glb",
    "models/chars/players/knight.glb",
    "models/chars/players/mage.glb",
    "models/chars/players/rogue.glb",
    "models/chars/players/barbarian.glb",
    "models/chars/players/paladin.glb",
    "models/chars/players/druid.glb",
    "models/chars/players/mage_classic.glb",
    "models/weapons/sword_1handed.glb",
    "models/weapons/staff.glb",
    "models/creatures/wolf.glb",
    "models/creatures/training_dummy.glb",
)
SOURCE_CODE = (
    "src/render/characters/index.ts",
    "src/render/characters/manifest.ts",
    "src/render/characters/npc_looks.ts",
    "src/render/characters/modular.ts",
    "src/render/characters/assets.ts",
    "src/ui/charselect_redesign.ts",
    "src/ui/start_skin_picker_portraits.ts",
    "src/sim/types.ts",
    "src/sim/data.ts",
)
LOOKUP_TOKENS = (
    "setModularLookProvider", "npcLookFor", "npcModularKeyFor",
    "createCharacterVisual", "ALL_CLASSES", "player_hunter", "Hunter",
    "character-create", "charcreate", "offline-select",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(value: str) -> bool:
    p = PurePosixPath(value)
    return (not p.is_absolute() and ".." not in p.parts
            and len(p.parts) >= 2 and "\\" not in value
            and p.parts[0] in {"models", "textures", "vfx", "ui", "audio", "fonts", "env", "skybox"}
            and p.suffix.lower() in p21.VALID_SUFFIXES)


def exact_cc0_provenance(path: str, specs: dict) -> str | None:
    """Accept one exact raw provider source (duplicates from same source okay)."""
    rows = specs.get("/" + path, [])
    if not rows or not safe_path(path):
        return None
    srcs = {x["sourceDescription"] for x in rows}
    licenses = {x["provenance"] for x in rows}
    if len(srcs) != 1 or len(licenses) != 1:
        return None
    kind = next(iter(licenses))
    return kind if kind.startswith("CC0_") else None


def ancestors_no_symlinks(path: Path, root: Path) -> bool:
    if root.is_symlink():
        return False
    p = root
    for x in path.relative_to(root).parts:
        p = p / x
        if p.is_symlink():
            return False
    return True


def classification(path: str, specs: dict, provisional: dict) -> dict:
    orig, dst = ORIGINAL / "public" / path, STAGE / "public" / path
    licensed = exact_cc0_provenance(path, specs)
    if path in PROTECTED:
        state = "PROTECTED_OWNED_P8"
    elif not ancestors_no_symlinks(orig, ORIGINAL) or not ancestors_no_symlinks(dst, STAGE):
        state = "REVIEW_SYMLINK"
    elif dst.is_file() and p21.check_binary(dst, path):
        # Replace only if the exact stage bytes are a known P22 temporary file.
        if path in provisional and sha(dst) == provisional[path] and licensed and p21.check_binary(orig, path):
            state = "CC0_REPLACE_PROVISIONAL"
        else:
            state = "PRESERVE_EXISTING"
    elif dst.exists() or dst.is_symlink():
        state = "REVIEW_INVALID_STAGE_NO_OVERWRITE"
    elif licensed and p21.check_binary(orig, path):
        state = "CC0_RESTORE_MISSING"
    else:
        state = "REVIEW_SOURCE_OR_LICENSE"
    return {"path": path, "state": state, "providerEvidence": licensed,
            "originalExists": orig.is_file(), "stageExists": dst.is_file(),
            "sourceBytes": orig.stat().st_size if orig.is_file() and not orig.is_symlink() else None}


def selector_scan():
    """Static diagnostic only: original vs HIGHFLY selectors and NPC dispatch."""
    records = []
    for rel in SOURCE_CODE:
        a, b = ORIGINAL / rel, STAGE / rel
        row = {"file": rel, "originalExists": a.is_file(),
               "stageExists": b.is_file(), "sameContent": None,
               "stageTokens": [], "originalTokens": []}
        if a.is_file() and b.is_file():
            row["sameContent"] = sha(a) == sha(b)
        for key, fp in (("originalTokens", a), ("stageTokens", b)):
            if fp.is_file() and not fp.is_symlink() and fp.stat().st_size < 4_000_000:
                txt = fp.read_text(encoding="utf8", errors="replace")
                row[key] = [s for s in LOOKUP_TOKENS if s in txt]
        records.append(row)
    # Search references to how the app wires the appearance provider, not just definitions.
    appearance_call_sites = []
    for root in (STAGE / "src",):
        if not root.is_dir():
            continue
        for file in root.rglob("*.ts"):
            if (not file.is_file() or file.is_symlink() or file.stat().st_size > 2_000_000):
                continue
            txt = file.read_text(encoding="utf8", errors="replace")
            if any(t in txt for t in ("setModularLookProvider(", "npcLookFor(", "offline-select", "charcreate-panel")):
                appearance_call_sites.append(file.relative_to(STAGE).as_posix())
    return {"staticOnly": True, "codeFiles": records,
            "appearanceCallSites": appearance_call_sites[:120],
            "needsRuntimeValidation": True,
            "note": "Removing player classes may break the selector/player spawn; it does not prove NPC assets are present. Do not restore 9 playable classes to fix NPC visuals."}


def stage_copy(src: Path, dst: Path, replace_provisional: bool, backup: Path | None):
    """Safe copy, preverified source: no overwrite except backed-up known P22 placeholder."""
    if not ancestors_no_symlinks(dst, STAGE):
        raise RuntimeError("P33_UNSAFE_TARGET_SYMLINK " + str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".p33-", suffix=".tmp",
                                         dir=dst.parent, delete=False) as f:
            temp = Path(f.name)
            with src.open("rb") as origin:
                shutil.copyfileobj(origin, f)
        if sha(temp) != sha(src):
            raise RuntimeError("P33_COPY_HASH_MISMATCH")
        if replace_provisional:
            if backup is None or not dst.is_file() or dst.is_symlink() or backup.exists():
                raise RuntimeError("P33_BACKUP_TARGET_INVALID")
            backup.parent.mkdir(parents=True, exist_ok=True)
            # A hard link retains exactly the old bytes after atomic replacement.
            os.link(dst, backup)
            os.replace(temp, dst)
            temp = None
        else:
            os.link(temp, dst)  # O_EXCL equivalent: fails if target exists
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def execute(apply: bool = False):
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    if not P30.is_file():
        raise RuntimeError("P33_P30_REPORT_MISSING_RUN_P30_FIRST")
    credits = p21.credits_state(ORIGINAL)
    specs = p21.build_spec_index(ORIGINAL, credits)
    provisional = {p.lstrip("/"): hashval for p, hashval in p23.p22_provisional_source().items()}
    paths = sorted({p.relative_to(ORIGINAL / "public").as_posix()
                    for p in (ORIGINAL / "public").rglob("*")
                    if p.is_file() and not p.is_symlink() and p21.safe_asset_path(
                        "/" + p.relative_to(ORIGINAL / "public").as_posix())})
    rows = [classification(path, specs, provisional) for path in paths]
    counts = dict(Counter(x["state"] for x in rows))
    picks = [x for x in rows if x["state"] in {"CC0_RESTORE_MISSING", "CC0_REPLACE_PROVISIONAL"}]
    pre_required = sum(x["sourceBytes"] for x in picks)
    if apply and pre_required + 128 * 1024 * 1024 > shutil.disk_usage(STAGE).free:
        raise RuntimeError("P33_INSUFFICIENT_DISK_SPACE_FOR_CC0_BATCH")
    done = []
    if apply:
        for row in picks:
            path = row["path"]
            origin = ORIGINAL / "public" / path
            target = STAGE / "public" / path
            backup = OUT / "backups-p22" / path
            # Repeat authorization, stage state and hash checks at copy time.
            if classification(path, specs, provisional)["state"] != row["state"]:
                raise RuntimeError("P33_SOURCE_OR_STAGE_CHANGED_ABORT")
            original_hash = sha(origin)
            stage_copy(origin, target, row["state"] == "CC0_REPLACE_PROVISIONAL", backup)
            if not p21.check_binary(target, path) or sha(target) != original_hash:
                raise RuntimeError("P33_POSTCOPY_MISMATCH " + path)
            done.append({"path": "/" + path, "state": row["state"], "sha256": original_hash})
    after = [classification(path, specs, provisional) for path in paths] if apply else rows
    after_by_path = {x["path"]: x for x in after}
    diagnostics = selector_scan()
    actors = [{**after_by_path.get(k, {"path":k,"state":"NOT_IN_ENUMERATED_CC0_TYPES"}),
               "runtimeModel": "/" + k} for k in ACTORS]
    status = {
        "phase": "HIGHFLY_P33_WORLD_CC0_REUSE_AND_HUNTER_DIAGNOSTIC",
        "mode": "APPLY" if apply else "DRY_RUN",
        "originalPin": p9.SHA,
        "originalPathsScanned": len(paths),
        "readyToRestoreOrReplaceProvisional": len(picks),
        "candidateBytes": pre_required,
        "before": counts, "after": dict(Counter(x["state"] for x in after)),
        "installed": len(done), "actorStatus": actors,
        "playerAndNpcSourceDiagnostics": diagnostics,
        "gameplayChanged": False, "sourceCodeChanged": False,
        "browserVerified": False, "allNpcVisibleVerified": False,
        "worldFullyRestored": False,
        "limitations": [
            "CC0 candidates require exact source-to-output spec and a credited third-party provider; artist-authored modifications may need independent review.",
            "Project-only and unknown files remain uninstalled; modular NPC assembly will not work if warrior_modular.glb is missing.",
            "NPC appearance runtime wiring and Hunter-only selector need browser testing and targeted source fix.",
            "This batch does not rebuild dist or deploy Pages. Run an independent private build and inspect browser network after.",
        ], "timestampUtc": datetime.now(timezone.utc).isoformat()
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P33_WORLD_SUMMARY.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    with (OUT / "P33_ALL_CC0_DECISIONS.csv").open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["path", "state"])
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "P33_RESTORED_SHA256.json").write_text(json.dumps(done, indent=2) + "\n", encoding="utf8")
    print("[HIGHFLY] P33 WORLD: " + json.dumps({
        "mode": status["mode"], "paths": len(paths), "restorable": len(picks),
        "restorableGiB": round(pre_required/1024**3, 3),
        "installed": len(done), "before": counts, "after": status["after"],
        "gameplayChanged": False, "browserVerified": False
    }, ensure_ascii=False), flush=True)
    print("[HIGHFLY] P33 ACTORS: " + json.dumps(
        {x["runtimeModel"]: x["state"] for x in actors}, ensure_ascii=False), flush=True)
    print("[HIGHFLY] P33 SELECTOR: " + json.dumps({
        "stageCodeDifferent": [x["file"] for x in diagnostics["codeFiles"] if x["sameContent"] is False],
        "stageMissing": [x["file"] for x in diagnostics["codeFiles"] if not x["stageExists"]],
        "callSites": diagnostics["appearanceCallSites"],
        "runtimeVerified": False
    }, ensure_ascii=False), flush=True)
    print("[HIGHFLY] P33 REPORT: " + str(OUT / "P33_WORLD_SUMMARY.json"))
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Restore exact-spec CC0 assets; replace only backed-up identical P22 placeholders")
    args = parser.parse_args()
    execute(apply=args.apply)


if __name__ == "__main__":
    main()
