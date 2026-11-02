"""Regression guard: one native real-browser lifetime log, no false license assertions."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def imported(path,key):
 spec=importlib.util.spec_from_file_location(key,ROOT/'scripts'/path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
logger=imported('highfly_clean_unified_lifecycle_log.py','hf_unified_test')

class UnifiedAndRightsTests(unittest.TestCase):
 def test_injected_logger_is_valid_js(self):
  js=logger.SCRIPT.removeprefix('<script id="hf-clean-unified-lifecycle-logger">').removesuffix('</script>')
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'log.js';f.write_text(js,encoding='utf8')
   run=subprocess.run(['node','--check',str(f)],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)
  self.assertIn('XMLHttpRequest',js)
  self.assertIn('fetch',js)
  self.assertIn('WORLD_LOADING_PROGRESS',js)
  self.assertIn('VISIBLE_ASSET_FAILURE',js)
  self.assertIn('USER_EXPORTED_REPORT',js)
  self.assertIn('window.__HF_CLEAN_UNIFIED__',js)
 def test_install_removes_two_old_buttons_and_exact_reversal(self):
  with tempfile.TemporaryDirectory() as d:
   work=Path(d)/'.workspace'
   stage=work/'highfly-origin-clean-0447'
   dist=stage/'.highfly-private-offline-dist'
   dist.mkdir(parents=True)
   html=dist/'index.html'
   original=('<html><head><!-- HIGHFLY_CLEAN_BOOTLOG_V1 -->'+
     '<script id="hf-clean-bootlog-bootstrap">console.log("old")</script>'+
     '<!-- HIGHFLY_CLEAN_BROWSER_ESM_V1 -->'+
     '<script id="hf-clean-browser-esm-probe">console.log("old2")</script>'+
     '</head><body><div id="offline-select"></div>'+
     '<script type="module" src="/assets/main-123.js"></script></body></html>')
   html.write_text(original)
   with patch.object(logger,'WORK',work),patch.object(logger,'STAGE',stage),\
        patch.object(logger,'DIST',dist),patch.object(logger,'INDEX',html),\
        patch.object(logger,'BACKUP',dist/'.bak'):
    logger.apply()
    patched=html.read_text()
    self.assertEqual(patched.count(logger.MARK),1)
    self.assertNotIn('hf-clean-bootlog-bootstrap',patched)
    self.assertNotIn('hf-clean-browser-esm-probe',patched)
    self.assertEqual(patched.count('DESCARGAR LOG'),1)
    logger.apply()
    logger.remove()
    self.assertEqual(html.read_text(),original)
 def test_recovery_and_audit_do_not_whitelist_project_content(self):
  recovery=(ROOT/'scripts/highfly_clean_safe_cc0_recovery_4181.py').read_text()
  media=(ROOT/'scripts/highfly_clean_private_media_license_audit.py').read_text()
  self.assertIn('CREDITS.md',recovery)
  self.assertIn('UNVERIFIED_OR_PROJECT_ASSET',recovery)
  self.assertIn("if rel in explicit:",recovery)
  self.assertIn("if stage.exists() or stage.is_symlink()",recovery)
  self.assertIn("legalGuarantee':False",recovery)
  self.assertIn("publicCommercialReleaseApproved':False",media)
  self.assertIn('MEDIA_MISSING_PROVENANCE_RECEIPT',media)

if __name__=='__main__':unittest.main()
