#!/usr/bin/env python3
"""Reassemble the two user-owned raw ZIP fragments inside wrapper ZIPs.

World engine target: ClaudeCraft v0.44.7 ONLY.
Input wrappers: KIT_COMPLETO_PARTE_01.zip -> fragmento_01.bin
                KIT_COMPLETO_PARTE_02.zip -> fragmento_02.bin
No media is copied into GitHub, the game source, public/ or dist/.
The reconstructed original stays inside .workspace/ (gitignored).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

EXPECTED = (
    ("KIT_COMPLETO_PARTE_01.zip", "fragmento_01.bin", 367001600),
    ("KIT_COMPLETO_PARTE_02.zip", "fragmento_02.bin", 277472105),
)
ROOT = Path(".workspace/private-imports")
INBOX = ROOT / "inbox"
OUTPUT = ROOT / "KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
REPORT = Path(".workspace/reports/kaykit-v7/FULL_ARCHIVE_RECONSTRUCTION.json")
MAX_INDEX_FILES = 100000
COPY_CHUNK = 2 * 1024 * 1024


def check_private_path(dest: Path) -> None:
    resolved = dest.absolute()
    if ".workspace/private-imports" not in resolved.as_posix():
        raise ValueError("Target must be in ignored .workspace/private-imports")
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Refusing to replace existing target: " + str(dest))


def pack_from_name(filename: str) -> str:
    parts = filename.replace("\\", "/").split("/")
    return next((part for part in parts if part.startswith("KayKit ")), "OTHER")


def safe_archive_name(filename: str) -> bool:
    if not filename or "\\" in filename or "\0" in filename or filename.startswith("/"):
        return False
    if ":" in filename:
        return False
    p = PurePosixPath(filename)
    return not any(part in ("..", ".", "") for part in filename.rstrip("/").split("/")) and not p.is_absolute()


def verify_and_index(filename: Path, verify_crc: bool = False) -> dict:
    with zipfile.ZipFile(filename) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_INDEX_FILES:
            raise ValueError("Unexpected member count in reassembled archive: " + str(len(entries)))
        packs = Counter()
        ext = Counter()
        seen = set()
        unsafe = []
        duplicate = []
        symlinks = []
        packed = 0
        raw = 0
        models = 0
        for m in entries:
            if m.is_dir():
                continue
            if not safe_archive_name(m.filename):
                unsafe.append(m.filename)
            folded = m.filename.casefold()
            if folded in seen:
                duplicate.append(m.filename)
            seen.add(folded)
            if stat.S_IFMT(m.external_attr >> 16) == stat.S_IFLNK:
                symlinks.append(m.filename)
            p = pack_from_name(m.filename)
            packs[p] += 1
            suffix = PurePosixPath(m.filename).suffix.lower()
            ext[suffix] += 1
            if suffix in (".glb", ".gltf", ".fbx", ".obj", ".blend"):
                models += 1
            packed += m.compress_size
            raw += m.file_size
        if unsafe or duplicate or symlinks:
            raise ValueError("Reconstructed archive contains unsafe or duplicate filenames. "
                             + "Unsafe=" + repr(unsafe[:3]) + " duplicate=" + repr(duplicate[:3])
                             + " symlinks=" + repr(symlinks[:3]))
        if verify_crc:
            # Verify every member's uncompressed CRC, without materializing it.
            # This may require decompressing gigabytes; user requests this separately.
            corrupt = archive.testzip()
            if corrupt is not None:
                raise ValueError("CRC or extraction failed for original member: " + corrupt)
        return {
            "archiveFiles": len(entries),
            "modelFiles": models,
            "uncompressedBytesTotal": raw,
            "compressedBytesMembers": packed,
            "packCounts": dict(sorted(packs.items())),
            "extensionCounts": dict(sorted(ext.items())),
            "examples": [m.filename for m in entries if not m.is_dir()][:16],
            "deepCrcVerified": verify_crc,
        }


def reconstruct(parts: tuple[Path, Path], output: Path, report: Path, deep_crc: bool = False):
    check_private_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    fd, tempname = tempfile.mkstemp(prefix=".highfly-reconstruct-", suffix=".zip",
                                   dir=output.parent)
    temp = Path(tempname)
    digest = hashlib.sha256()
    total = 0
    try:
        with os.fdopen(fd, "wb") as out:
            for outer_path, (expected_file, member, size) in zip(parts, EXPECTED):
                if outer_path.name != expected_file:
                    raise ValueError("Wrong fragment order: expected " + expected_file)
                with zipfile.ZipFile(outer_path) as wrapper:
                    members = [i for i in wrapper.infolist() if not i.is_dir()]
                    if len(members) != 1 or members[0].filename != member:
                        raise ValueError("Unexpected wrapper content in " + outer_path.name)
                    if members[0].file_size != size:
                        raise ValueError("Wrong fragment size for " + member)
                    if stat.S_IFMT(members[0].external_attr >> 16) == stat.S_IFLNK:
                        raise ValueError("Wrapper contains a symlink")
                    with wrapper.open(members[0]) as source:
                        copied = 0
                        while True:
                            chunk = source.read(COPY_CHUNK)
                            if not chunk:
                                break
                            out.write(chunk)
                            digest.update(chunk)
                            copied += len(chunk)
                            total += len(chunk)
                        # Python validates the outer wrapper CRC as source reaches EOF.
                        if copied != size:
                            raise ValueError("Fragment size mismatch after copy: " + member)
            out.flush()
            os.fsync(out.fileno())

        if total != sum(row[2] for row in EXPECTED):
            raise ValueError("Reconstructed original byte length mismatch")
        # A valid central directory at the very end proves the concatenated stream
        # is structurally a readable ZIP; does NOT prove each model CRC unless flagged.
        indexed = verify_and_index(temp, verify_crc=deep_crc)
        if not any(name != "OTHER" for name in indexed["packCounts"]):
            raise ValueError("No KayKit pack directory found in rebuilt ZIP; investigate before use")
        check_private_path(output)
        os.replace(temp, output)
        summary = {
            "project": "HIGHFLY ORIGIN",
            "base": "ClaudeCraft v0.44.7",
            "mediaReleaseApproved": False,
            "status": "PRIVATE_USER_KAYKIT_ZIP_REBUILT; NOT EXTRACTED OR PUBLISHED",
            "sourceWrappers": [p.name for p in parts],
            "assembledZip": str(output),
            "assembledBytes": total,
            "sha256": digest.hexdigest(),
            **indexed,
        }
        report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        return summary
    finally:
        if temp.exists():
            temp.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=INBOX)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--deep-crc", action="store_true",
                        help="Read/decompress all internal members to verify every CRC (slower).")
    args = parser.parse_args()
    parts = tuple(args.input_dir / row[0] for row in EXPECTED)
    for p in parts:
        if not p.is_file():
            parser.error("Missing wrapper: " + str(p))
    summary = reconstruct(parts, args.output, args.report, args.deep_crc)
    print("[HIGHFLY] KAYKIT V7 ORIGINAL RECONSTRUCTED AND INDEXED")
    for key in ("assembledZip", "assembledBytes", "sha256", "archiveFiles",
                "modelFiles", "uncompressedBytesTotal", "deepCrcVerified"):
        print(f"  {key}: {summary[key]}")
    print("[HIGHFLY] PACKS:")
    for name, n in sorted(summary["packCounts"].items(), key=lambda x: -x[1]):
        print(f"  {name}: {n} files")
    print("[HIGHFLY] Index report:", args.report)
    print("[HIGHFLY] No models extracted, no game changes, no public upload. License approval remains BLOCKED.")


if __name__ == "__main__":
    main()
