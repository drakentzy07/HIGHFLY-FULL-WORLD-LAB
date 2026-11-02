"""P69 native creator layout only; opt-in diagnostic without fake model."""
from pathlib import Path
import importlib.util,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p69_creator',ROOT/'scripts/highfly_p69_creator_native_layout.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def html():
 classes=''.join('<button class="mini-class" data-class="'+x+'">'+x+'</button>' for x in p.CLASSES)
 return ('<!doctype html><html><head><!-- HIGHFLY_P69_NATIVE_LOADER_CLEAN -->\n'
   '</head><body><div id="server-opt-offline"></div>'
   '<div id="offline-select"><div class="char-create">'
   '<input id="char-name" /><div id="offline-appearance"></div>'
   '<div id="offline-preview-container"></div>'
   '<div id="offline-class-details"></div><button id="btn-start-offline"></button>'
   +classes+'</div></div></body></html>')
class CreatorTest(unittest.TestCase):
 def setUp(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
  old={x:getattr(p,x) for x in ('ROOT','WORK','LAB','HTML','MAIN','CSS','DIAG','BACKUP','REPORT')}
  self.addCleanup(lambda:[setattr(p,x,y) for x,y in old.items()])
  p.ROOT=Path(temp.name);p.WORK=p.ROOT/'.workspace'
  p.LAB=p.WORK/'highfly-p69-restore-lab'
  p.HTML=p.LAB/'index.html';p.MAIN=p.LAB/'src/main.ts'
  p.CSS=p.LAB/'public/highfly/p69_native_creator_clean.css'
  p.DIAG=p.LAB/'public/highfly/p69_native_creator_diagnostic.js'
  p.BACKUP=p.LAB/'.hf-p69-native-creator-before.html'
  p.REPORT=p.WORK/'reports/highfly-world7/P69_NATIVE_CREATOR_CLEAN.json'
  p.MAIN.parent.mkdir(parents=True);p.CSS.parent.mkdir(parents=True)
  self.html=html();p.HTML.write_text(self.html)
  p.MAIN.write_text('// HIGHFLY_P69_FURY_CORE HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES')
  active=p.WORK/'highfly-origin-stage-p0';active.mkdir()
  (active/'index.html').write_text('P64 UNTOUCHED')
  historic=p.WORK/'highfly-p43-restore-lab';historic.mkdir()
  (historic/'index.html').write_text('P43 UNTOUCHED')
 def test_refuses_missing_native_controls(self):
  p.HTML.write_text(self.html.replace('id="offline-preview-container"','id="no-preview"'))
  with self.assertRaisesRegex(RuntimeError,'P69_CREATOR_HTML_ANCHOR_DRIFT'):
   p.run(True)
  self.assertFalse(p.BACKUP.exists())
 def test_dry_run_does_not_change_anything(self):
  p.run(False)
  self.assertEqual(p.HTML.read_text(),self.html)
  self.assertFalse(p.CSS.exists())
 def test_apply_creator_only(self):
  p.run(True)
  self.assertEqual(p.BACKUP.read_text(),self.html)
  self.assertEqual((p.WORK/'highfly-origin-stage-p0/index.html').read_text(),'P64 UNTOUCHED')
  self.assertEqual((p.WORK/'highfly-p43-restore-lab/index.html').read_text(),'P43 UNTOUCHED')
  self.assertIn('HIGHFLY_P69_NATIVE_CREATOR_RESTORE',p.HTML.read_text())
  self.assertEqual(p.MAIN.read_text(),'// HIGHFLY_P69_FURY_CORE HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES')
  css=p.CSS.read_text()
  self.assertIn('#offline-select:not([hidden])',css)
  self.assertIn('.mini-class[data-class]',css)
  self.assertIn('offline-class-details',css)
  self.assertNotIn('#loading-screen',css)
  self.assertNotIn('model.glb',css)
  diag=p.DIAG.read_text()
  self.assertIn("has('hf_p69_creator_diag')",diag)
  self.assertIn("querySelectorAll('canvas')",diag)
  self.assertNotIn('localStorage',diag)
  self.assertNotIn('fetch(',diag)
  with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as f:
   f.write(diag);f.flush()
   proc=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr)
  self.assertTrue(p.REPORT.exists())
 def test_reapply_fails_safely(self):
  p.run(True)
  with self.assertRaisesRegex(RuntimeError,'P69_CREATOR_ALREADY_INSTALLED_STOP'):p.run(True)
 def test_legacy_p47_class_hider_does_not_pass(self):
  p.HTML.write_text(self.html.replace('</head>',
    '<link rel="stylesheet" href="/highfly/p47.css" /></head>'))
  with self.assertRaisesRegex(RuntimeError,'P69_CREATOR_LEGACY_FILTER_STILL_ENABLED'):p.run(True)
if __name__=='__main__':unittest.main()
