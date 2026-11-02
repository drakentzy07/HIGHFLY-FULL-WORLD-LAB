"""Checks for private, rollback-safe HIGHFLY CLEAN offline bundling plan."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_private_bundle",ROOT/"scripts/highfly_clean_private_offline_bundle.py")
bundle=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)

class BundleTest(unittest.TestCase):
 def test_local_gate_mode_and_build_output_scope(self):
  self.assertIn("return isDev || import.meta.env.MODE === 'highfly-clean-private-offline';",bundle.LOCAL)
  self.assertIn(".highfly-private-offline-dist",bundle.CONFIG_BODY)
  self.assertIn("rollupOptions",bundle.CONFIG_BODY)
  self.assertIn("svelte()",bundle.CONFIG_BODY)
  self.assertIn("index.html",bundle.CONFIG_BODY)
  self.assertIn("preview:{host:'0.0.0.0',port:4181",bundle.CONFIG_BODY)
  self.assertNotIn("pages",bundle.CONFIG_BODY.lower())
 def test_preflight_rejects_unknown_stage(self):
  with tempfile.TemporaryDirectory() as td:
   stage=Path(td)/".workspace"/"fake-stage"
   with patch.object(bundle,"STAGE",stage):
    with self.assertRaisesRegex(RuntimeError,"PRIVATE_BUNDLE"):
     bundle.check()
 def test_no_public_publish_or_original_code_mutation(self):
  src=(ROOT/"scripts/highfly_clean_private_offline_bundle.py").read_text("utf8")
  self.assertIn('"publishApproved":False',src)
  self.assertIn('GATE.write_text(old,"utf8")',src)
  self.assertIn('shutil.rmtree(OUT)',src)
  self.assertNotIn("git push",src)

if __name__=="__main__":unittest.main()
