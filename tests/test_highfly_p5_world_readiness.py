import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_p5_world_readiness.py"
SPEC = importlib.util.spec_from_file_location("highfly_p5_world_readiness", SCRIPT)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class HighflyP5Tests(unittest.TestCase):
    def fixture(self, root):
        original = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        report = root / ".workspace/reports/highfly-p5"
        (original / ".git").mkdir(parents=True)
        (original / "public/models/biome").mkdir(parents=True)
        (original / "public/textures").mkdir()
        (original / "public/models/biome/hexb_home.glb").write_bytes(b"private-original-asset")
        (original / "public/textures/ground.png").write_bytes(b"texture")
        (stage / "public/highfly-private-p4").mkdir(parents=True)
        (stage / "public/highfly-private-p4/hero.glb").write_bytes(b"private-kaykit-hero")
        (stage / "src/render/characters").mkdir(parents=True)
        (stage / "src/sim").mkdir(parents=True)
        (stage / "src/render/characters/manifest.ts").write_text(
            "/* // HIGHFLY_P4_VISUAL_BRIDGE_START */\n"
            "const a = '/models/biome/hexb_home.glb';\n"
            "const b = 'textures/ground.png';\n",
            encoding="utf8"
        )
        (stage / "src/sim/eastbrook_layout.ts").write_text(
            "const b = '/models/biome/hexb_home.glb';", encoding="utf8"
        )
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(
            json.dumps({"sourceCommit": m.SOURCE_SHA, "originalPublicMediaCopied": False, "stats": {"codeFiles": 5314}}),
            encoding="utf8"
        )
        return original, stage, report

    def test_literal_refs_are_diagnostic_only(self):
        names = m.quoted_media_literals(
            "const a = '/models/biome/town.glb';\n"
            "const b = 'textures/hero.png';\n"
            "const c = SOMETHING_DYNAMIC;"
        )
        self.assertIn("models/biome/town.glb", names)
        self.assertIn("textures/hero.png", names)
        self.assertNotIn("skeleton.glb", names)

    def test_readonly_and_original_media_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original, stage, output = self.fixture(root)
            before = (original / "public/models/biome/hexb_home.glb").read_bytes()
            with patch.object(m, "ROOT", root), patch.object(m.subprocess, "check_output", return_value=m.SOURCE_SHA + "\n"):
                result = m.audit(stage, original, output)
            self.assertEqual(result["referencePublicFileCount"], 2)
            self.assertEqual(result["independentStagePublicFileCount"], 1)
            self.assertEqual(result["sameRelativePathMissing"], 2)
            self.assertEqual(result["referencedButNotInStage"], 2)
            self.assertTrue(result["noFilesCopiedOrAlteredInGames"])
            self.assertEqual((original / "public/models/biome/hexb_home.glb").read_bytes(), before)
            self.assertFalse((stage / "public/models/biome/hexb_home.glb").exists())
            self.assertTrue((output / "WORLD_READINESS_P5.json").exists())

    def test_rejects_missing_p4_bridge(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original, stage, report = self.fixture(root)
            manifest = stage / "src/render/characters/manifest.ts"
            manifest.write_text("export const VISUALS = {};", encoding="utf8")
            with patch.object(m, "ROOT", root), patch.object(m.subprocess, "check_output", return_value=m.SOURCE_SHA + "\n"):
                with self.assertRaisesRegex(RuntimeError, "P4_WORLD_BRIDGE_NOT_FOUND"):
                    m.audit(stage, original, report)
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
