#!/usr/bin/env python3
"""P37 isolated tests: verify NPC-only visual dispatch and source safety."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p37_npc_cc0_roles as p37

class P37Tests(unittest.TestCase):
    def fixture(self):
        return ("const MOB_KEYS: Record<string, string> = {};\n"
                "const NPC_KEYS: Record<string, string> = {};\n"
                "export function visualKeyFor(e: Entity): string {\n"
                "  if (e.kind === 'player') return 'player_warrior';\n"
                "  if (e.kind === 'mob') return 'mob_bandit';\n"
                "  // npcs — Brother Aldric recurs in every hub under suffixed ids\n"
                "  return NPC_KEYS[e.templateId] ?? 'npc_villager';\n"
                "}\n")
    def test_inserts_native_role_defs_before_dispatch(self):
        s=p37.patch_manifest(self.fixture())
        self.assertEqual(s.count("models/chars/players/"), 6)
        self.assertEqual(s.count("animUrls: []"), 1)  # shared role factory
        self.assertIn("highfly_npc_druid", s)
        self.assertIn("ferryman_odo: 'druid'", s)
        self.assertIn("overseer_pell: 'barbarian'", s)
        self.assertIn("npcBaseKey === 'npc_knight'", s)
        self.assertTrue(s.index("HIGHFLY_P37_NPC_BASES") < s.index("const MOB_KEYS:"))
        self.assertTrue(s.index("if (e.kind === 'player')") < s.index("const tutorialRole"))
        self.assertTrue(s.index("if (e.kind === 'mob')") < s.index("const tutorialRole"))
    def test_rejects_second_install(self):
        with self.assertRaisesRegex(RuntimeError, "P37_ALREADY_APPLIED"):
            p37.patch_manifest(p37.patch_manifest(self.fixture()))
    def test_rejects_source_drift(self):
        with self.assertRaisesRegex(RuntimeError, "P37_MANIFEST_ANCHOR_DRIFT"):
            p37.patch_manifest("bad source")
    def test_explicit_six_models_and_nine_roles(self):
        self.assertEqual(len(p37.MODEL_NAMES), 6)
        self.assertEqual(p37.DEFS.count("models/chars/players/"), 6)
        self.assertIn("quartermaster_finch: 'rogue'", p37.DEFS)
        self.assertIn("tidewarden_nel: 'druid'", p37.DEFS)

if __name__ == "__main__":
    unittest.main()
