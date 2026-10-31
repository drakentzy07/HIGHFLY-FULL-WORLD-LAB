#!/usr/bin/env python3
"""HIGHFLY P29: Hunter-only player, diverse NPCs, monsters, loot, dummy and VFX audit.

Read-only. The 48 distinct browser failures come from the user's 31 Oct 2026
13:56 JSON. No copyrighted media is copied, downloaded or synthesized.
Crucial: the single universal Hunter applies ONLY to the playable character.
NPCs retain their distinct ClaudeCraft identities, visual roles, gear and
animation; the many original rig names (knight/mage/rogue/barbarian) may also
be referenced by NPCs. NEVER erase them just because their names are class
names. A missing KTX2 variant does not prove its mesh or a skill is absent.
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
  # Verified against v0.44.7 src/render/characters/manifest.ts.
  # 'knight' / 'paladin' / 'mage' etc are NPC VISUAL RIGS; they do NOT
  # imply that HIGHFLY's playable Hunter must have those classes.
  "npc_modular_warrior":"models/chars/modular/warrior_modular.glb",
  "npc_knight":"models/chars/players/knight.glb",
  "npc_mage":"models/chars/players/mage.glb",
  "npc_villager_rogue":"models/chars/players/rogue.glb",
  "npc_smith_barbarian":"models/chars/players/barbarian.glb",
  "npc_reliquary_paladin":"models/chars/players/paladin.glb",
  "npc_herbalist_druid":"models/chars/players/druid.glb",
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
# Visual/gameplay contracts. None of these rows can be silently
# homogenized into a single NPC rig, a single humanoid mob or a static dummy.
# The Hunter Universal choice changes PLAYER classes, not world inhabitants.
VISUAL_POLICY={
 "player":{
   "target":"ONE_HUNTER_UNIVERSAL",
   "rule":"One persistent playable Hunter. Any learnable physical/magic skills; no player class lock.",
   "models":"OWNED_PLAYER_RIG_AND_APPEARANCE; inventory equipment and looks may change independently of class."
 },
 "npc":{
   "target":"PRESERVE_DIVERSE_ORIGINAL_NPC_ROLES",
   "rule":"Retain all NPC IDs, names, spawn locations, faction/shop/quest/dialogue behavior; never replace all NPCs with Hunter.",
   "models":"Choose distinct compatible human/villager/guard/merchant/blacksmith/elder rigs and outfits from KayKit Complete SOURCE V7.",
   "visualSources":["src/render/characters/npc_looks.ts","src/render/characters/manifest.ts"],
   "note":"Old knight/mage/rogue/barbarian GLB identifiers are also used as NPC bases, not proof of playable classes."
 },
 "creatures":{
   "target":"KEEP_EACH_SPECIES",
   "rule":"Preserve monster ID, AI, hitbox, attacks, zone spawns, drops and animation-role requirements.",
   "models":"Use corresponding CC0 Quaternius/other approved packs or KayKit Complete monsters, not generic human stand-ins."
 },
 "training":{
   "target":"KEEP_ATTACKABLE_PRACTICE_TARGETS",
   "rule":"Keep existing dummy IDs, quest triggers, health profiles, hit/cast metrics and no-aggro behavior.",
   "models":"Owned rigged dummy with required Idle/Walk/Run/Attack/Hit/Death clip contract or a reviewed manifest change.",
   "visualSources":["src/sim/content/practice_dummies.ts","src/render/characters/manifest.ts"]
 },
 "loot":{
   "target":"PRESERVE_DROP_EQUIPMENT_AND_INVENTORY",
   "rule":"Keep loot tables, amounts, stats, rarity, pickup, corpse looting and stack behavior.",
   "models":"Replace only visuals/icons from owned KayKit and other verified CC0 sources; item logic unchanged."
 },
 "skills":{
   "target":"UNIVERSAL_SKILL_COLLECTION_NOT_CLASS_TREE",
   "rule":"Ability behavior, cooldown, purchase/drop/quest/fusion and effects must be preserved/adapted for the Hunter.",
   "models":"Use own visual effects preserving per-skill runtime target sockets and animated named-node contracts."
 },
}
NPC_ROLE_BASE_RIGS={
  "guard":"models/chars/players/knight.glb",
  "mage_or_religious_npc":"models/chars/players/mage.glb",
  "villager":"models/chars/players/rogue.glb",
  "blacksmith":"models/chars/players/barbarian.glb",
  "reliquary_keeper":"models/chars/players/paladin.glb",
  "reedhand_healer":"models/chars/players/druid.glb",
  "modular_npc":"models/chars/modular/warrior_modular.glb",
}
# These paths are role-based illustrations of original manifest mappings,
# NOT a requirement to copy original binaries, or exact NPC appearance proof.
def source_usage(path:Path,terms:list[str])->dict:
    if not path.is_file() or path.is_symlink():
        return {"present":False,"termsFound":[],"termsMissing":terms}
    text=path.read_text(encoding="utf8",errors="replace")
    found=[term for term in terms if term in text]
    return {"present":True,"termsFound":found,
            "termsMissing":[term for term in terms if term not in found]}

def visual_contract_checks()->dict:
    characters=STAGE/"src/render/characters"
    manifest=source_usage(characters/"manifest.ts",[
        "npc_knight:", "npc_mage:", "npc_smith:", "npc_villager:",
        "mob_training_dummy:", "npc_modular_"
    ])
    looks=source_usage(characters/"npc_looks.ts",[
        "NPC_LOOKS", "npcModularKeyFor"
    ])
    dispatch=source_usage(characters/"index.ts",[
        "npcModularKeyFor", "createCharacterVisual"
    ])
    creature=source_usage(STAGE/"src/sim/content/practice_dummies.ts",[
        "HUB_TRAINING_DUMMY_ID", "FRIENDLY_PLAYER_DUMMY_ID"
    ])
    return {
        "visualManifestRoleMappings":manifest,
        "npcIndividuatedLooks":looks,
        "npcVisualDispatch":dispatch,
        "trainingDummyGameSystem":creature,
        "playerOnlyUniversalHunter":True,
        "npcHomogenizationAllowed":False,
        "oldRigOrSkinAssetCanBeDeletedWithoutConsumerAudit":False,
        "note":"These are static source checks. Missing staged source does not prove missing compiled runtime behavior."
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
        with path.open("rb") as handle:
            return handle.read(12)==b"\xabKTX 20\xbb\r\n\x1a\n"
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
    if url.startswith("/textures/skins/"):return "LEGACY_RIG_SKIN_USAGE_AUDIT"
    return "UNKNOWN"

def action(url):
    role=classify(url)
    if role=="LEGACY_RIG_SKIN_USAGE_AUDIT":
        return "TRACE_NPC_AND_PLAYER_RIG_CONSUMERS_BEFORE_CHANGE; KEEP_NPC_ROLE_DIVERSITY_AND_KAYKIT_SOURCE_V7; DO_NOT_AUTO_DELETE"
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
    contracts=visual_contract_checks()
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
      "visualPolicy":VISUAL_POLICY,
      "npcRoleReferenceRigs":NPC_ROLE_BASE_RIGS,
      "visualContractSourceChecks":contracts,
      "recommendedOrder":[
          "Preserve original NPC names, quest roles and per-NPC look mapping; diagnose NPC actor rig residency, clips, camera and draw visibility separately from player Hunter",
          "Restore training dummy using owned KayKit animated model and existing dummy sim ID and visual clips",
          "Rebuild active combat VFX using own effects while preserving named-node animation contract",
          "Audit users of all legacy class-named skin KTX2 assets before removal; player is Hunter only but NPC knight/mage/rogue/barbarian bases must remain distinct",
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
      "correctedActorPathsUsed":True,
      "missingActorAssetPaths":[x["url"] for x in actors if not x["stageValid"]],
      "sourceModulesInStage":sum(x["stageSourcePresent"] for x in systems),
      "sourceModulesExpected":len(systems),
      "npcVisibleVerified":False,"playerVisibleVerified":False,
      "singlePlayableHunterDesign":True,
      "npcVisualRoleDiversityPreservedAsRequirement":True,
      "npcVisualContractSourceChecks":{key:value["present"]
         for key,value in contracts.items() if isinstance(value,dict) and "present" in value},
      "skillsAndVfxVerified":False,
    },ensure_ascii=False))
    print("[HIGHFLY] P29 REPORT: "+str(path))
    return report

if __name__=="__main__":
    inspect()
