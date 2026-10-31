#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p42_spanish_hunter as p
class TestP42(unittest.TestCase):
 def test_spanish_and_only_hunter(self):
  out=p.patch({
   p.FILES[0]:"let currentLanguage: SupportedLanguage = 'en';",
   p.FILES[1]:"<html><head></head></html>",
  })
  self.assertIn("= 'es'",out[p.FILES[0]])
  self.assertIn('data-class="warrior"',out[p.FILES[1]])
  self.assertIn("HIGHFLY_P42_SINGLE_HUNTER",out[p.FILES[1]])
 def test_no_sim_class_rewrites(self):
  self.assertIn("Cazador universal",p.JS)
  self.assertIn("NPC",p.JS)
 def test_refuses_drift(self):
  with self.assertRaisesRegex(RuntimeError,"P42_ANCHOR_DRIFT"):
   p.patch(dict.fromkeys(p.FILES,"missing"))
if __name__=="__main__":unittest.main()
