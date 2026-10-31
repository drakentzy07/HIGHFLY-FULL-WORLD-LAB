#!/usr/bin/env python3
"""P34: private-stage fixed-rig recovery when WOC modular library is unavailable.

Dry-run by default. Reversible source patch with exact anchors and backups.
Never copies restricted model art; never alters sim/NPC IDs/quests/classes.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
ORIGINAL=p9.ORIGINAL
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p34-fixed-actors"
INDEX="src/render/characters/index.ts"
MANIFEST="src/render/characters/manifest.ts"
MODULAR="models/chars/modular/warrior_modular.glb"
ALDRIC="models/chars/players/mage_classic.glb"
MARK="HIGHFLY_P34_FIXED_ACTOR_FALLBACK"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def replace_one(text,old,new,label):
    n=text.count(old)
    if n!=1:raise RuntimeError(f"P34_ANCHOR_CHANGED {label}: {n}")
    return text.replace(old,new,1)

def prepare(index,manifest,missing_modular,missing_aldric):
    """Source transformation; no on-disk mutation. Explicit precondition tests."""
    edits={}
    if missing_modular:
        edits[INDEX]=replace_one(
            index,"  modularLookProvider = fn;",
            "  // "+MARK+": unavailable authored modular model. Use fixed-role rigs.\n"
            "  modularLookProvider = null;",
            "setModularLookProvider")
        edits[MANIFEST]=replace_one(
            manifest,
            "  for (const def of Object.values(VISUALS)) {\n"
            "    if (def.lazyPreload) continue; // fetched on demand, not at boot",
            "  for (const def of Object.values(VISUALS)) {\n"
            "    // "+MARK+": do not preload an unavailable modular part library.\n"
            "    if (def.modular) continue;\n"
            "    if (def.lazyPreload) continue; // fetched on demand, not at boot",
            "manifestUrls")
    if missing_aldric:
        if not missing_modular:
            raise RuntimeError("P34_ALDRIC_REQUIRES_MODULAR_FALLBACK_CONTEXT")
        s=edits[MANIFEST]
        s=replace_one(
            s,"  if (e.templateId.startsWith('brother_aldric')) return 'npc_aldric';",
            "  // "+MARK+": use verified CC0 mage until custom Aldric model is legal.\n"
            "  if (e.templateId.startsWith('brother_aldric')) return 'npc_mage';",
            "Aldric visualKeyFor")
        s=replace_one(
            s,"    if (def.modular) continue;",
            "    if (def.modular) continue;\n"
            "    // "+MARK+": no missing Aldric-only rig at preload.\n"
            "    if (def.url === 'models/chars/players/mage_classic.glb') continue;",
            "Aldric preload")
        edits[MANIFEST]=s
    return edits

def run(apply=False):
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    missing_modular=not(STAGE/"public"/MODULAR).is_file()
    missing_aldric=not(STAGE/"public"/ALDRIC).is_file()
    if missing_modular:
        for model in ("knight","mage","rogue","barbarian","paladin","druid"):
            path=STAGE/"public/models/chars/players"/(model+".glb")
            if not path.is_file() or path.is_symlink():
                raise RuntimeError("P34_FIXED_RIG_MISSING "+str(path))
    inputs={}
    for rel in (INDEX,MANIFEST):
        path=STAGE/rel
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("P34_STAGE_SOURCE_MISSING "+rel)
        inputs[rel]=path.read_text(encoding="utf8")
    if any(MARK in x for x in inputs.values()):
        raise RuntimeError("P34_ALREADY_APPLIED_CHECK_REPORT")
    changes=prepare(inputs[INDEX],inputs[MANIFEST],missing_modular,missing_aldric)
    if apply:
        for rel in changes:
            backup=OUT/"source-backups"/rel
            if backup.exists() or backup.is_symlink():
                raise RuntimeError("P34_BACKUP_ALREADY_EXISTS "+str(backup))
        for rel in changes:
            source=STAGE/rel
            backup=OUT/"source-backups"/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,backup)
            if digest(source)!=digest(backup):
                raise RuntimeError("P34_BACKUP_HASH_MISMATCH")
        for rel,text in changes.items():
            path=STAGE/rel
            if path.read_text(encoding="utf8")!=inputs[rel]:
                raise RuntimeError("P34_SOURCE_CHANGED_ABORT")
            path.write_text(text,encoding="utf8")
    OUT.mkdir(parents=True,exist_ok=True)
    result={
        "mode":"APPLY" if apply else "DRY_RUN",
        "modularMissing":missing_modular,
        "aldricClassicMissing":missing_aldric,
        "plannedFiles":list(changes),
        "patchedFiles":list(changes) if apply else [],
        "simChanged":False,
        "originalSourceChanged":False,
        "classesRestored":False,
        "npcOriginalLooksFullyRestored":False,
        "browserVerified":False,
        "needsPrivateBuild":True,
        "timestampUtc":datetime.now(timezone.utc).isoformat()
    }
    (OUT/"P34_FIXED_ACTOR_FALLBACK.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("[HIGHFLY] P34 FIXED ACTOR FALLBACK: "+json.dumps(result,ensure_ascii=False))
    print("[HIGHFLY] P34 REPORT: "+str(OUT/"P34_FIXED_ACTOR_FALLBACK.json"))
    return result

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--apply",action="store_true")
    run(cli.parse_args().apply)

if __name__=="__main__":main()
