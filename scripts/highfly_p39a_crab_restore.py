#!/usr/bin/env python3
"""HIGHFLY P39A — recover original CC0 Quaternius crabs and preload their GLBs.

Exact source / copyright test:
  scripts/assets/specs/characters.json maps Quaternius CrabEnemy.glb to
  models/creatures/crabenemy.glb. Quaternius FAQ confirms CC0. Auxiliary
  anim GLBs are built from this rig by upstream MIT scripts. Do not extract
  a restricted character model or insert a geometric placeholder.
 
Preserve P38 and P36, all quests/loot/monster IDs, and the Hunter.
Dry run by default; --apply copies missing assets, backs up 3 TS files,
adds exact direct-public paths and explicit preload before world entry.
No public deploy, no generated files or private ZIP committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

ORIGINAL = p9.ORIGINAL
STAGE = p9.STAGE
OUT = ROOT / ".workspace/reports/highfly-p39a-crab-visual"
MODELS = (
    "models/creatures/crabenemy.glb",
    "models/creatures/crabenemy_hit_variety_anims.glb",
    "models/creatures/crab_ability_anims.glb",
)
SOURCES = (
    "src/render/assets/media.ts",
    "src/render/characters/assets.ts",
    "src/main.ts",
)
MARK = "HIGHFLY_P39A_CC0_CRAB_PRELOAD"


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_glb(path: Path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("P39A_MISSING_OR_SYMLINK_GLTF " + str(path))
    if path.stat().st_size < 20:
        raise RuntimeError("P39A_GLTF_TOO_SMALL " + str(path))
    with path.open("rb") as fp:
        magic, version, size = struct.unpack("<4sII", fp.read(12))
    if magic != b"glTF" or version != 2 or size != path.stat().st_size:
        raise RuntimeError("P39A_INVALID_GLTF " + str(path))


def exact_provenance() -> None:
    spec = json.loads((ORIGINAL / "scripts/assets/specs/characters.json").read_text(encoding="utf8"))
    rows = [i for i in spec.get("items", []) if i.get("out") == MODELS[0]]
    if len(rows) != 1 or rows[0].get("src") != "tmp/asset_src/quaternius_creatures/CrabEnemy.glb":
        raise RuntimeError("P39A_CRAB_NOT_VERIFIED_QUATERNIUS_SOURCE")
    # These are in the pinned original source under the MIT code license;
    # their rig pose samples derive from original Quaternius CC0 model.
    for generator in ("scripts/build_crab_anims.mjs",
                      "scripts/build_enemy_bite_hit_variety_anims.mjs"):
        if not (ORIGINAL / generator).is_file():
            raise RuntimeError("P39A_ANIM_GENERATOR_MISSING " + generator)
    for rel in MODELS:
        checked_glb(ORIGINAL / "public" / rel)
        target = STAGE / "public" / rel
        if target.is_symlink():
            raise RuntimeError("P39A_STAGE_SYMLINK " + rel)
        if target.exists():
            checked_glb(target)
            if hash_file(target) != hash_file(ORIGINAL / "public" / rel):
                raise RuntimeError("P39A_STAGE_DIFFERENT_MODEL_NO_OVERWRITE " + rel)


def patch_one(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        raise RuntimeError("P39A_ANCHOR_CHANGED " + label + " count=" + str(n))
    return src.replace(old, new, 1)


def patch_sources(source: dict[str, str]) -> dict[str, str]:
    if any(MARK in s for s in source.values()):
        raise RuntimeError("P39A_ALREADY_APPLIED")
    media = source[SOURCES[0]]
    media = patch_one(
        media,
        "  'models/biome/hex_target.glb',",
        "  'models/biome/hex_target.glb',\n"
        "  // " + MARK + ": verified Quaternius CC0 body and MIT-generated rig donors.\n"
        "  'models/creatures/crabenemy.glb',\n"
        "  'models/creatures/crabenemy_hit_variety_anims.glb',\n"
        "  'models/creatures/crab_ability_anims.glb',",
        "media:direct-public-cc0",
    )
    assets = source[SOURCES[1]]
    preloader = """
// HIGHFLY_P39A_CC0_CRAB_PRELOAD: complete crab rig + authored clip donors.
// Shares normal gltfByUrl cache with resolvedGltf(); this matters because
// shore_scuttler/mister_crabs (and other areas) all use mob_crab.
const HIGHFLY_P39A_CRAB_URLS = [
  'models/creatures/crabenemy.glb',
  'models/creatures/crabenemy_hit_variety_anims.glb',
  'models/creatures/crab_ability_anims.glb',
] as const;
export async function preloadHighflyCrabAssets(): Promise<void> {
  const responses = await Promise.allSettled(
    HIGHFLY_P39A_CRAB_URLS.map((url) => prepareCharacterUrl(url)),
  );
  const failed = responses.flatMap((result, i) =>
    result.status === 'rejected' ? [HIGHFLY_P39A_CRAB_URLS[i]] : [],
  );
  console.info('[HIGHFLY P39A] crab meshes + donor preloads',
    HIGHFLY_P39A_CRAB_URLS.length - failed.length, '/',
    HIGHFLY_P39A_CRAB_URLS.length);
  if (failed.length) console.warn('[HIGHFLY P39A] crab assets failed', failed);
}
"""
    assets = patch_one(
        assets,
        "export async function preloadHighflyNpcRoleBodies(): Promise<void> {",
        preloader + "\nexport async function preloadHighflyNpcRoleBodies(): Promise<void> {",
        "assets:before-npc-preloader",
    )
    main = source[SOURCES[2]]
    main = patch_one(
        main,
        "  preloadHighflyNpcRoleBodies,\n",
        "  preloadHighflyNpcRoleBodies,\n  preloadHighflyCrabAssets,\n",
        "main:assets-import",
    )
    main = patch_one(
        main,
        "  await preloadHighflyNpcRoleBodies();",
        "  await preloadHighflyNpcRoleBodies();\n"
        "  // " + MARK + ": preload visible tutorial enemies before renderer entry.\n"
        "  await preloadHighflyCrabAssets();",
        "main:before-world-entry",
    )
    return dict(zip(SOURCES, (media, assets, main)))


def no_ancestor_symlinks(path: Path, root: Path):
    if root.is_symlink():
        raise RuntimeError("P39A_STAGE_ROOT_IS_SYMLINK")
    path.relative_to(root)
    curr = root
    for piece in path.relative_to(root).parts:
        curr = curr / piece
        if curr.is_symlink():
            raise RuntimeError("P39A_STAGE_PATH_CONTAINS_SYMLINK " + str(curr))


def copy_create_only(original: Path, stage: Path):
    no_ancestor_symlinks(stage, STAGE)
    stage.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".highfly-p39a-", suffix=".tmp",
            dir=stage.parent, delete=False
        ) as out:
            tmp = Path(out.name)
            with original.open("rb") as src:
                shutil.copyfileobj(src, out)
        if hash_file(tmp) != hash_file(original):
            raise RuntimeError("P39A_COPY_HASH_MISMATCH")
        os.link(tmp, stage)  # no overwrite even with concurrent creation
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)


def run(apply=False):
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    original_manifest = (ORIGINAL / "src/render/characters/manifest.ts").read_text(encoding="utf8")
    staged_manifest = (STAGE / "src/render/characters/manifest.ts").read_text(encoding="utf8")
    mapping = "shore_scuttler: 'mob_crab'"
    if mapping not in original_manifest or mapping not in staged_manifest:
        raise RuntimeError("P39A_CRAB_TEMPLATE_MAPPING_CHANGED")
    if "mob_crab: {" not in staged_manifest or "crabenemy.glb" not in staged_manifest:
        raise RuntimeError("P39A_CRAB_VISUAL_MANIFEST_MISSING")
    exact_provenance()
    inputs = {}
    for rel in SOURCES:
        f = STAGE / rel
        if not f.is_file() or f.is_symlink():
            raise RuntimeError("P39A_STAGE_SOURCE_MISSING " + rel)
        inputs[rel] = f.read_text(encoding="utf8")
    changes = patch_sources(inputs)
    missing = [s for s in MODELS if not (STAGE / "public" / s).exists()]
    if apply:
        for rel in SOURCES:
            bak = OUT / "backups" / rel
            if bak.exists() or bak.is_symlink():
                raise RuntimeError("P39A_BACKUP_ALREADY_EXISTS " + rel)
        for rel in SOURCES:
            f = STAGE / rel
            bak = OUT / "backups" / rel
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, bak)
            if hash_file(f) != hash_file(bak):
                raise RuntimeError("P39A_BACKUP_FAILURE " + rel)
        for rel in missing:
            copy_create_only(ORIGINAL / "public" / rel, STAGE / "public" / rel)
        for rel in SOURCES:
            if (STAGE / rel).read_text(encoding="utf8") != inputs[rel]:
                raise RuntimeError("P39A_SOURCE_CHANGED_ABORT")
            (STAGE / rel).write_text(changes[rel], encoding="utf8")
    result = {
        "phase": "P39A_QUATERNIUS_CC0_CRAB_VISIBILITY",
        "mode": "APPLY" if apply else "DRY_RUN",
        "sourceProvenance": "Quaternius CrabEnemy -> original WOC GLB",
        "sourceLicenseBasis": "Quaternius pack CC0; donor code MIT (WOC source)",
        "originalModels": list(MODELS),
        "missingBefore": missing,
        "installed": list(missing) if apply else [],
        "rpgChanged": False, "lootChanged": False,
        "playerClassesChanged": False, "offlineSaveChanged": False,
        "npcFallbackPreserved": True, "browserVerified": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat()
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P39A_CRAB_REPORT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf8",
    )
    print("[HIGHFLY] P39A CRAB: " + json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--apply", action="store_true")
    args = cli.parse_args()
    run(apply=args.apply)
