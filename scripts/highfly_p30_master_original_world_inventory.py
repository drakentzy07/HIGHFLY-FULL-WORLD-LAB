#!/usr/bin/env python3
"""HIGHFLY P30: one global pinned-ClaudeCraft 0.44.7 asset + NPC + systems inventory.

Read-only. Crosses all public media (not only observed errors), original
src->out converter specs, source-code literal uses, original NPC visual
mappings/looks, game-system source modules, local built stage, user-owned
KayKit SOURCE V7 and source CREDITS. Includes every gameplay-art category.
Static evidence is NOT proof of runtime spawn/behavior or per-file licensing.
No copies, deletions, source rewrites, deployments or visual substitutions.
"""
from __future__ import annotations
import csv,json,re,sys,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p23_real_kaykit_upgrade as p23
import highfly_p25_source_first_asset_audit as p25
import highfly_p29_actor_skill_vfx_audit as p29
ORIGINAL=p9.ORIGINAL
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p30-master"
MEDIA={".glb",".gltf",".obj",".fbx",".png",".jpg",".jpeg",".webp",".ktx2",".hdr",
".exr",".ogg",".mp3",".wav",".flac",".woff",".woff2",".ttf",".svg",".bin",".basis",".mp4"}
CODE={".ts",".tsx",".js",".mjs",".py",".json"}
TOKENS=re.compile(r"(?<![A-Za-z0-9_./-])/?((?:models|textures|vfx|ui|audio|fonts|skybox|skyboxes|env|assets)/[A-Za-z0-9_./-]+)")
def categories(path):
    s=path.casefold();n=PurePosixPath(s).name;result=[]
    def a(x):
        if x not in result:result.append(x)
    if s.startswith("models/chars/"):
        a("CHARACTERS")
        if "/npc_gear/" in s or "/modular/" in s:a("NPC")
    if s.startswith("models/creatures/") or s.startswith("ui/mobs/"):a("MONSTERS")
    if "dummy" in s or s.startswith("models/tools/"):a("INTERACTIONS_MOVEMENT")
    if s.startswith(("models/weapons/","ui/weapons/")) or "weapon" in n:a("WEAPONS")
    if any(x in s for x in ("armor","armour","helmet","shield","chestplate","boots","gauntlet","npc_gear")):a("ARMOR")
    if any(x in s for x in ("ship","boat","dock","ferry","wharf","sail","harbor","harbour","watercraft")):a("SHIPS")
    if s.startswith(("models/foliage/","textures/foliage/")) or any(x in n for x in
       ("tree","grass","plant","flower","mushroom","willow","palm","fish","bird","fox","wolf")):a("FLORA_FAUNA_VEGETATION")
    if any(x in s for x in ("water","lava","terrain","rain","snow","weather","sky","cloud","ground","river","ocean","sea")):a("WATER_LAVA_TERRAIN_WEATHER")
    if any(x in s for x in ("house","home","tavern","inn","building","chapel","church","market","smith","lodge","windmill","barracks","stables")):a("BUILDINGS")
    if s.startswith(("models/dungeon/","models/biome/","models/drakelands_kit/")) or any(x in s for x in ("bridge","wall","gate","pillar","tower","castle","floor")):a("STRUCTURES")
    if s.startswith(("ui/items/","models/resources/")) or "chest" in s or "crate" in s or "loot" in s:a("LOOT");a("ITEMS")
    if s.startswith(("ui/skills/","vfx/","textures/vfx/","ui/auras/")) or "spell" in s:a("SKILLS_VFX")
    if s.startswith(("ui/","fonts/")):a("MENUES_HUD")
    if s.startswith("audio/"):a("AUDIO")
    if s.startswith(("models/props/","models/quest/","models/world_quests/")):a("ITEMS")
    return result or ["OTHER"]
def all_media():
    root=ORIGINAL/"public"
    if not root.is_dir():raise RuntimeError("P30_ORIGINAL_MEDIA_MISSING")
    result={}
    for x in root.rglob("*"):
        if x.is_file() and not x.is_symlink() and x.suffix.casefold() in MEDIA:
            result[x.relative_to(root).as_posix()]=x.stat().st_size
    return result
def code_files():
    for dirname in ("src","scripts","server","android"):
        base=ORIGINAL/dirname
        if not base.is_dir():continue
        for x in base.rglob("*"):
            if x.is_file() and not x.is_symlink() and x.suffix.casefold() in CODE and x.stat().st_size<4_000_000:
                if not any(s in x.parts for s in ("node_modules","dist","build","tests")):
                    yield x
def code_references(media:set[str]):
    refs=defaultdict(list);sources=[];top=Counter()
    for x in code_files():
        rel=x.relative_to(ORIGINAL).as_posix()
        sources.append((rel,x.stat().st_size))
        try:lines=x.read_text(encoding="utf8",errors="replace").splitlines()
        except OSError:continue
        for i,line in enumerate(lines,1):
            if len(line)>12000:continue
            matches={m.group(1) for m in TOKENS.finditer(line)}
            for path in matches & media:
                if len(refs[path])<8:refs[path].append(rel+":"+str(i))
                top[rel]+=1
    return dict(refs),sources,top
def ts_table(src,head):
    m=re.search(head+r"\s*=\s*\{\s*\n",src)
    if not m:return ""
    t=src[m.end():];end=re.search(r"^};\s*$",t,re.M)
    return t[:end.start()] if end else ""
def expand(s):
    for k,v in (("PLAYERS","models/chars/players"),("MODULAR","models/chars/modular"),
                ("CREATURES","models/creatures"),("WEAPONS","models/weapons")):
        s=s.replace(chr(36)+"{"+k+"}",v)
    return None if chr(36)+"{" in s else "/"+s.lstrip("/")
def npc_inventory():
    root=ORIGINAL/"src/render/characters"
    manifest=(root/"manifest.ts").read_text(encoding="utf8")
    appearance=(root/"npc_looks.ts").read_text(encoding="utf8")
    table=ts_table(manifest,r"const NPC_KEYS:\s*Record<string,\s*string>")
    ids=dict(re.findall(r"^  ([a-z0-9_]+):\s*'(npc_[a-z0-9_]+)'",table,re.M))
    if not ids:raise RuntimeError("P30_NPC_TABLE_COULD_NOT_BE_PARSED")
    visual={}
    for m in re.finditer(r"^  (npc_[a-z0-9_]+):\s*\{\s*\n(.*?)^  \},",manifest,re.M|re.S):
        body=m.group(2)
        path=re.search(r"^    url:\s*\x60([^\x60]+)\x60",body,re.M)
        if not path:continue
        donor=re.search(r"^    animUrls:\s*\[(.*?)\]",body,re.S|re.M)
        anims=re.findall(r"\x60([^\x60]+)\x60",donor.group(1)) if donor else []
        visual[m.group(1)]={"model":expand(path.group(1)),
                            "animations":[expand(a) for a in anims]}
    looks_source=ts_table(appearance,r"export const NPC_LOOKS:\s*Record<string,\s*NpcLookDef>")
    found=list(re.finditer(r"^  ([a-z][a-z0-9_]+):\s*\{",looks_source,re.M))
    looks={}
    for i,m in enumerate(found):
        data=looks_source[m.end():found[i+1].start() if i+1<len(found) else len(looks_source)]
        def val(pattern):
            z=re.search(pattern,data);return z.group(1) if z else None
        looks[m.group(1)]={"wardrobe":val(r"worn:\s*kit\('([^']+)'\)"),
                           "outfit":val(r"outfit:\s*'([^']+)'"),
                           "heldProps":val(r"props:\s*'([^']+)'")}
    npc=[]
    for name,key in sorted(ids.items()):
        look=looks.get(name)
        if look:
            key="npc_modular_"+(look["heldProps"] or "none")
            model="/models/chars/modular/warrior_modular.glb"
            anim=["/models/chars/players/rogue.glb",
                  "/models/chars/players/rogue_hit_variety_anims.glb"]
        else:
            model=visual.get(key,{}).get("model")
            anim=visual.get(key,{}).get("animations",[])
        npc.append({"npcId":name,"npcOriginalVisualKey":key,"modelUrl":model,
                    "animationDonorUrls":anim,"individualLook":look,
                    "gameplayIdentityChanged":False,
                    "location":"NOT_IN_VISUAL_MANIFEST_VERIFY_IN_CONTENT_OR_RUNTIME"})
    for name,look in sorted(looks.items()):
        if name not in ids:
            npc.append({"npcId":name,"npcOriginalVisualKey":"npc_modular_"+(look["heldProps"] or "none"),
                        "modelUrl":"/models/chars/modular/warrior_modular.glb",
                        "animationDonorUrls":["/models/chars/players/rogue.glb"],
                        "individualLook":look,"gameplayIdentityChanged":False,
                        "location":"DYNAMIC_LOOK_NEEDS_SPAWN_LOOKUP"})
    return npc,len(ids),len(looks),len(visual)
CONTENT_TYPES={"NpcDef":"NPC","MobTemplate":"MONSTERS",
               "ItemDef":"ITEMS_LOOT_EQUIPMENT","QuestDef":"QUESTS"}
RECORD_EXPORT=re.compile(
    r"export const ([A-Z_0-9]+):\s*Record<string,\s*(NpcDef|MobTemplate|ItemDef|QuestDef)>\s*=\s*\{\s*\n")
RECORD_KEY=re.compile(r"^  (?:'([a-zA-Z0-9_]+)'|([a-zA-Z0-9_]+)):\s*\{",re.M)

def content_records_from_source(raw,rel):
    """Read literal exported typed data records with id, name, coords and
    quest/loot association fields. This is static syntax: computed/spread
    definitions are flagged separately rather than invented."""
    rows=[]
    for declared in RECORD_EXPORT.finditer(raw):
        name,typename=declared.group(1),declared.group(2)
        tail=raw[declared.end():]
        end=re.search(r"^};\s*$",tail,re.M)
        if end is None:continue
        body=tail[:end.start()]
        keys=list(RECORD_KEY.finditer(body))
        for i,m in enumerate(keys):
            item_id=m.group(1) or m.group(2)
            snippet=body[m.end():keys[i+1].start() if i+1<len(keys) else len(body)]
            def field(rx):
                match=re.search(rx,snippet,re.M)
                return match.group(1) if match else None
            name_field=field(r"^\s{4}name:\s*'([^']+)'")
            family=field(r"^\s{4}family:\s*'([^']+)'")
            title=field(r"^\s{4}title:\s*'([^']+)'")
            x=field(r"pos:\s*\{\s*x:\s*(-?\d+(?:\.\d+)?)")
            z=field(r"pos:\s*\{[^\}]*z:\s*(-?\d+(?:\.\d+)?)")
            q=re.search(r"\bquestIds:\s*\[([^\]]{0,1200})\]",snippet,re.S)
            quests=re.findall(r"['\x22]([a-z0-9_]+)['\x22]",q.group(1)) if q else []
            rows.append({
                "kind":CONTENT_TYPES[typename],"simType":typename,
                "sourceModule":rel,"exportedTable":name,
                "id":item_id,"displayName":name_field,"title":title,
                "family":family,"positionX":x,"positionZ":z,
                "questIds":quests,"sourceStaticOnly":True
            })
    return rows

def master_content_records(root):
    files=sorted((root/"src/sim/content").rglob("*.ts"))
    data=root/"src/sim/data.ts"
    if data.is_file():files.append(data)
    rows=[]
    for file in files:
        if not file.is_file() or file.is_symlink() or file.stat().st_size>4_000_000:continue
        rel=file.relative_to(root).as_posix()
        rows.extend(content_records_from_source(
            file.read_text(encoding="utf8",errors="replace"),rel))
    return rows

def mob_visual_index(root):
    manifest=(root/"src/render/characters/manifest.ts").read_text(encoding="utf8")
    mobkey=ts_table(manifest,r"const MOB_KEYS:\s*Record<string,\s*string>")
    family=ts_table(manifest,r"const FAMILY_KEYS:\s*Record<string,\s*string>")
    named=dict(re.findall(r"^  ([a-z0-9_]+):\s*'(mob_[a-z0-9_]+)'",mobkey,re.M))
    families=dict(re.findall(r"^  ([a-z0-9_]+):\s*'([a-z0-9_]+)'",family,re.M))
    visual={}
    for m in re.finditer(r"^  ((?:mob_|skel_)[a-z0-9_]+):\s*\{\s*\n(.*?)^  \},",
                         manifest,re.M|re.S):
        body=m.group(2)
        model=re.search(r"^    url:\s*\x60([^\x60]+)\x60",body,re.M)
        if model:
            visual[m.group(1)]=expand(model.group(1))
    return named,families,visual

def content_classification(row):
    """This is NOT a claim about an item's exact equipment rule."""
    name=(row["id"]+" "+str(row["displayName"] or "")).lower()
    result=[row["kind"]]
    if row["kind"]=="ITEMS_LOOT_EQUIPMENT":
        result.extend(["ITEMS","LOOT"])
        if any(x in name for x in ("sword","axe","bow","spear","hammer","staff","dagger","weapon","mace")):
            result.append("WEAPONS")
        if any(x in name for x in ("armor","armour","robe","helm","boot","ring","shield","gauntlet","glove")):
            result.append("ARMOR")
    return list(dict.fromkeys(result))

def credits_evidence(path,lines):
    needles=("public/"+path,path)
    return [{"creditsLine":i,"line":line[:700]} for i,line in enumerate(lines,1)
            if line.startswith("|") and any((chr(96)+n+chr(96)) in line for n in needles)][:5]
def game_source_categories(file):
    if file.startswith("src/sim/"):return "SIM_NPC_LOOT_MONSTER_SKILLS_ZONES"
    if file.startswith("src/render/"):return "RENDER_CHARACTERS_VFX_ENVIRONMENT"
    if file.startswith("src/ui/"):return "MENUES_HUD_INVENTORY_QUESTS"
    if file.startswith(("src/controls/","src/input/")):return "INTERACTIONS_MOVEMENT"
    if file.startswith("scripts/assets/"):return "ASSET_BUILD_AND_IMPORT"
    if file.startswith("src/net/"):return "NETWORK"
    return "OTHER_SOURCE"
def run():
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    originals=all_media()
    specs=p25.outspec_index(ORIGINAL)
    credits=p25.credited(ORIGINAL)
    credit_lines=(ORIGINAL/"CREDITS.md").read_text(encoding="utf8").splitlines()
    npc,static_count,look_count,visual_count=npc_inventory()
    sim_records=master_content_records(ORIGINAL)
    by_id=defaultdict(list)
    for record in sim_records:
        by_id[(record["kind"],record["id"])].append(record)
    for row in npc:
        matches=by_id.get(("NPC",row["npcId"]),[])
        row["simulationDefinitions"]=matches[:8]
        # Real numeric coordinates ONLY when present in an original NPC record.
        positions=[{"x":x["positionX"],"z":x["positionZ"],"source":x["sourceModule"]}
                   for x in matches if x["positionX"] is not None and x["positionZ"] is not None]
        row["verifiedOriginalStaticCoordinates"]=positions
    mobnames,mobfamilies,mobvisuals=mob_visual_index(ORIGINAL)
    for record in sim_records:
        record["categories"]=content_classification(record)
        if record["kind"]=="MONSTERS":
            key=mobnames.get(record["id"]) or mobfamilies.get(record["family"]) or "mob_bandit"
            record["originalMobVisualKey"]=key
            record["originalModelUrl"]=mobvisuals.get(key)
            record["modelMappingEvidence"]="STATIC_OVERRIDE_OR_FAMILY_FALLBACK_REVIEW"
    with zipfile.ZipFile(p23.ARCHIVE) as z:
        _,kaykit=p23.zip_index(z)
    temp={p.lstrip("/"):sha for p,sha in p23.p22_provisional_source().items()}
    historical=set(p29.FAILURES)
    for path,n in (("reports/highfly_p20_runtime_missing_paths.json",314),
                   ("reports/highfly_p21_fresh_missing_266.json",266)):
        historical.update(p25.from_capture(ROOT/path,n))
    media=set(originals)|{p.lstrip("/") for p in historical}
    refs,source_files,top=code_references(media)
    npc_reverse=defaultdict(list)
    for row in npc:
        for url in [row["modelUrl"],*row["animationDonorUrls"]]:
            if url:npc_reverse[url.lstrip("/")].append(row["npcId"])
    rows=[];roles=Counter();status=Counter();licences=Counter()
    for path in sorted(media):
        observed="/"+path in historical
        spec=specs.get("/"+path,[])
        providers={x["sourceProvider"] for x in spec}
        p=next(iter(providers)) if len(providers)==1 else None
        credit=credits_evidence(path,credit_lines)
        if p in credits and credits.get(p):
            license_status=("OWNED_COMPLETE_SOURCE_V7_ONLY" if p=="KayKit" else "SPEC_PROVIDER_CC0_REUSE_CANDIDATE")
        elif credit:
            license_status="EXACT_CREDITS_ROW_REQUIRES_TERMS_INSPECTION"
        else:
            license_status="NO_EXACT_REUSE_PROOF_OR_PROJECT_ART"
        stage=STAGE/"public"/path
        built=STAGE/"dist"/path
        present=stage.is_file() and not stage.is_symlink()
        provisional=present and path in temp and p12.digest(stage)==temp[path]
        next_action="REPLACE_P22_PROVISIONAL" if provisional else (
            "RESTORE_OR_REVIEW_MISSING_ASSET" if not present else
            "CHECK_RUNTIME_ERRORS" if observed and "/"+path in p29.FAILURES else
            "PRESERVE_IF_LICENSE_VERIFIED")
        src_candidate=[]
        if path.startswith("models/") and path.endswith(".glb"):
            for x in kaykit.get(p23.clean_basename(Path(path).stem),[])[:10]:
                src_candidate.append({"pack":x["pack"],"sourceZip":x["member"],
                                      "compatibleRigNotYetVerified":True})
        row={"asset":"/"+path,"categories":categories(path),
             "originalPresent":path in originals,
             "originalBytes":originals.get(path),
             "stagePresent":present,"distPresent":built.is_file(),
             "p22Provisional":provisional,"browserRequested":observed,
             "postWorldEntryFailed":"/"+path in p29.FAILURES,
             "originalRawSources":[x["exactRawSource"] for x in spec],
             "sourceConverterSpecs":[x["upstreamSpec"] for x in spec],
             "providerFromSpec":p,"licenseEvidenceStatus":license_status,
             "exactCreditsRow":credit,"sourceLiteralUses":refs.get(path,[]),
             "npcConsumers":npc_reverse.get(path,[])[:25],
             "ownedV7FilenameCandidates":src_candidate,"nextAction":next_action}
        rows.append(row);status[next_action]+=1;licences[license_status]+=1
        for cat in row["categories"]:roles[cat]+=1
    OUT.mkdir(parents=True,exist_ok=True)
    def csvout(filename,content,fields):
        with (OUT/filename).open("w",encoding="utf8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            for row in content:
                writer.writerow({k:json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(list,dict))
                                 else row.get(k) for k in fields})
    csvout("P30_ALL_MEDIA_AND_USAGE.csv",rows,list(rows[0]))
    csvout("P30_EVERY_NPC_AND_VISUAL.csv",npc,list(npc[0]))
    csvout("P30_SIM_NPC_MOBS_ITEMS_LOOT_QUESTS.csv",sim_records,
           list(sim_records[0]) if sim_records else ["kind","sourceModule","id"])
    csvout("P30_EVERY_SOURCE_SYSTEM.csv",
           [{"category":game_source_categories(name),
             "codePath":name,"stageSourcePresent":(STAGE/name).is_file(),"bytes":size}
            for name,size in source_files],
           ["category","codePath","stageSourcePresent","bytes"])
    summary={"phase":"HIGHFLY_P30_ONE_MASTER_AUDIT_ORIGINAL_WOC0447",
        "mode":"READ_ONLY","timestampUtc":datetime.now(timezone.utc).isoformat(),
        "allSourcePublicMediaCount":len(originals),
        "sourceMediaPlusKnownRuntimePaths":len(media),
        "knownBrowserFailurePaths":len(historical),
        "conversionSpecDestinations":len(specs),
        "codeFilesInspected":len(source_files),
        "npcIdMappings":static_count,"npcAuthoredLooks":look_count,
        "npcVisualArchetypes":visual_count,"npcRows":len(npc),
        "originalContentEntityRecordsParsed":len(sim_records),
        "originalContentByKind":dict(Counter(x["kind"] for x in sim_records)),
        "npcsWithLiteralSourceCoordinates":sum(
            bool(x["verifiedOriginalStaticCoordinates"]) for x in npc),
        "mobsWithOriginalVisualModel":sum(
            x.get("originalModelUrl") is not None for x in sim_records if x["kind"]=="MONSTERS"),
        "kaykitOwnedV7SourceModels":sum(map(len,kaykit.values())),
        "assetCategories":dict(roles),"assetActionStates":dict(status),
        "licenseEvidenceStates":dict(licences),
        "gameplayChanged":False,"noMediaCopied":True,
        "playableClass":"ONE_UNIVERSAL_HUNTER_ONLY_PLAYER",
        "limitations":[
          "Static source scan cannot resolve dynamic asset URLs or prove all runtime entities loaded.",
          "NPC world position, quest and shop associations may require deeper source/runtime tracing.",
          "Categorization is path/filename evidence, sometimes multiple categories or OTHER.",
          "Manifest maps NPC visual keys, not proof of body visibility, skeletal clips or animation.",
          "Provider credit plus src->out spec is an eligibility lead; unknown media not free under MIT.",
          "No replacement is authorized by filename similarity alone."],
        "outputs":["P30_ALL_MEDIA_AND_USAGE.csv","P30_EVERY_NPC_AND_VISUAL.csv",
                   "P30_SIM_NPC_MOBS_ITEMS_LOOT_QUESTS.csv",
                   "P30_EVERY_SOURCE_SYSTEM.csv","P30_MASTER_SUMMARY.json"]}
    (OUT/"P30_MASTER_SUMMARY.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("[HIGHFLY] P30 MASTER AUDIT: "+json.dumps({
       "mediaInOriginal":len(originals),"assetPathsAudited":len(media),
       "npcRows":len(npc),
       "simulationRecords":len(sim_records),
       "npcsWithCoordinates":summary["npcsWithLiteralSourceCoordinates"],
       "kaykitSourceModels":summary["kaykitOwnedV7SourceModels"],
       "codeFiles":len(source_files),"categories":dict(roles),
       "actions":dict(status),"gameplayChanged":False},ensure_ascii=False))
    print("[HIGHFLY] P30 REPORT DIRECTORY: "+str(OUT))
    return summary
if __name__=="__main__":run()
