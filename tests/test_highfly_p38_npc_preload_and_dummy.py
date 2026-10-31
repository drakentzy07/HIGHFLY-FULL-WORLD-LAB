#!/usr/bin/env python3
"""P38 regression: source anchors, exact CC0 routes and game logic untouched."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p38_npc_preload_and_dummy as p

class TestP38(unittest.TestCase):
    def sample(self):
        return {
            p.FILES[0]: ("export function assetUrl(url: string): string {\n"
                         "  const logical = logicalPath(url);\n  if (import.meta.env.DEV) x\n}\n"),
            p.FILES[1]: "function resolvedGltf(url: string): GLTF { return x; }\n",
            p.FILES[2]: ("  charactersReady,\n  ensureCharacterUrl,\n"
                         "  loadPhaseEnd('assets-ready');\n  const spectateBadge\n"),
            p.FILES[3]: ("HIGHFLY_P37_NPC_BASES\n"
                         "    url: " + chr(96) + '$' + '{CREATURES}/training_dummy.glb' + chr(96) + ',\n'),
        }

    def test_patch_wires_six_cc0_preloads(self):
        got = p.patch_sources(self.sample())
        self.assertIn("HIGHFLY_P38_DIRECT_CC0_MEDIA", got[p.FILES[0]])
        self.assertIn("await preloadHighflyNpcRoleBodies();", got[p.FILES[2]])
        self.assertIn("Promise.allSettled", got[p.FILES[1]])
        self.assertIn("models/biome/hex_target.glb", got[p.FILES[3]])
        for model in p.CHARACTERS:
            self.assertIn("models/chars/players/" + model + ".glb", got[p.FILES[0]])
            self.assertIn("models/chars/players/" + model + ".glb", got[p.FILES[1]])
        self.assertIn("HIGHFLY_P37_NPC_BASES", got[p.FILES[3]])

    def test_custom_highfly_media_resolver_kept(self):
        # Regression for real user Codespaces P38 red:
        # the stage media.ts no longer has the old upstream if (import.meta.env.DEV).
        source = self.sample()
        source[p.FILES[0]] = (
            "export function assetUrl(url: string): string {\n"
            "  const logical = url.replace(/^\\\\/+/, '');\n"
            "  const customMedia = HIGHFLY_OVERRIDES[logical];\n"
            "  return customMedia ?? '/media/' + logical;\n"
            "}\n"
        )
        patched = p.patch_sources(source)[p.FILES[0]]
        self.assertIn("HIGHFLY_P38_DIRECT_CC0_MEDIA.has(highflyP38Logical)", patched)
        self.assertIn("const customMedia = HIGHFLY_OVERRIDES[logical];", patched)
        self.assertLess(patched.index("HIGHFLY_P38_DIRECT_CC0_MEDIA.has("),
                        patched.index("const customMedia ="))

    def test_idempotent_guard(self):
        fixed = p.patch_sources(self.sample())
        with self.assertRaisesRegex(RuntimeError, "P38_ALREADY_APPLIED"):
            p.patch_sources(fixed)

    def test_source_drift_aborts(self):
        source = self.sample()
        source[p.FILES[2]] = "unexpected code"
        with self.assertRaisesRegex(RuntimeError, "P38_SOURCE_ANCHOR_DRIFT"):
            p.patch_sources(source)

if __name__ == "__main__":
    unittest.main()
