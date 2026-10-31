#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p36_npc_visible_fallback as p36

class P36Tests(unittest.TestCase):
    def source(self):
        return ("export function createCharacterVisual(e) {\n"
                "  try { return new CharacterVisual('x'); } catch (err) {\n"
                "    // HIGHFLY_P35_ACTOR_UI\n"
                "    console.error('character visual unavailable, skipping view');\n"
                "    return null;\n  }\n}\n"
                "export function other() { return null; }\n")
    def test_npc_only_and_safe_player_rigs(self):
        text=p36.patched_source(self.source())
        self.assertIn("e.kind === 'npc' && !formKey",text)
        self.assertIn("npc_fixed_fallback_success",text)
        self.assertIn("'player_warrior'",text)
        self.assertIn("export function other() { return null; }",text)
    def test_idempotent_abort(self):
        text=p36.patched_source(self.source())
        with self.assertRaisesRegex(RuntimeError,"P36_ALREADY_APPLIED"):
            p36.patched_source(text)
    def test_requires_p35_and_catches_drift(self):
        with self.assertRaisesRegex(RuntimeError,"REQUIRES_P35"):
            p36.patched_source(self.source().replace("HIGHFLY_P35_ACTOR_UI","NO_P35"))
        with self.assertRaisesRegex(RuntimeError,"ANCHOR_DRIFT"):
            p36.patched_source(self.source().replace("    return null;","    return undefined;"))
if __name__=="__main__":
    unittest.main()
