"""Safety and recovery tests for extracting P43 without overwriting active P64."""
import importlib.util
import io
import json
import tarfile
import tempfile
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_p43_recovery",ROOT/"scripts/highfly_p43_isolated_recovery.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class P43RecoveryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.work=Path(t.name)/".workspace"
        self.stage=self.work/"highfly-origin-stage-p0"
        self.lab=self.work/"highfly-p43-restore-lab"
        self.archive=self.work/"checkpoints/HIGHFLY-P43-BEFORE-P45.tar.gz"
        self.report=self.work/"reports/highfly-world7/P43_ISOLATED_RESTORE.json"
        self.archive.parent.mkdir(parents=True)
        self.stage.mkdir(parents=True)
        (self.stage/"src").mkdir()
        (self.stage/"src/main.ts").write_text("CURRENT BAD P64 MAIN","utf8")
        (self.stage/"index.html").write_text("CURRENT BAD P64 HTML","utf8")
        (self.stage/"public").mkdir()
        (self.stage/"public/owned_asset.png").write_bytes(b"PRIVATE IMAGE")
        (self.stage/"node_modules/vite/bin").mkdir(parents=True)
        (self.stage/"node_modules/vite/bin/vite.js").write_text("VITE","utf8")
        (self.stage/"package.json").write_text('{"name":"highfly","private":true}',"utf8")
        (self.stage/"vite.config.ts").write_text("export default {}","utf8")
        (self.stage/"HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit":p.SOURCE_COMMIT,
            "originalPublicMediaCopied":False
        }),"utf8")
        self.manifest={"src/main.ts":b"P43 MAIN",
                       "index.html":b"P43 GOOD HTML with P42 hunter",
                       "src/thing.ts":b"data from old snapshot",
                       "public/highfly_p40_icons.js":b"console.log('old icons')"}
        self.write_archive()

    def write_archive(self,extra=None):
        with tarfile.open(self.archive,"w:gz") as tf:
            d=tarfile.TarInfo("src")
            d.type=tarfile.DIRTYPE
            tf.addfile(d)
            entries=list(self.manifest.items())+(extra or [])
            for name,bytes_ in entries:
                m=tarfile.TarInfo(name)
                m.size=len(bytes_)
                tf.addfile(m,io.BytesIO(bytes_))

    def plan(self):
        return p.inspect(archive=self.archive,stage=self.stage,lab=self.lab,work=self.work)

    def apply(self,build_runner=None):
        return p.apply(archive=self.archive,stage=self.stage,lab=self.lab,
                       report=self.report,work=self.work,build_runner=
                       build_runner or (lambda lab:(0,"synthetic build green")))

    def test_preflight_readonly(self):
        x=self.plan()
        self.assertEqual(x["members"],5)
        self.assertFalse(self.lab.exists())
        self.assertEqual((self.stage/"index.html").read_text(),"CURRENT BAD P64 HTML")

    def test_isolated_extraction_does_not_mutate_active_stage(self):
        x=self.apply()
        self.assertEqual(x["result"],"BUNDLE_BUILT_BROWSER_PENDING")
        self.assertEqual((self.lab/"index.html").read_bytes(),self.manifest["index.html"])
        self.assertEqual((self.stage/"index.html").read_text(),"CURRENT BAD P64 HTML")
        self.assertEqual((self.stage/"src/main.ts").read_text(),"CURRENT BAD P64 MAIN")
        self.assertTrue((self.lab/"public").is_symlink())
        self.assertTrue((self.lab/"node_modules").is_symlink())
        self.assertEqual((self.lab/"public/owned_asset.png").read_bytes(),b"PRIVATE IMAGE")
        self.assertEqual((self.lab/"package.json").read_text(),
                         '{"name":"highfly","private":true}')
        self.assertTrue(self.report.is_file())

    def test_missing_checkpoint_rejected(self):
        self.archive.unlink()
        with self.assertRaisesRegex(RuntimeError,"P43_CHECKPOINT_MISSING"):
            self.plan()
        self.assertFalse(self.lab.exists())

    def test_existing_lab_not_overwritten(self):
        self.lab.mkdir()
        (self.lab/"existing.txt").write_text("keep","utf8")
        with self.assertRaisesRegex(RuntimeError,"P43_LAB_ALREADY_EXISTS"):
            self.apply()
        self.assertEqual((self.lab/"existing.txt").read_text(),"keep")

    def test_unsafe_member_traversal_rejected(self):
        self.write_archive(extra=[("src/../../escape.ts",b"evil")])
        with self.assertRaisesRegex(RuntimeError,"P43_UNSAFE_ARCHIVE_MEMBER"):
            self.apply()
        self.assertFalse(self.lab.exists())

    def test_unsafe_special_member_rejected(self):
        with tarfile.open(self.archive,"w:gz") as tf:
            for name,content in self.manifest.items():
                m=tarfile.TarInfo(name);m.size=len(content)
                tf.addfile(m,io.BytesIO(content))
            bad=tarfile.TarInfo("src/evil_link.ts")
            bad.type=tarfile.SYMTYPE;bad.linkname="/etc/passwd"
            tf.addfile(bad)
        with self.assertRaisesRegex(RuntimeError,"P43_UNSAFE_ARCHIVE_MEMBER"):
            self.plan()

    def test_accidentally_newer_html_rejected(self):
        self.manifest["index.html"]=b"HIGHFLY_P46_OFFICIAL_IDENTITY"
        self.write_archive()
        with self.assertRaisesRegex(RuntimeError,"P43_SNAPSHOT_CONTAINS_LATER_P46_UI"):
            self.apply()
        self.assertEqual((self.stage/"index.html").read_text(),"CURRENT BAD P64 HTML")

    def test_no_marked_success_if_build_red(self):
        outcome=self.apply(build_runner=lambda lab:(2,"Vite build failed"))
        self.assertEqual(outcome["result"],"BUNDLE_FAILED_REVIEW_LOG")
        self.assertFalse(outcome["browserVerified"])
        self.assertEqual((self.stage/"src/main.ts").read_text(),"CURRENT BAD P64 MAIN")

if __name__=="__main__":unittest.main()
