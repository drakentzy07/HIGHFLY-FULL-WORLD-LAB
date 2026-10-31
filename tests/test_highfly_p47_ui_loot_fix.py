import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p47_ui_loot_fix as p
class P47Tests(unittest.TestCase):
 def fixture(self):return "<head><!-- HIGHFLY_P46_OFFICIAL_IDENTITY --></head>"
 def test_p46_anchor_and_no_double_apply(self):
  changed=p.patched_html(self.fixture())
  self.assertIn("highfly/p47.css",changed)
  self.assertIn("highfly/p47.js",changed)
  with self.assertRaisesRegex(RuntimeError,"P47_ALREADY_APPLIED"):p.patched_html(changed)
 def test_requires_real_p46(self):
  with self.assertRaisesRegex(RuntimeError,"P47_P46_NOT_APPLIED"):
   p.patched_html("<head></head>")
 def test_loading_uses_real_progress(self):
  self.assertIn("#loading-screen #ls-fill",p.CSS)
  self.assertNotIn("setInterval",p.JS)
  self.assertIn("box-shadow:none",p.CSS)
 def test_native_gender_editor_not_fake(self):
  self.assertIn("#offline-appearance",p.JS)
  self.assertIn("ac-tabs",p.JS)
  self.assertNotIn("HOMBRE</button>",p.JS)
 def test_icon_art_fallback_only(self):
  self.assertGreaterEqual(len(p.DRAW),8)
  self.assertIn("addEventListener('error'",p.JS)
  self.assertIn("img.dataset.highflyP47Icon",p.JS)
  for x in p.DRAW.values():self.assertIn("<svg",p.svg(*x))
 def test_no_save_overwrites(self):
  self.assertNotIn("localStorage.setItem",p.JS)
  self.assertNotIn("startOffline",p.JS)
if __name__=="__main__":unittest.main()
