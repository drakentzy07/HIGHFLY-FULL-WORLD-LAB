import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p45b_branding as p
class TestP45B(unittest.TestCase):
 def test_loading_logo_and_editor(self):
  t=p.patch_html("<html><head></head><body></body></html>")
  self.assertIn("highfly-origin-splash.svg",t)
  self.assertIn("CAZADOR UNIVERSAL",t)
  self.assertIn("offline-skin-row",t)
  self.assertIn("skin-row click",p.JS)
 def test_own_art_and_no_skill_claim(self):
  self.assertIn("<svg",p.SVG)
  self.assertIn("HIGHFLY",p.SVG)
  self.assertIn("están en desarrollo",p.JS)
 def test_double_patch_guard(self):
  with self.assertRaisesRegex(RuntimeError,"P45B_ALREADY_APPLIED"):
   p.patch_html(p.patch_html("<head></head>"))
if __name__=="__main__":unittest.main()
