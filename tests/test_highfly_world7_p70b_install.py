"""P70-B stage installer contracts on synthetic private data."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "scripts/highfly_world7_p70b_install.py"
spec = importlib.util.spec_from_file_location("p70b_bridge", PATH)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class P70BTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage = self.root / ".workspace/highfly-origin-stage-p0"
        self.stage.mkdir(parents=True)
        self.main = self.stage / "src/main.ts"
        self.main.parent.mkdir(parents=True)
        self.original = (
            "import { Sim } from './sim/sim';\n"
            "// HIGHFLY_P13_OWNED_KNIGHT_PREVIEW\n"
            "// HIGHFLY_P69_FURY_CORE\n"
            "async function startOffline(name:string, skin=0) {\n"
            "  const sim = new Sim();\n"
            "  sim.setPlayerSkin(sim.playerId, skin);\n"
            "}\n")
        self.main.write_text(self.original, "utf8")
        self.source = self.root / "pilot/highfly_hunter_runtime_p70b.ts"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("export const SESSION_ONLY = true;\n", "utf8")
        self.out = self.root / ".workspace/reports/highfly-world7/p70b"
        self.root_patch = mock.patch.object(p, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_preflight_builds_safe_plan_without_writing(self):
        plan = p.plan(self.stage, self.source)
        self.assertIn("registerHighflyHunterSession(sim", plan["revised"])
        self.assertIn("defineHighflyHunterIdentity(name, skin)", plan["revised"])
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.stage / p.MODULE).exists())

    def test_missing_p69_fails_closed(self):
        self.main.write_text(self.original.replace("HIGHFLY_P69_FURY_CORE", "MISSING"), "utf8")
        with self.assertRaisesRegex(RuntimeError, "REQUIRES_P69"):
            p.plan(self.stage, self.source)

    def test_old_source_anchor_drift_fails_closed(self):
        self.main.write_text(self.original.replace("sim.setPlayerSkin", "sim.setAvatar"), "utf8")
        with self.assertRaisesRegex(RuntimeError, "SKIN_ANCHOR_DRIFT"):
            p.plan(self.stage, self.source)

    def test_apply_and_build_success_writes_private_only(self):
        with mock.patch.object(p.p9, "preflight", return_value={}), \
             mock.patch.object(p, "plan", side_effect=lambda stage: p.plan(stage, self.source)), \
             mock.patch.object(p.subprocess, "run") as build:
            result = p.run(True, stage=self.stage, out=self.out)
        self.assertEqual(result["mode"], "BUILD_GREEN_BROWSER_PENDING")
        self.assertTrue(build.called)
        self.assertTrue((self.stage / p.MODULE).is_file())
        self.assertTrue((self.out / "P70B_STATUS.json").is_file())
        self.assertNotEqual(self.main.read_text("utf8"), self.original)

    def test_build_failure_rolls_back_private_stage(self):
        with mock.patch.object(p.p9, "preflight", return_value={}), \
             mock.patch.object(p, "plan", side_effect=lambda stage: p.plan(stage, self.source)), \
             mock.patch.object(p.subprocess, "run", side_effect=RuntimeError("build red")):
            with self.assertRaisesRegex(RuntimeError, "build red"):
                p.run(True, stage=self.stage, out=self.out)
        self.assertEqual(self.main.read_text("utf8"), self.original)
        self.assertFalse((self.stage / p.MODULE).exists())
        self.assertFalse((self.out / "P70B_STATUS.json").exists())

if __name__ == "__main__":
    unittest.main()
