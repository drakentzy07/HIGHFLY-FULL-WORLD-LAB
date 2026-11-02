"""P64 entry V2: verify real UI correction and recoverability, not browser playability."""
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
    "hf_p64_v2",ROOT/"scripts/highfly_world7_p64_entry_v2.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def h(data):return hashlib.sha256(data).hexdigest()

class P64EntryV2Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.work=Path(t.name)/".workspace"
        self.stage=self.work/"highfly-origin-stage-p0"
        self.out=self.work/"reports/highfly-world7/p64-entry-v2"
        self.status=self.work/"reports/highfly-world7/p64-entry-clean/P64_ENTRY_STATUS.json"
        self.stage.mkdir(parents=True)
        self.status.parent.mkdir(parents=True)
        self.old={}
        for rel,data in ((p.CSS_REL,p.p64entry.CSS.encode()),
                         (p.JS_REL,p.p64entry.JS.encode()),
                         (p.HTML_REL,b"<html><head>Native ClaudeCraft</head></html>")):
            target=self.stage/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            self.old[rel]=data
        self.status.write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "assets":{rel:h(self.old[rel]) for rel in (p.CSS_REL,p.JS_REL)},
            "htmlSha256":h(self.old[p.HTML_REL]),
        }),encoding="utf8")
        pre=patch.object(p.p9,"preflight",return_value={})
        pre.start()
        self.addCleanup(pre.stop)

    def runit(self,apply=False,build=None):
        return p.run(apply,stage=self.stage,work=self.work,out=self.out,
                     entry_status=self.status,build=build)

    def test_dry_run_preserves_everything(self):
        self.assertEqual(self.runit()["mode"],"DRY_RUN")
        for rel,data in self.old.items():
            self.assertEqual((self.stage/rel).read_bytes(),data)
        self.assertFalse(self.out.exists())

    def test_green_updates_only_existing_two_files(self):
        result=self.runit(True,build=lambda:{"exitCode":0})
        self.assertEqual(result["mode"],"BUILD_GREEN_BROWSER_PENDING")
        self.assertEqual((self.stage/p.CSS_REL).read_text(),p.NEW_CSS)
        self.assertEqual((self.stage/p.JS_REL).read_text(),p.NEW_JS)
        self.assertEqual((self.stage/p.HTML_REL).read_bytes(),self.old[p.HTML_REL])
        self.assertEqual(self.runit()["mode"],"BUILD_GREEN_BROWSER_PENDING")
        for rel in (p.CSS_REL,p.JS_REL):
            self.assertEqual((self.out/"backups"/rel).read_bytes(),self.old[rel])

    def test_loader_has_no_embedded_ui_image(self):
        pos=p.NEW_CSS.index("body #loading-screen.visible {")
        end=p.NEW_CSS.index("body #loading-screen .ls-logo",pos)
        block=p.NEW_CSS[pos:end]
        self.assertNotIn("url(",block)
        self.assertIn("background-image:",block)
        self.assertIn("2147483200",block)
        self.assertIn("width:100vw",block)
        self.assertIn("height:100dvh",block)

    def test_start_art_is_kept_but_bottom_baked_cta_is_masked(self):
        self.assertIn("url('/highfly/official/highfly_splash.png')",p.NEW_CSS)
        self.assertIn("#090719 30%",p.NEW_CSS)
        self.assertIn("#start-screen.hf-p46-entry",p.NEW_CSS)

    def test_progress_uses_original_fill_never_fakes_width(self):
        self.assertIn("const width=fill.style.width.trim()",p.NEW_JS)
        self.assertNotIn("fill.style.width=",p.NEW_JS)
        self.assertIn("Sin avance visible",p.NEW_JS)
        self.assertIn("unhandledrejection",p.NEW_JS)

    def test_build_red_restore_exact_byte_for_byte(self):
        with self.assertRaisesRegex(RuntimeError,"PRIVATE_BUILD_FAILED"):
            self.runit(True,build=lambda:{"exitCode":1})
        for rel,data in self.old.items():
            self.assertEqual((self.stage/rel).read_bytes(),data)
        self.assertFalse((self.out/p.STATUS_NAME).exists())

    def test_css_stage_drift_fails_closed(self):
        (self.stage/p.CSS_REL).write_bytes(b"unrelated modified css")
        with self.assertRaisesRegex(RuntimeError,"ENTRY_V2_STAGE_DRIFT"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_html_stage_drift_fails_closed(self):
        (self.stage/p.HTML_REL).write_bytes(b"modified html")
        with self.assertRaisesRegex(RuntimeError,"ENTRY_V2_HTML_HAS_CHANGED"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_unknown_prior_report_blocks_change(self):
        self.status.write_text('{"mode":"NOT_GREEN"}',encoding="utf8")
        with self.assertRaisesRegex(RuntimeError,"PREVIOUS_ENTRY_NOT_GREEN"):
            self.runit()
        self.assertFalse(self.out.exists())

    def test_previous_backup_cannot_be_overwritten(self):
        self.out.mkdir()
        with self.assertRaisesRegex(RuntimeError,"EXISTING_BACKUP_REVIEW_REQUIRED"):
            self.runit(True,build=lambda:{"exitCode":0})

if __name__=="__main__":
    unittest.main()
