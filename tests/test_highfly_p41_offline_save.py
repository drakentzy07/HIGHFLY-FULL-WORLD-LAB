#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p41_offline_save as s
class Tests(unittest.TestCase):
 def test_state_and_export(self):
  for x in ("serializeCharacter(sim.playerId)","window.setInterval(save,15000)",
            "pagehide","localStorage.setItem(KEY,json)","EXPORTAR"):
   self.assertIn(x,s.TS)
 def test_patch_abort_on_source_drift(self):
  with self.assertRaisesRegex(RuntimeError,"P41_ANCHOR_DRIFT"):
   s.patch(dict.fromkeys(s.FILES,"bad"))
if __name__=="__main__":unittest.main()
