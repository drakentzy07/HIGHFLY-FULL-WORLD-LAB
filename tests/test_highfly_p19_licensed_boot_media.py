#!/usr/bin/env python3
"""P19 checks: provenance, strict spec allowlist, exact types, never overwrites."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p19_licensed_boot_media as p19


class P19LicenseBootTests(unittest.TestCase):
    def test_credited_license_must_be_redistributable(self):
        credits = (
            "| Stylized Nature MegaKit (trees, rocks, bushes, mushrooms, grass)"
            " | Quaternius | x | CC0 1.0 | Yes |\n"
            "| Nature Kit, Particle Pack (VFX sprites)"
            " | Kenney | x | CC0 1.0 | Yes |\n"
            "| Water normal maps | three.js | x | MIT | Yes, attribution required |\n"
            "| Original logo | ClaudeCraft | x | Project asset | With the project only |\n"
        )
        self.assertTrue(p19.credit_present(credits, p19.FOLIAGE_CREDIT, "CC0 1.0"))
        self.assertTrue(p19.credit_present(credits, p19.PARTICLE_CREDIT, "CC0 1.0"))
        self.assertTrue(p19.credit_present(credits, "Water normal maps", "MIT"))
        self.assertFalse(p19.credit_present(credits, "Original logo", "CC0 1.0"))

    def test_spec_only_from_original_cc0_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / p19.SPEC
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"items": [{
                "src": "tmp/asset_src/quaternius_nature/extracted/glTF/Pine_1.gltf",
                "out": "models/foliage/pine_1.glb"
            }]}))
            self.assertEqual(p19.exact_spec_foliage(root),
                             ["models/foliage/pine_1.glb"])
            target.write_text(json.dumps({"items": [{
                "src": "tmp/asset_src/project-only/Pine_1.gltf",
                "out": "models/foliage/pine_1.glb"
            }]}))
            with self.assertRaises(RuntimeError):
                p19.exact_spec_foliage(root)

    def test_allowlisted_paths(self):
        self.assertTrue(p19.is_path_safe("models/foliage/pine_1.glb", "glb"))
        self.assertTrue(p19.is_path_safe("textures/water/waternormals.jpg", "water"))
        for path in ("models/props/custom.glb", "models/foliage/../props/foo.glb",
                     "models/foliage/a.png", "/models/foliage/pine_1.glb"):
            self.assertFalse(p19.is_path_safe(path, "glb"))

    def test_project_credits_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            ref = Path(directory) / "reference"
            stage = Path(directory) / "stage"
            (ref / "public").mkdir(parents=True)
            (stage / "public").mkdir(parents=True)
            (ref / "CREDITS.md").write_text("| wrong | CC0 1.0 | Yes |")
            with self.assertRaisesRegex(RuntimeError, "CREDIT_UNVERIFIED"):
                p19.plan(ref, stage)


if __name__ == "__main__":
    unittest.main()
