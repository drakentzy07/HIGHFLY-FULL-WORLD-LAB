#!/usr/bin/env python3
"""P34 source-transform tests; no private stage or art needed."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p34_fixed_actor_fallback as p34

class Tests(unittest.TestCase):
    index="export function setModularLookProvider(fn:any){\n  modularLookProvider = fn;\n}"
    manifest=("  for (const def of Object.values(VISUALS)) {\n"
        "    if (def.lazyPreload) continue; // fetched on demand, not at boot\n}\n"
        "  if (e.templateId.startsWith('brother_aldric')) return 'npc_aldric';")
    def test_fixed_rigs_and_mage_fallback(self):
        got=p34.prepare(self.index,self.manifest,True,True)
        self.assertEqual(set(got),{p34.INDEX,p34.MANIFEST})
        self.assertIn("modularLookProvider = null;",got[p34.INDEX])
        self.assertIn("if (def.modular) continue;",got[p34.MANIFEST])
        self.assertIn("return 'npc_mage';",got[p34.MANIFEST])
        self.assertIn("mage_classic.glb",got[p34.MANIFEST])
    def test_keep_aldric_if_available(self):
        got=p34.prepare(self.index,self.manifest,True,False)
        self.assertIn("return 'npc_aldric'",got[p34.MANIFEST])
    def test_no_changes_if_modular_available(self):
        self.assertEqual(p34.prepare(self.index,self.manifest,False,False),{})
    def test_refuse_source_drift(self):
        with self.assertRaisesRegex(RuntimeError,"P34_ANCHOR_CHANGED"):
            p34.prepare(self.index,"unknown",True,True)

if __name__=="__main__":unittest.main()
