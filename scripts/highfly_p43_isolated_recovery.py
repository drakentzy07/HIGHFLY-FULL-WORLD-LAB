#!/usr/bin/env python3
"""HIGHFLY recovery laboratory: compare historic P43 snapshot without touching P64.

Read-only preflight by default. --apply extracts the independently stored
HIGHFLY-P43-BEFORE-P45.tar.gz into a NEW private lab, adds only dev-server
dependencies / current licensed public assets as symlinks, and checks a Vite
build. NEVER mutates the active stage, source checkpoint, original 0.44.7,
game saves or localStorage. No automatic promotion/deployment.

Preview: run node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 4175
from the output lab, then open Codespaces port 4175 privately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/".workspace"
STAGE=WORK/"highfly-origin-stage-p0"
CKPT=WORK/"checkpoints/HIGHFLY-P43-BEFORE-P45.tar.gz"
LAB=WORK/"highfly-p43-restore-lab"
REPORT=WORK/"reports/highfly-world7/P43_ISOLATED_RESTORE.json"
NEEDED=("src/main.ts","index.html")
SOURCE_COMMIT="493c35a108cef6c8aa290e8793107b1cd117886e"
MAX_UNPACKED=2_000_000_000
BANNED_TOP={".git","dist",".hf_manual_backup_20261102","node_modules",".vite",".cache"}

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()

def allowed_member(member:tarfile.TarInfo)->tuple[str,...]:
    # Reject special files, unsafe paths, and anything outside known checkpoint
    # roots. Tar member paths always use POSIX separators.
    name=member.name.removeprefix("./")
    pieces=PurePosixPath(name).parts
    if (not pieces or name.startswith("/") or "\\" in name or
            any(p in (".","..","") for p in pieces) or
            pieces[0] not in ("src","index.html","public") or
            (pieces[0]=="public" and pieces!=("public","highfly_p40_icons.js")) or
            (pieces[0]=="index.html" and pieces!=("index.html",)) or
            not (member.isfile() or member.isdir()) or
            member.size<0 or member.size>MAX_UNPACKED):
        raise RuntimeError("P43_UNSAFE_ARCHIVE_MEMBER_"+repr(member.name))
    return pieces

def inspect(*,archive=CKPT,stage=STAGE,lab=LAB,work=WORK):
    for label,p in (("stage",stage),("archive",archive),("lab",lab)):
        if p.is_symlink() or not p.resolve().is_relative_to(work.resolve()):
            raise RuntimeError("P43_UNSAFE_PATH_"+label)
    if not stage.is_dir():raise RuntimeError("P43_ACTIVE_STAGE_MISSING")
    if not archive.is_file():raise RuntimeError("P43_CHECKPOINT_MISSING")
    if lab.exists():raise RuntimeError("P43_LAB_ALREADY_EXISTS_NO_OVERWRITE")
    status=stage/"HIGHFLY_STAGE_STATUS.json"
    if not status.is_file():raise RuntimeError("P43_STAGE_MANIFEST_MISSING")
    info=json.loads(status.read_text("utf8"))
    if info.get("sourceCommit")!=SOURCE_COMMIT:
        raise RuntimeError("P43_ACTIVE_STAGE_UNEXPECTED_SOURCE_COMMIT")
    if info.get("originalPublicMediaCopied") is not False:
        raise RuntimeError("P43_PRIVATE_MEDIA_PROVENANCE_UNEXPECTED")
    nm=stage/"node_modules"
    if not nm.is_dir() or not (nm/"vite/bin/vite.js").is_file():
        raise RuntimeError("P43_NODE_MODULES_MISSING")
    if not (stage/"public").is_dir():
        raise RuntimeError("P43_PUBLIC_ASSETS_MISSING")
    manifest={}
    total=0
    with tarfile.open(archive,"r:gz") as tf:
        for member in tf.getmembers():
            parts=allowed_member(member)
            normalized="/".join(parts)
            if normalized in manifest:
                raise RuntimeError("P43_DUPLICATE_ARCHIVE_MEMBER_"+normalized)
            manifest[normalized]=member
            if member.isfile():total+=member.size
            if total>MAX_UNPACKED:
                raise RuntimeError("P43_ARCHIVE_EXPANDED_TOO_LARGE")
    for rel in NEEDED:
        if rel not in manifest or not manifest[rel].isfile():
            raise RuntimeError("P43_ARCHIVE_MISSING_"+rel)
    if "src" not in manifest:
        raise RuntimeError("P43_ARCHIVE_NO_SRC_ROOT")
    return {"archiveSha256":sha256_file(archive),"members":len(manifest),
            "expandedBytes":total,"items":manifest}

def apply(*,archive=CKPT,stage=STAGE,lab=LAB,report=REPORT,
          work=WORK,build=True,build_runner=None):
    check=inspect(archive=archive,stage=stage,lab=lab,work=work)
    if report.exists() or report.is_symlink():
        raise RuntimeError("P43_REPORT_ALREADY_EXISTS_REVIEW_BEFORE_RETRY")
    lab.mkdir(parents=True,exist_ok=False)
    # Native app build config: copy only small root-level config files.
    # Large private media and existing deps stay in the active stage and are
    # shared read-only by this Vite preview (no duplication or publish).
    copied=[]
    try:
        for p in stage.iterdir():
            if p.name in BANNED_TOP or p.name in ("src","public","index.html"):
                continue
            dest=lab/p.name
            if p.is_symlink():
                # Avoid importing unknown links or public-private surprises.
                continue
            if p.is_file() and p.stat().st_size<=8_000_000:
                shutil.copy2(p,dest);copied.append(p.name)
            elif p.is_dir() and p.name in ("shared","packages","vendor","server"):
                dest.symlink_to(p,target_is_directory=True)
                copied.append(p.name+" (shared read-only source)")
        (lab/"public").symlink_to(stage/"public",target_is_directory=True)
        (lab/"node_modules").symlink_to(stage/"node_modules",target_is_directory=True)
        with tarfile.open(archive,"r:gz") as tf:
            for member in tf:
                pieces=allowed_member(member)
                dest=lab.joinpath(*pieces)
                if member.isdir():
                    dest.mkdir(parents=True,exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    if dest.exists() or dest.is_symlink():
                        raise RuntimeError("P43_DUPLICATE_DEST_"+str(dest))
                    f=tf.extractfile(member)
                    if f is None:raise RuntimeError("P43_ARCHIVE_FILE_UNREADABLE_"+str(dest))
                    with f, dest.open("xb") as out:
                        shutil.copyfileobj(f,out,1024*1024)
                    if dest.stat().st_size!=member.size:
                        raise RuntimeError("P43_ARCHIVE_FILE_SIZE_MISMATCH_"+str(dest))
        # Read back the key files; inspect snapshot provenance so the isolated
        # lab does not quietly use the current contaminated index.html.
        html=(lab/"index.html").read_text("utf8")
        if "HIGHFLY_P46_OFFICIAL_IDENTITY" in html:
            raise RuntimeError("P43_SNAPSHOT_CONTAINS_LATER_P46_UI")
        if "HIGHFLY_P48_FURY_MOBILE" in html:
            raise RuntimeError("P43_SNAPSHOT_CONTAINS_LATER_P48_UI")
        if "HIGHFLY_P64_ENTRY_CLEAN" in html:
            raise RuntimeError("P43_SNAPSHOT_CONTAINS_LATER_P64_UI")
        outcome={"phase":"P43_ISOLATED_SNAPSHOT","result":"SNAPSHOT_EXTRACTED_BROWSER_PENDING",
            "archive":str(archive),"archiveSha256":check["archiveSha256"],
            "sourceRoot":str(lab),"sourceFiles":check["members"],
            "indexSha256":sha256_file(lab/"index.html"),
            "mainSha256":sha256_file(lab/"src/main.ts"),
            "sourceCommit":SOURCE_COMMIT,
            "copiedBuildEntries":copied,
            "activeP64Modified":False,"publicSharedReadOnlyIntended":True,
            "offlineSavesNotMigrated":True,"browserVerified":False,
            "notes":"P43 already includes Hunter-only P42 presentation; focus on entry first.",
            "privatePreviewPort":4175}
        if build:
            if build_runner is None:
                env=os.environ.copy()
                env.update({"VITE_HIGHFLY_P4":"1","VITE_HIGHFLY_OFFLINE_LAB":"1",
                            "NODE_OPTIONS":"--max-old-space-size=4096"})
                cp=subprocess.run(
                    ["node",str(lab/"node_modules/vite/bin/vite.js"),
                     "build","--base=/","--outDir","dist"],
                    cwd=lab,env=env,text=True,capture_output=True,
                    timeout=240,check=False)
                exit_code=cp.returncode
                transcript=(cp.stdout+"\n"+cp.stderr)[-50000:]
            else:
                exit_code,transcript=build_runner(lab)
            report.parent.mkdir(parents=True,exist_ok=True)
            (lab/"P43_BUILD_LOG.txt").write_text(transcript,encoding="utf8")
            outcome["buildExitCode"]=exit_code
            outcome["result"]="BUNDLE_BUILT_BROWSER_PENDING" if exit_code==0 else "BUNDLE_FAILED_REVIEW_LOG"
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(outcome,indent=2,ensure_ascii=False)+"\n","utf8")
        return outcome
    except BaseException:
        # Leave the isolated lab for inspection; do NOT undo or touch stage,
        # and never clear any archive or progress.
        print("[P43 ISOLATED] ERROR: active P64 and checkpoints unchanged; "
              "partial P43 lab retained for inspection.",file=sys.stderr)
        raise

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    if args.apply:
        result=apply()
    else:
        v=inspect()
        result={"phase":"P43_ISOLATED_SNAPSHOT","mode":"DRY_RUN",
            "archiveSha256":v["archiveSha256"],
            "members":v["members"],
            "expandedBytes":v["expandedBytes"],
            "willCreate":str(LAB),"willChangeActiveP64":False,
            "willOverwriteAnything":False,"browserVerified":False}
    print("[HIGHFLY P43 ISOLATED] "+json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
