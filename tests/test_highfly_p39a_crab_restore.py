#!/usr/bin/env python3
"""P39A: isolated, no project assets required."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p39a_crab_restore as p


class TestP39A(unittest.TestCase):
    def sample(self):
        return {
            p.SOURCES[0]: (
                "const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([\n"
                "  'models/biome/hex_target.glb',\n]);"
            ),
            p.SOURCES[1]: (
                "export async function preloadHighflyNpcRoleBodies(): Promise<void> { return; }"
            ),
            p.SOURCES[2]: (
                "  preloadHighflyNpcRoleBodies,\n"
                "  await preloadHighflyNpcRoleBodies();"
            ),
        }

    def test_three_crab_rig_assets_loaded(self):
        o = p.patch_sources(self.sample())
        for model in p.MODELS:
            self.assertIn(model, o[p.SOURCES[0]])
            self.assertIn(model, o[p.SOURCES[1]])
        self.assertIn("await preloadHighflyCrabAssets();", o[p.SOURCES[2]])
        self.assertIn("await preloadHighflyNpcRoleBodies();", o[p.SOURCES[2]])
        self.assertIn("Promise.allSettled", o[p.SOURCES[1]])

    def test_no_second_apply(self):
        o = p.patch_sources(self.sample())
        with self.assertRaisesRegex(RuntimeError, "P39A_ALREADY_APPLIED"):
            p.patch_sources(o)

    def test_drift_fails_safe(self):
        s = self.sample()
        s[p.SOURCES[0]] = "changed"
        with self.assertRaisesRegex(RuntimeError, "P39A_ANCHOR_CHANGED"):
            p.patch_sources(s)

    def test_original_3_paths_only(self):
        self.assertEqual(len(p.MODELS), 3)
        self.assertEqual(p.MODELS[0], "models/creatures/crabenemy.glb")


if __name__ == "__main__":
    unittest.main()
