#!/usr/bin/env python3
"""Diagnose packaging of KayKit archive parts safely, without extraction.

Prints archive member names, extensions, byte signatures. If a ZIP contains
another ZIP, optionally indexes its nested members privately (without
extracting models). Never writes to the game tree or GitHub.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

MAX_FILES = 100000
MAX_NESTED_BYTES = 2 * 1024 * 1024 * 1024

def detect(header: bytes) -> str:
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if header.startswith(b"\x1f\x8b"):
        return "gzip"
    if header.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z"
    if header.startswith(b"Rar!\x1a\x07"):
        return "rar"
    if len(header) > 263 and header[257:262] == b"ustar":
        return "tar"
    return "unknown"

def index_archive(archive: zipfile.ZipFile, depth: int, nested: bool, source: str):
    members = archive.infolist()
    if len(members) > MAX_FILES:
        raise ValueError("Archive contains too many entries")
    files = [m for m in members if not m.is_dir()]
    print(f"[HIGHFLY] {source}: {len(members)} entries, {len(files)} files")
    packs = Counter()
    for info in files:
        for part in info.filename.replace("\\", "/").split("/"):
            if part.startswith("KayKit "):
                packs[part] += 1
                break
    if packs:
        print("[HIGHFLY] KayKit pack breakdown:", json.dumps(packs, ensure_ascii=False))
    for info in files[:18]:
        with archive.open(info) as stream:
            header = stream.read(512)
        fmt = detect(header)
        print(json.dumps({
            "name": info.filename, "uncompressed_bytes": info.file_size,
            "compressed_bytes": info.compress_size, "inner_format": fmt
        }, ensure_ascii=False))
        if depth == 0 and nested and fmt == "zip":
            if info.file_size > MAX_NESTED_BYTES:
                print("[HIGHFLY] Skipped nested index: over 2GiB")
                continue
            with tempfile.TemporaryFile() as temp:
                with archive.open(info) as source_stream:
                    shutil.copyfileobj(source_stream, temp, length=2 * 1024 * 1024)
                temp.seek(0)
                try:
                    with zipfile.ZipFile(temp) as inner:
                        index_archive(inner, depth=1, nested=False,
                                      source="nested inside " + info.filename)
                except zipfile.BadZipFile:
                    print("[HIGHFLY] Inner file has ZIP signature but is not a complete ZIP")
    return len(files)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("archives", type=Path, nargs="+")
    p.add_argument("--nested", action="store_true",
                   help="Index nested ZIP, temporarily spools data to disk; does not extract models.")
    args = p.parse_args()
    for archive_file in args.archives:
        if not archive_file.is_file():
            raise FileNotFoundError(archive_file)
        try:
            with zipfile.ZipFile(archive_file) as archive:
                index_archive(archive, depth=0, nested=args.nested,
                              source=archive_file.name)
        except zipfile.BadZipFile:
            print("[HIGHFLY] NOT_A_VALID_ZIP:", archive_file)
            raise
    print("[HIGHFLY] READ-ONLY CHECK COMPLETE: no model extracted or published.")

if __name__ == "__main__":
    main()
