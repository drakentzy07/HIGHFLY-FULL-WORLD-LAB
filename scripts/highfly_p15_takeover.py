#!/usr/bin/env python3
"""HIGHFLY P15 — conservative full-stage takeover orchestration.

Keeps source game's MIT RPG systems and layout, fills missing source code,
installs only strictly matched owned KayKit assets + individually verifiable
third-party CC0/Apache runtime media, stages private HIGHFLY branding, writes
a provenance ledger, audits and builds. NO public publication or playability
claim. The much larger non-matching media roster remains deliberately visible.

Usage:
  python3 scripts/highfly_p15_takeover.py               # plan
  python3 scripts/highfly_p15_takeover.py --apply       # apply + private build
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
ZIP = ROOT / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
REPORT = ROOT / ".workspace/reports/highfly-p15"
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p14_full_migration_audit as p14

# CREDITS.md at the pinned 0.44.7 commit explicitly describes these
# families as redistributable. Entries below are a STRICT positive list.
# Unlisted/restricted media, including project-only art, is excluded.
SAFE_MEDIA_FAMILIES = (
    ("basis/", "Basis Universal KTX2 transcoder", "Apache-2.0",
     ("basis/basis_transcoder.js", "basis/basis_transcoder.wasm")),
    ("textures/terrain/", "Terrain PBR textures", "CC0 1.0",
     ("Grass001", "Ground023", "Rock026", "Rock051", "Rock060",
      "Ground071", "Ground080", "PavingStones046", "Snow010A",
      "Ground054", "Ground095A", "Ground093A", "Rock029",
      "Lava004", "Gravel024", "Rock035")),
    ("textures/structures/", "Surface-detail PBR textures", "CC0 1.0",
     ("Bark012", "Bricks076A", "Bricks076B", "Fabric030",
      "Metal013", "Plaster007")),
    ("textures/structures/", "Worn-metal surface-detail PBR texture", "CC0 1.0",
     ("RustCoarse01",)),
    ("textures/structures/", "Medieval wood surface-detail PBR texture", "CC0 1.0",
     ("MedievalWood",)),
    ("textures/foliage/", "Canopy clump-detail textures", "CC0 1.0",
     ("Moss002",)),
    ("textures/battleground/", "Thornhollow battleground terrain textures", "CC0 1.0",
     (".jpg",)),  # immediate folder ONLY: excludes unlicensed decals
    ("env/", "HDRI environment maps", "CC0 1.0",
     ("kloofendal_48d_partly_cloudy_puresky",
      "belfast_open_field", "kiara_1_dawn", "dikhololo_night")),
)
COPY_MAX_FILE_BYTES = 90_000_000
MAX_IMPORT_BATCHES = 5
SOURCE_CODE_SUFFIXES = p14.CODE_SUFFIXES
# Locally generated audit metadata present in the reference checkout but not
# tracked source code. It is not a runtime asset and must never block takeover.
GENERATED_DIAGNOSTICS_SKIP = frozenset({
    "src/ui/i18n.status.json",
})

# New FIRST-PARTY graphic, not sourced from ClaudeCraft, owned by HIGHFLY.
HIGHFLY_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" width="700" height="220" viewBox="0 0 700 220" role="img" aria-labelledby="t d">
<title id="t">HIGHFLY ORIGIN</title><desc id="d">Original HIGHFLY blue and violet wordmark</desc>
<defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#26d5ff"/><stop offset="1" stop-color="#9164ff"/></linearGradient></defs>
<path d="M95 38 150 19 189 45 159 62 151 85 140 73 126 117 112 84 76 70 125 65Z" fill="url(#g)" opacity=".95"/>
<path d="M82 90 46 146 103 123 135 190 142 127 194 156 168 113 153 127 120 156 103 111Z" fill="none" stroke="url(#g)" stroke-width="7" stroke-linejoin="round"/>
<text x="212" y="115" fill="#f4faff" font-family="Arial,Helvetica,sans-serif" font-size="80" font-weight="800" letter-spacing="7">HIGHFLY</text>
<text x="217" y="167" fill="#71dfff" font-family="Arial,Helvetica,sans-serif" font-size="37" font-weight="500" letter-spacing="17">ORIGIN</text></svg>
"""
# Inline icon, unlike the original source logos, can ship with HIGHFLY.
HIGHFLY_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="24" fill="#090d22"/><path d="M16 78 54 17 70 49 112 27 74 110 53 71Z" fill="#40d6ff" stroke="#9068ff" stroke-width="5" stroke-linejoin="round"/></svg>
"""


def digest(file: Path) -> str:
    sha = hashlib.sha256()
    with file.open("rb") as source:
        for blob in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(blob)
    return sha.hexdigest()


def private(*paths: Path) -> None:
    root = (ROOT / ".workspace").resolve()
    for file in paths:
        if not file.resolve().is_relative_to(root):
            raise RuntimeError("P15_PRIVATE_DIRECTORY_ONLY: " + str(file))


def row_with_credit(credits: str, phrase: str, license_tag: str) -> str:
    for row in credits.splitlines():
        if (row.startswith("|") and phrase in row and license_tag in row
                and ("| Yes |" in row or "| Yes, attribution required |" in row)):
            return row.strip()
    raise RuntimeError("CREDITS_LICENSE_ROW_NOT_VERIFIED: " + phrase)


def allowed_media(original: Path, stage: Path, credits: str) -> list[dict]:
    source = original / "public"
    destination = stage / "public"
    found = []
    for prefix, clue, license_tag, roots in SAFE_MEDIA_FAMILIES:
        evidence = row_with_credit(credits, clue, license_tag)
        folder = source / prefix
        if not folder.is_dir():
            continue
        # Apache transcoders are TWO exact files, never match extra plugins.
        # Terrain and PBR textures require explicitly named source IDs.
        # Battleground CC0 JPEGs only at immediate level, not under decals/.
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise RuntimeError("ORIGINAL_MEDIA_SYMLINK_BLOCKED: " + str(path))
            if not path.is_file():
                continue
            rel = path.relative_to(source).as_posix()
            sub = path.relative_to(folder)
            if prefix == "basis/":
                ok = rel in roots
            elif prefix == "textures/battleground/":
                ok = len(sub.parts) == 1 and path.suffix.lower() == ".jpg"
            else:
                # Match an entire source ID token, not an arbitrary substring.
                # E.g. Rock026_Color.ktx2 is accepted, Rock0260 is not.
                stem = path.stem.lower()
                ok = any(re.search(r"(?<![a-z0-9])" + re.escape(x.lower()) +
                                   r"(?=[^a-z0-9]|$)", stem) for x in roots)
            if not ok:
                continue
            if path.stat().st_size > COPY_MAX_FILE_BYTES:
                raise RuntimeError("APPROVED_MEDIA_OVERSIZE: " + rel)
            target = destination / rel
            if target.is_symlink():
                raise RuntimeError("HIGHFLY_MEDIA_SYMLINK_REJECTED: " + rel)
            if target.exists():
                # Never overwrite independently added HIGHFLY asset.
                continue
            found.append({"src": path, "dest": target, "relative": rel,
                          "license": license_tag, "evidence": evidence})
    return found


def missing_code(original: Path, stage: Path) -> list[dict]:
    info = p14.code_inventory(original, stage)
    result = []
    for relative in info["missingCodeFiles"]:
        if not relative.startswith(("src/", "server/", "data/")):
            raise RuntimeError("P15_UNEXPECTED_MISSING_CODE_PATH: " + relative)
        # Generated i18n status is diagnostic metadata in the reference
        # checkout, not tracked application source. P14 may count it as code
        # based solely on its .json suffix; skip without copying its bytes.
        if relative in GENERATED_DIAGNOSTICS_SKIP:
            continue
        src = original / relative
        dst = stage / relative
        if (src.suffix.lower() not in SOURCE_CODE_SUFFIXES or src.is_symlink()
                or not src.is_file() or src.stat().st_size > 6_000_000
                or dst.exists() or dst.is_symlink()):
            raise RuntimeError("P15_UNSAFE_MIT_CODE: " + relative)
        result.append({"src": src, "dest": dst, "relative": relative})
    return result


def original_license(original: Path) -> str:
    credits_file = original / "CREDITS.md"
    license_file = original / "LICENSE"
    if not credits_file.is_file() or not license_file.is_file():
        raise RuntimeError("SOURCE_LICENSE_REGISTER_MISSING")
    license_text = license_file.read_text(encoding="utf8")
    if "MIT License" not in license_text or "Copyright (c) 2026 Levy Street" not in license_text:
        raise RuntimeError("MIT_LICENSE_SIGNATURE_MISMATCH")
    content = credits_file.read_text(encoding="utf8")
    if not content.startswith("# Asset Credits and Asset Licenses"):
        raise RuntimeError("CREDITS_REGISTER_SIGNATURE_MISMATCH")
    return content


def stage_brand_html(src: str) -> str:
    if "HIGHFLY_P15_BRAND" in src:
        return src
    if "World of ClaudeCraft" not in src or "/worldofclaudecraft-logo.png" not in src:
        raise RuntimeError("HTML_BRANDING_SOURCE_SIGNATURE_MISMATCH")
    src = src.replace("World of ClaudeCraft", "HIGHFLY ORIGIN")
    src = src.replace("World of Claudecraft", "HIGHFLY ORIGIN")
    src = src.replace("content=\"ClaudeCraft\"", "content=\"HIGHFLY\"")
    src = src.replace('src="/worldofclaudecraft-logo.png"',
                      'src="/highfly-private-p15/highfly-logo.svg"')
    src = src.replace('src="/icon-192.png"',
                      'src="/highfly-private-p15/highfly-icon.svg"')
    # Remove SEO that would claim HIGHFLY is the old project's official site.
    src = re.sub(r'<link\b(?=[^>]*\brel="(?:canonical|alternate)")'
                 r'(?=[^>]*worldofclaudecraft\.com)[^>]*>\s*', "", src,
                 flags=re.IGNORECASE)
    src = re.sub(r'<script type="application/ld\+json">.*?</script>', "", src,
                 flags=re.DOTALL)
    src = re.sub(r'<meta\b(?=[^>]*(?:og:url|og:image|twitter:image))'
                 r'(?=[^>]*worldofclaudecraft\.com)[^>]*>\s*', "", src,
                 flags=re.IGNORECASE)
    # Original outbound project promotional links remain in copied HTML and
    # must be removed during final HIGHFLY UI rewrite; do not imply release ready.
    src = src.replace("</head>", "  <!-- HIGHFLY_P15_BRAND: private first-party logo / title; original UI remains under migration -->\n</head>", 1)
    return src


def prepare(original: Path, stage: Path, archive: Path, out: Path) -> dict:
    private(original, stage, archive, out)
    p9.preflight(original, stage, p9.REPORT)
    p12.validate(original, stage, archive, out)
    credits = original_license(original)
    code = missing_code(original, stage)
    media = allowed_media(original, stage, credits)
    docs = []
    for name in ("index.html", "play.html"):
        path = stage / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("ORIGINAL_HTML_ENTRY_MISSING: " + name)
        s = path.read_text(encoding="utf8")
        docs.append((path, s, stage_brand_html(s)))
    with __import__("zipfile").ZipFile(archive) as z:
        index = p12.index_models(p12.zip_members(z))
    avail = p12.source_manifest(original, stage, index)
    skipped_generated = sorted(set(p14.code_inventory(original, stage)["missingCodeFiles"])
                               & GENERATED_DIAGNOSTICS_SKIP)
    return {"code": code, "approvedMedia": media, "html": docs,
            "skippedGeneratedDiagnostics": skipped_generated,
            "remainingExactKayKitModels": len(avail["exactMatches"]),
            "unmatchedModelCount": sum(v for k, v in avail["statuses"].items()
                                       if k != "EXACT_SOURCE_NAME")}


def save_safe(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        raise RuntimeError("P15_TARGET_ALREADY_EXISTS: " + str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Copy-only, source/target safety enforced above.
    shutil.copy2(src, dst)


def apply(original: Path = ORIGINAL, stage: Path = STAGE,
          archive: Path = ZIP, out: Path = REPORT,
          include_models: bool = True, run_build: bool = True) -> dict:
    plan = prepare(original, stage, archive, out)
    out.mkdir(parents=True, exist_ok=True)
    audit_before = p14.audit(original, stage, archive, out / "before")
    copied_code = []
    copied_media = []
    for row in plan["code"]:
        save_safe(row["src"], row["dest"])
        copied_code.append({"path": row["relative"], "sha256": digest(row["dest"]),
                            "license": "MIT", "source": "pinned MIT game code"})
    # Keep root copyright notice with the preserved code.
    source_license = original / "LICENSE"
    stage_license = stage / "LICENSE"
    if not stage_license.exists():
        save_safe(source_license, stage_license)
    elif digest(stage_license) != digest(source_license):
        # Don't overwrite a potentially separate HIGHFLY-owned license;
        # preserve third-party MIT notice under its own explicit filename.
        notice = stage / "THIRD_PARTY_SOURCE_MIT_LICENSE.txt"
        if not notice.exists():
            save_safe(source_license, notice)
    for row in plan["approvedMedia"]:
        save_safe(row["src"], row["dest"])
        copied_media.append({"path": row["relative"],
                             "sha256": digest(row["dest"]),
                             "license": row["license"],
                             "copyrightEvidence": row["evidence"],
                             "origin": "CC0 / Apache licensed source media registered in pinned CREDITS.md"})
    logo_dir = stage / "public/highfly-private-p15"
    logo_dir.mkdir(parents=True, exist_ok=True)
    for filename, value in (("highfly-logo.svg", HIGHFLY_LOGO),
                            ("highfly-icon.svg", HIGHFLY_ICON)):
        path = logo_dir / filename
        if path.exists() and path.read_text(encoding="utf8") != value:
            raise RuntimeError("HIGHFLY_FIRST_PARTY_BRAND_CONTENT_CONFLICT")
        path.write_text(value, encoding="utf8")
    touched = []
    for path, before, after in plan["html"]:
        if path.read_text(encoding="utf8") != before:
            raise RuntimeError("P15_HTML_MODIFIED_DURING_IMPORT")
        if before != after:
            backup = out / (path.name + ".before")
            if not backup.exists():
                backup.write_text(before, encoding="utf8")
            path.write_text(after, encoding="utf8")
            touched.append(path.name)
    imported_kaykit = []
    if include_models:
        for index in range(MAX_IMPORT_BATCHES):
            import zipfile
            with zipfile.ZipFile(archive, "r") as z:
                idx = p12.index_models(p12.zip_members(z))
            roster = p12.source_manifest(original, stage, idx)
            batch = roster["exactMatches"][:p12.MAX_IMPORTS]
            if not batch:
                break
            added = p12.import_batch(original, stage, out, archive, batch)
            imported_kaykit.extend(added)
            print(f"[HIGHFLY] P15 KAYKIT BATCH {index+1}: imported={len(added)}; "
                  f"remainingApprox={max(0, len(roster['exactMatches']) - len(added))}", flush=True)
    after = p14.audit(original, stage, archive, out / "after")
    result = {
        "phase": "P15_HIGHFLY_OWNERSHIP_MIGRATION",
        "sourceGame": "world-of-claudecraft-v0.44.7",
        "codeLicense": "MIT; copyright notice retained",
        "gameplayVerified": False, "releaseApproved": False,
        "originalReferenceModified": False,
        "simRpgCorePreserved": after["coreRpgCodeIdentical"],
        "codeFilesRecovered": copied_code,
        "skippedGeneratedDiagnostics": plan["skippedGeneratedDiagnostics"],
        "approvedSourceMediaRecovered": copied_media,
        "ownedKayKitModelsAdded": imported_kaykit,
        "privateBrandedEntries": touched,
        "firstPartyBrand": ["/highfly-private-p15/highfly-logo.svg",
                            "/highfly-private-p15/highfly-icon.svg"],
        "fullCodeMissingBefore": len(audit_before["code"]["missingCodeFiles"]),
        "fullCodeMissingAfter": len(after["code"]["missingCodeFiles"]),
        "unresolvedMediaReferences": after["media"]["literalReferencesUnresolved"],
        "unmatchedOrAmbiguousModels": after["ownedKayKitWorld"]["modelMatchingStatuses"],
        "onlineOriginalFeaturesStillInCode": True,
        "hunterUniversalComplete": False,
        "nativeS23UltraHudComplete": False,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "note": "This is a conservative integration step, NOT full independence from legacy visual/game design nor proof of playable world.",
    }
    build = p9.smoke(original, stage, p9.REPORT) if run_build else None
    if build is not None:
        result["viteBuild"] = {"status": build["result"], "exitCode": build["exitCode"]}
    (out / "P15_HIGHFLY_OWNERSHIP.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("[HIGHFLY] P15 MIGRATION RESULT: " + json.dumps({
        "MITSourceRecovered": len(copied_code),
        "licensedCC0OrApacheMediaRecovered": len(copied_media),
        "KayKitOwnedModelsAdded": len(imported_kaykit),
        "remainingLiteralMediaReferences": result["unresolvedMediaReferences"],
        "rpgCodeIntact": result["simRpgCorePreserved"],
        "buildExitCode": result.get("viteBuild", {}).get("exitCode"),
        "gameplayVerified": False, "publicReleaseApproved": False,
    }, ensure_ascii=False))
    if not result["simRpgCorePreserved"]:
        raise SystemExit("P15_PROTECTED_RPG_SOURCE_MISMATCH")
    if build is not None and build["exitCode"] != 0:
        raise SystemExit("P15_PRIVATE_BUILD_FAILED_LOG_AVAILABLE")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-models", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        plan = prepare(ORIGINAL, STAGE, ZIP, REPORT)
        print("[HIGHFLY] P15 PLAN: " + json.dumps({
            "missingMITFiles": len(plan["code"]),
            "skippedGeneratedDiagnostics": plan["skippedGeneratedDiagnostics"],
            "verifiableCC0ApacheMedia": len(plan["approvedMedia"]),
            "remainingExactKayKitModels": plan["remainingExactKayKitModels"],
            "unmatchedOrAmbiguousWorldModels": plan["unmatchedModelCount"],
            "privateBrandingPending": [p.name for p, a, b in plan["html"] if a != b],
            "originalMediaUnlicensedCopied": False,
        }, ensure_ascii=False))
        return
    apply(include_models=not args.no_models, run_build=not args.no_build)


if __name__ == "__main__":
    main()
