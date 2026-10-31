#!/usr/bin/env python3
"""P36: conservative NPC-only visual fallback in the private staged game.
P35 may show native NPC visual constructor failures invisible to fetch probes.
Does not alter entity identity, quests, vendors, player classes, or saved data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p9_private_build_smoke as p9

STAGE=p9.STAGE
OUT=Path(__file__).resolve().parents[1]/".workspace/reports/highfly-p36-npc-fallback"
SOURCE="src/render/characters/index.ts"
MARK="HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK"
END_ANCHOR="    return null;\n  }\n}"
PATCH="""
    // HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK: NPC VISUAL ONLY.
    // Preserve sim identity, dialogue, vendor/quest data and player classes.
    if (e.kind === 'npc' && !formKey) {
      const roleRig =
        key === 'npc_knight' || key === 'npc_reliquary_keeper'
          ? 'player_paladin'
          : key === 'npc_mage' || key === 'npc_aldric' ||
              key === 'npc_villager_robed' || key === 'npc_chronicler'
            ? 'player_mage'
            : key === 'npc_smith'
              ? 'player_shaman'
              : 'player_rogue';
      const candidates = [roleRig, 'player_warrior'];
      for (const fallbackKey of candidates) {
        try {
          // Use a known CC0 body; avoid main/off-hand inventory attachments.
          const fallback = new CharacterVisual(
            fallbackKey, e.color, 0, null, null, null, null, opts,
          );
          fallback.budgetedWeaponLight = true;
          if (typeof window !== 'undefined') {
            const d = (window as unknown as {
              __highflyP35?: {
                record: (kind: string, data: Record<string, unknown>) => void;
              };
            }).__highflyP35;
            d?.record('npc_fixed_fallback_success', {
              id: e.id, templateId: e.templateId,
              originalVisualKey: key, fallbackKey,
            });
          }
          return fallback;
        } catch (backupError) {
          const reason = backupError instanceof Error
            ? backupError.message : String(backupError);
          logAssetMissOnce(
            fallbackKey + ':' + reason,
            'HIGHFLY NPC fixed fallback unavailable (' + fallbackKey + '):',
            backupError,
          );
        }
      }
    }
"""

def patched_source(text):
    if MARK in text:
        raise RuntimeError("P36_ALREADY_APPLIED")
    start=text.find("export function createCharacterVisual(")
    if start < 0:
        raise RuntimeError("P36_VISUAL_FACTORY_NOT_FOUND")
    tail=text[start:]
    if tail.count(END_ANCHOR)!=1:
        raise RuntimeError("P36_FACTORY_CATCH_ANCHOR_DRIFT")
    position=tail.find(END_ANCHOR)
    if "character visual unavailable, skipping view" not in tail[:position]:
        raise RuntimeError("P36_INCORRECT_CATCH")
    if "HIGHFLY_P35_ACTOR_UI" not in tail[:position]:
        raise RuntimeError("P36_REQUIRES_P35_SOURCE_INSTRUMENTATION")
    return text[:start]+tail[:position]+PATCH+tail[position:]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    path=STAGE/SOURCE
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("P36_SOURCE_MISSING")
    original=path.read_text(encoding="utf8")
    changed=patched_source(original)
    wanted=("knight","mage","rogue","barbarian","paladin")
    missing=[name for name in wanted
             if not (STAGE/"public/models/chars/players"/(name+".glb")).is_file()]
    if missing:
        raise RuntimeError("P36_REQUIRED_CC0_ACTOR_MISSING "+str(missing))
    if args.apply:
        backup=OUT/"backups"/SOURCE
        if backup.exists() or backup.is_symlink():
            raise RuntimeError("P36_BACKUP_ALREADY_EXISTS")
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,backup)
        if hashlib.sha256(backup.read_bytes()).digest()!=hashlib.sha256(path.read_bytes()).digest():
            raise RuntimeError("P36_BACKUP_MISMATCH")
        if path.read_text(encoding="utf8")!=original:
            raise RuntimeError("P36_SOURCE_CHANGED")
        path.write_text(changed,encoding="utf8")
    OUT.mkdir(parents=True,exist_ok=True)
    report={"phase":"HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK",
            "mode":"APPLY" if args.apply else "DRY_RUN",
            "source":SOURCE,"npcOnly":True,"rpgChanged":False,
            "nineClassesRestored":False,"saveSystemChanged":False,
            "npcVisibleBrowserVerified":False}
    (OUT/"P36_STATUS.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("[HIGHFLY] P36 NPC FIX: "+json.dumps(report))

if __name__=="__main__":
    main()
