#!/usr/bin/env python3
"""P39B synthetic tests for safe generalized mob visual repair."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p39b_all_mob_visuals as m

class P39BTests(unittest.TestCase):
    def sample(self):
        return {
          m.SOURCES[0]: (
            "const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([\n"
            "  'models/creatures/crab_ability_anims.glb',\n]);"
          ),
          m.SOURCES[1]: (
            "export function startStreamedCharacterPreloads(): number {return 2;}"
          ),
          m.SOURCES[2]: (
            "import { type AssembleOptions, modularHeadFor } from './assets';\n"
            "export function createCharacterVisual() {\n"
            " try { return {}; } catch (err) {\n"
            "    // HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK: NPC VISUAL ONLY.\n"
            "    return null;\n  }\n}\n"
          ),
        }
    def test_parses_all_mob_keys_and_donors(self):
        sample=(
          "  mob_wolf: {\n"
          "    url: \u0060${CREATURES}/wolf.glb\u0060,\n"
          "    animUrls: [\u0060${CREATURES}/wolf_hit.glb\u0060],\n"
          "  },\n"
          "  mob_crab: {\n"
          "    url: \u0060${CREATURES}/crabenemy.glb\u0060,\n"
          "  },\n"
          "  mob_skeleton: {\n"
          "    url: \u0060models/chars/enemies/skeleton_warrior.glb\u0060,\n"
          "  },\n"
        )
        d=m.mob_visual_dependencies(sample)
        self.assertIn("models/creatures/wolf.glb",d["mob_wolf"])
        self.assertIn("models/creatures/wolf_hit.glb",d["mob_wolf"])
        self.assertIn("models/creatures/crabenemy.glb",d["mob_crab"])
        self.assertIn("models/chars/enemies/skeleton_warrior.glb",d["mob_skeleton"])
    def test_patches_one_pass_and_preserves_p36(self):
        x=m.patch_sources(self.sample(),[
            "models/creatures/wolf.glb",
            "models/creatures/crabenemy.glb",
        ])
        self.assertIn("HIGHFLY_P39B_MOB_CC0_URLS",x[m.SOURCES[1]])
        self.assertIn("ensureHighflyMobVisualAssets(key)",x[m.SOURCES[2]])
        self.assertIn("HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK",x[m.SOURCES[2]])
        self.assertIn("'models/creatures/wolf.glb'",x[m.SOURCES[0]])
    def test_refuses_double_apply(self):
        x=m.patch_sources(self.sample(),["models/creatures/wolf.glb"])
        with self.assertRaisesRegex(RuntimeError,"P39B_ALREADY_APPLIED"):
            m.patch_sources(x,["models/creatures/wolf.glb"])
    def test_refuses_source_drift(self):
        x=self.sample();x[m.SOURCES[2]]="changed"
        with self.assertRaisesRegex(RuntimeError,"P39B_SOURCE_ANCHOR_CHANGED"):
            m.patch_sources(x,["models/creatures/wolf.glb"])

if __name__=="__main__":
    unittest.main()
