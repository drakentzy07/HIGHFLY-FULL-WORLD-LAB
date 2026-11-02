"""P69 isolated recovery: no overwrites, P64 untouched, public model media linked."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('highfly_p69_isolated',ROOT/'scripts/highfly_world7_p69_isolated_recovery.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class P69RecoverTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.old={n:getattr(p,n) for n in ('ROOT','WORK','STAGE','LAB','REPORT')}
        self.addCleanup(lambda: [setattr(p,k,v) for k,v in self.old.items()])
        p.ROOT=Path(t.name)
        p.WORK=p.ROOT/'.workspace'
        p.STAGE=p.WORK/'highfly-origin-stage-p0'
        p.LAB=p.WORK/'highfly-p69-restore-lab'
        p.REPORT=p.WORK/'reports/highfly-world7/P69_ISOLATED_RESCUE.json'
        (p.STAGE/'src/game').mkdir(parents=True)
        (p.STAGE/'src/main.ts').write_text('P64 ORIGINAL SOURCE')
        (p.STAGE/'src/game/mobile_controls.ts').write_text('P64 ORIGINAL MOVEMENT')
        (p.STAGE/'public/highfly/official').mkdir(parents=True)
        (p.STAGE/'public/highfly/official/splash.svg').write_text('LICENSED MEDIA')
        (p.STAGE/'public/ui').mkdir()
        (p.STAGE/'public/ui/test.svg').write_text('STAGE ASSET')
        (p.STAGE/'node_modules/vite/bin').mkdir(parents=True)
        (p.STAGE/'node_modules/vite/bin/vite.js').write_text('VITE DEV')
        (p.STAGE/'package.json').write_text('{"name":"test"}')
        self.overlay={
          'index.html':b'<html><head></head><body>P69</body></html>',
          'src/main.ts':b'P69 ORIGINAL SOURCE',
          'src/game/mobile_controls.ts':b'P69 ORIGINAL MOVEMENT',
          'src/game/highfly_fury_skill_touch.ts':b'// P69 native aim',
          'public/highfly/p69_fury_core.css':b'/* P69 CSS */',
        }
        self.patch=patch.object(p,'preflight',return_value=(self.overlay,{},{}))
        self.patch.start();self.addCleanup(self.patch.stop)

    def test_exact_p69_lab_and_unchanged_p64(self):
        output=p.apply()
        self.assertEqual(output['mode'],'APPLY')
        self.assertFalse(output['stageP64Modified'])
        self.assertFalse(output['commercialReleaseApproved'])
        self.assertEqual((p.LAB/'src/main.ts').read_bytes(),self.overlay['src/main.ts'])
        self.assertEqual((p.LAB/'src/game/mobile_controls.ts').read_bytes(),
                         self.overlay['src/game/mobile_controls.ts'])
        self.assertEqual((p.STAGE/'src/main.ts').read_text(),'P64 ORIGINAL SOURCE')
        self.assertEqual((p.STAGE/'src/game/mobile_controls.ts').read_text(),
                         'P64 ORIGINAL MOVEMENT')
        self.assertTrue((p.LAB/'public/ui').is_symlink())
        self.assertTrue((p.LAB/'public/highfly/official').is_symlink())
        self.assertFalse((p.LAB/'src/main.ts').is_symlink())
        self.assertFalse((p.LAB/'index.html').is_symlink())
        self.assertEqual((p.LAB/'public/highfly/p69_fury_core.css').read_bytes(),
                         self.overlay['public/highfly/p69_fury_core.css'])
        self.assertTrue(p.REPORT.is_file())

    def test_no_overwrite_on_second_attempt(self):
        p.apply()
        with self.assertRaises(FileExistsError):
            p.apply()

    def test_private_stage_assets_not_copied(self):
        p.apply()
        self.assertTrue((p.LAB/'public/ui/test.svg').exists())
        self.assertEqual((p.LAB/'public/ui/test.svg').resolve(),
                         (p.STAGE/'public/ui/test.svg').resolve())

if __name__=='__main__':unittest.main()
