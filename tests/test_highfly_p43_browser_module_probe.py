"""Safety checks for the opt-in browser main.ts fetch diagnostic."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hf_p43_main_fetch',ROOT/'scripts/highfly_p43_browser_module_probe.py')
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class BrowserModuleProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old={k:getattr(p,k) for k in ('WORK','LAB','JS','BACKUP','REPORT')}
        self.addCleanup(lambda: [setattr(p,k,v) for k,v in self.old.items()])
        p.WORK=Path(self.tmp.name)/'.workspace'
        p.LAB=p.WORK/'highfly-p43-restore-lab'
        p.JS=p.LAB/'public/highfly_p43_android_diag.js'
        p.BACKUP=p.LAB/'.hf-p43-android-diag-before-fetch.js'
        p.REPORT=p.WORK/'reports/P43_DIAG_FETCH_MAIN_INSTALL.json'
        p.JS.parent.mkdir(parents=True)
        self.original="""(function(){const flag='hf_p43_diag';
  function report(){
    return flag;
  }
})();
"""
        p.JS.write_text(self.original)
        active=p.WORK/'highfly-origin-stage-p0'
        active.mkdir()
        (active/'src').mkdir()
        (active/'src/main.ts').write_text('P64 MUST NOT CHANGE')

    def test_injects_optin_fetch_and_backup_only(self):
        p.run()
        modified=p.JS.read_text()
        self.assertIn('HIGHFLY_P43_BROWSER_MAIN_FETCH_CHECK',modified)
        self.assertIn("credentials:'same-origin'",modified)
        self.assertIn("cache:'no-store'",modified)
        self.assertIn("BROWSER FETCH MAIN",modified)
        self.assertEqual(p.BACKUP.read_text(),self.original)
        self.assertEqual((p.WORK/'highfly-origin-stage-p0/src/main.ts').read_text(),'P64 MUST NOT CHANGE')
        self.assertTrue(p.REPORT.is_file())
        with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as f:
            f.write(modified);f.flush()
            result=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_no_overwrite(self):
        p.run()
        with self.assertRaisesRegex(RuntimeError,'P43_BROWSER_FETCH_DIAG_ALREADY_INSTALLED'):
            p.run()

    def test_no_change_without_original_anchor(self):
        p.JS.write_text("not existing diag")
        with self.assertRaisesRegex(RuntimeError,'P43_DIAG_ANCHOR_DRIFT'):
            p.run()
        self.assertFalse(p.BACKUP.exists())
if __name__=='__main__':unittest.main()
