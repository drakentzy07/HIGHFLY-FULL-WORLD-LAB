import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p45c_fury_foundation as p
class Tests(unittest.TestCase):
 def test_four_hit_and_dash_math_contract(self):
  self.assertIn("FURY_COMBO_RESET_MS = 780",p.TS)
  self.assertIn("finisher: next === 4",p.TS)
  self.assertIn("furyDirectionalDash(",p.TS)
  self.assertIn("furyCanUseSkill(",p.TS)
 def test_native_mobile_not_new_joystick(self):
  self.assertIn("#mobile-action-attack",p.CSS)
  self.assertIn("#mobile-jump",p.CSS)
  self.assertNotIn("document.createElement('button')",p.TS)
 def test_not_claiming_full_sim_combat(self):
  self.assertIn("not full integration",p.__doc__)
  self.assertNotIn("sim.applyDamage",p.TS)
if __name__=="__main__":unittest.main()
