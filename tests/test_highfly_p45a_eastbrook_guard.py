import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p45a_eastbrook_guard as p
class Tests(unittest.TestCase):
 def sample(self):
  return (
   "  const buildingGroups: THREE.Object3D[] = [];\n"
   "  for (const building of EASTBROOK_LAYOUT.buildings) {\n"
   "      const built = buildKitBuilding(building, kitTemplate.raw, groundAt);\n"
   "      group.add(built.group);\n"
   "    const built = buildBuilding(building, template, groundAt, atlas);\n"
   "    group.add(built.group);\n"
  )
 def test_modifies_both_and_no_sim(self):
  s=p.patch(self.sample())
  self.assertEqual(s.count("highflyP45CheckBuilding(building, built.group)"),2)
  self.assertIn("measured.y > Math.max(27",s)
  self.assertIn("hf_hide_eastbrook",s)
  self.assertIn("visual.visible = false",s)
 def test_reapplication_safe(self):
  with self.assertRaisesRegex(RuntimeError,"P45_ALREADY_APPLIED"):
   p.patch(p.patch(self.sample()))
 def test_drift_fail(self):
  with self.assertRaisesRegex(RuntimeError,"P45_ANCHOR_DRIFT"):
   p.patch("other")
if __name__=="__main__":unittest.main()
