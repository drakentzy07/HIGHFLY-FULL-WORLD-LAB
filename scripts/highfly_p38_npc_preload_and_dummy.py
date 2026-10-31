#!/usr/bin/env python3
"""HIGHFLY P38 — fix verified NPC preloading + replace missing practice dummy art.

User P35 2026-10-31 conclusively shows highfly_npc_{rogue,druid,...} failing
with 'character asset not preloaded'; P36 then displays player_warrior.
The P20 log separately shows missing /models/creatures/training_dummy.glb.
This script adjusts ONLY the private staged game. It does not change gameplay,
NPC identities, player class selection, quests, loot, persistence or public Git.

* route six proven KayKit CC0 character GLBs to their real public/ URL rather
  than the original generated /media/ hashed manifest URL;
* explicitly load six NPC bodies before constructing the world renderer,
  not merely register them in the broad original failed preload sweep;
* replace the missing project-only 3D training dummy VISUAL with a real CC0
  KayKit Medieval Hexagon target prop ('hex_target.glb'), keeping dummy sim
  IDs / durability / damage metrics / quests untouched;
* preserve P36 fallback; guard anchors, backup all files, compare hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
ORIGINAL = p9.ORIGINAL
OUT = ROOT / ".workspace/reports/highfly-p38-npc-preload-and-dummy"
FILES = (
    "src/render/assets/media.ts",
    "src/render/characters/assets.ts",
    "src/main.ts",
    "src/render/characters/manifest.ts",
)
MARK = "HIGHFLY_P38_CC0_NPC_PRELOAD"
TARGET = "models/biome/hex_target.glb"
CHARACTERS = ("knight", "mage", "rogue", "barbarian", "paladin", "druid")

# Existing public/ assets restored P33 are not automatically under /media/...,
# since stage public/ is NOT the upstream original Vite generated media tree.
MEDIA_PATCH = """
// HIGHFLY_P38_CC0_NPC_PRELOAD: the verified KayKit bodies in HIGHFLY's
// private stage are public/ logical paths, not upstream /media/hash paths.
const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([
  'models/chars/players/knight.glb',
  'models/chars/players/mage.glb',
  'models/chars/players/rogue.glb',
  'models/chars/players/barbarian.glb',
  'models/chars/players/paladin.glb',
  'models/chars/players/druid.glb',
  'models/biome/hex_target.glb',
]);

"""

# prepareCharacterUrl is defined before resolvedGltf in ClaudeCraft assets.ts.
ASSETS_PATCH = """
// HIGHFLY_P38_CC0_NPC_PRELOAD: keep NPC bodies resident BEFORE the renderer
// can build world NPC views. Uses the same GLTF cache as resolvedGltf().
const HIGHFLY_P38_NPC_URLS = [
  'models/chars/players/knight.glb',
  'models/chars/players/mage.glb',
  'models/chars/players/rogue.glb',
  'models/chars/players/barbarian.glb',
  'models/chars/players/paladin.glb',
  'models/chars/players/druid.glb',
] as const;
export async function preloadHighflyNpcRoleBodies(): Promise<void> {
  const results = await Promise.allSettled(
    HIGHFLY_P38_NPC_URLS.map((url) => prepareCharacterUrl(url)),
  );
  const failures = results
    .map((result, i) => ({ result, url: HIGHFLY_P38_NPC_URLS[i] }))
    .filter((x) => x.result.status === 'rejected');
  if (failures.length > 0) {
    console.warn(
      '[HIGHFLY P38] Some KayKit NPC bodies failed explicit GLTF preload:',
      failures.map((x) => x.url),
    );
  }
  console.info('[HIGHFLY P38] NPC role GLTFs resident',
    HIGHFLY_P38_NPC_URLS.length - failures.length,
    '/', HIGHFLY_P38_NPC_URLS.length);
}

"""

MAIN_PRELOAD = """  // HIGHFLY_P38_CC0_NPC_PRELOAD: resolve approved role bodies before NPC
  // creation; P36 remains a safe fallback only for genuine loading failures.
  await preloadHighflyNpcRoleBodies();
"""

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError("P38_SOURCE_ANCHOR_DRIFT " + label + " count=" + str(count))
    return text.replace(old, new, 1)


def patch_sources(sources: dict[str, str]) -> dict[str, str]:
    if any(MARK in v for v in sources.values()):
        raise RuntimeError("P38_ALREADY_APPLIED")
    media = sources[FILES[0]]
    media = replace_once(media, "export function assetUrl(url: string): string {",
                         MEDIA_PATCH + "export function assetUrl(url: string): string {",
                         "media-header")
    media = replace_once(media, "  const logical = logicalPath(url);\n  if (import.meta.env.DEV)",
                         "  const logical = logicalPath(url);\n"
                         "  if (HIGHFLY_P38_DIRECT_CC0_MEDIA.has(logical)) return '/' + logical;\n"
                         "  if (import.meta.env.DEV)",
                         "media-direct-route")
    assets = sources[FILES[1]]
    assets = replace_once(assets, "function resolvedGltf(url: string): GLTF {",
                          ASSETS_PATCH + "function resolvedGltf(url: string): GLTF {",
                          "character-cache-before-resolvedGltf")
    main = sources[FILES[2]]
    main = replace_once(main,
                        "  charactersReady,\n  ensureCharacterUrl,",
                        "  charactersReady,\n  preloadHighflyNpcRoleBodies,\n  ensureCharacterUrl,",
                        "main-character-import")
    main = replace_once(main,
                        "  loadPhaseEnd('assets-ready');\n  const spectateBadge",
                        "  loadPhaseEnd('assets-ready');\n"
                        + MAIN_PRELOAD + "  const spectateBadge",
                        "main-world-entry")
    manifest = sources[FILES[3]]
    manifest = replace_once(manifest,
                            "    url: \`\${CREATURES}/training_dummy.glb\`,",
                            "    // HIGHFLY_P38_CC0_NPC_PRELOAD: exact-source CC0 "
                            "KayKit Medieval Hexagon target prop.\n"
                            "    // No owned ClaudeCraft Tripo training_dummy GLB is shipped.\n"
                            "    url: 'models/biome/hex_target.glb',",
                            "training-dummy-visual")
    if "HIGHFLY_P37_NPC_BASES" not in manifest or "HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK" not in sources[FILES[1]].replace("IGNORE", "") and False:
        # P36 lives in src/render/characters/index.ts, verified in preflight.
        if "HIGHFLY_P37_NPC_BASES" not in manifest:
            raise RuntimeError("P38_P37_ROLE_CATALOG_MISSING")
    return dict(zip(FILES, (media, assets, main, manifest)))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def original_target_licensed() -> None:
    spec = json.loads(
        (ORIGINAL / "scripts/assets/specs/gale_camp.json").read_text(encoding="utf8")
    )
    rows = [x for x in spec.get("items", []) if x.get("out") == TARGET]
    if len(rows) != 1 or "KayKit Medieval Hexagon Pack" not in rows[0].get("src", "") or not rows[0]["src"].endswith("/decoration/props/target.gltf"):
        raise RuntimeError("P38_TARGET_SOURCE_NOT_KAYKIT_HEXAGON")
    credits = (ORIGINAL / "CREDITS.md").read_text(encoding="utf8")
    if not any("| Medieval Hexagon Pack" in line
               and "| CC0 1.0 | Yes |" in line
               for line in credits.splitlines()):
        raise RuntimeError("P38_TARGET_CC0_CREDIT_NOT_VERIFIED")
    f = ORIGINAL / "public" / TARGET
    if not f.is_file() or f.is_symlink():
        raise RuntimeError("P38_CC0_TARGET_FILE_NOT_IN_ORIGINAL " + str(f))
    with f.open("rb") as data:
        header = data.read(12)
    if len(header) != 12:
        raise RuntimeError("P38_TARGET_GLB_TOO_SHORT")
    magic, version, length = struct.unpack("<4sII", header)
    if (magic, version, length) != (b"glTF", 2, f.stat().st_size):
        raise RuntimeError("P38_TARGET_INVALID_GLB")


def validate() -> dict[str, str]:
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    original_target_licensed()
    idx = STAGE / "src/render/characters/index.ts"
    if not idx.is_file() or "HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK" not in idx.read_text(encoding="utf8"):
        raise RuntimeError("P38_P36_VISIBLE_NPC_SAFETY_NET_MISSING")
    for name in CHARACTERS:
        f = STAGE / "public/models/chars/players" / (name + ".glb")
        if not f.is_file() or f.is_symlink():
            raise RuntimeError("P38_CC0_NPC_BODY_MISSING " + str(f))
        if f.open("rb").read(4) != b"glTF":
            raise RuntimeError("P38_CC0_NPC_BODY_INVALID_GLB " + str(f))
    src = {}
    for rel in FILES:
        f = STAGE / rel
        if not f.is_file() or f.is_symlink():
            raise RuntimeError("P38_STAGE_SOURCE_MISSING " + rel)
        src[rel] = f.read_text(encoding="utf8")
    return src


def run(apply: bool = False) -> dict:
    source = validate()
    changed = patch_sources(source)
    target_src = ORIGINAL / "public" / TARGET
    target_dst = STAGE / "public" / TARGET
    if target_dst.is_symlink():
        raise RuntimeError("P38_CC0_TARGET_STAGE_SYMLINK")
    if target_dst.is_file() and sha(target_src) != sha(target_dst):
        raise RuntimeError("P38_TARGET_ALREADY_EXISTS_DIFFERENT_BYTES")
    if target_dst.exists() and not target_dst.is_file():
        raise RuntimeError("P38_TARGET_STAGE_NOT_FILE")
    if apply:
        for rel in FILES:
            b = OUT / "source-backups" / rel
            if b.exists() or b.is_symlink():
                raise RuntimeError("P38_BACKUP_ALREADY_EXISTS " + rel)
        for rel in FILES:
            f = STAGE / rel
            b = OUT / "source-backups" / rel
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, b)
            if sha(f) != sha(b):
                raise RuntimeError("P38_BACKUP_HASH_FAILED " + rel)
        if not target_dst.exists():
            target_dst.parent.mkdir(parents=True, exist_ok=True)
            # Create-only. Do not overwrite the model if an editor adds it.
            with target_dst.open("xb") as f, target_src.open("rb") as src:
                shutil.copyfileobj(src, f)
            if sha(target_dst) != sha(target_src):
                raise RuntimeError("P38_CC0_TARGET_COPY_MISMATCH")
        for rel in FILES:
            f = STAGE / rel
            if f.read_text(encoding="utf8") != source[rel]:
                raise RuntimeError("P38_STAGE_MODIFIED_DURING_APPLY " + rel)
            f.write_text(changed[rel], encoding="utf8")
    status = {
        "phase": "P38_REAL_NPC_PRELOAD_KAYKIT_DUMMY",
        "mode": "APPLY" if apply else "DRY_RUN",
        "npcBodies": list(CHARACTERS),
        "npcRoleGLBsPreloadedBeforeWorld": "CODE_INSTALLED_NOT_BROWSER_VERIFIED",
        "dummyVisual": TARGET,
        "dummyVisualLicense": "KayKit Medieval Hexagon Pack CC0 1.0",
        "dummyAssetExists": target_dst.is_file(),
        "oldClaudeTripoDummyUsed": False,
        "p36SafetyFallbackPreserved": True,
        "npcGameplayChanged": False,
        "trainingDummyGameplayChanged": False,
        "playerClassesChanged": False,
        "offlineSaveChanged": False,
        "browserVerified": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P38_SUMMARY.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    print("[HIGHFLY] P38 FIX: " + json.dumps(status, ensure_ascii=False))
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
