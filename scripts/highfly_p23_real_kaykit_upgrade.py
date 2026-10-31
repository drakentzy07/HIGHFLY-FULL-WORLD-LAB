#!/usr/bin/env python3
"""HIGHFLY P23: real KayKit/CC0 pack art over P22 temporary procedural meshes.

No 'looks somewhat similar' replacements: semantic/name match in the user's
real KayKit COMPLETE archive (or proven imported CC0 stage assets) only.
Never takes project-only or restricted ClaudeCraft media. Preserves the RPG.
Protects authored P8 files, does not touch characters, mounts, ports/entrances
with functional geometry, or upstream source code.

Also repairs the two remaining missing loading-screen WebPs using original
HIGHFLY SVG art converted to WebP by sharp.

Dry run: python3 scripts/highfly_p23_real_kaykit_upgrade.py
Apply:   python3 scripts/highfly_p23_real_kaykit_upgrade.py --apply
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21
import highfly_p22_owned_asset_rebuilder as p22

STAGE=p22.STAGE
REFERENCE=p22.REFERENCE
ARCHIVE=p12.ZIP
OUTPUT=ROOT/".workspace/reports/highfly-p23"
P22_REPORT=ROOT/".workspace/reports/highfly-p22/P22_RECOVERY_266.json"
P21_REPORT=ROOT/".workspace/reports/highfly-p21/P21_RUNTIME_314_LICENSED_RECOVERY.json"
P12_REPORT=ROOT/".workspace/reports/highfly-p12/WORLD_KAYKIT_P12.json"
P8_REPORT=ROOT/".workspace/reports/highfly-p8/EASTBROOK_OWNED_BUILDINGS_P8.json"
REPAIR_IMAGES=(
    "/textures/loading/fenbridge-rain-skiff.webp",
    "/textures/loading/hollow-crypt-empty.webp",
)
# Complex pieces must not be changed to an unrelated simple kit mesh.
STRUCTURAL_NO_SWAP_PATTERNS=(
    r"^/models/props/(eastbrook_|fenbridge_|wickharbor_|wyrmwatch_|kmed_)",
    r"^/models/props/(harbor_|rift_|delve_|dungeon_door_|hoard_entrance)",
    r"^/models/props/(marsh_plank_bridge|marsh_root_wall|wildheart_.*(bridge|platform|pyramid|gate))",
    r"^/models/dungeon/ignivar_prop_(bridge_|lift_|lava_channel|tower_|gate|staircase)",
    r"^/models/mounts/",
    r"^/models/creatures/",
    r"^/models/battleground/",
    r"^/models/props/(windrider_glider|streetlamp_|nythraxis_|farm_)",
    r"^/models/props/(maze_hedge_arch|maze_hedge_wall|destructible_wall)",
    r"^/models/quest/(crypt_|gravecaller_|gravewyrm_|bastion_|sanctum_)",
)
# Safe semantic equivalences only. These remain subject to unique source
# selection and review: none implies identical collision/animations.
SAFE_SYNONYMS={
    "fallback_crate":("crate",),
    "supply_crate":("crate",),
    "lost_caravan_goods":("crate",),
    "damaged_crate":("crate",),
    "banker_chest":("chest",),
    "hoard_reward_chest":("chest",),
    "waterlogged_barrel":("barrel",),
    "gather_wood_pile":("wood_pile",),
    "wood_log_stack":("log_stack",),
    "gather_ore_vein":("ore_vein",),
    "gather_herb_cluster":("herb_cluster",),
    "ignivar_prop_anvil":("anvil",),
    "ignivar_prop_chain":("chain",),
    "ignivar_prop_chain_link":("chain_link",),
    "ignivar_prop_cannon":("cannon",),
    "ignivar_prop_stone_floor":("floor_tile_large",),
    "gravestone_2":("gravestone_b", "gravestone_2"),
    "gravestone_3":("gravestone_c", "gravestone_3"),
    "dummy":("training_dummy",),
    "fence":("fence",),
    "signpost":("signpost",),
    "broken_planks":("planks_broken",),
    "fallen_anchor":("anchor",),
    "fallen_coconuts":("coconut",),
    "fen_mushrooms":("mushroom",),
    "fen_log":("log",),
    "fen_reeds":("reeds",),
    "fen_lilies":("lily",),
    "willow_tree":("willow",),
    "crystal_amethyst_cluster":("crystal_amethyst",),
    "crystal_mound_cave":("crystal_cluster",),
    "gather_ore_vein":("ore_vein",),
}
# Known pack family priority by category. Uses the actual SOURCE archive, not
# the project's pinned ClaudeCraft art or the P22-generated source geometry.
PACK_PREFERENCES={
    "dungeon":("Dungeon", "RPG Tools", "Furniture", "Halloween"),
    "drakelands_kit":("Medieval Hexagon", "Dungeon", "Halloween", "Furniture", "RPG Tools"),
    "props":("Furniture", "RPG Tools", "Resource", "Halloween", "Forest", "Medieval Hexagon","Dungeon"),
    "biome":("Medieval Hexagon", "Forest"),
    "resources":("Resource", "Forest", "RPG Tools"),
    "quest":("RPG Tools", "Dungeon", "Resource","Halloween"),
    "world_quests":("Pirate", "Resource", "Furniture"),
    "vfx":("RPG Tools",),
}
SOURCE_LIMIT=40_000_000
MAX_ARCHIVE_MEMBERS=100000
MAX_REPLACEMENTS=249


def fingerprint(path:Path) -> str:
    return p12.digest(path)


def is_structural(path:str) -> bool:
    return any(re.search(rule,path) for rule in STRUCTURAL_NO_SWAP_PATTERNS)


def safe_zip_name(member:str)->bool:
    p=PurePosixPath(member)
    return (not p.is_absolute() and ".." not in p.parts and
            "\\" not in member and len(member)<800)


def zip_index(zipfile_obj:zipfile.ZipFile):
    table=p12.zip_members(zipfile_obj)
    if len(table)>MAX_ARCHIVE_MEMBERS:
        raise RuntimeError("P23_KAYKIT_TOO_MANY_ARCHIVE_MEMBERS")
    indexed=defaultdict(list)
    for filename,info in table.items():
        p=PurePosixPath(filename)
        if p.suffix.lower()!=".gltf" or info.file_size>SOURCE_LIMIT:
            continue
        if not safe_zip_name(filename) or "gltf" not in [x.lower() for x in p.parts]:
            continue
        # Each SOURCE pack is its own directory. The archive wrapper
        # "KayKit Complete V7" is NOT a licensed pack identity! Restrict the
        # search to directories strictly above Assets/gltf/<asset>.gltf and
        # reject any "Complete"/"Collection" wrapper. A foreign pack nested
        # inside the ZIP must not inherit the wrapper's KayKit branding.
        packs=[
            part for part in p.parts[:-3]
            if part.startswith("KayKit ")
            and "complete" not in part.casefold() and "collection" not in part.casefold()
        ]
        if not packs:
            continue
        # Deepest individual KayKit source pack; supports a pack at ZIP root,
        # plus standard <root>/KayKit <pack>/Assets/gltf/ archives.
        pack=packs[-1]
        # Only the user's verified KayKit Complete source archive is accepted.
        # An arbitrary parent directory is never sufficient provenance.
        indexed[p.stem.casefold()].append({
            "member":filename,"pack":pack,"stem":p.stem.casefold(),
            "source":"USER_OWNED_KAYKIT_COMPLETE"})
    return table,indexed


def clean_basename(name:str)->str:
    return re.sub(r"[^a-z0-9]+","_",name.casefold()).strip("_")


def model_stems(path:str)->list[str]:
    p=PurePosixPath(path)
    stem=clean_basename(p.stem)
    # Exact name is most trustworthy. Other aliases only if explicitly listed.
    results=[stem]
    if stem.startswith("ignivar_prop_"):
        results.append(stem[len("ignivar_prop_"):])
    if stem.startswith("hex_"):
        results.extend(("building_"+stem[4:],stem[4:]))
    if stem.startswith("drakelands_"):
        results.append(stem[len("drakelands_"):])
    results.extend(clean_basename(x) for x in SAFE_SYNONYMS.get(stem,()))
    return list(dict.fromkeys(results))


def rank_pack(pack:str,category:str)->int:
    prefers=PACK_PREFERENCES.get(category,())
    for i,entry in enumerate(prefers):
        if entry.casefold() in pack.casefold():
            return i
    return 100


def match_archive(path:str,index:dict)->dict:
    if is_structural(path):
        return {"method":"KEEP_P22_CONTRACT_REVIEW","reason":"animation_or_scale_collision_contract"}
    category=PurePosixPath(path).parts[2]
    stems=model_stems(path)
    for order,stem in enumerate(stems):
        matches=[x for x in index.get(stem,[])
                 if rank_pack(x["pack"],category)<100]
        # Any duplicate in highest priority pack MUST be disambiguated,
        # never arbitrarily select one among two model variants.
        if not matches:
            continue
        best=min(rank_pack(x["pack"],category) for x in matches)
        nearest=[x for x in matches if rank_pack(x["pack"],category)==best]
        if len(nearest)==1:
            return {"method":"REPLACE_WITH_OWNED_KAYKIT",
                    "sourceZipMember":nearest[0]["member"],"sourcePack":nearest[0]["pack"],
                    "sourceStem":stem,"matchRule":"EXACT" if order==0 else "CURATED_ALIAS"}
        return {"method":"AMBIGUOUS_KAYKIT_VARIANTS",
                "sourceStem":stem,"candidates":sorted(x["member"] for x in nearest)[:8]}
    return {"method":"NO_KAYKIT_SEMANTIC_MATCH"}


def p22_provisional_source():
    if not P22_REPORT.is_file():
        raise RuntimeError("P23_P22_APPLY_REPORT_MISSING")
    report=json.loads(P22_REPORT.read_text(encoding="utf8"))
    if report.get("mode")!="APPLY" or report.get("captured")!=266:
        raise RuntimeError("P23_EXPECTS_P22_APPLY_266")
    entries={}
    for x in report.get("installed",[]):
        if x.get("generation")=="ORIGINAL_PROCEDURAL_FIRST_PASS":
            entries[x["path"]]=x["sha256"]
    if len(entries)!=249:
        raise RuntimeError("P23_EXPECTED_249_P22_PROVISIONAL_GENERATIONS: "+str(len(entries)))
    return entries


def staged_proof():
    """Optional proven CC0 assets already loaded in stage by earlier phases."""
    sources={}
    def add(path,sha,origin):
        if not p21.safe_asset_path(path):
            return
        s=STAGE/"public"/path.lstrip("/")
        if s.is_file() and not s.is_symlink() and fingerprint(s)==sha and p21.check_binary(s,path):
            sources[path]={"origin":origin,"sha256":sha}
    if P8_REPORT.is_file():
        doc=json.loads(P8_REPORT.read_text(encoding="utf8"))
        for entry in doc.get("buildings",[]):
            if entry.get("publicUrl") and entry.get("glbSha256"):
                add(entry["publicUrl"],entry["glbSha256"],"USER_OWNED_KAYKIT_P8")
    if P12_REPORT.is_file():
        doc=json.loads(P12_REPORT.read_text(encoding="utf8"))
        for entry in doc.get("imported",[]):
            if entry.get("target") and entry.get("sha256"):
                add("/"+entry["target"].lstrip("/"),entry["sha256"],"USER_OWNED_KAYKIT_P12")
    if P21_REPORT.is_file():
        doc=json.loads(P21_REPORT.read_text(encoding="utf8"))
        for entry in doc.get("installed",[]):
            if entry.get("provenance","").startswith("CC0_"):
                add(entry["path"],entry["sha256"],"PROVEN_PINNED_CC0_P21")
    return sources


def exact_stage_match(path:str,proof:dict)->dict|None:
    if is_structural(path):
        return None
    stem=clean_basename(PurePosixPath(path).stem)
    category=PurePosixPath(path).parts[2]
    matches=[]
    for source,record in proof.items():
        if source==path or Path(source).suffix.lower()!=".glb":
            continue
        # Only identical stem and useful family. NEVER guess from containment.
        if clean_basename(Path(source).stem)!=stem:
            continue
        src_category=PurePosixPath(source).parts[2]
        if src_category!=category and (
            category=="dungeon" and src_category not in ("biome","dungeon") or
            category not in ("dungeon","props","drakelands_kit","biome","resources","quest","world_quests","vfx")
        ):
            continue
        matches.append((source,record))
    if len(matches)!=1:
        return None
    src,record=matches[0]
    return {"method":"REPLACE_WITH_PROVEN_CC0_STAGE",
            "source":src,"sourceSha256":record["sha256"],
            "provenance":record["origin"],
            "matchRule":"EXACT_STEM"}


def is_p22_file(path:Path, expected_hash:str)->bool:
    if path.is_symlink() or not path.is_file() or fingerprint(path)!=expected_hash:
        return False
    if not p22.p21.check_binary(path,str(path)):
        return False
    with path.open("rb") as stream:
        header=stream.read(20)
        if header[:4]!=b"glTF" or header[16:20]!=b"JSON":return False
        n=int.from_bytes(header[12:16],"little")
        if n>2_000_000:return False
        obj=json.loads(stream.read(n))
    return (obj.get("asset",{}).get("generator")=="HIGHFLY P22 original procedural geometry"
            and obj.get("nodes",[{}])[0].get("extras",{}).get("highflyOrigin")
                =="original_procedural_p22")


def paths_to_plan(index:dict,proof:dict,provisional:dict):
    rows=[]
    for url,sha in sorted(provisional.items()):
        target=STAGE/"public"/url.lstrip("/")
        row={"path":url,"originalP22Sha256":sha}
        if is_p22_file(target,sha):
            row["status"]="P22_PROVISIONAL_PRESENT"
            match=exact_stage_match(url,proof) or match_archive(url,index)
            row.update(match)
        elif target.is_file() and not target.is_symlink() and p21.check_binary(target,url):
            row.update({"status":"TARGET_MODIFIED_AFTER_P22","method":"DO_NOT_OVERWRITE_EXISTING"})
        else:
            row.update({"status":"BROKEN_OR_MISSING_P22","method":"BLOCK_BAD_STAGE_STATE"})
        rows.append(row)
    return rows


def loading_svg(path:str)->str:
    fen="fenbridge" in path
    name="FENBRIDGE" if fen else "HOLLOW CRYPT"
    sub="TRAVESIA BAJO LA LLUVIA" if fen else "SILENCIO EN LA CRIPTA"
    accent="#5bb9db" if fen else "#9d77e6"
    if fen:
        scene=(
            '<path d="M0 440 L230 270 440 440 660 310 900 420 1090 250 1280 420 1280 720 0 720Z" fill="#182e3e"/>'
            '<path d="M0 520 Q450 470 1280 520 V720 H0Z" fill="#143b4c"/>'
            '<path d="M365 515 L915 515 825 590 470 590Z" fill="#6f4937" stroke="#d9ae76" stroke-width="8"/>'
            '<path d="M630 513 L630 260 M630 270 L790 480 L630 480 Z" stroke="#b9d4da" stroke-width="8" fill="#d4d5ca"/>'
            '<path d="M0 600 Q210 570 450 610 T1000 605 T1280 620" fill="none" stroke="#92bdc5" stroke-width="5"/>'
            +''.join('<path d="M%d 150 l-32 120" stroke="#76a0bc" stroke-opacity=".5" stroke-width="3"/>'%(i*64+16) for i in range(21)))
    else:
        scene=(
            '<path d="M0 410 L0 100 L1280 100 L1280 410 L1190 410 L1190 280 L930 280 L930 410 L350 410 L350 280 L90 280 L90 410Z" fill="#25263d"/>'
            '<path d="M300 650 L430 350 Q640 160 850 350 L980 650Z" fill="#111c32" stroke="#68648d" stroke-width="26"/>'
            '<path d="M420 650 L515 400 L765 400 L860 650Z" fill="#251e39"/>'
            '<path d="M530 560 L565 465 L715 465 L750 560Z" fill="#77839b" stroke="#b9adc8" stroke-width="6"/>'
            '<circle cx="635" cy="360" r="72" fill="#664894" opacity=".7"/>'
            '<path d="M515 650 L565 560 L715 560 L765 650Z" fill="#2f344b"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">'
            f'<rect width="1280" height="720" fill="#101626"/>'
            f'<circle cx="650" cy="390" r="340" fill="{accent}" opacity=".14"/>'
            +scene+
            f'<text x="640" y="100" text-anchor="middle" font-family="sans-serif" font-size="49" letter-spacing="12" fill="{accent}" font-weight="bold">{name}</text>'
            f'<text x="640" y="151" text-anchor="middle" font-family="sans-serif" font-size="22" letter-spacing="5" fill="#ced7e3">{sub}</text>'
            '<text x="640" y="688" text-anchor="middle" font-family="sans-serif" font-size="21" letter-spacing="6" fill="#b7cadd">HIGHFLY ORIGIN</text></svg>')


def make_loading(path:str,destination:Path):
    svg=loading_svg(path)
    script=("const sharp=require('sharp');let b=[];"
            "process.stdin.on('data',x=>b.push(x));"
            "process.stdin.on('end',async()=>{try{await sharp(Buffer.concat(b)).webp({quality:86}).toFile(process.argv[1]);}"
            "catch(e){console.error(e);process.exit(1)}});")
    p=subprocess.run(["node","-e",script,str(destination)],cwd=REFERENCE,
                    input=svg,encoding="utf8",capture_output=True,timeout=90)
    if p.returncode or not p21.check_binary(destination,path):
        raise RuntimeError("P23_HIGHFLY_LOADING_WEBP_FAILED: "+p.stderr[-600:])


def convert_zip_asset(z,table,member:str,target:Path,workspace:Path):
    # p12 validates local glTF dependencies inside its pack and only extracts
    # the one selected source. This is not a blind extraction of the ZIP.
    input=p12.unpack_selected(z,table,member,workspace)
    binary=REFERENCE/"node_modules/.bin/gltf-transform"
    if not binary.is_file():raise RuntimeError("P23_GLTF_TRANSFORM_MISSING")
    p=subprocess.run([str(binary),"copy",str(input),str(target)],
                     cwd=REFERENCE,encoding="utf8",capture_output=True,timeout=120)
    if p.returncode or not p21.check_binary(target,"/models/p23.glb"):
        raise RuntimeError("P23_KAYKIT_CONVERSION_FAILED: "+member+" "+p.stderr[-400:])


def perform(rows:list[dict], z:zipfile.ZipFile, table:dict, provisional:dict,
            image_paths:list[str], max_models:int):
    chosen=[r for r in rows if r["method"] in (
        "REPLACE_WITH_OWNED_KAYKIT","REPLACE_WITH_PROVEN_CC0_STAGE")]
    if len(chosen)>MAX_REPLACEMENTS or not 0<=max_models<=MAX_REPLACEMENTS:
        raise RuntimeError("P23_REPLACEMENT_LIMIT_INVALID")
    chosen=chosen[:max_models]
    OUTPUT.mkdir(parents=True,exist_ok=True)
    installed=[]
    with tempfile.TemporaryDirectory(prefix="p23-safe-",dir=OUTPUT) as temp:
        tmp=Path(temp)
        prepared=[]
        for index,row in enumerate(chosen):
            url=row["path"]
            target=STAGE/"public"/url.lstrip("/")
            if not is_p22_file(target,provisional[url]):
                raise RuntimeError("P23_SOURCE_CHANGED_ABORT: "+url)
            dst=tmp/("new-"+str(index)+".glb")
            if row["method"]=="REPLACE_WITH_OWNED_KAYKIT":
                convert_zip_asset(z,table,row["sourceZipMember"],dst,tmp/("src-"+str(index)))
                src_label=row["sourceZipMember"]
            else:
                src=STAGE/"public"/row["source"].lstrip("/")
                if (src.is_symlink() or not src.is_file() or
                        fingerprint(src)!=row["sourceSha256"] or
                        not p21.check_binary(src,row["source"])):
                    raise RuntimeError("P23_PROVEN_CC0_SOURCE_CHANGED: "+row["source"])
                shutil.copyfile(src,dst)
                src_label=row["source"]
            if not p21.check_binary(dst,url):raise RuntimeError("P23_BAD_REPLACEMENT: "+url)
            prepared.append((url,target,dst,src_label,row["method"]))
        for index,url in enumerate(image_paths):
            target=STAGE/"public"/url.lstrip("/")
            if target.is_symlink() or target.exists():
                raise RuntimeError("P23_IMAGE_TARGET_ALREADY_EXISTS: "+url)
            dst=tmp/("loading-"+str(index)+".webp")
            make_loading(url,dst)
            prepared.append((url,target,dst,"HIGHFLY_ORIGINAL_IMAGE","GENERATE_HIGHFLY_LOADING"))
        # All assets generated before any of them are written to stage.
        for url,target,dst,origin,method in prepared:
            backup=None
            if url in provisional:
                if not is_p22_file(target,provisional[url]):
                    raise RuntimeError("P23_P22_TARGET_CHANGED_DURING_PREPARE: "+url)
                backup=OUTPUT/"p22-originals"/url.lstrip("/")
                backup.parent.mkdir(parents=True,exist_ok=True)
                if not backup.exists():
                    shutil.copy2(target,backup)
                    if fingerprint(backup)!=provisional[url]:
                        raise RuntimeError("P23_BACKUP_VERIFICATION_FAILED: "+url)
            elif target.exists() or target.is_symlink():
                raise RuntimeError("P23_IMAGE_TARGET_CHANGED_DURING_PREPARE: "+url)
            target.parent.mkdir(parents=True,exist_ok=True)
            os.replace(dst,target)
            installed.append({"path":url,"method":method,"source":origin,
                             "newSha256":fingerprint(target),
                             "p22Backup":str(backup) if backup else None})
    return installed


def rollback_applied(installed:list[dict])->list[str]:
    """Restore exact P22 stage bytes if an unexpected build/packaging failure occurs."""
    restored=[]
    for row in reversed(installed):
        url=row["path"]
        target=STAGE/"public"/url.lstrip("/")
        if not target.is_file() or target.is_symlink() or fingerprint(target)!=row["newSha256"]:
            raise RuntimeError("P23_ROLLBACK_REFUSE_CHANGED_FILE: "+url)
        if row["p22Backup"]:
            backup=Path(row["p22Backup"])
            if not backup.is_file() or backup.is_symlink():
                raise RuntimeError("P23_ROLLBACK_BACKUP_MISSING: "+url)
            expected=p22_provisional_source()[url]
            if fingerprint(backup)!=expected:
                raise RuntimeError("P23_ROLLBACK_BACKUP_HASH_MISMATCH: "+url)
            with tempfile.NamedTemporaryFile(prefix="p23-rollback-",dir=target.parent,delete=False) as f:
                temp=Path(f.name)
            try:
                shutil.copyfile(backup,temp)
                if fingerprint(temp)!=expected:
                    raise RuntimeError("P23_ROLLBACK_RESTORED_HASH_BAD: "+url)
                os.replace(temp,target)
            finally:
                temp.unlink(missing_ok=True)
        else:
            target.unlink()
        restored.append(url)
    return restored


def status_after(installed:list[dict]):
    counters=Counter()
    errors=[]
    for row in installed:
        url=row["path"]
        src=STAGE/"public"/url.lstrip("/")
        dst=STAGE/"dist"/url.lstrip("/")
        good=(p21.check_binary(src,url) and p21.check_binary(dst,url)
              and fingerprint(src)==fingerprint(dst)
              and fingerprint(src)==row["newSha256"])
        counters["BUNDLED_VERIFIED" if good else "BAD_BUNDLE"]+=1
        if not good:errors.append(url)
    return dict(counters),errors


def run(apply:bool=False,max_models:int=249):
    p9.preflight(REFERENCE,STAGE,p9.REPORT)
    p12.validate(REFERENCE,STAGE,ARCHIVE,OUTPUT)
    provisional=p22_provisional_source()
    proof=staged_proof()
    with zipfile.ZipFile(ARCHIVE) as z:
        table,index=zip_index(z)
        rows=paths_to_plan(index,proof,provisional)
        methods=dict(Counter(row["method"] for row in rows))
        to_image=[url for url in REPAIR_IMAGES if not (STAGE/"public"/url.lstrip("/")).exists()]
        blocked_image=[url for url in REPAIR_IMAGES if (STAGE/"public"/url.lstrip("/")).is_symlink()]
        if blocked_image:raise RuntimeError("P23_IMAGE_SYMLINK_BLOCKED: "+str(blocked_image))
        installed=[]
        build=None
        build_exception=None
        if apply:
            if methods.get("BLOCK_BAD_STAGE_STATE",0):
                raise RuntimeError("P23_P22_STAGE_MISSING_ABORT")
            installed=perform(rows,z,table,provisional,to_image,max_models)
            try:
                build=p9.smoke()["exitCode"]
            except Exception as exc:
                build_exception=str(exc)
                build=-1
        result,errors=status_after(installed) if apply and build==0 else ({},[])
        rollback_paths=[]
        if apply and (build!=0 or errors):
            rollback_paths=rollback_applied(installed)
        report={
            "phase":"HIGHFLY_P23_REAL_CC0_PACK_VISUAL_TAKEOVER",
            "mode":"APPLY" if apply else "DRY_RUN",
            "timestampUtc":datetime.now(timezone.utc).isoformat(),
            "sourceArchive":str(ARCHIVE),
            "archiveGltfCandidates":sum(map(len,index.values())),
            "provenStageCC0Assets":len(proof),
            "p22TemporaryModels":len(provisional),
            "sourceAndRightsPolicy":"USER_OWNED_KAYKIT_CC0_AND_PROVEN_IMPORTED_CC0_ONLY",
            "noClaudeCraftRestrictedOrProjectMediaCopied":True,
            "rpgSimulationCodeModified":False,
            "gameplayVerified":False,
            "visualQualityVerified":False,
            "pass1SafeReplacementsReady":sum(methods.get(k,0) for k in (
                "REPLACE_WITH_OWNED_KAYKIT","REPLACE_WITH_PROVEN_CC0_STAGE")),
            "remainingProceduralModelsBeforeApply":methods.get("NO_KAYKIT_SEMANTIC_MATCH",0)
                 +methods.get("KEEP_P22_CONTRACT_REVIEW",0)
                 +methods.get("AMBIGUOUS_KAYKIT_VARIANTS",0),
            "methodCounts":methods,"twoLoadingArtMissing":to_image,
            "installed":installed,"bundledStatuses":result,"bundleErrors":errors,
            "buildExitCode":build,"buildException":build_exception,
            "rollbackPaths":rollback_paths,"rollbackPerformed":bool(rollback_paths),
            "remainingP22ProceduralAfterApply":249-sum(
                x["path"].endswith(".glb") for x in installed) if apply and not rollback_paths else 249,
            "items":rows,
            "followup":"Review source scales, orientation, render/collision, mobile performance, and world entry."}
        OUTPUT.mkdir(parents=True,exist_ok=True)
        file=OUTPUT/"P23_REAL_KAYKIT_VISUAL_TAKEOVER.json"
        file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        summary={"mode":report["mode"],"p22TemporaryModels":len(provisional),
                 "kaykitZipModelsIndexed":report["archiveGltfCandidates"],
                 "methods":methods,"realPackModelsInstalled":sum(x["path"].endswith(".glb") for x in installed),
                 "loadingImagesInstalled":sum(x["path"].endswith(".webp") for x in installed),
                 "remainingP22Procedural":report["remainingP22ProceduralAfterApply"],
                 "bundleStatuses":result,"buildExitCode":build,
                 "rollbackPerformed":bool(rollback_paths),"gameplayVerified":False}
        print("[HIGHFLY] P23 "+report["mode"]+": "+json.dumps(summary,ensure_ascii=False))
        print("[HIGHFLY] P23 REPORT: "+str(file))
        if apply and (build!=0 or errors):
            raise SystemExit("P23_BUILD_OR_ASSET_PACKAGING_FAILED")
        return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--max-models",type=int,default=249)
    options=parser.parse_args()
    run(options.apply,options.max_models)
