#!/usr/bin/env python3
"""HIGHFLY KayKit ZIP intake. Default INSPECT ONLY; optional safe private extraction.

Use only with ZIPs the user owns. Never copies output into the public repo or
original ClaudeCraft public/. Source version remains pinned to v0.44.7.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile

MAX_ARCHIVE_ENTRIES = 80000
MAX_MEMBER_BYTES = 400 * 1024 * 1024
MAX_SELECTED_BYTES = 850 * 1024 * 1024
PACKS_DEFAULT = ("KayKit Adventurers 2.0", "KayKit Medieval Hexagon Pack 1.0.1")
MEDIA_TYPES = {".glb", ".gltf", ".bin", ".png", ".jpg", ".jpeg", ".webp",
               ".fbx", ".obj", ".mtl", ".blend", ".wav", ".ogg"}


def canonical_name(name: str) -> str:
    """Reject zip-slip and unsafe Windows/macOS path syntax."""
    name = name.replace("\\", "/")
    p = PurePosixPath(name)
    if (not name or name.startswith("/") or ".." in p.parts or
            ":" in name or "\0" in name or any(c in name for c in "\r\n") or
            any(not part or part == "." for part in name.rstrip("/").split("/"))):
        raise ValueError(f"Unsafe archive entry: {name!r}")
    return str(p)


def get_pack(relative: str) -> str | None:
    parts = PurePosixPath(relative).parts
    return next((p for p in parts if p.startswith("KayKit ") and
                 not p.startswith("KayKit Complete")), None)


def inspect_archive(filename: Path, selected_packs: tuple[str, ...]):
    records = []
    seen = set()
    with zipfile.ZipFile(filename) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("Too many ZIP members")
        for info in members:
            if info.is_dir():
                continue
            name = canonical_name(info.filename)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if kind == stat.S_IFLNK:
                raise ValueError("ZIP symlinks are forbidden: " + name)
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError("Oversized ZIP file: " + name)
            folded = name.casefold()
            if folded in seen:
                raise ValueError("Ambiguous duplicate ZIP filename: " + name)
            seen.add(folded)
            pack = get_pack(name)
            selected = bool(pack and any(pack.casefold() == p.casefold() for p in selected_packs))
            records.append({"name": name, "pack": pack or "OTHER",
                            "selected": selected, "bytes": info.file_size,
                            "extension": PurePosixPath(name).suffix.lower(),
                            "crc32": info.CRC, "archive": str(filename.name)})
    return records


def build_plan(archives, packs):
    files = []
    for archive in archives:
        files.extend(inspect_archive(archive, packs))
    count = collections.Counter(x["pack"] for x in files)
    selected = [x for x in files if x["selected"]]
    total = sum(x["bytes"] for x in selected)
    duplicates = collections.defaultdict(list)
    for item in selected:
        duplicates[item["name"].casefold()].append(item)
    conflicts = [key for key, same in duplicates.items() if
                 len({(x["bytes"], x["crc32"]) for x in same}) != 1]
    if conflicts:
        raise ValueError("Conflicting source copies: " + ", ".join(conflicts[:8]))
    if total > MAX_SELECTED_BYTES:
        raise ValueError("Selected files too large, reduce to one pack")
    return {"project": "HIGHFLY ORIGIN", "sourceGameVersion": "0.44.7",
            "status": "PRIVATE_KAYKIT_ARCHIVE_INSPECTION_NO_RELEASE_APPROVAL",
            "archiveCount": len(archives), "fileCount": len(files),
            "countByPack": dict(count), "selectedPacks": list(packs),
            "selectedFileCount": len(selected), "selectedUncompressedBytes": total,
            "sampleSelected": [x["name"] for x in selected[:40]],
            "files": files}


def safe_extract(archives, plan, destination):
    # Approved only for private ignored workspace; never to git tracked source.
    resolved = destination.resolve()
    if "/.workspace/private-imports/" not in resolved.as_posix() + "/":
        raise ValueError("Destination must be under .workspace/private-imports/")
    chosen = set(plan["selectedPacks"])
    seen = set()
    destination.mkdir(parents=True, exist_ok=True)
    extracted = 0
    for archive_file in archives:
        with zipfile.ZipFile(archive_file) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = canonical_name(info.filename)
                pack = get_pack(name)
                if pack not in chosen:
                    continue
                if name.casefold() in seen:
                    continue
                seen.add(name.casefold())
                target = destination.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() or target.is_symlink():
                    raise FileExistsError("Refusing to overwrite existing file: " + str(target))
                fd, tmp = tempfile.mkstemp(prefix=".highfly-partial-", dir=target.parent)
                try:
                    with os.fdopen(fd, "wb") as dst, archive.open(info) as src:
                        copied = 0
                        while True:
                            chunk = src.read(1 << 20)
                            if not chunk:
                                break
                            copied += len(chunk)
                            if copied > MAX_MEMBER_BYTES:
                                raise ValueError("ZIP extraction exceeded file size limit")
                            dst.write(chunk)
                        if copied != info.file_size:
                            raise ValueError("ZIP extraction mismatched declared size")
                    os.replace(tmp, target)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)
                extracted += 1
    return extracted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--pack", action="append", help="One exact KayKit pack name")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--destination", type=Path,
                        default=Path(".workspace/private-imports/kaykit-v7-selected"))
    args = parser.parse_args()
    packs = tuple(args.pack or PACKS_DEFAULT)
    for archive in args.archives:
        if not archive.is_file() or archive.suffix.lower() != ".zip":
            parser.error("Missing ZIP: " + str(archive))
    plan = build_plan(args.archives, packs)
    print("[HIGHFLY] ZIP library checked:",
          json.dumps({key: val for key, val in plan.items() if key != "files"}, ensure_ascii=False))
    report = args.report or Path(".workspace/reports/kaykit-v7/ZIP_IMPORT_PLAN.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    print("[HIGHFLY] Written metadata report:", report)
    if args.extract:
        if not plan["selectedFileCount"]:
            raise ValueError("No selected KayKit pack files in supplied archive(s). Nothing extracted.")
        n = safe_extract(args.archives, plan, args.destination)
        print("[HIGHFLY] Private pack extracted:", n, "files into", args.destination)
    else:
        print("[HIGHFLY] INSPECTION ONLY. No files extracted, no build changed, no public upload.")


if __name__ == "__main__":
    main()
