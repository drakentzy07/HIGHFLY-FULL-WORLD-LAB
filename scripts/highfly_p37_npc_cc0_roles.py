#!/usr/bin/env python3
"""P37: give HIGHFLY NPCs diverse, independently licensed KayKit CC0 bodies.

Private-stage-only Vite manifest patch. Does not restore nine playable classes,
change quests/vendors/saves, or copy original unlicensed modular meshes.
Strips missing optional attach GLBs and extra anim donors from NPC body defs;
uses the 6 existing P33-approved CC0 player model GLBs, while retaining the
existing P36 last-resort visibility fallback. Safe dry run, backups, hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9

STAGE = p9.STAGE
ORIGINAL = p9.ORIGINAL
OUT = ROOT / ".workspace/reports/highfly-p37-npc-role-rigs"
SOURCE = "src/render/characters/manifest.ts"
INDEX = "src/render/characters/index.ts"
MARK = "HIGHFLY_P37_NPC_CC0_ROLE_RIGS"
DEFS_ANCHOR = "const MOB_KEYS: Record<string, string> = {"
NPC_ANCHOR = "  // npcs — Brother Aldric recurs in every hub under suffixed ids"
MODEL_NAMES = ("knight", "mage", "rogue", "barbarian", "paladin", "druid")

# All six runtime model paths were recovered and checked by P33 from KayKit CC0.
# These role visuals deliberately avoid NOT-YET-RESTORED hit-variety donors,
# weapon/gear attaches and skin overlays. GLBs retain native embedded clips.
DEFS = """
// HIGHFLY_P37_NPC_CC0_ROLE_RIGS — temporary native KayKit CC0 body catalog.
// No nine player classes and no ClaudeCraft-owned modular GLB are required.
// One character's sim/templateId/quest/vendor remains the same in every role.
const HIGHFLY_P37_NPC_BASES = [
  ['knight', 'npc_knight', 'models/chars/players/knight.glb'],
  ['mage', 'npc_mage', 'models/chars/players/mage.glb'],
  ['rogue', 'npc_villager', 'models/chars/players/rogue.glb'],
  ['barbarian', 'npc_smith', 'models/chars/players/barbarian.glb'],
  ['paladin', 'npc_reliquary_keeper', 'models/chars/players/paladin.glb'],
  ['druid', 'npc_edda_reedhand', 'models/chars/players/druid.glb'],
] as const;
for (const [role, sourceKey, modelPath] of HIGHFLY_P37_NPC_BASES) {
  VISUALS['highfly_npc_' + role] = {
    ...VISUALS[sourceKey],
    url: modelPath,
    // A role's body must not vanish because a donor or held-item GLB is absent.
    animUrls: [],
    attach: [],
    // Preserve the embedded model look; no unauthorized modular pieces.
    modular: false,
    tint: 'entity',
    tintStrength: 0.13,
  };
}

// The tutorial roles were authored in npc_looks.ts; map them onto the
// nearest independently usable CC0 body until a legal modular library exists.
const HIGHFLY_P37_TUTORIAL_ROLES: Readonly<Record<string, string>> = {
  wayfarer_bryn: 'rogue',
  instructor_maren: 'knight',
  quartermaster_finch: 'rogue',
  bursar_wick: 'mage',
  ferryman_odo: 'druid',
  warden_tam: 'rogue',
  overseer_pell: 'barbarian',
  drillmaster_rook: 'knight',
  tidewarden_nel: 'druid',
};
"""

DISPATCH = """
  // HIGHFLY_P37_NPC_CC0_ROLE_RIGS: NPCs keep authored RPG identities.
  // Only the visual key changes; player and mob dispatch above are untouched.
  const tutorialRole = HIGHFLY_P37_TUTORIAL_ROLES[e.templateId];
  if (tutorialRole) return 'highfly_npc_' + tutorialRole;
  if (e.templateId.startsWith('brother_aldric')) return 'highfly_npc_mage';
  const npcBaseKey = NPC_KEYS[e.templateId] ?? 'npc_villager';
  if (npcBaseKey === 'npc_knight') return 'highfly_npc_knight';
  if (npcBaseKey === 'npc_reliquary_keeper') return 'highfly_npc_paladin';
  if (npcBaseKey === 'npc_mage' ||
      npcBaseKey === 'npc_aldric' ||
      npcBaseKey === 'npc_chronicler' ||
      npcBaseKey === 'npc_villager_robed') return 'highfly_npc_mage';
  if (npcBaseKey === 'npc_smith') return 'highfly_npc_barbarian';
  if (npcBaseKey === 'npc_edda_reedhand') return 'highfly_npc_druid';
  return 'highfly_npc_rogue';
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_manifest(source: str) -> str:
    if MARK in source:
        raise RuntimeError("P37_ALREADY_APPLIED")
    if source.count(DEFS_ANCHOR) != 1 or source.count(NPC_ANCHOR) != 1:
        raise RuntimeError("P37_MANIFEST_ANCHOR_DRIFT")
    # Important: write role defs ABOVE MOB_KEYS and NPC_KEYS, before manifestUrls()
    # is called by the asset loader. Definition order is JS module evaluation order.
    updated = source.replace(DEFS_ANCHOR, DEFS + "\n" + DEFS_ANCHOR, 1)
    updated = updated.replace(NPC_ANCHOR, DISPATCH + NPC_ANCHOR, 1)
    if updated.count(MARK) != 3:  # definitions comment + 2 dispatch comments
        # Allow future comment edits only if both insertion sites are present.
        if "HIGHFLY_P37_TUTORIAL_ROLES" not in updated or "HIGHFLY_P37_NPC_BASES" not in updated:
            raise RuntimeError("P37_PATCH_INCOMPLETE")
    return updated


def validate_stage() -> None:
    p9.preflight(ORIGINAL, STAGE, p9.REPORT)
    # P36 provides the fallback safety net if an unknown NPC or new role still
    # fails; never discard a known-working solution to fix appearances.
    index = STAGE / INDEX
    if not index.is_file() or index.is_symlink():
        raise RuntimeError("P37_INDEX_MISSING")
    txt = index.read_text(encoding="utf8")
    if "HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK" not in txt:
        raise RuntimeError("P37_REQUIRES_P36_VISIBILITY_SAFETY_NET")
    if "HIGHFLY_P34_FIXED_ACTOR_FALLBACK" not in txt:
        raise RuntimeError("P37_REQUIRES_P34_NO_MODULAR_PROVIDER")
    for model in MODEL_NAMES:
        f = STAGE / "public/models/chars/players" / (model + ".glb")
        if not f.is_file() or f.is_symlink():
            raise RuntimeError("P37_MISSING_APPROVED_KAYKIT_GLB " + str(f))
        with f.open("rb") as stream:
            if stream.read(4) != b"glTF":
                raise RuntimeError("P37_INVALID_GLB " + str(f))


def run(apply: bool = False) -> dict:
    validate_stage()
    src = STAGE / SOURCE
    if not src.is_file() or src.is_symlink():
        raise RuntimeError("P37_MANIFEST_MISSING")
    original = src.read_text(encoding="utf8")
    changed = patch_manifest(original)
    backup = OUT / "source-backups" / SOURCE
    if apply:
        if backup.exists() or backup.is_symlink():
            raise RuntimeError("P37_BACKUP_ALREADY_EXISTS")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, backup)
        if sha256(src) != sha256(backup):
            raise RuntimeError("P37_BACKUP_HASH_MISMATCH")
        if src.read_text(encoding="utf8") != original:
            raise RuntimeError("P37_SOURCE_CHANGED_ABORT")
        src.write_text(changed, encoding="utf8")
        if src.read_text(encoding="utf8") != changed:
            raise RuntimeError("P37_WRITE_VERIFICATION_FAILED")
    result = {
        "phase": "HIGHFLY_P37_NPC_CC0_ROLE_RIGS",
        "mode": "APPLY" if apply else "DRY_RUN",
        "sixCC0RigsVerified": list(MODEL_NAMES),
        "tutorialNPCsMapped": 9,
        "roleDefinitions": 6,
        "p36SafetyFallbackPreserved": True,
        "playerClassesChanged": False,
        "npcIDsPositionsQuestVendorChanged": False,
        "offlineSaveChanged": False,
        "trainingDummyChanged": False,
        "privateBuildStillRequired": True,
        "npcVisualVarietyBrowserVerified": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P37_CC0_NPC_ROLES.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    print("[HIGHFLY] P37 NPC ROLES: " + json.dumps(result, ensure_ascii=False))
    print("[HIGHFLY] P37 REPORT: " + str(OUT / "P37_CC0_NPC_ROLES.json"))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
