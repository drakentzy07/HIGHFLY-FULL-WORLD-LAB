import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p50_shell_and_scene_audit as p
class Tests(unittest.TestCase):
 def html(self):
  return "<head><!-- HIGHFLY_P46_OFFICIAL_IDENTITY -->\n<!-- HIGHFLY_P47_UI_LOOT_REAL_EDITOR -->\n<!-- HIGHFLY_P48_FURY_MOBILE --></head>"
 def test_shell_single_image_and_native_loading(self):
  result=p.patch_html(self.html())
  self.assertIn("highfly/p50_shell.css",result)
  self.assertIn("#loading-screen::before",p.CSS)
  self.assertIn("content:none!important",p.CSS)
  self.assertIn("highfly_splash.png",p.CSS)
  self.assertIn("#loading-screen #ls-fill",p.CSS)
  self.assertNotIn("setInterval",p.CSS)
 def test_exact_only_qa_badges(self):
  self.assertIn("HIGHFLY P35",p.JS)
  self.assertIn("HIGHFLY LOG",p.JS)
  self.assertIn("el.children.length>0",p.JS)
  self.assertNotIn("querySelectorAll('*')",p.JS)
 def test_eastbrook_actual_render_roots(self):
  content="  group.userData.wallSegmentCount = EASTBROOK_LAYOUT.wall.segments.length;"
  out=p.patch_town(content)
  self.assertIn("new THREE.Box3().setFromObject(obj)",out)
  self.assertIn("hf_audit_eastbrook",out)
  self.assertIn("COPIAR DIAGNOSTICO",out)
  with self.assertRaisesRegex(RuntimeError,"P50_ALREADY_APPLIED_TOWN"):p.patch_town(out)
 def test_guard_against_double_apply(self):
  with self.assertRaisesRegex(RuntimeError,"P50_ALREADY_APPLIED"):p.patch_html(p.patch_html(self.html()))
 def test_no_touch_save_sim_tutorial(self):
  self.assertNotIn("localStorage.setItem",p.JS)
  self.assertNotIn("p.onGround",p.TOWN_AUDIT)
  self.assertNotIn("world.clear",p.TOWN_AUDIT)
if __name__=="__main__":unittest.main()
