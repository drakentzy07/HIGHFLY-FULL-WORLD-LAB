"""P43 Android diagnostic: opt-in only, backups, original game/stage untouched."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_p43_diag",ROOT/"scripts/highfly_p43_android_runtime_diag.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class RuntimeDiagTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.base=Path(t.name)
        old={n:getattr(p,n) for n in ['ROOT','WORK','LAB','HTML','TARGET','BACKUP','REPORT']}
        self.addCleanup(lambda: [setattr(p,n,v) for n,v in old.items()])
        p.ROOT=self.base
        p.WORK=self.base/'.workspace'
        p.LAB=p.WORK/'highfly-p43-restore-lab'
        p.HTML=p.LAB/'index.html'
        p.TARGET=p.LAB/'public/highfly_p43_android_diag.js'
        p.BACKUP=p.LAB/'.hf-p43-android-diag-backup-index.html'
        p.REPORT=p.WORK/'reports/highfly-world7/P43_ANDROID_RUNTIME_DIAG_INSTALL.json'
        (p.LAB/'public').mkdir(parents=True)
        p.HTML.write_text('<!doctype html><html><head><title>HIGHFLY</title></head>'
          '<body><div id="server-opt-offline"></div>'
          '<!-- HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES --></body></html>',encoding='utf8')
        self.stage=p.WORK/'highfly-origin-stage-p0'
        self.stage.mkdir()
        (self.stage/'index.html').write_text('UNMODIFIED P64','utf8')

    def test_runtime_diag_has_early_hooks_and_optin(self):
        self.assertIn("has('hf_p43_diag')",p.JS)
        self.assertIn("'unhandledrejection'",p.JS)
        self.assertIn("'error'",p.JS)
        self.assertIn('server-opt-offline',p.JS)
        self.assertIn("navigator.clipboard",p.JS)
        self.assertNotIn('localStorage',p.JS)
        self.assertNotIn('sessionStorage',p.JS)
        self.assertNotIn('fetch(',p.JS)
        self.assertNotIn('requestFullscreen(',p.JS)
        with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as f:
            f.write(p.JS);f.flush()
            res=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
            self.assertEqual(res.returncode,0,res.stderr)

    def test_apply_only_isolated_lab_and_backup(self):
        original=p.HTML.read_text('utf8')
        p.run()
        text=p.HTML.read_text('utf8')
        self.assertIn(p.TAG,text)
        self.assertLess(text.index(p.TAG),text.index('<title>'))
        self.assertEqual(p.BACKUP.read_text('utf8'),original)
        self.assertEqual(p.TARGET.read_text('utf8'),p.JS)
        self.assertEqual((self.stage/'index.html').read_text('utf8'),'UNMODIFIED P64')
        self.assertTrue(p.REPORT.is_file())

    def test_no_repeat_install_or_overwrite(self):
        p.run()
        with self.assertRaisesRegex(RuntimeError,'P43_DIAG_ALREADY_INSTALLED'):
            p.run()

    def test_refuses_missing_expected_marker(self):
        p.HTML.write_text(p.HTML.read_text('utf8').replace(
            'HIGHFLY_P43_RESTORE_NATIVE_9_CLASSES','WRONG_MARK'),encoding='utf8')
        with self.assertRaisesRegex(RuntimeError,'P43_EXPECTED_RECOVERY_MARKER_MISSING'):
            p.run()
        self.assertFalse(p.TARGET.exists())
        self.assertFalse(p.BACKUP.exists())

if __name__=='__main__':unittest.main()
