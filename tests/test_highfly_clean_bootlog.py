"""Highfly clean boot diagnostics safety and early CSS checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hfcleanboot",ROOT/"scripts/highfly_clean_bootlog.py")
boot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)

class BootLogTest(unittest.TestCase):
 def test_installs_first_head_script_and_independent_css_then_restores(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td)/".workspace"
   lab=base/"highfly-origin-clean-0447"
   lab.mkdir(parents=True)
   css=lab/"src/styles"
   css.mkdir(parents=True)
   (css/"index.css").write_text("body{background:black}")
   (css/"index.extra.css").write_text("body{margin:0}")
   html=lab/"index.html"
   original='<html>\n<head>\n<title>Original</title>\n</head>\n<body><div id="offline-select"><button data-class="warrior"></button></div></body></html>'
   html.write_text(original)
   with patch.object(boot,"WORK",base),patch.object(boot,"LAB",lab),\
        patch.object(boot,"INDEX",html),patch.object(boot,"BACKUP",lab/".backup"):
    boot.install()
    modified=html.read_text()
    self.assertEqual(modified.count(boot.TAG),2) # marker + inline script comment
    self.assertLess(modified.find('hf-clean-bootlog-bootstrap'),modified.find('<title>'))
    self.assertIn('href="/src/styles/index.css?direct"',modified)
    self.assertIn('href="/src/styles/index.extra.css?direct"',modified)
    self.assertIn('window.__HF_CLEAN_LOG__',modified)
    boot.repair_css()  # repeated repair must be safe
    boot.remove()
    self.assertEqual(html.read_text(),original)

 def test_non_clean_lab_refused(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td)/".workspace"
   with patch.object(boot,"WORK",base),\
        patch.object(boot,"LAB",base/"something-else"):
    with self.assertRaisesRegex(RuntimeError,"ONLY_CLEAN"):
     boot.require_clean()

 def test_url_readout_does_not_include_query_params(self):
  self.assertIn('url.pathname',boot.SCRIPT)
  self.assertNotIn('url.search',boot.SCRIPT)
  self.assertIn("unhandledrejection",boot.SCRIPT)
  self.assertIn("RESOURCE_ERROR",boot.SCRIPT)
  self.assertIn("DESCARGAR LOG",boot.SCRIPT)

if __name__=="__main__":
 unittest.main()
