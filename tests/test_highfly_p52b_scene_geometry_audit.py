import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p52b_scene_geometry_audit as p
class P52BTest(unittest.TestCase):
 def test_once(self):
  s=p.patch(p.ANCHOR)
  self.assertIn(p.MARK,s)
  with self.assertRaisesRegex(RuntimeError,"P52B_ALREADY_APPLIED"):p.patch(s)
 def test_missing_anchor(self):
  with self.assertRaisesRegex(RuntimeError,"P52B_RENDERER_ANCHOR_DRIFT"):p.patch("no eastbrook")
 def test_full_scene_bounds(self):
  self.assertIn("this.scene.traverse",p.TS)
  self.assertIn("bb.setFromObject(mesh)",p.TS)
  self.assertIn("mesh instanceof THREE.InstancedMesh",p.TS)
  self.assertIn("hf_hide_giant",p.TS)
 def test_not_changed_by_default(self):
  self.assertIn("get('hf_audit_giants') === '1'",p.TS)
  self.assertIn("hasProbe",p.TS)
if __name__=="__main__":unittest.main()
