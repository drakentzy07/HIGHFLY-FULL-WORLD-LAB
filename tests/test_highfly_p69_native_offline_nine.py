"""P69 native offline and nine-class restore: guarded no-touch P64/P43 tests."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p69_offline',ROOT/'scripts/highfly_p69_native_offline_nine.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def html():
 classes=''.join('<button class="mini-class" data-class="'+x+'">'+x+'</button>' for x in p.CLASSES)
 return ('<!doctype html><html><head>\n'
         '<style id="highfly-p42-hunter-styles">#offline-select .mini-class{display:none}</style>\n'
         '<script defer src="/highfly_p42_hunter.js"></script>\n'
         '<style id="highfly-p45-brand-css">.a{display:none}</style>\n'
         '<script defer src="/highfly_p45_branding.js"></script>\n'
         '<link rel="stylesheet" href="/highfly/p47.css" />\n'
         '<script defer src="/highfly/p47.js"></script>\n'
         '<!-- HIGHFLY_P69_FURY_CORE -->\n'
         '<!-- HIGHFLY_P69_NATIVE_LOADER_CLEAN -->\n'
         '</head><body><div id="server-opt-offline"></div>'
         '<div id="charcreate-panel">'+classes+'</div>'
         '<div id="offline-select">'+classes+'</div></body></html>')
def main():
 return """// HIGHFLY_P69_FURY_CORE
// HIGHFLY_P41_OFFLINE_SAVE
function readHighflySave(){}
const btn = handleOfflineSelect;
const offline = 'server-opt-offline';
const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);
function start(){
    applyServerMode('online');
}
"""
class Tests(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
  old={k:getattr(p,k) for k in ('ROOT','WORK','LAB','HTML','MAIN','BACKUP','REPORT')}
  self.addCleanup(lambda: [setattr(p,k,v) for k,v in old.items()])
  p.ROOT=Path(tmp.name);p.WORK=p.ROOT/'.workspace'
  p.LAB=p.WORK/'highfly-p69-restore-lab'
  p.HTML=p.LAB/'index.html';p.MAIN=p.LAB/'src/main.ts'
  p.BACKUP=p.LAB/'.hf-p69-offline-nine-classes-backup'
  p.REPORT=p.WORK/'reports/highfly-world7/P69_NATIVE_OFFLINE_NINE_CLASSES.json'
  p.MAIN.parent.mkdir(parents=True)
  p.HTML.write_text(html(),encoding='utf8')
  p.MAIN.write_text(main(),encoding='utf8')
  p64=p.WORK/'highfly-origin-stage-p0'
  p64.mkdir()
  (p64/'index.html').write_text('P64 ORIGINAL')
  p43=p.WORK/'highfly-p43-restore-lab'
  p43.mkdir()
  (p43/'index.html').write_text('P43 ORIGINAL')
 def test_original_nine_class_markup_and_old_filters_removed(self):
  out,removed=p.edit_html(html())
  self.assertEqual(len(p.CLASSES),9)
  self.assertIn('P42_HUNTER_SCRIPT',removed)
  self.assertIn('P45_HUNTER_STYLE',removed)
  self.assertIn('P47_OVERRIDE_CSS',removed)
  self.assertNotIn('highfly_p42_hunter.js',out)
  self.assertNotIn('highfly_p45_branding.js',out)
  self.assertNotIn('highfly/p47.css',out)
  self.assertIn('id="charcreate-panel"',out)
  self.assertIn('HIGHFLY_P69_NATIVE_LOADER_CLEAN',out)
  self.assertIn('HIGHFLY_P69_FURY_CORE',out)
 def test_dev_mode_only_and_native_online_option_kept(self):
  out=p.edit_main(main())
  self.assertIn('const offlineAvailable = import.meta.env.DEV;',out)
  self.assertIn("applyServerMode(offlineAvailable ? 'offline' : 'online')",out)
  self.assertIn("server-opt-offline",out)
  self.assertIn('HIGHFLY_P69_FURY_CORE',out)
 def test_apply_only_p69_with_backups(self):
  p.run(False)
  self.assertFalse(p.BACKUP.exists())
  p.run(True)
  self.assertEqual((p.BACKUP/'index.html').read_text(),html())
  self.assertEqual((p.BACKUP/'src/main.ts').read_text(),main())
  self.assertIn('HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES',p.HTML.read_text())
  self.assertEqual((p.WORK/'highfly-origin-stage-p0/index.html').read_text(),'P64 ORIGINAL')
  self.assertEqual((p.WORK/'highfly-p43-restore-lab/index.html').read_text(),'P43 ORIGINAL')
  self.assertTrue(p.REPORT.exists())
 def test_no_reapply(self):
  p.run(True)
  with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED_OR_BACKUP_EXISTS'):
   p.run(True)
 def test_missing_class_refused(self):
  p.HTML.write_text(html().replace('data-class="druid"','data-class="unknown"'))
  with self.assertRaisesRegex(RuntimeError,'NATIVE_CONTROL_MISSING_druid'):p.run(True)
  self.assertFalse(p.BACKUP.exists())
 def test_unknown_offline_gate_refused(self):
  p.MAIN.write_text(main().replace('offlineAvailable','offlinePermit'))
  with self.assertRaisesRegex(RuntimeError,'OFFLINE_GATE_DRIFT'):p.run(True)
  self.assertFalse(p.BACKUP.exists())
if __name__=='__main__':unittest.main()
