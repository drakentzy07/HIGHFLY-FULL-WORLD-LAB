#!/usr/bin/env python3
"""HIGHFLY P29: post-world-entry actor, training dummy, skill VFX and legacy skin audit.

Read-only. The 48 distinct browser failures come from the user's 31 Oct 2026
13:56 JSON. No copyrighted media is copied, downloaded or synthesized.
Crucial: missing KTX2 variants do NOT prove a missing NPC/character GLB; and
an empty skill bar does NOT prove the ability simulation was removed.
"""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p21_runtime_asset_recovery as p21
import highfly_p12_world_kaykit_batch as p12

STAGE=p9.STAGE
SOURCE=p9.ORIGINAL
OUT=ROOT/".workspace/reports/highfly-p29"
VFX_GLBS=[
"/vfx/bone-reaper/soul.glb",
"/vfx/boulder/boulder.glb",
"/vfx/bone-reaper/scythe.glb",
"/vfx/forge-hammer/hammer.glb",
"/vfx/ice-age/pillars.glb",
"/vfx/orbital-lightning/orb.glb",
"/vfx/orbital-lightning/impact.glb",
"/vfx/pulsars/orb.glb",
"/vfx/tentacles/tentacle.glb",
]
VFX_KTX2=[
"/textures/vfx/contact/cut.ktx2",
"/textures/vfx/contact/crush.ktx2",
"/textures/vfx/contact/pierce.ktx2",
"/textures/vfx/production/warrior_crush.ktx2",
]
SKINS={}
for cls,styles in {
"knight":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
"paladin":["alt_a","alt_suit_prismatic","alt_suit_chrome"],
"ranger":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
"rogue":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
"mage":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
"barbarian":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
"druid":["alt_a","alt_b","alt_c","alt_suit_prismatic","alt_suit_chrome"],
}.items():
    SKINS[cls]=["/textures/skins/"+cls+"/"+style+".ktx2" for style in styles]

FAILURES=(
    VFX_GLBS+VFX_KTX2+[
        "/models/creatures/training_dummy.glb",
        "/textures/loading/duskmoor-eclipse.webp",
    ]+sum(SKINS.values(),[])
)
# All these are diagnostic candidates, not a proof of which actor is invisible.
ACTOR_PROBES={
  "npc_modular_warrior":"models/chars/modular/warrior_modular.glb",
  "npc_knight":"models/chars/knight.glb",
  "npc_mage":"models/chars/mage.glb",
  "npc_villager_rogue":"models/chars/rogue.glb",
  "npc_smith_barbarian":"models/chars/barbarian.glb",
  "npc_weapon_sword":"models/weapons/sword_1handed.glb",
  "npc_weapon_staff":"models/weapons/staff.glb",
}
SIM_PROBES={
 "npc_looks":"src/render/characters/npc_looks.ts",
 "npc_visual_dispatch":"src/render/characters/index.ts",
 "player_and_mob_visual_manifest":"src/render/characters/manifest.ts",
 "character_asset_loading":"src/render/characters/assets.ts",
 "npc_simulation":"src/sim/content/proving_shore.ts",
 "practice_dummy_simulation":"src/sim/content/practice_dummies.ts",
 "quest_tutorial_simulation":"src/sim/tutorial/dummy_drill.ts",
 "skill_source":"src/sim/content/classes.ts",
}
PROJECT_ONLY=[
"/models/creatures/training_dummy.glb",
*VFX_GLBS,
"/textures/loading/duskmoor-eclipse.webp",
]
# These exact upstream model groups are explicitly documented in CREDITS.md
# as project art and may not be treated as independently licensed CC0.
def binary_valid(path:Path)->bool:
    if not path.is_file() or path.is_symlink() or path.stat().st_size<12:
        return False
    suffix=path.suffix.lower()
    if suffix==".glb":
        return p21.check_binary(path,"/models/p29.glb")
    if suffix==".ktx2":
        return path.open("rb").read(12)==b"\xabKTX 20\xbb\r\n\x1a\n"
    if suffix==".webp":
        return p21.check_binary(path,"/textures/p29.webp")
    if suffix==".png":
        return p21.check_binary(path,"/textures/p29.png")
    return False

def classify(url:str)->str:
    if url in VFX_GLBS:return "BOSS_VFX_SPECIAL_GLBS"
    if url in VFX_KTX2:return "COMBAT_KTX2_TEXTURES"
    if url=="/models/creatures/training_dummy.glb":return "TRAINING_DUMMY_RIG"
    if url=="/textures/loading/duskmoor-eclipse.webp":return "LOADING_ART"
    if url.startswith("/textures/skins/"):return "OLD_CLASS_SKIN_VARIANT"
    return "UNKNOWN"

def action(url):
    role=classify(url)
    if role=="OLD_CLASS_SKIN_VARIANT":
        return "AUDIT_AND_DECOUPLE_LEGACY_CLASS_VARIANTS_FROM_UNIVERSAL_HUNTER; NO_BLIND_KTX2_COPY"
    if role=="TRAINING_DUMMY_RIG":
        return "REBUILD_OWNED_KAYKIT_ANIMATED_RIG_COMPATIBLE_WITH_RENDER_MANIFEST_CLIPS"
    if role=="BOSS_VFX_SPECIAL_GLBS":
        return "REIMPLEMENT_WITH_ORIGINAL_HIGHFLY_MESH_VFX_AND_REQUIRED_NAMED_NODE_CONTRACTS"
    if role=="COMBAT_KTX2_TEXTURES":
        return "CHECK_PNG_SOURCE_FALLBACK_AND_GENERATE_OWN_KTX2_ONLY_IF_ACTIVE_VFX_NEEDS_IT"
    return "CREATE_FIRST_PARTY_LOADING_IMAGE_NOT_COPY_PROJECT_ONLY_ART"

def inspect():
    p9.preflight(SOURCE,STAGE,p9.REPORT)
    if len(FAILURES)!=48 or len(set(FAILURES))!=48:
        raise RuntimeError("P29_EXPECTED_EXACT_48_UNIQUE_BROWSER_FAILURES")
    rows=[]
    for url in FAILURES:
        if not p21.safe_asset_path(url) and not url.endswith(".ktx2"):
            raise RuntimeError("P29_INVALID_URL "+url)
        rel=url.lstrip("/")
        stage=STAGE/"public"/rel
        dist=STAGE/"dist"/rel
        original=SOURCE/"public"/rel
        rows.append({
          "url":url,"category":classify(url),
          "stagePresent":stage.is_file(),"stageValid":binary_valid(stage),
          "builtPresent":dist.is_file(),"builtValid":binary_valid(dist),
          "upstreamPresent":original.is_file(),"upstreamBinaryValid":binary_valid(original),
          "redistribution":"PROJECT_SPECIFIC_OR_UNKNOWN_LICENSE_DO_NOT_COPY" if url in PROJECT_ONLY
                           else "REVIEW_SOURCE_LICENSE_AND_HUNTER_RELEVANCE",
          "nextAction":action(url),
        })
    actors=[]
    for role,raw in ACTOR_PROBES.items():
        stage=STAGE/"public"/raw
        original=SOURCE/"public"/raw
        actors.append({"role":role,"url":"/"+raw,
              "stagePresent":stage.is_file(),"stageValid":binary_valid(stage),
              "upstreamPresent":original.is_file(),
              "note":"Presence only; does not verify skinning, clips, spawn, visibility or camera."})
    systems=[]
    for system,rel in SIM_PROBES.items():
        src=STAGE/rel
        orig=SOURCE/rel
        systems.append({"system":system,"stageSourcePresent":src.is_file(),
                        "upstreamSourcePresent":orig.is_file(),
                        "note":"Source presence not proof of runtime wiring or active gameplay."})
    by_category=Counter(x["category"] for x in rows)
    missing_by_category=Counter(x["category"] for x in rows if not x["stageValid"])
    report={
      "phase":"HIGHFLY_P29_ACTORS_TRAINING_SKILLS_VFX_AUDIT",
      "mode":"READ_ONLY",
      "dateUtc":datetime.now(timezone.utc).isoformat(),
      "distinctBrowserFailures":len(rows),
      "categories":dict(by_category),
      "stillMissingInStage":dict(missing_by_category),
      "stageMissingCount":sum(not x["stageValid"] for x in rows),
      "originalMediaCopied":False,
      "gameCodeChanged":False,
      "currentPlayerVisibleVerified":False,
      "npcVisibleVerified":False,
      "trainingDummyAttackableVerified":False,
      "skillsPlayableVerified":False,
      "vfxRenderedVerified":False,
      "warning":"Network failures alone cannot prove absent actors, quests, skills or combat simulation. Log of screenshot started after initial preload.",
      "fileFailures":rows,"actorModels":actors,"sourceModules":systems,
      "recommendedOrder":[
          "Inspect NPC and player actor rig model residency/clip mapping, camera and render visibility",
          "Restore training dummy using owned KayKit animated model and existing dummy sim ID and visual clips",
          "Rebuild active combat VFX using own effects while preserving named-node animation contract",
          "Disconnect legacy class KTX2 alt variants from Hunter Universal; preserve only original licensed skin pipeline",
          "Iterative browser probe in Proving Shore, then world zones and combat to catch lazy-load assets",
      ]}
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"P29_WORLD_ENTRY_ACTORS_SKILLS_VFX_48.json"
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("[HIGHFLY] P29 AUDIT: "+json.dumps({
      "failures":48,"grouped":dict(by_category),
      "stageStillMissing":dict(missing_by_category),
      "actorModelsPresent":sum(x["stageValid"] for x in actors),
      "actorModelsChecked":len(actors),
      "sourceModulesInStage":sum(x["stageSourcePresent"] for x in systems),
      "sourceModulesExpected":len(systems),
      "npcVisibleVerified":False,"playerVisibleVerified":False,
      "skillsAndVfxVerified":False,
    },ensure_ascii=False))
    print("[HIGHFLY] P29 REPORT: "+str(path))
    return report

if __name__=="__main__":
    inspect()
