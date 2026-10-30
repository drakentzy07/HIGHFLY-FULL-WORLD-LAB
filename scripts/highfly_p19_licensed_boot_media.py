#!/usr/bin/env python3
"""HIGHFLY P19: strictly licensed critical boot media recovery.

Recover only exact Quaternius foliage models from a pinned MIT mapping spec,
the 16 explicitly Kenney-credited sprites used in vfx.ts, and three.js MIT
water normal textures, from the pinned private reference checkout. Never copy
project-only art, generated props, or arbitrary original game media.
Writes only to the ignored HIGHFLY stage and a private report; no deployment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12

REF = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
OUT = ROOT / ".workspace/reports/highfly-p19"
SPEC = "scripts/assets/specs/foliage.json"
SPRITES = (
    "light_01", "light_02", "flare_01", "spark_04", "spark_06",
    "star_07", "magic_01", "magic_04", "twirl_01", "flame_03",
    "fire_01", "smoke_05", "trace_05", "slash_02", "dirt_02", "circle_05",
)
WATER_NORMALS = ("waternormals.jpg", "Water_1_M_Normal.jpg", "Water_2_M_Normal.jpg")
FOLIAGE_CREDIT = "Stylized Nature MegaKit (trees, rocks, bushes, mushrooms, grass)"
PARTICLE_CREDIT = "Particle Pack (VFX sprites)"
MAX_BYTES = 90_000_000


def is_path_safe(path: str, kind: str) -> bool:
    p = PurePosixPath(path)
    if (p.is_absolute() or ".." in p.parts or "\\" in path or
            len(p.parts) != 3 or p.parts[0] not in ("models", "textures", "vfx")):
        return False
    if kind == "glb":
        return p.parts[0:2] == ("models", "foliage") and p.suffix == ".glb"
    if kind == "sprite":
        return p.parts[0] == "vfx" and p.parts[1] == "" and p.suffix == ".png"
    if kind == "water":
        return p.parts[:2] == ("textures", "water") and p.name in WATER_NORMALS
    return False


def png_ok(file: Path) -> bool:
    return file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def jpg_ok(file: Path) -> bool:
    with file.open("rb") as f:
        return f.read(3) == b"\xff\xd8\xff"


def credit_present(credits: str, needle: str, license_tag: str) -> bool:
    for line in credits.splitlines():
        if line.startswith("|") and needle in line and f"| {license_tag} |" in line and (
                "| Yes |" in line or "| Yes, attribution required |" in line):
            return True
    return False


def exact_spec_foliage(original: Path) -> list[str]:
    file = original / SPEC
    if not file.is_file() or file.is_symlink() or file.stat().st_size > 2_000_000:
        raise RuntimeError("P19_PINNED_FOLIAGE_SPEC_MISSING")
    data = json.loads(file.read_text(encoding="utf8"))
    if not isinstance(data.get("items"), list):
        raise RuntimeError("P19_FOLIAGE_SPEC_INVALID")
    out = []
    for item in data["items"]:
        src = str(item.get("src", ""))
        dest = str(item.get("out", ""))
        if not src.startswith("tmp/asset_src/quaternius_nature/extracted/glTF/"):
            raise RuntimeError("P19_NON_QUATERNIUS_FOLIAGE_SOURCE: " + src)
        p = PurePosixPath(dest)
        if p.parts[:2] != ("models", "foliage") or p.suffix != ".glb" or (
                len(p.parts) != 3 or ".." in p.parts or "\\" in dest):
            raise RuntimeError("P19_FOLIAGE_DESTINATION_UNSAFE: " + dest)
        if dest in out:
            raise RuntimeError("P19_FOLIAGE_DESTINATION_DUPLICATED: " + dest)
        out.append(dest)
    return out


def plan(original: Path, stage: Path) -> dict:
    credits_path = original / "CREDITS.md"
    if not credits_path.is_file() or credits_path.is_symlink():
        raise RuntimeError("P19_PINNED_CREDITS_UNAVAILABLE")
    credits = credits_path.read_text(encoding="utf8")
    # Validate exact "CC0 Yes" declarations; avoid copy if source provenance changes.
    if not credit_present(credits, FOLIAGE_CREDIT, "CC0 1.0"):
        raise RuntimeError("P19_FOLIAGE_CC0_CREDIT_UNVERIFIED")
    if not credit_present(credits, PARTICLE_CREDIT, "CC0 1.0"):
        raise RuntimeError("P19_PARTICLE_CC0_CREDIT_UNVERIFIED")
    if not credit_present(credits, "Water normal maps", "MIT"):
        raise RuntimeError("P19_WATER_MIT_CREDIT_UNVERIFIED")
    vfx_text = (original / "src/render/vfx.ts").read_text(encoding="utf8")
    if "Sprite atlas: 16 cherry-picked Kenney sprites" not in vfx_text:
        raise RuntimeError("P19_VFX_SOURCE_CREDIT_UNVERIFIED")
    import re
    match = re.search(r"const SPRITE_FILES\s*=\s*\[([^]]+)\]\s*as const;", vfx_text, re.S)
    if not match or tuple(re.findall(r"'([^']+)'", match.group(1))) != SPRITES:
        raise RuntimeError("P19_SPRITE_WHITELIST_MISMATCH")
    requests = (
        [(x, "glb", "Quaternius Stylized Nature MegaKit", "CC0 1.0")
         for x in exact_spec_foliage(original)] +
        [(f"vfx/{x}.png", "sprite", "Kenney Particle Pack", "CC0 1.0")
         for x in SPRITES] +
        [(f"textures/water/{x}", "water", "three.js r165 examples",
          "MIT attribution required") for x in WATER_NORMALS]
    )
    results = []
    seen = set()
    for rel, kind, origin, license_tag in requests:
        if rel in seen or not (
                # The sprite root is vfx/name.png, two path components.
                (kind == "sprite" and len(PurePosixPath(rel).parts) == 2
                 and PurePosixPath(rel).parts[0] == "vfx"
                 and PurePosixPath(rel).suffix == ".png") or
                (kind != "sprite" and is_path_safe(rel, kind))):
            raise RuntimeError("P19_UNSAFE_SOURCE_WHITELIST: " + rel)
        seen.add(rel)
        source = original / "public" / rel
        dest = stage / "public" / rel
        row = {"path": rel, "kind": kind, "origin": origin,
               "license": license_tag}
        if dest.is_symlink() or dest.is_dir():
            raise RuntimeError("P19_UNSAFE_DESTINATION: " + rel)
        if dest.is_file():
            row["status"] = "ALREADY_PRESENT"
        elif not source.is_file() or source.is_symlink():
            row["status"] = "SOURCE_MISSING"
        elif source.stat().st_size > MAX_BYTES or source.stat().st_size < 8:
            row["status"] = "SOURCE_SIZE_UNSAFE"
        elif kind == "glb" and not p12.glb_valid(source):
            row["status"] = "SOURCE_BAD_GLB"
        elif kind == "sprite" and not png_ok(source):
            row["status"] = "SOURCE_BAD_PNG"
        elif kind == "water" and not jpg_ok(source):
            row["status"] = "SOURCE_BAD_JPG"
        else:
            row["status"] = "VERIFIED_READY"
            row["sha256"] = p12.digest(source)
            row["bytes"] = source.stat().st_size
        results.append(row)
    return {"items": results, "ready": [r for r in results if r["status"] == "VERIFIED_READY"]}


def install(original: Path, stage: Path, rows: list[dict]) -> list[dict]:
    # All inputs prevalidated; copy to temporary names inside the target folder
    # before rename so a partial file can never be served by Vite.
    copied = []
    for row in rows:
        src = original / "public" / row["path"]
        dest = stage / "public" / row["path"]
        if dest.exists() or dest.is_symlink() or not src.is_file() or src.is_symlink():
            raise RuntimeError("P19_SOURCE_OR_DESTINATION_CHANGED: " + row["path"])
        if p12.digest(src) != row["sha256"]:
            raise RuntimeError("P19_SOURCE_DIGEST_CHANGED: " + row["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".highfly-p19-", dir=dest.parent, delete=False
            ) as tmp:
                temp_file = Path(tmp.name)
                with src.open("rb") as reader:
                    shutil.copyfileobj(reader, tmp)
            if p12.digest(temp_file) != row["sha256"]:
                raise RuntimeError("P19_TEMP_COPY_SHA256_MISMATCH: " + row["path"])
            if dest.exists() or dest.is_symlink():
                raise RuntimeError("P19_DESTINATION_RACE: " + row["path"])
            os.replace(temp_file, dest)
            copied.append({"path": row["path"], "sha256": row["sha256"],
                           "license": row["license"], "origin": row["origin"]})
        finally:
            if temp_file is not None:
                temp_file.unlink(missing_ok=True)
    return copied


def execute(apply: bool, build: bool) -> dict:
    p9.preflight(REF, STAGE, p9.REPORT)
    state = plan(REF, STAGE)
    copied = install(REF, STAGE, state["ready"]) if apply else []
    result = {
        "phase": "P19_LICENSED_BOOT_MEDIA_RECOVERY",
        "sourceCommit": p9.SHA, "mode": "APPLY" if apply else "DRY_RUN",
        "items": state["items"], "installed": copied,
        "verifiedReadyBefore": len(state["ready"]),
        "sourceMediaLicense": "Quaternius CC0; Kenney CC0; three.js MIT",
        "nonAllowlistedOriginalMediaCopied": False,
        "projectOnlyMediaCopied": False,
        "originalSimModified": False, "gameplayVerified": False,
        "publicReleaseApproved": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
    }
    if apply and build:
        result["buildExitCode"] = p9.smoke()["exitCode"]
    OUT.mkdir(parents=True, exist_ok=True)
    report = OUT / "P19_LICENSED_BOOT_MEDIA.json"
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    from collections import Counter
    summary = Counter(x["status"] for x in state["items"])
    print("[HIGHFLY] P19 " + result["mode"] + ": " + json.dumps({
        "statusesBefore": dict(summary), "installed": len(copied),
        "buildExitCode": result.get("buildExitCode"), "playableVerified": False
    }, ensure_ascii=False))
    print("[HIGHFLY] P19 REPORT: " + str(report))
    print("[HIGHFLY] NO PROJECT-ONLY MEDIA. NO PUBLIC DEPLOY.")
    if result.get("buildExitCode") not in (None, 0):
        raise SystemExit("P19_BUILD_FAILED_REVIEW_P9_LOG")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    execute(args.apply, not args.no_build)


if __name__ == "__main__":
    main()
