"""Opt-in P43 module ESM linking diagnostic stays inside lab, retains backups."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hf43link',ROOT/'scripts/highfly_p43_module_link_probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class ModuleLinkProbeTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        old={k:getattr(p,k) for k in ['WORK','LAB','JS','BACKUP','REPORT']}
        self.addCleanup(lambda: [setattr(p,k,v) for k,v in old.items()])
        p.WORK=Path(t.name)/'.workspace'
        p.LAB=p.WORK/'highfly-p43-restore-lab'
        p.JS=p.LAB/'public/highfly_p43_android_diag.js'
        p.BACKUP=p.LAB/'.hf-p43-android-diag-before-module-link.js'
        p.REPORT=p.WORK/'reports/P43_MODULE_LINK_PROBE_INSTALL.json'
        p.JS.parent.mkdir(parents=True)
        self.src="""(function(){
    const query='hf_p43_diag';
    function mount(){
      const buttons=document.createElement('div');
      const title=document.createElement('div');
      const bar=document.createElement('div');
      const host=document.createElement('div');
      const pre=document.createElement('pre');
      const copy=document.createElement('button');
      const hide=document.createElement('button');
      function add(a,b){}
      function tick(){}
    copy.textContent='COPIAR'; hide.textContent='OCULTAR';
    buttons.append(copy,hide);bar.append(title,buttons);host.append(bar,pre);document.body.append(host);
    }
})();
"""
        p.JS.write_text(self.src)
        active=p.WORK/'highfly-origin-stage-p0'
        active.mkdir()
        (active/'index.html').write_text('P64 UNTOUCHED')

    def test_works_backups_and_syntax(self):
        p.run()
        js=p.JS.read_text()
        self.assertIn('HF_P43_LINK_PROBE_V1',js)
        self.assertIn("tryModule.onclick=async()=>",js)
        self.assertIn("await import('/src/main.ts')",js)
        self.assertNotIn('localStorage',js)
        self.assertEqual(p.BACKUP.read_text(),self.src)
        self.assertEqual((p.WORK/'highfly-origin-stage-p0/index.html').read_text(),'P64 UNTOUCHED')
        self.assertTrue(p.REPORT.exists())
        with tempfile.NamedTemporaryFile('w',suffix='.js') as f:
            f.write(js);f.flush()
            z=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
            self.assertEqual(z.returncode,0,z.stderr)

    def test_no_reapply(self):
        p.run()
        with self.assertRaisesRegex(RuntimeError,'P43_LINK_PROBE_NOT_READY_OR_ALREADY_INSTALLED'):
            p.run()

if __name__=='__main__':unittest.main()
