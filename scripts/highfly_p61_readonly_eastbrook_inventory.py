#!/usr/bin/env python3
"""P61 HIGHFLY: AUDITORIA DE EASTBROOK, SIN MODIFICAR FUENTES NI MODELOS.

Compara IDs, modelos y posiciones autorales con el stage privado,
disponibilidad/sha256 de GLB, roles de NPCs y razones del fallback Warrior.
Genera JSON/CSV y un resumen corto. NO ejecuta Vite ni altera el mundo.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
OUT = ROOT / ".workspace/reports/highfly-p61"
PIN = "493c35a108cef6c8aa290e8793107b1cd117886e"
NUM = r"-?\d+(?:\.\d+)?"
BUILD_RE = re.compile(
    r"makeBuilding\(\s*'(?P<id>[^']+)',\s*'(?P<url>[^']+)',"
    r"\s*'(?P<kind>[^']+)',\s*\{\s*x:\s*(?P<x>"+NUM+r"),"
    r"\s*z:\s*(?P<z>"+NUM+r")\s*\},\s*(?P<w>"+NUM+r"),"
    r"\s*(?P<h>"+NUM+r"),\s*(?P<d>"+NUM+r"),"
    r"\s*(?P<rot>"+NUM+r")",
    re.S,
)
STALL_RE = re.compile(
    r"\['(?P<id>eastbrook_market_stall_[^']+)',\s*'(?P<variant>[^']+)',"
    r"\s*\{\s*x:\s*(?P<x>"+NUM+r"),\s*z:\s*(?P<z>"+NUM+r")\s*\},"
    r"\s*(?P<rotation>"+NUM+r")\]",
)
NPC_RE = re.compile(r"makeNpc\(\s*'(?P<id>[^']+)'")
NPC_KEY_RE = re.compile(r"^\s*(?P<id>[a-z][a-z0-9_]+):\s*'(?P<key>npc_[a-z0-9_]+)'", re.M)


def text(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("P61_REQUIRED_SOURCE_MISSING: " + str(path))
    return path.read_text(encoding="utf-8")


def section(source: str, start: str, end: str) -> str:
    if source.count(start) != 1:
        raise RuntimeError("P61_LAYOUT_ANCHOR_BAD: " + start)
    return source.split(start, 1)[1].split(end, 1)[0]


def parse_buildings(layout: str) -> list[dict]:
    block = section(layout, "const BUILDINGS = [", "] as const;")
    rows = []
    for match in BUILD_RE.finditer(block):
        rec = match.groupdict()
        rows.append({"id": rec["id"], "kind": "building", "originalAssetUrl": rec["url"],
                     "role": rec["kind"], "x": float(rec["x"]), "z": float(rec["z"]),
                     "width": float(rec["w"]), "height": float(rec["h"]),
                     "depth": float(rec["d"]), "rotation": float(rec["rot"])})
    if len(rows) < 11:
        raise RuntimeError("P61_EXPECTED_AT_LEAST_11_OFFICIAL_EASTBROOK_BUILDINGS: " + str(len(rows)))
    return rows


def parse_stalls(layout: str) -> list[dict]:
    block = section(layout, "const MARKET_STALL_SPECS = [", "] as const;")
    rows = [{"id": m["id"], "kind": "market_stall",
             "originalAssetUrl": "/models/props/eastbrook_market_stall.glb",
             "role": "market_" + m["variant"], "x": float(m["x"]), "z": float(m["z"]),
             "width": 2.8, "height": 2.7, "depth": 2.2,
             "rotation": float(m["rotation"])}
            for m in STALL_RE.finditer(block)]
    if len(rows) != 2:
        raise RuntimeError("P61_EXPECTED_TWO_MARKET_STALLS: " + str(len(rows)))
    return rows


def scan_npc_calls(block: str) -> list[dict]:
    """Capture balanced call text, not a fragile regex on nested facingToward()."""
    rows = []
    for m in NPC_RE.finditer(block):
        start = m.start()
        pos = block.find("(", start)
        depth = 0
        quote = None
        esc = False
        end = None
        for k in range(pos, len(block)):
            c = block[k]
            if quote:
                if esc: esc = False
                elif c == "\\": esc = True
                elif c == quote: quote = None
            elif c == chr(39) or c == chr(34): quote = c
            elif c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    end = k+1
                    break
        if end is None:raise RuntimeError("P61_UNCLOSED_NPC: " + m["id"])
        call = block[start:end]
        ids = re.findall(r"'([a-z][a-z0-9_]+)'",call)
        rows.append({"id":m["id"],"placementCode":re.sub(r"\s+"," ",call)[:280],
                    "namedAnchorIds":ids[1:], "roleFromCode":None})
    if len(rows) < 10:
        raise RuntimeError("P61_TOO_FEW_NPCS: "+str(len(rows)))
    return rows


def parse_npcs(layout: str) -> list[dict]:
    return scan_npc_calls(section(layout,"const NPCS = [","] as const;"))


def assigned_roles_from_p44(src: str) -> dict[str,str]:
    """Read the explicit P44 ROLES dict as syntax, never run another script."""
    tree = ast.parse(src)
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if any(isinstance(t,ast.Name) and t.id=="ROLES" for t in statement.targets):
                result=ast.literal_eval(statement.value)
                if isinstance(result,dict) and all(isinstance(k,str) and isinstance(v,str)
                    for k,v in result.items()):
                    return result
    raise RuntimeError("P61_P44_ROLES_NOT_FOUND")


def role_from_base(key: str) -> str:
    return {"npc_knight":"knight","npc_reliquary_keeper":"paladin",
            "npc_mage":"mage","npc_aldric":"mage","npc_chronicler":"mage",
            "npc_villager_robed":"mage","npc_smith":"barbarian",
            "npc_edda_reedhand":"druid"}.get(key,"rogue")


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def local_asset_info(url: str) -> dict:
    """No uploads, no redistribution, no automatic license inference."""
    rel=url.lstrip("/")
    if ".." in Path(rel).parts or not rel.endswith(".glb"):
        return {"url":url,"status":"not_a_safe_glb_path"}
    result={"url":url}
    for name,base in (("original",ORIGINAL),("highflyStage",STAGE)):
        f=base/"public"/rel
        valid=f.is_file() and not f.is_symlink()
        result[name]={"present":valid}
        if valid:
            result[name].update(bytes=f.stat().st_size,sha256=digest(f))
    original=result["original"].get("sha256")
    actual=result["highflyStage"].get("sha256")
    result["matchingBytes"]=bool(original and actual and original==actual)
    result["licenseDecision"]="UNKNOWN_NEEDS_PER_ASSET_PROVENANCE"
    return result


def inventory() -> dict:
    original_layout=text(ORIGINAL/"src/sim/eastbrook_layout.ts")
    staged_layout=text(STAGE/"src/sim/eastbrook_layout.ts")
    if original_layout != staged_layout:
        raise RuntimeError("P61_PROTECTED_LAYOUT_DRIFT: do not infer original IDs from modified stage")
    building_rows=parse_buildings(staged_layout)
    stall_rows=parse_stalls(staged_layout)
    npc_rows=parse_npcs(staged_layout)
    p44=text(ROOT/"scripts/highfly_p44_world_visuals.py")
    p37=text(ROOT/"scripts/highfly_p37_npc_cc0_roles.py")
    roles=assigned_roles_from_p44(p44)
    stage_manifest=text(STAGE/"src/render/characters/manifest.ts")
    stage_assets=text(STAGE/"src/render/characters/assets.ts")
    stage_index=text(STAGE/"src/render/characters/index.ts")
    stage_main=text(STAGE/"src/main.ts")
    original_manifest=text(ORIGINAL/"src/render/characters/manifest.ts")
    npc_block=section(original_manifest,"const NPC_KEYS: Record<string, string> = {","};")
    original_mapping={m["id"]:m["key"] for m in NPC_KEY_RE.finditer(npc_block)}
    role_dispatch="HIGHFLY_P37_NPC_CC0_ROLE_RIGS" in stage_manifest
    role_override="HIGHFLY_P44_EASTBROOK_NPCS" in stage_manifest
    preload_source="HIGHFLY_P38_CC0_NPC_PRELOAD" in stage_assets
    preload_main="await preloadHighflyNpcRoleBodies();" in stage_main
    fallback="HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK" in stage_index
    for n in npc_rows:
        base=original_mapping.get(n["id"],"npc_villager")
        role=roles.get(n["id"]) or role_from_base(base)
        # P37 has special case for Brother Aldric, not the default village.
        if n["id"].startswith("brother_aldric"):role="mage"
        n["originalVisualKey"]=base
        n["highflyIntendedRole"]=role if role_dispatch else None
        n["highflyP44IndividualOverride"]=n["id"] in roles and role_override
        n["highflyRoleAsset"]="models/chars/players/"+role+".glb"
        f=STAGE/"public"/n["highflyRoleAsset"]
        n["roleModelAvailable"]=f.is_file() and not f.is_symlink()
        n["visualOutcome"]="NOT_BROWSER_VERIFIED"
        n["possibleWarriorFallback"]=fallback
        n["notes"]="Needs browser actor trace; source mappings do not prove displayed body."
    buildings=building_rows+stall_rows+[
        {"id":"eastbrook_realm_builder_monument","kind":"monument","role":"realm builder",
         "originalAssetUrl":"/models/props/eastbrook_realm_builder_monument.glb",
         "x":-14.75,"z":-102},
        {"id":"eastbrook_weekly_vault","kind":"weekly_vault","role":"vault",
         "originalAssetUrl":"source-defined geometry / inspect renderer",
         "x":21,"z":-119}
    ]
    assets={}
    for b in buildings:
        url=b["originalAssetUrl"]
        if url.endswith(".glb"):
            assets[url]=assets.get(url) or local_asset_info(url)
            b["asset"]=assets[url]
        b["visibleInBrowser"]="NOT_VERIFIED"
        b["collisionChangeAllowed"]=False
        b["licenseDecision"]="REQUIRES_SOURCE_AND_SPEC_VERIFICATION"
    for b in buildings:
        if b["id"]=="eastbrook_market_stall_provisions":
            b["p59ConfirmedHit"]={"sceneRoot":"eastbrookTownRebuild",
                "meshName":"highflyMicro:eastbrook_market_stall_provisions:solid",
                "observedWorldSize":[3.234,2.7,3.036],
                "note":"This proves which object was hit, NOT which bytes its renderer loaded."}
    present={role:(STAGE/"public/models/chars/players"/(role+".glb")).is_file()
             for role in ("knight","mage","rogue","barbarian","paladin","druid","warrior")}
    return {"phase":"P61_READONLY_EASTBROOK_NPC_BUILDING_AUDIT",
            "mode":"READ_ONLY_REPORT","timestampUtc":datetime.now(timezone.utc).isoformat(),
            "originalPinned":PIN,"referenceLayoutEqualToStage":True,
            "counts":{"officialBuildings":len(building_rows),"marketStalls":len(stall_rows),
                      "enumeratedNpcs":len(npc_rows),"totalInventoryObjects":len(buildings)},
            "npcPipeline":{"p37RoleDispatchInStage":role_dispatch,
               "p44IndividualOverrideInStage":role_override,
               "p38CharacterPreloadInStage":preload_source,
               "p38PreloadCallInStage":preload_main,
               "p36WarriorFallbackInStage":fallback,
               "roleModelExists":present,
               "explanation":"Warrior-looking NPCs can mean fallback after load failure. Source inspection cannot prove actual fallback calls."},
            "buildings":buildings,"npcs":npc_rows,
            "uniqueAssets":list(assets.values()),
            "licenseNotice":"MIT for repository source does not automatically prove licenses of independently sourced GLB/texture files.",
            "gameplayModified":False,"modelsModified":False,"sourcePatched":False}


def write_outputs(data: dict) -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    main=OUT/"P61_EASTBROOK_AUDIT.json"
    main.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    csv_path=OUT/"P61_EASTBROOK_OBJECTS.csv"
    with csv_path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["type","id","role","x","z","sourceGLB","stageGLBpresent",
                    "sameBytesAsOriginal","license","browserVerified"])
        for e in data["buildings"]:
            a=e.get("asset",{})
            w.writerow([e.get("kind"),e.get("id"),e.get("role"),e.get("x"),e.get("z"),
                        e.get("originalAssetUrl"),a.get("highflyStage",{}).get("present"),
                        a.get("matchingBytes"),e["licenseDecision"],e["visibleInBrowser"]])
        for n in data["npcs"]:
            w.writerow(["npc",n["id"],n["highflyIntendedRole"],"", "",n["highflyRoleAsset"],
                        n["roleModelAvailable"],"", "REVERIFY_KAYKIT_SOURCE",n["visualOutcome"]])
    print("[HIGHFLY P61] AUDITORÍA SOLO LECTURA — juego original y stage intactos")
    print("Edificios originales:",data["counts"]["officialBuildings"],
          "| Puestos:",data["counts"]["marketStalls"],
          "| NPC:",data["counts"]["enumeratedNpcs"])
    print("Estado de NPC:",json.dumps(data["npcPipeline"],ensure_ascii=False))
    print("REPORTE JSON:",main)
    print("CATÁLOGO CSV:",csv_path)
    print("No hay run, build, deploy ni modificación del mapa.")


def run() -> None:
    # Check exact origin PIN so a changed upstream copy cannot masquerade as 0.44.7.
    import subprocess
    sha=subprocess.check_output(["git","-C",str(ORIGINAL),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P61_REFERENCE_VERSION_MISMATCH "+sha)
    write_outputs(inventory())


if __name__=="__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
