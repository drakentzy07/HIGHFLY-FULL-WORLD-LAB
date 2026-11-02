"""Regression tests: P64 native entry consolidation with byte-exact recovery."""
from __future__ import annotations
import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location(
    "hf_p64_entry",ROOT/"scripts/highfly_world7_p64_entry_cleanup.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

class P64EntryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo=Path(tmp.name)
        self.work=self.repo/".workspace"
        self.stage=self.work/"highfly-origin-stage-p0"
        self.out=self.work/"reports/highfly-world7/p64-entry-clean"
        self.p64=self.work/"reports/highfly-world7/p64-clean-recovery/P64_CLEAN_STATUS.json"
        self.p64.parent.mkdir(parents=True)
        self.stage.mkdir(parents=True)
        self.html=(
          '<html><head>\n'
          '<!-- HIGHFLY_P46_OFFICIAL_IDENTITY -->\n'
          '<!-- HIGHFLY_P48_FURY_MOBILE -->\n'
          '<style id="highfly-p42-hunter-styles">\n'
          '#offline-select .mini-class {display:none}\n</style>\n'
          '<script defer src="/highfly_p42_hunter.js"></script>\n'
          '<style id="highfly-p45-brand-css">\n'
          '#offline-select .mini-class {display:none}\n</style>\n'
          '<script defer src="/highfly_p45_branding.js"></script>\n'
          '<link rel="stylesheet" href="/highfly/p47.css" />\n'
          '<script defer src="/highfly/p47.js"></script>\n'
          '<link rel="stylesheet" href="/highfly/p48.css" />\n'
          '</head><body>'
          '<div id="offline-select"><button class="mini-class" data-class="mage">Mago</button></div>'
          '<div id="loading-screen"><div class="ls-progress"><div id="ls-fill"></div></div></div>'
          '</body></html>\n'
        ).encode("utf8")
        (self.stage/"index.html").write_bytes(self.html)
        image=self.stage/"public/highfly/official/highfly_splash.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"one owned test asset"+b"\x00"*12000)
        self.p64.write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "sourceSha256":{"index.html":sha(self.html)},
        }),"utf8")
        p9=patch.object(p.p9,"preflight",return_value={})
        p9.start()
        self.addCleanup(p9.stop)

    def runit(self,apply=False,build=None):
        return p.run(apply,repo=self.repo,stage=self.stage,out=self.out,p64=self.p64,
                     build=build)

    def test_dry_run_non_destructive(self):
        self.assertEqual(self.runit()["mode"],"DRY_RUN")
        self.assertEqual((self.stage/"index.html").read_bytes(),self.html)
        self.assertFalse(self.out.exists())

    def test_green_clean_removes_only_old_presentation(self):
        result=self.runit(True,build=lambda:{"exitCode":0})
        self.assertEqual(result["mode"],"BUILD_GREEN_BROWSER_PENDING")
        updated=(self.stage/"index.html").read_text()
        for old in ("highfly_p42_hunter.js","highfly_p45_branding.js",
                    "highfly/p47.css","highfly/p47.js",
                    'highfly-p42-hunter-styles','highfly-p45-brand-css'):
            self.assertNotIn(old,updated)
        self.assertIn("data-class=\"mage\"",updated)
        self.assertIn("highfly/p48.css",updated)
        self.assertIn("p64_entry_clean.css",updated)
        self.assertIn("p64_entry_progress.js",updated)
        self.assertEqual((self.out/p.BACKUP).read_bytes(),self.html)
        self.assertEqual(self.runit()["mode"],"BUILD_GREEN_BROWSER_PENDING")

    def test_css_hides_controls_until_true_gameplay(self):
        self.assertIn("body:has(#loading-screen.visible) #mobile-dodge",p.CSS)
        self.assertIn("body:not(.game-active) #mobile-controls",p.CSS)
        self.assertIn("background-image:url('/highfly/official/highfly_splash.png')",p.CSS)
        self.assertIn("#hf-entry-progress-detail",p.CSS)

    def test_readout_reads_real_engine_not_fake_percentage(self):
        self.assertIn("const width=fill.style.width.trim()",p.JS)
        self.assertNotIn("fill.style.width=",p.JS)
        self.assertIn("Sin avance visible",p.JS)
        self.assertIn("loader.classList.contains('visible')",p.JS)

    def test_build_failure_rollback_all(self):
        with self.assertRaisesRegex(RuntimeError,"ENTRY_VITE_BUILD_RED"):
            self.runit(True,build=lambda:{"exitCode":1})
        self.assertEqual((self.stage/"index.html").read_bytes(),self.html)
        self.assertFalse((self.stage/p.CSS_FILE).exists())
        self.assertFalse((self.stage/p.JS_FILE).exists())
        self.assertTrue((self.out/p.BACKUP).exists())

    def test_stage_drift_fails_closed(self):
        (self.stage/"index.html").write_bytes(self.html+b"unknown alteration")
        with self.assertRaisesRegex(RuntimeError,"ENTRY_P64_HTML_CHANGED"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_missing_owned_splash_fails_closed(self):
        (self.stage/"public/highfly/official/highfly_splash.png").unlink()
        with self.assertRaisesRegex(RuntimeError,"ENTRY_ORIGINAL_SPLASH_MISSING"):
            self.runit(True,build=lambda:{"exitCode":0})

    def test_incomplete_splash_fails_closed(self):
        self.stage.joinpath("public/highfly/official/highfly_splash.png").write_bytes(b"tiny")
        with self.assertRaisesRegex(RuntimeError,"ENTRY_ORIGINAL_SPLASH_MISSING"):
            self.runit()

    def test_unknown_markup_never_rewrites_native_editor(self):
        broken=self.html.replace(b"highfly_p42_hunter.js",b"unexpected_script.js")
        (self.stage/"index.html").write_bytes(broken)
        self.p64.write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "sourceSha256":{"index.html":sha(broken)}}),"utf8")
        with self.assertRaisesRegex(RuntimeError,"ENTRY_LINK_ANCHOR_DRIFT"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_marker_not_applied_twice(self):
        self.runit(True,build=lambda:{"exitCode":0})
        self.assertEqual(self.runit()["mode"],"BUILD_GREEN_BROWSER_PENDING")

if __name__=="__main__":
    unittest.main()
