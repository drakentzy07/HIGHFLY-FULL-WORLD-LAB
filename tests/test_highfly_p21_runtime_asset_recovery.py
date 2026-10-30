#!/usr/bin/env python3
"""HIGHFLY P21: run-capture and licensed bulk import guards."""
from __future__ import annotations

from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p21_runtime_asset_recovery as p21


def glb_minimal(file: Path):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(struct.pack("<4sII", b"glTF", 2, 20) + struct.pack("<I4s", 0, b"JSON"))


class P21RuntimeAuditTests(unittest.TestCase):
    def test_rejects_paths_that_escape_or_target_unexpected_roots(self):
        self.assertTrue(p21.safe_asset_path("/models/props/house_1.glb"))
        self.assertTrue(p21.safe_asset_path("/vfx/spark_01.png"))
        self.assertTrue(p21.safe_asset_path("/textures/loading/x.webp"))
        for value in ("/models/props/../private/secret.glb", "https://bad/glb",
                      "/script.js", "/models/props/foo.exe",
                      "/models/props\\a.glb", "/media/bad.glb"):
            self.assertFalse(p21.safe_asset_path(value), value)

    def test_only_verifiable_provider_source_is_cc0(self):
        credits = {x: True for x in p21.CREDIT_AUTHOR}
        self.assertEqual(p21.spec_license(
            "tmp/asset_src/quaternius_nature/extracted/glTF/Pine_1.gltf",
            credits), "CC0_QUATERNIUS")
        self.assertEqual(p21.spec_license(
            "<redacted-local-path> Complete KayKit Collection v5/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/buildings/green/building_castle_green.gltf",
            credits), "CC0_KAYKIT")
        self.assertIsNone(p21.spec_license("tmp/asset_src/generated/proprietary.glb", credits))
        self.assertIsNone(p21.spec_license("/private/source/model.glb", credits))

    def test_provenance_approval_not_inferred_from_naming(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            r = root / "reference"
            s = root / "stage"
            spec = r / "scripts/assets/specs/world.json"
            spec.parent.mkdir(parents=True)
            items = [
                {"out": "models/props/house_1.glb", "src": "tmp/asset_src/quaternius_village/house_1.gltf"},
                {"out": "models/props/owner_statue.glb", "src": "tmp/asset_src/owner_custom/statue.gltf"},
            ]
            spec.write_text(json.dumps({"items": items}))
            upstream = r / "public/models/props/house_1.glb"
            glb_minimal(upstream)
            glb_minimal(r / "public/models/props/owner_statue.glb")
            credits = {x: True for x in p21.CREDIT_AUTHOR}
            index = p21.build_spec_index(r, credits)
            approved = p21.classify("/models/props/house_1.glb", s, r, index)
            unapproved = p21.classify("/models/props/owner_statue.glb", s, r, index)
            self.assertEqual(approved["status"], "EXACT_CC0_IMPORT_READY")
            self.assertEqual(unapproved["status"], "LICENSE_OR_SPEC_REVIEW_REQUIRED")

    def test_stage_not_dist_is_not_misreported_as_missing_media(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            reference = root / "reference"
            glb_minimal(stage / "public/models/props/house_1.glb")
            row = p21.classify("/models/props/house_1.glb", stage, reference, {})
            self.assertEqual(row["status"], "STAGED_BUT_NOT_BUNDLED")
            self.assertTrue(row["sourcePublicExists"])
            self.assertFalse(row["distExists"])

    def test_credit_matching_parenthetical_author(self):
        with tempfile.TemporaryDirectory() as folder:
            r = Path(folder)
            lines = [
                "| Quaternius pack | Quaternius | URL | CC0 1.0 | Yes |",
                "| Kenney pack | Kenney | URL | CC0 1.0 | Yes |",
                "| KayKit characters | Kay Lousberg (KayKit) | URL | CC0 1.0 | Yes |",
                "| ambientCG textures | ambientCG | URL | CC0 1.0 | Yes |",
                "| Poly Haven textures | Poly Haven | URL | CC0 1.0 | Yes |",
            ]
            (r / "CREDITS.md").write_text("\n".join(lines))
            self.assertTrue(all(p21.credits_state(r).values()))


if __name__ == "__main__":
    unittest.main()
