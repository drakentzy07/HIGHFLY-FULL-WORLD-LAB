#!/usr/bin/env python3
"""P29 new-world 48 failures and protected actor/VFX safety contract."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p29_actor_skill_vfx_audit as p29

class P29Tests(unittest.TestCase):
    def test_capture_exact_48_paths_and_disjoint_categories(self):
        self.assertEqual(len(p29.FAILURES),48)
        self.assertEqual(len(set(p29.FAILURES)),48)
        self.assertEqual(len(p29.VFX_GLBS),9)
        self.assertEqual(len(p29.VFX_KTX2),4)
        self.assertEqual(sum(len(v) for v in p29.SKINS.values()),33)
        self.assertEqual(len(p29.SKINS),7)

    def test_dummy_is_an_original_animated_rig_not_generic_procedural_cube(self):
        url="/models/creatures/training_dummy.glb"
        self.assertIn(url,p29.PROJECT_ONLY)
        self.assertIn("ANIMATED_RIG",p29.action(url))
        self.assertEqual(p29.classify(url),"TRAINING_DUMMY_RIG")

    def test_legacy_class_skins_cannot_be_misread_as_missing_npc_models(self):
        url="/textures/skins/knight/alt_a.ktx2"
        self.assertEqual(p29.classify(url),"OLD_CLASS_SKIN_VARIANT")
        self.assertNotIn(url,p29.PROJECT_ONLY)
        self.assertIn("DECOUPLE",p29.action(url))

    def test_special_vfx_are_not_copied_as_cc0(self):
        for path in p29.VFX_GLBS:
            self.assertIn(path,p29.PROJECT_ONLY)
            self.assertIn("NAMED_NODE",p29.action(path))

    def test_kxt2_magic_is_checked_not_200_html_fallback(self):
        url="/textures/skins/knight/alt_a.ktx2"
        with TemporaryDirectory() as temp:
            path=Path(temp)/"alt_a.ktx2"
            path.write_text("<!doctype html>spa fallback")
            self.assertFalse(p29.binary_valid(path))
            path.write_bytes(b"\xabKTX 20\xbb\r\n\x1a\n"+b"\0"*32)
            self.assertTrue(p29.binary_valid(path))
    
    def test_actor_glb_file_presence_never_claims_visible_character(self):
        self.assertGreater(len(p29.ACTOR_PROBES),4)
        self.assertIn("npc_modular_warrior",p29.ACTOR_PROBES)
        self.assertIn("npc_visual_dispatch",p29.SIM_PROBES)
        self.assertIn("practice_dummy_simulation",p29.SIM_PROBES)

if __name__=="__main__":
    unittest.main()
