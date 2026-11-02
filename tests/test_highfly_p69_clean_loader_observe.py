"""P69 loader presentation and real-progress readout remain isolated.

No progress spoofing, no changes to game/Sim, public image or saved data.
"""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hf69_loader',ROOT/'scripts/highfly_p69_clean_loader_observe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class P69NativeLoaderTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        old={n:getattr(p,n) for n in ('ROOT','WORK','LAB','HTML','PUBLIC','CSS','JS','BACKUP','REPORT')}
        self.addCleanup(lambda: [setattr(p,n,v) for n,v in old.items()])
        p.ROOT=pathlib.Path(temp.name)
        p.WORK=p.ROOT/'.workspace'
        p.LAB=p.WORK/'highfly-p69-restore-lab'
        p.HTML=p.LAB/'index.html'
        p.PUBLIC=p.LAB/'public/highfly'
        p.CSS=p.PUBLIC/'p69_loader_clean.css'
        p.JS=p.PUBLIC/'p69_loader_observe.js'
        p.BACKUP=p.LAB/'.hf-p69-loader-before-index.html'
        p.REPORT=p.WORK/'reports/highfly-world7/P69_LOADER_CLEAN_OBSERVE.json'
        p.PUBLIC.mkdir(parents=True)
        self.original='''<!doctype html><html><head>
<link rel="stylesheet" href="/highfly/p68_fury_recovery.css" />
<link rel="stylesheet" href="/highfly/p69_fury_core.css" />
</head><body><!-- HIGHFLY_P69_FURY_CORE -->
<div id="start-screen"></div>
<div id="loading-screen">
<div class="ls-progress">
<div id="ls-status">Cargando...</div>
<div class="ls-bar"><div id="ls-fill" style="width:23%"></div></div>
</div></div>
</body></html>'''
        p.HTML.write_text(self.original,encoding='utf8')
        self.active=p.WORK/'highfly-origin-stage-p0'
        self.active.mkdir()
        (self.active/'index.html').write_text('ACTIVE P64 DO NOT CHANGE')
        self.p43=p.WORK/'highfly-p43-restore-lab'
        self.p43.mkdir()
        (self.p43/'index.html').write_text('P43 DO NOT CHANGE')

    def test_dry_run_no_files_changed(self):
        p.run(False)
        self.assertEqual(p.HTML.read_text(),self.original)
        self.assertFalse(p.CSS.exists())
        self.assertFalse(p.JS.exists())
        self.assertFalse(p.BACKUP.exists())

    def test_install_backup_and_no_game_progress_override(self):
        p.run(True)
        actual=p.HTML.read_text('utf8')
        self.assertIn('HIGHFLY_P69_NATIVE_LOADER_CLEAN',actual)
        self.assertEqual(p.BACKUP.read_text('utf8'),self.original)
        self.assertEqual((self.active/'index.html').read_text(),'ACTIVE P64 DO NOT CHANGE')
        self.assertEqual((self.p43/'index.html').read_text(),'P43 DO NOT CHANGE')
        self.assertIn('body #loading-screen.visible',p.CSS.read_text())
        self.assertIn("body:has(#loading-screen.visible) #start-screen",p.CSS.read_text())
        self.assertIn("fill.style.width.trim()",p.JS.read_text())
        self.assertIn("status.textContent",p.JS.read_text())
        self.assertIn("'unhandledrejection'",p.JS.read_text())
        self.assertNotIn("fill.style.width=",p.JS.read_text())
        self.assertNotIn("fill.style.width =",p.JS.read_text())
        self.assertNotIn("localStorage",p.JS.read_text())
        self.assertNotIn("sessionStorage",p.JS.read_text())
        self.assertTrue(p.REPORT.is_file())
        with tempfile.NamedTemporaryFile('w',suffix='.js') as f:
            f.write(p.JS.read_text());f.flush()
            z=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
            self.assertEqual(z.returncode,0,z.stderr)

    def test_reapply_refused_preserve_lab(self):
        p.run(True)
        before=p.HTML.read_text('utf8')
        with self.assertRaisesRegex(RuntimeError,'P69_LOADER_ALREADY_INSTALLED'):
            p.run(True)
        self.assertEqual(p.HTML.read_text('utf8'),before)

    def test_missing_native_loader_does_not_modify(self):
        p.HTML.write_text(self.original.replace('id="ls-fill"','id="fake-fill"'))
        with self.assertRaisesRegex(RuntimeError,'P69_LOADER_REQUIRED_NATIVE_MARKER_MISSING'):
            p.run(True)
        self.assertFalse(p.BACKUP.exists())
        self.assertFalse(p.CSS.exists())
        self.assertFalse(p.JS.exists())

if __name__=='__main__':unittest.main()
