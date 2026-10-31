import sys,unittest,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p45d_big_batch as p
class Tests(unittest.TestCase):
 def test_guards(self):
  s=inspect.getsource(p.preflight)
  self.assertIn("P45D_P41_OFFLINE_SAVES_MISSING",s)
  self.assertIn("P45D_P39B_MOB_REPAIR_MISSING",s)
  self.assertIn("already_p44()",s)
 def test_backup_build_rollback(self):
  s=inspect.getsource(p.run)
  for term in ("create_checkpoint()","restore_checkpoint()","clean_newfiles(",
               "p44.run(True)","a.run(True)","b.run(True)","c.run(True)",
               "highfly_p9_private_build_smoke.py"):
   self.assertIn(term,s)
 def test_no_public_deploy(self):
  self.assertNotIn("gh-pages",inspect.getsource(p.run))
if __name__=="__main__":unittest.main()
