#!/usr/bin/env python3
"""HIGHFLY ORIGIN CLEAN 0.44.7 — pinned native offline RPG, 9 real classes.

One clean integration, not a P64/P74 patch:
  --apply builds a new isolated lab from original pinned MIT source code,
  with ONLY independently credited CC0 from original conversion specs and
  independently hash-recorded USER-OWNED KayKit V7 imports from previous work.
  --purge-0454 deletes the unwanted 0.45.4 checkout ONLY after a separate,
  guarded check (clean git, no active process, no inbound symlinks), with the
  new 0.44.7 clean lab already prepared. Never touches 0.44.7 original.
Default is read-only preflight. Never transfers art into public GitHub.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p21_runtime_asset_recovery as p21
import highfly_p25_source_first_asset_audit as p25
ORIGINAL=ROOT/".workspace/claudecraft-v0.44.7"
LEGACY=ROOT/".workspace/claudecraft-v0.45.4"
STAGE=ROOT/".workspace/highfly-origin-stage-p0"
LAB=ROOT/".workspace/highfly-origin-clean-0447"
TMP=ROOT/".workspace/.highfly-clean-0447-build"
REPORT=ROOT/".workspace/reports/highfly-clean-0447/INSTALL_STATUS.json"
PIN="493c35a108cef6c8aa290e8793107b1cd117886e"
CLASSES=("warrior","paladin","hunter","rogue","priest","shaman","mage","warlock","druid")
CC0_PROVIDERS={"Quaternius","Kenney","ambientCG","Poly Haven","loafbrr"}
ALLOW_SUFFIX={".glb",".png",".jpg",".jpeg",".webp"}
MAX_SINGLE=100_000_000
MAX_TOTAL=1_200_000_000
MAX_FILES=3000
# Actual import receipts are the only way to reuse approved/owned staged files;
# NEVER link stage public as a whole or copy generated P22 placeholders.
RECEIPTS=(
 ("highfly-p12/WORLD_KAYKIT_P12.json","imported","target","sha256","sourceZipMember"),
 ("highfly-p18/P18_EXACT_KAYKIT_IMPORT.json","imported","target","sha256","sourceZipMember"),
 ("highfly-p23/P23_REAL_KAYKIT_VISUAL_TAKEOVER.json","installed","path","newSha256","method"),
 ("highfly-p24/P24_SOURCE_V7_LEGACY_MIGRATION.json","installed","path","sourceV7Sha256","sourceZipMember"),
)
# All source modules stay original; no Hunter Universal, DrakenLAB, FURY overlays.
# Minimal HTML title rename is optional; preserve all native menus for QA.

def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def safe_path(url):
 v=str(url).lstrip("/")
 pp=PurePosixPath(v)
 return (not pp.is_absolute() and ".." not in pp.parts
   and len(pp.parts)>=3 and pp.parts[0] in ("models","textures","vfx","ui")
   and pp.suffix.lower() in ALLOW_SUFFIX
   and re.fullmatch(r"[A-Za-z0-9_./-]+",v) is not None)

def require_file(path,base):
 if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base.resolve()):
  raise RuntimeError("CLEAN0447_UNSAFE_OR_MISSING_FILE "+str(path))
 return path

def require_dir(path,base):
 if path.is_symlink() or not path.is_dir() or not path.resolve().is_relative_to(base.resolve()):
  raise RuntimeError("CLEAN0447_UNSAFE_OR_MISSING_DIR "+str(path))
 return path

def provenance():
 specs=p25.outspec_index(ORIGINAL)
 credits=p25.credited(ORIGINAL)
 selected={}
 reasons=Counter()
 for url,rows in sorted(specs.items()):
  if not safe_path(url):continue
  rel=url.lstrip("/")
  srcs={row.get("exactRawSource") for row in rows}
  providers={row.get("sourceProvider") for row in rows}
  if len(srcs)!=1 or len(providers)!=1:
   reasons["AMBIGUOUS_SOURCE_SPEC"]+=1;continue
  source=next(iter(srcs));provider=next(iter(providers))
  if (provider not in CC0_PROVIDERS or not credits.get(provider,False)
   or not isinstance(source,str) or not source.replace("\\","/").startswith("tmp/asset_src/")):
   reasons["RESTRICTED_UNVERIFIED_OR_KAYKIT_NOT_FROM_OWN_SOURCE"]+=1;continue
  file=ORIGINAL/"public"/rel
  if not file.is_file() or file.is_symlink():
   reasons["NO_PINNED_BINARY"]+=1;continue
  if not p21.check_binary(file,url):
   reasons["INVALID_BINARY"]+=1;continue
  selected[rel]={"source":str(file),"sha256":digest(file),
    "bytes":file.stat().st_size,"provider":provider,"rights":"CC0_1.0_CREDITS_EXACT_SPEC",
    "specPaths":sorted({r["upstreamSpec"] for r in rows})}
 return selected,reasons,credits

def owned_v7_receipts(selected):
 counts=Counter()
 for receipt,field,key,hash_key,source_key in RECEIPTS:
  file=ROOT/".workspace/reports"/receipt
  if not file.is_file() or file.is_symlink():
   counts["RECEIPT_MISSING"]+=1;continue
  try:doc=json.loads(file.read_text("utf8"))
  except (OSError,ValueError):
   counts["RECEIPT_INVALID"]+=1;continue
  if doc.get("mode") not in ("APPLY","BUILD_GREEN_BROWSER_PENDING"):
   counts["RECEIPT_NOT_APPLIED"]+=1;continue
  if doc.get("rollbackPerformed") or doc.get("rollbackPaths"):
   counts["RECEIPT_ROLLED_BACK"]+=1;continue
  rows=doc.get(field,[])
  if not isinstance(rows,list):continue
  for row in rows:
   if not isinstance(row,dict):continue
   url=row.get(key,"")
   if not safe_path(url):
    counts["BAD_RECEIPT_PATH"]+=1;continue
   rel=url.lstrip("/")
   src=row.get(source_key)
   if (receipt.startswith("highfly-p23/") and src!="REPLACE_WITH_OWNED_KAYKIT"):
    counts["NON_OWNED_P23_SKIPPED"]+=1;continue
   if (not isinstance(src,str) or not src or
    (receipt.startswith("highfly-p23/") is False and
     ("kaykit" not in src.casefold() and "assets/gltf" not in src.casefold()))):
    counts["RECEIPT_NOT_OWNED_SOURCE_V7"]+=1;continue
   sha=row.get(hash_key)
   if not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{64}",sha):
    counts["RECEIPT_WITHOUT_SHA256"]+=1;continue
   stage=STAGE/"public"/rel
   if not stage.is_file() or stage.is_symlink() or not p21.check_binary(stage,"/"+rel) or digest(stage)!=sha:
    counts["RECEIPT_FILE_CHANGED_OR_MISSING"]+=1;continue
   candidate={"source":str(stage),"sha256":sha,"bytes":stage.stat().st_size,
    "provider":"USER_OWNED_KAYKIT_V7","rights":"OWN_SOURCE_RECEIPT_HASH_VERIFIED",
    "receipt":receipt}
   old=selected.get(rel)
   if old and old["sha256"]!=candidate["sha256"]:
    # A user-owned source takes precedence over the same original output URL,
    # but make the decision transparent; never overwrite the pinned source.
    counts["OWNED_OVERRIDES_CC0_ORIGINAL_PATH"]+=1
   selected[rel]=candidate
   counts["OWNED_V7_ADDED"]+=1
 return counts

def preflight():
 require_dir(ROOT/".workspace",ROOT/".workspace")
 require_dir(ORIGINAL,ROOT/".workspace")
 require_dir(ORIGINAL/"src",ORIGINAL)
 require_dir(ORIGINAL/"public",ORIGINAL)
 require_dir(ORIGINAL/"scripts",ORIGINAL)
 require_dir(ORIGINAL/"node_modules",ORIGINAL)
 require_file(ORIGINAL/"index.html",ORIGINAL)
 require_file(ORIGINAL/"src/main.ts",ORIGINAL)
 require_file(ORIGINAL/"vite.config.ts",ORIGINAL)
 require_file(ORIGINAL/"LICENSE",ORIGINAL)
 require_file(ORIGINAL/"CREDITS.md",ORIGINAL)
 if not (ORIGINAL/"node_modules/vite/bin/vite.js").is_file():
  raise RuntimeError("CLEAN0447_VITE_NOT_INSTALLED")
 got=subprocess.check_output(["git","-C",str(ORIGINAL),"rev-parse","HEAD"],text=True).strip()
 if got!=PIN:raise RuntimeError("CLEAN0447_WRONG_ORIGINAL_COMMIT "+got)
 if any(p.exists() or p.is_symlink() for p in (LAB,TMP,REPORT)):
  raise RuntimeError("CLEAN0447_OUTPUT_EXISTS_NO_OVERWRITE")
 original_html=(ORIGINAL/"index.html").read_text("utf8")
 original_main=(ORIGINAL/"src/main.ts").read_text("utf8")
 if "HIGHFLY_P69" in original_main or "HIGHFLY_P71" in original_main:
  raise RuntimeError("CLEAN0447_ORIGINAL_SOURCE_IS_CONTAMINATED")
 if "const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);" not in original_main:
  raise RuntimeError("CLEAN0447_NATIVE_OFFLINE_GATE_MISSING")
 if original_main.count("    applyServerMode('online');")!=1:
  raise RuntimeError("CLEAN0447_NATIVE_REALM_DEFAULT_ANCHOR_CHANGED")
 for cls in CLASSES:
  if len(re.findall('data-class="'+cls+'"',original_html))<2:
   raise RuntimeError("CLEAN0447_NATIVE_CLASS_MISSING "+cls)
 selected,blocked,credits=provenance()
 owned_counts=owned_v7_receipts(selected)
 if len(selected)>MAX_FILES or sum(r["bytes"] for r in selected.values())>MAX_TOTAL:
  raise RuntimeError("CLEAN0447_ASSET_IMPORT_BUDGET_EXCEEDED")
 # Invariant: every selected source is pinned original CC0 or user-owned
 # receipt-validated SOURCE V7, no generated geometry or borrowed project art.
 return selected,blocked,credits,owned_counts

def prepare_files(selected,blocked,credits,owned_counts):
 TMP.mkdir(mode=0o700)
 try:
  shutil.copytree(ORIGINAL/"src",TMP/"src",symlinks=False)
  for file in ORIGINAL.iterdir():
   if (not file.is_file() or file.is_symlink() or file.stat().st_size>8_000_000
    or file.name in (".env",".env.local") or file.name.startswith(".env.")):
    continue
   shutil.copy2(file,TMP/file.name)
  # Required build directories are MIT source code reused from the immutable
  # source checkout, not copied from ANY previously patched HIGHFLY stage.
  for name in ("scripts","server","shared","packages","config"):
   src=ORIGINAL/name
   if src.is_dir() and not src.is_symlink():
    (TMP/name).symlink_to(src,target_is_directory=True)
  (TMP/"node_modules").symlink_to(ORIGINAL/"node_modules",target_is_directory=True)
  (TMP/"public").mkdir()
  metadata_count=0
  for source in (ORIGINAL/"public").rglob("*"):
   if not source.is_file() or source.is_symlink():continue
   if source.suffix.lower() not in (".json",".js",".mjs",".css",".html",".txt",".webmanifest"):continue
   if source.stat().st_size>1_000_000:continue
   raw=source.read_bytes()
   if b"data:image/" in raw or b"data:audio/" in raw:continue
   rel=source.relative_to(ORIGINAL/"public")
   target=TMP/"public"/rel
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(raw)
   metadata_count+=1
  # Minimal behavioral change: original Vite mode selects real offline path.
  main=TMP/"src/main.ts"
  old=main.read_text("utf8")
  new=old.replace("    applyServerMode('online');",
    "    applyServerMode(offlineAvailable ? 'offline' : 'online');",1)
  if old==new:raise RuntimeError("CLEAN0447_OFFLINE_DEFAULT_PATCH_FAIL")
  main.write_text(new,encoding="utf8")
  # LICENSE kept, all original NPC identities + sim + Eastbrook positions intact.
  installed=[]
  for rel,entry in selected.items():
   source=Path(entry["source"])
   if not source.is_file() or source.is_symlink() or digest(source)!=entry["sha256"]:
    raise RuntimeError("CLEAN0447_VERIFIED_SOURCE_CHANGED "+rel)
   target=TMP/"public"/rel
   if target.exists() or target.is_symlink():
    raise RuntimeError("CLEAN0447_MEDIA_OVERLAPS_METADATA "+rel)
   target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source,target)
   if digest(target)!=entry["sha256"]:
    raise RuntimeError("CLEAN0447_COPY_VERIFY_FAILED "+rel)
   installed.append({"path":"/"+rel,"sha256":entry["sha256"],
      "licenseEvidence":entry["rights"],"provider":entry["provider"],
      "sourceSpecOrReceipt":entry.get("specPaths",entry.get("receipt"))})
  missing=[]
  actor_paths=(
   "models/chars/players/knight.glb","models/chars/players/mage.glb",
   "models/chars/players/rogue.glb","models/chars/players/barbarian.glb",
   "models/chars/players/paladin.glb","models/chars/players/druid.glb",
   "models/chars/modular/warrior_modular.glb",
   "models/weapons/sword_1handed.glb","models/creatures/wolf.glb"
  )
  for rel in actor_paths:
   src=TMP/"public"/rel
   if not src.is_file():missing.append(rel)
  # If the original source has unauthorized art references they remain unresolved
  # (404) rather than bundling unauthorized assets. This is NOT a shipped build.
  result={"project":"HIGHFLY_ORIGIN_CLEAN_0447",
   "status":"LAB_PREPARED_BROWSER_UNVERIFIED",
   "createdUtc":datetime.now(timezone.utc).isoformat(),
   "baseCommit":PIN,
   "source":"immutable pinned original MIT code + verified CC0 exact converter outputs + owned KayKit V7 receipts",
   "originalNativeNineClassButtons":list(CLASSES),"nativeOfflineDevMode":True,
   "simulationCopiedFromOriginal":True,
   "noHighflyOldSourceOverlays":True,
   "installedMedia":len(installed),"installedMediaByProvider":dict(Counter(r["provider"] for r in installed)),
   "metaFilesCopied":metadata_count,
   "ownedReceiptSummary":dict(owned_counts),"originalExcluded":dict(blocked),
   "criticalActorModelsNotYetPresent":missing,
   "allNpcVisibleConfirmed":False,"allBuildingsCorrectConfirmed":False,
   "worldPlayableConfirmed":False,
   "sourceMediaApprovedForPublicRelease":False,
   "port":4180,
   "notes":[
    "Some critical player and NPC GLBs may still be missing; no fake mesh substituted",
    "Original class models require exact rigs/animation donors; being in HTML does not prove 3D previews",
    "This lab intentionally does NOT inherit any P22 geometry or P64/P74 code patches",
    "Restore missing visuals only from owned SOURCE or independent CC0 provenance",
    "Keep the lab PRIVATE until every asset/dependency is reviewed"
   ],
   "mediaManifest":installed}
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  if REPORT.exists() or REPORT.is_symlink():raise RuntimeError("CLEAN0447_REPORT_ALREADY_EXISTS")
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
  TMP.rename(LAB)
  print("[HIGHFLY CLEAN CREATED] "+json.dumps({
   "lab":str(LAB),"port":4180,
   "nativeClasses":9,"approvedAssets":len(installed),
   "providerCounts":result["installedMediaByProvider"],
   "criticalActorAssetsStillMissing":missing,
   "worldPlayableConfirmed":False,
   "report":str(REPORT),
   "otherVersionsModified":False},ensure_ascii=False,indent=2))
 except BaseException:
  if TMP.is_dir() and not TMP.is_symlink():shutil.rmtree(TMP)
  raise

def find_inbound_symlinks(path):
 base=(ROOT/".workspace")
 inbound=[]
 for here,dirs,files in os.walk(base,followlinks=False):
  parent=Path(here)
  dirs[:]=[d for d in dirs if d not in ("node_modules",".git",".cache","dist")
   and not str(parent/d).startswith(str(path))]
  for name in dirs+files:
   candidate=parent/name
   if candidate.is_symlink():
    try:dest=candidate.resolve()
    except OSError:continue
    if dest==path.resolve() or path.resolve() in dest.parents:
     inbound.append(str(candidate))
     if len(inbound)>30:return inbound
 return inbound

def purge_0454():
 # Explicit user-requested space cleanup, but never delete dirty checkout,
 # current processes, symlinked dependencies, or something not under .workspace.
 if not LAB.is_dir() or LAB.is_symlink() or not (LAB/"src/main.ts").is_file():
  raise RuntimeError("CLEAN0447_LAB_NOT_READY_DO_NOT_PURGE_0454")
 require_dir(LEGACY,ROOT/".workspace")
 if LEGACY.resolve()==ORIGINAL.resolve() or LEGACY.resolve()==LAB.resolve():
  raise RuntimeError("CLEAN0447_PROTECTED_SOURCE_COLLISION")
 if not (LEGACY/".git").exists():
  raise RuntimeError("CLEAN0447_LEGACY_NOT_GIT_CHECKOUT_REVIEW_BEFORE_REMOVAL")
 state=subprocess.run(["git","-C",str(LEGACY),"status","--porcelain","--untracked-files=all"],
   text=True,capture_output=True,timeout=35)
 if state.returncode or state.stdout.strip():
  raise RuntimeError("CLEAN0447_LEGACY_HAS_UNCOMMITTED_OR_UNTRACKED_DATA_DO_NOT_DELETE")
 # Preserve any process still using the old checkout.
 proc=subprocess.run(["ps","-eo","args"],text=True,capture_output=True)
 if proc.returncode==0:
  for line in proc.stdout.splitlines():
   if str(LEGACY) in line and "ps -eo args" not in line:
    raise RuntimeError("CLEAN0447_LEGACY_IN_USE_BY_ACTIVE_PROCESS")
 inbound=find_inbound_symlinks(LEGACY)
 if inbound:raise RuntimeError("CLEAN0447_LEGACY_LINKED_FROM_OTHER_LABS "+repr(inbound[:12]))
 # No wildcard, only the explicitly requested 0.45.4 exact directory.
 size=sum(f.stat().st_size for f in LEGACY.rglob("*") if f.is_file() and not f.is_symlink())
 shutil.rmtree(LEGACY)
 print("[HIGHFLY CLEAN PURGE] deleted unused 0.45.4 checkout only",
       round(size/1024**3,2),"GiB of file data (approx); no other paths touched")

def main():
 a=argparse.ArgumentParser()
 group=a.add_mutually_exclusive_group()
 group.add_argument("--apply",action="store_true")
 group.add_argument("--purge-0454",action="store_true")
 args=a.parse_args()
 if args.purge_0454:
  purge_0454();return
 selected,blocked,credits,owned=preflight()
 print("[HIGHFLY CLEAN PREFLIGHT] "+json.dumps({
  "basePinnedSHA":PIN,"nineNativeClasses":list(CLASSES),
  "verifiedMediaReady":len(selected),
  "providers":dict(Counter(x["provider"] for x in selected.values())),
  "verifiedOwnedReceipts":dict(owned),
  "blockedAssetReasons":dict(blocked),
  "target":str(LAB),"mode":"APPLY" if args.apply else "DRY_RUN",
  "oldStagesUntouched":True,"licenseStatus":"CC0_AND_OWNED_RECEIPTS_ONLY"
 },ensure_ascii=False,indent=2))
 if args.apply:prepare_files(selected,blocked,credits,owned)

if __name__=="__main__":main()
