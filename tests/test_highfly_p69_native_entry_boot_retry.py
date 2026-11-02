"""P69 native entry boot recovery is opt-in and preserves original module tag."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p69_entry_boot",ROOT/"scripts/highfly_p69_native_entry_boot_retry.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class EntryBootRetryTests(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
  old={k:getattr(p,k) for k in ["ROOT","WORK","LAB","HTML","JS","BACKUP","REPORT"]}
  self.addCleanup(lambda: [setattr(p,k,v) for k,v in old.items()])
  p.ROOT=Path(tmp.name);p.WORK=p.ROOT/'.workspace';p.LAB=p.WORK/'highfly-p69-restore-lab'
  p.HTML=p.LAB/'index.html';p.JS=p.LAB/'public/highfly/p69_native_boot_retry.js'
  p.BACKUP=p.LAB/'.hf-p69-before-native-boot-retry.html'
  p.REPORT=p.WORK/'reports/highfly-world7/P69_ENTRY_NATIVE_BOOT_RETRY.json'
  (p.LAB/'src').mkdir(parents=True)
  (p.LAB/'public/highfly').mkdir(parents=True)
  self.html='''<html><head><!-- HIGHFLY_P69_FURY_CORE --><!-- HIGHFLY_P69_NATIVE_LOADER_CLEAN --></head>
<body><div id="server-select"></div><div id="server-opt-offline"></div>
<script type="module" src="/src/main.ts"></script></body></html>'''
  p.HTML.write_text(self.html,encoding='utf8')
  (p.LAB/'src/main.ts').write_text('// HIGHFLY_P69_FURY_CORE\\n// HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES\\n')
  self.p64=p.WORK/'highfly-origin-stage-p0';self.p64.mkdir()
  (self.p64/'index.html').write_text('P64 HTML UNCHANGED')
  self.p43=p.WORK/'highfly-p43-restore-lab';self.p43.mkdir()
  (self.p43/'index.html').write_text('P43 HTML UNCHANGED')
 def test_dry_run_nothing_written(self):
  p.run(False)
  self.assertEqual(p.HTML.read_text(),self.html)
  self.assertFalse(p.JS.exists());self.assertFalse(p.BACKUP.exists())
 def test_apply_only_index_and_new_optin_file(self):
  p.run(True)
  html=p.HTML.read_text()
  self.assertIn(p.MARK,html)
  self.assertEqual(html.count(p.ENTRY),1)
  self.assertEqual(p.BACKUP.read_text(),self.html)
  js=p.JS.read_text()
  self.assertIn("has('hf_p69_boot')",js)
  self.assertIn("await import('/src/main.ts')",js)
  self.assertIn("nativeInitialized",js)
  self.assertIn("REINTENTAR MOTOR",js)
  self.assertNotIn("localStorage",js)
  self.assertNotIn("sessionStorage",js)
  self.assertFalse((p.LAB/'src/main.ts').is_symlink())
  self.assertEqual((self.p64/'index.html').read_text(),'P64 HTML UNCHANGED')
  self.assertEqual((self.p43/'index.html').read_text(),'P43 HTML UNCHANGED')
  self.assertTrue(p.REPORT.exists())
  with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as f:
   f.write(js);f.flush()
   out=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
   self.assertEqual(out.returncode,0,out.stderr)
 def test_preflight_rejects_unexpected_script(self):
  p.HTML.write_text(self.html.replace(p.ENTRY,'<script src="/newgame.js"></script>'))
  with self.assertRaisesRegex(RuntimeError,'NATIVE_MODULE_TAG_DRIFT'):p.run(True)
  self.assertFalse(p.BACKUP.exists())
 def test_preflight_rejects_missing_offline_recovery(self):
  (p.LAB/'src/main.ts').write_text('// HIGHFLY_P69_FURY_CORE')
  with self.assertRaisesRegex(RuntimeError,'NINE_CLASS_OFFLINE_PATCH_NOT_INSTALLED'):p.run(True)
  self.assertFalse(p.JS.exists())
 def test_refuses_overwrite(self):
  p.run(True)
  with self.assertRaisesRegex(RuntimeError,'ALREADY_INSTALLED'):p.run(True)
if __name__=='__main__':unittest.main()
