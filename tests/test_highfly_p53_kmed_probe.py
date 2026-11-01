import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p53_kmed_probe as p
class P53Tests(unittest.TestCase):
 def test_exact_anchor(self):
  result=p.patch("HIGHFLY_P52B_GLOBAL_EASTBROOK_GEOMETRY_AUDIT\n"+p.ANCHOR)
  self.assertIn(p.MARK,result)
  with self.assertRaisesRegex(RuntimeError,"P53_ALREADY_APPLIED"):p.patch(result)
 def test_requires_p52b(self):
  with self.assertRaisesRegex(RuntimeError,"P53_REQUIRES_P52B"):p.patch(p.ANCHOR)
 def test_no_mutations_default(self):
  self.assertIn("get('hf_probe_eastbrook_kmed') === 'hide'",p.INSERT)
  self.assertNotIn("localStorage",p.INSERT)
  self.assertNotIn("this.sim.",p.INSERT)
 def test_bounds_and_material(self):
  for token in ("r.material.startsWith('kmed:')","r.z >= -155","r.z <= -68","r.x >= -29","r.x <= 24","r.renderMesh.visible = false"):
   self.assertIn(token,p.INSERT)
 def test_does_not_hide_all_scene(self):
  self.assertIn("candidates.filter",p.INSERT)
  self.assertNotIn("this.scene.visible = false",p.INSERT)
if __name__=="__main__":unittest.main()
