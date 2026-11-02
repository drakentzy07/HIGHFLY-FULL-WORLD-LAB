"""P71 read-only character visual matrix test with a synthetic stage."""
from __future__ import annotations
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("p71_matrix", ROOT / "scripts/highfly_world7_p71_visual_matrix.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class P71VisualMatrixTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.stage = self.repo / ".workspace/highfly-origin-stage-p0"
        target = self.stage / "src/render/characters/manifest.ts"
        target.parent.mkdir(parents=True)
        target.write_text(
            "\n".join("  player_" + c + ": swims({\n    url: " +
                      chr(96) + "$" + "{PLAYERS}/" + c + ".glb" + chr(96) + ",\n  }),"
                      for c in m.CLASSES), "utf8")
        self.patch = patch.object(m, "ROOT", self.repo)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_exactly_nine_but_no_assets(self):
        report = m.analyze(self.stage)
        self.assertEqual(report["modelCount"], 9)
        self.assertEqual(len(report["classes"]), 9)
        self.assertFalse(any(x.get("filePresent") for x in report["classes"].values()))
        self.assertFalse(report["gameplayTested"])
        self.assertEqual(report["classes"]["mage"]["declaredModel"], "models/chars/players/mage.glb")

    def test_unresolved_rig_is_flagged_not_guessed(self):
        manifest = self.stage / "src/render/characters/manifest.ts"
        manifest.write_text(manifest.read_text("utf8").replace(
            "player_mage: swims(", "player_mage: something_else("), "utf8")
        report = m.analyze(self.stage)
        self.assertEqual(report["classes"]["mage"]["status"], "MANIFEST_MODEL_NOT_RESOLVED")

    def test_symlinked_stage_never_scanned(self):
        outside = self.repo / "outside"
        outside.mkdir()
        linked = self.repo / ".workspace/linked-stage"
        linked.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "UNSAFE"):
            m.analyze(linked)

if __name__ == "__main__":
    unittest.main()
