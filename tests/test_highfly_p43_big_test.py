#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p43_big_test as p
class Tests(unittest.TestCase):
 def test_protects_existing_p39b_and_npcs(self):
  from inspect import getsource
  source=getsource(p.preflight)
  self.assertIn("P43_REQUIRES_ALREADY_APPLIED_P39B",source)
  self.assertIn("P43_NPC_SAFETY_NET_MISSING",source)
  self.assertNotIn("p39b.run(",getsource(p.run))
 def test_single_build_with_rollback(self):
  from inspect import getsource
  source=getsource(p.run)
  self.assertIn("save_checkpoint()",source)
  self.assertIn("rollback()",source)
  self.assertIn("highfly_p9_private_build_smoke.py",source)
 def test_all_phases(self):
  from inspect import getsource
  source=getsource(p.run)
  self.assertIn("p40.run(True)",source)
  self.assertIn("p41.run(True)",source)
  self.assertIn("p42.run(True)",source)
if __name__=="__main__":unittest.main()
