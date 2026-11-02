"""P71B regression guard: detects wrong Entity.cls and repairs the private stage safely."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "p71b_class_fix", ROOT / "scripts/highfly_world7_p71b_fix_class_field.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class ClassFieldRepairTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage = self.root / ".workspace/highfly-origin-stage-p0"
        self.out = self.root / ".workspace/reports/highfly-world7/p71"
        self.out.mkdir(parents=True)
        self.main = self.stage / "src/main.ts"
        self.main.parent.mkdir(parents=True)
        self.original = (
            "import type { PlayerClass } from './sim/types';\n"
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "mountDrakenLab({\n"
            "  currentClass: offlineSim.player.cls,\n"
            "  playerName: offlineSim.player.name,\n"
            "  onChoose: (cls) => restartDrakenLab(cls, offlineSim.player.name),\n"
            "});\n"
        )
        self.main.write_text(self.original, "utf8")
        self.status = self.out / "P71_STATUS.json"
        self.status.write_text(json.dumps({
            "mode": "BUILD_GREEN_BROWSER_PENDING",
            "sourceHashes": {"src/main.ts": hashlib.sha256(self.original.encode()).hexdigest()}
        }), "utf8")

    def preflight(self):
        return p.preflight(stage=self.stage, out=self.out, repo=self.root)

    def runit(self, apply=False, build=None):
        return p.run(apply, stage=self.stage, out=self.out, repo=self.root, build=build)

    def test_read_only_by_default(self):
        self.assertEqual(self.runit()["mode"], "READY")
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.out / p.BACKUP).exists())

    def test_apply_fixes_live_class_field_once(self):
        res = self.runit(True, build=lambda: {"exitCode": 0})
        self.assertEqual(res["mode"], "BUILD_GREEN_BROWSER_PENDING")
        source = self.main.read_text("utf8")
        self.assertEqual(source.count(p.NEW), 1)
        self.assertNotIn(p.OLD, source)
        self.assertEqual((self.out / p.BACKUP).read_text("utf8"), self.original)
        self.assertEqual(self.runit()["mode"], "ALREADY_REPAIRED")

    def test_build_failed_restores_previous_code(self):
        with self.assertRaisesRegex(RuntimeError, "BUILD_FAILED"):
            self.runit(True, build=lambda: {"exitCode": 1})
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.out / "P71B_STATUS.json").exists())

    def test_refuses_changed_stage_hash(self):
        self.main.write_text(self.original + "// unrelated modification\n", "utf8")
        with self.assertRaisesRegex(RuntimeError, "STAGE_MODIFIED"):
            self.runit(True, build=lambda: {"exitCode": 0})
        self.assertFalse((self.out / p.BACKUP).exists())

    def test_refuses_backup_overwrite(self):
        backup = self.out / p.BACKUP
        backup.parent.mkdir(exist_ok=True)
        backup.write_text("Precious previous backup", "utf8")
        with self.assertRaisesRegex(RuntimeError, "PREVIOUS_REPAIR"):
            self.runit(True, build=lambda: {"exitCode": 0})
        self.assertEqual(backup.read_text("utf8"), "Precious previous backup")
        self.assertEqual(self.main.read_text("utf8"), self.original)

    def test_refuses_symlink_main(self):
        outside = self.root / "outside"
        outside.write_text(self.original, "utf8")
        self.main.unlink()
        self.main.symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "REQUIRED_INPUT"):
            self.preflight()
        self.assertEqual(outside.read_text("utf8"), self.original)

    def test_refuses_bad_marker_count(self):
        self.main.write_text(self.original.replace(p.MARK, "GONE", 1), "utf8")
        with self.assertRaisesRegex(RuntimeError, "INVALID_MARKER"):
            self.preflight()

if __name__ == "__main__":
    unittest.main()
