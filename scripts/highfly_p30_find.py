#!/usr/bin/env python3
"""Search P30 master audit by NPC ID, model path, item, mob, quest or source.

Read-only. Examples:
python3 scripts/highfly_p30_find.py brother_halven
python3 scripts/highfly_p30_find.py paladin.glb
python3 scripts/highfly_p30_find.py training_dummy
python3 scripts/highfly_p30_find.py loot --limit 12
"""
from __future__ import annotations
import argparse,csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/".workspace/reports/highfly-p30-master"
FILES=(
  ("NPC","P30_EVERY_NPC_AND_VISUAL.csv"),
  ("SIM","P30_SIM_NPC_MOBS_ITEMS_LOOT_QUESTS.csv"),
  ("ASSET","P30_ALL_MEDIA_AND_USAGE.csv"),
  ("SYSTEM","P30_EVERY_SOURCE_SYSTEM.csv"),
)
def query(q, limit=25):
    needle=q.strip().casefold()
    if not needle:raise ValueError("P30_QUERY_REQUIRED")
    if limit<=0 or limit>200:raise ValueError("P30_LIMIT_RANGE_1_TO_200")
    hits=[]
    for group,filename in FILES:
        path=REPORT/filename
        if not path.is_file():
            raise RuntimeError("P30_MASTER_AUDIT_NOT_RUN: "+str(path))
        with path.open("r",encoding="utf8",newline="") as stream:
            for row in csv.DictReader(stream):
                if needle in " ".join(str(v) for v in row.values()).casefold():
                    hits.append({"group":group,"key":(
                        row.get("npcId") or row.get("id") or row.get("asset") or row.get("codePath")),
                        "data":row})
                    if len(hits)>=limit:return hits
    return hits

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("name",help="NPC ID, file, mob, quest, item, VFX or system")
    parser.add_argument("--limit",type=int,default=25)
    args=parser.parse_args()
    results=query(args.name,args.limit)
    print("[HIGHFLY] P30 SEARCH: "+str(args.name)+" -> "+str(len(results))+" matches (max "+str(args.limit)+")")
    for r in results:
        print("  "+r["group"]+" :: "+str(r["key"]))
        for prop in ("displayName","title","positionX","positionZ","modelUrl",
                     "npcOriginalVisualKey","family","sourceModule","nextAction",
                     "providerFromSpec","licenseEvidenceStatus","sourceConverterSpecs"):
            val=r["data"].get(prop)
            if val and val not in ("null","[]","None"):
                print("    "+prop+": "+str(val)[:240])
    return results

if __name__=="__main__":
    main()
