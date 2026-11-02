"""Verify additive real-Chrome ESM diagnostic is safe and reversible."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_browser_esm",ROOT/"scripts/highfly_clean_browser_esm_probe.py")
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class NativeChromeProbeTests(unittest.TestCase):
 def test_inserts_after_early_logger_and_restores_original(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp)/".workspace"
   lab=base/"highfly-origin-clean-0447";lab.mkdir(parents=True)
   html=lab/"index.html"
   original=('<html><head><script id="hf-clean-bootlog-bootstrap">'+probe.boot.TAG+
      '</script></head><body><div id="offline-select">'+
      '<button data-class="warrior"></button></div>'+
      '<script type="module" src="/src/main.ts"></script></body></html>')
   html.write_text(original)
   with patch.object(probe,"LAB",lab),patch.object(probe,"HTML",html),\
        patch.object(probe,"BACKUP",lab/".original"):
    probe.apply()
    edited=html.read_text()
    self.assertIn("PROBAR MOTOR",edited)
    self.assertEqual(edited.count(probe.MARK),1)
    self.assertLess(edited.index('hf-clean-browser-esm-probe'),
     edited.index('src="/src/main.ts"'))
    self.assertIn("await import('/src/main.ts')",edited)
    self.assertIn("BROWSER_MAIN_IMPORT_FAILED",edited)
    probe.apply()
    probe.remove()
    self.assertEqual(html.read_text(),original)
    self.assertFalse((lab/".original").exists())
 def test_no_automatic_game_import(self):
  source=probe.PLUGIN
  self.assertIn("button.addEventListener('click',()=>void run())",source)
  self.assertIn("await import('/src/main.ts')",source)
  self.assertIn("window.__HF_CLEAN_LOG__?.events",source)
  self.assertNotIn("localStorage.setItem",source)
  self.assertNotIn("indexedDB.deleteDatabase",source)

if __name__=="__main__":unittest.main()
