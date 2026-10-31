#!/usr/bin/env python3
"""P31 pilot: verified CC0 Quaternius wolf restore, exact original runtime path.

Default: read-only dry-run. --apply: stage ONE vetted source GLB without
changing ClaudeCraft, NPC/gameplay source, manifests, Git history or public Pages.
No source pack redistribution, no guessed KayKit substitutions, no overwrite.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / '.workspace/claudecraft-v0.44.7'
STAGE = ROOT / '.workspace/highfly-origin-stage-p0'
REPORT = ROOT / '.workspace/reports/highfly-p31-cc0'
PIN = '493c35a108cef6c8aa290e8793107b1cd117886e'
WOLF = 'models/creatures/wolf.glb'
RAW_SOURCE = 'tmp/asset_src/quaternius_creatures/Wolf.glb'
SPEC = 'scripts/assets/specs/characters.json'


def same_pinned_reference(reference: Path) -> bool:
    if not (reference / '.git').is_dir():
        return False
    found = subprocess.check_output(
        ['git', '-C', str(reference), 'rev-parse', 'HEAD'],
        text=True, stderr=subprocess.DEVNULL).strip()
    return found == PIN


def source_has_verified_credits(spec_json: dict, credits_text: str) -> bool:
    matching = [item for item in spec_json.get('items', [])
                if item.get('out') == WOLF]
    # A single exact upstream source, not a filename resemblance or broad CC0 claim.
    if len(matching) != 1 or matching[0].get('src') != RAW_SOURCE:
        return False
    return any(
        line.startswith('|') and 'Animated creatures (wolf,' in line
        and '| Quaternius |' in line and '| CC0 1.0 | Yes |' in line
        for line in credits_text.splitlines()
    )


def glb_size(path: Path) -> int:
    if not path.is_file() or path.is_symlink():
        raise ValueError('P31_SOURCE_FILE_MISSING_OR_LINK')
    size = path.stat().st_size
    if size < 20 or size > 100_000_000:
        raise ValueError('P31_SOURCE_GLB_SIZE_INVALID')
    with path.open('rb') as f:
        magic, version, recorded_size = struct.unpack('<4sII', f.read(12))
    if magic != b'glTF' or version != 2 or recorded_size != size:
        raise ValueError('P31_SOURCE_GLB_HEADER_INVALID')
    return size


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_no_symlink_ancestors(path: Path, root: Path) -> None:
    rel = path.relative_to(root)
    cur = root
    if cur.is_symlink():
        raise ValueError('P31_STAGE_ROOT_SYMLINK')
    for part in rel.parts:
        cur = cur / part
        if cur.is_symlink():
            raise ValueError('P31_TARGET_SYMLINK: ' + str(cur))


def restore_atomically(source: Path, destination: Path) -> None:
    """Create without clobbering a concurrent target, even if it appears mid-copy."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmpname = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,
                                         prefix='.p31-wolf-', suffix='.tmp',
                                         delete=False) as tmp:
            tmpname = Path(tmp.name)
            with source.open('rb') as f:
                shutil.copyfileobj(f, tmp)
        if digest(source) != digest(tmpname):
            raise RuntimeError('P31_TEMP_COPY_HASH_MISMATCH')
        os.link(tmpname, destination)  # fails if already exists; never overwrite
    finally:
        if tmpname is not None:
            tmpname.unlink(missing_ok=True)


def run(apply: bool = False) -> dict:
    if not same_pinned_reference(ORIGINAL):
        raise RuntimeError('P31_ORIGINAL_COMMIT_NOT_PINNED_0447')
    marker = STAGE / 'HIGHFLY_STAGE_STATUS.json'
    if not marker.is_file() or marker.is_symlink():
        raise RuntimeError('P31_STAGE_MARKER_MISSING')
    if json.loads(marker.read_text(encoding='utf8')).get('sourceCommit') != PIN:
        raise RuntimeError('P31_STAGE_ORIGIN_MISMATCH')
    # License + provenance is a strict AND; source model alone is not enough.
    spec = json.loads((ORIGINAL / SPEC).read_text(encoding='utf8'))
    credits = (ORIGINAL / 'CREDITS.md').read_text(encoding='utf8')
    if not source_has_verified_credits(spec, credits):
        raise RuntimeError('P31_WOLF_CC0_PROVENANCE_NOT_CONFIRMED')
    src = ORIGINAL / 'public' / WOLF
    dst = STAGE / 'public' / WOLF
    count = glb_size(src)
    verify_no_symlink_ancestors(dst, STAGE)
    source_hash = digest(src)
    result = 'ELIGIBLE_MISSING_IN_STAGE'
    if dst.exists() or dst.is_symlink():
        glb_size(dst)
        if digest(dst) != source_hash:
            raise RuntimeError('P31_TARGET_EXISTS_DIFFERENT_HASH_NEVER_OVERWRITE')
        result = 'ALREADY_IDENTICAL'
    elif apply:
        restore_atomically(src, dst)
        if glb_size(dst) != count or digest(dst) != source_hash:
            raise RuntimeError('P31_POSTCOPY_CHECK_FAILED')
        result = 'RESTORED_CC0_VERIFIED'
    report = {
        'phase': 'HIGHFLY_P31_QUATERNIUS_CC0_WOLF_PILOT',
        'mode': 'APPLY' if apply else 'DRY_RUN', 'result': result,
        'file': '/' + WOLF, 'provider': 'Quaternius',
        'upstreamSpec': SPEC, 'upstreamRawSource': RAW_SOURCE,
        'licenseSource': 'CREDITS.md Animated creatures (wolf...) | Quaternius | CC0 1.0 | Yes',
        'sourceBytes': count, 'sourceSha256': source_hash,
        'stageSha256': digest(dst) if dst.is_file() else None,
        'gameplayChanged': False, 'otherAssetsChanged': False,
        'timestampUtc': datetime.now(timezone.utc).isoformat(),
        'warning': 'Static restoration does not prove a visible spawned wolf or fully working clips.'
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / 'P31_WOLF_CC0_REUSE.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    print('[HIGHFLY] P31 CC0 WOLF: ' + json.dumps({
        'mode': report['mode'], 'result': result, 'sourceBytes': count,
        'sha256': source_hash, 'target': '/' + WOLF,
        'gameplayChanged': False}, ensure_ascii=False))
    print('[HIGHFLY] P31 REPORT: ' + str(REPORT / 'P31_WOLF_CC0_REUSE.json'))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true',
                        help='Restore exactly one verified Quaternius CC0 wolf GLB into private stage')
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == '__main__':
    main()
