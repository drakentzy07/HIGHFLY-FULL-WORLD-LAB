"""P71 DrakenLAB: guarded, zero-mutation dry-run and rollback contracts."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_world7_p71_drakenlab.py"
spec = importlib.util.spec_from_file_location("p71_drakenlab", SCRIPT)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class DrakenLabInstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.stage = self.root / ".workspace/highfly-origin-stage-p0"
        (self.stage / "src/sim").mkdir(parents=True)
        self.main = self.stage / "src/main.ts"
        self.ts = self.root / "pilot/highfly_drakenlab_p71.ts"
        self.css = self.root / "pilot/highfly_drakenlab_p71.css"
        self.ts.parent.mkdir(parents=True)
        self.ts.write_text("export const marker = true;\n", "utf8")
        self.css.write_text(".hf-lab { color: white; }\n", "utf8")
        self.main.write_text(
            "import { Sim } from './sim';\n"
            "// HIGHFLY_P69_FURY_CORE\n"
            "// HIGHFLY_P68_FURY_GOLDEN_RECOVERY\n"
            "async function startGame() {\n"
            "  document.body.classList.add('game-active');\n"
            "}\n"
            "async function startOffline() {}\n"
            "const startupParams = new URLSearchParams(location.search);\n"
            "if (editorPlaytest) {\n"
            "} else if (diagnosticsAutoOffline) {\n"
            "  void startOffline('warrior', 'Diagnostics', 0);\n"
            "}\n", "utf8"
        )
        self.original = self.main.read_text("utf8")
        (self.stage / "src/sim/types.ts").write_text(
            "export type PlayerClass = " + " | ".join(p.EXPECTED_CLASSES) + ";\n", "utf8")
        self.out = self.root / ".workspace/reports/highfly-world7/p71"

    def patches(self):
        return patch.object(p.p9, "preflight", return_value={"ok": True})

    def test_dry_plan_preserves_files_and_rpg(self):
        data = p.plan(self.stage, self.root)
        self.assertEqual(data["newMain"].count(p.MARK), 2)
        self.assertIn("offlineSim.player.templateId as PlayerClass", data["newMain"])
        self.assertNotIn("offlineSim.player.cls", data["newMain"])
        self.assertIn("void startOffline(highflyDrakenLabBoot.cls", data["newMain"])
        self.assertIn("VITE_HIGHFLY_OFFLINE_LAB", data["newMain"])
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.stage / p.MODULE).exists())

    def test_all_nine_classes_required(self):
        types = self.stage / "src/sim/types.ts"
        types.write_text("export type PlayerClass = 'warrior';", "utf8")
        with self.assertRaisesRegex(RuntimeError, "NINE_CLASSES"):
            p.plan(self.stage, self.root)

    def test_p69_required(self):
        self.main.write_text(self.original.replace("HIGHFLY_P69_FURY_CORE", "MISSING"), "utf8")
        with self.assertRaisesRegex(RuntimeError, "P69_NOT_DETECTED"):
            p.plan(self.stage, self.root)

    def test_partial_anchor_fails_closed(self):
        self.main.write_text(self.original.replace("diagnosticsAutoOffline", "somethingElse"), "utf8")
        with self.assertRaisesRegex(RuntimeError, "ANCHOR_DRIFT"):
            p.plan(self.stage, self.root)

    def test_apply_compiles_and_marks_browser_pending(self):
        with self.patches(), patch.object(p.p9, "smoke", return_value={"exitCode": 0}) as build:
            result = p.run(True, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(result["mode"], "BUILD_GREEN_BROWSER_PENDING")
        self.assertTrue(build.called)
        self.assertTrue((self.stage / p.MODULE).is_file())
        self.assertTrue((self.out / "P71_STATUS.json").is_file())
        self.assertNotEqual(self.main.read_text("utf8"), self.original)
        self.assertTrue(p.plan(self.stage, self.root)["already"])

    def test_preexisting_visual_matrix_report_is_preserved(self):
        # Exact real-world regression: visual audit writes this directory first.
        self.out.mkdir(parents=True)
        visual = self.out / "P71_VISUAL_MATRIX.md"
        visual.write_text("nine class models found", "utf8")
        with self.patches(), patch.object(p.p9, "smoke", return_value={"exitCode": 0}):
            result = p.run(True, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(result["mode"], "BUILD_GREEN_BROWSER_PENDING")
        self.assertEqual(visual.read_text("utf8"), "nine class models found")
        self.assertTrue((self.out / "backup/src/main.ts").exists())
        self.assertTrue((self.out / "P71_STATUS.json").exists())

    def test_existing_backup_blocks_without_overwrite(self):
        backup = self.out / "backup/src/main.ts"
        backup.parent.mkdir(parents=True)
        backup.write_text("precious previous backup", "utf8")
        with self.patches(), patch.object(p.p9, "smoke") as build:
            with self.assertRaisesRegex(RuntimeError, "EXISTING_INSTALL_BACKUP"):
                p.run(True, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(backup.read_text("utf8"), "precious previous backup")
        self.assertEqual(self.main.read_text("utf8"), self.original)
        build.assert_not_called()

    def test_build_red_reverts_all_stage_files(self):
        with self.patches(), patch.object(p.p9, "smoke", return_value={"exitCode": 1}):
            with self.assertRaisesRegex(RuntimeError, "VITE_BUILD_FAILED"):
                p.run(True, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.stage / p.MODULE).exists())
        self.assertFalse((self.stage / p.CSS).exists())
        self.assertFalse((self.out / "P71_STATUS.json").exists())

    def test_dry_run_does_not_mutate_even_when_preflight_passes(self):
        with self.patches(), patch.object(p.p9, "smoke") as build:
            result = p.run(False, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(result["mode"], "DRY_RUN")
        self.assertFalse(self.out.exists())
        self.assertEqual(self.main.read_text("utf8"), self.original)
        build.assert_not_called()

    def test_second_application_never_rebuilds(self):
        with self.patches(), patch.object(p.p9, "smoke", return_value={"exitCode": 0}):
            p.run(True, stage=self.stage, repo=self.root, out=self.out)
        with self.patches(), patch.object(p.p9, "smoke") as build:
            result = p.run(True, stage=self.stage, repo=self.root, out=self.out)
        self.assertEqual(result["mode"], "ALREADY_INSTALLED")
        build.assert_not_called()

    def test_symlink_stage_fails_closed(self):
        outside = self.root / "outside"
        outside.mkdir()
        newstage = self.root / ".workspace/symlink-stage"
        newstage.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "PRIVATE_STAGE"):
            p.plan(newstage, self.root)

if __name__ == "__main__":
    unittest.main()
