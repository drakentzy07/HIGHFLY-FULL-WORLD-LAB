import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_p11_private_hunter_preview.py"
SPEC = importlib.util.spec_from_file_location("highfly_p11", SCRIPT)
p11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p11)


class P11PrivateHunterTests(unittest.TestCase):
    def fixture(self, root: Path):
        stage = root / ".workspace/highfly-origin-stage-p0"
        (stage / "src/render/characters").mkdir(parents=True)
        for url in p11.OWNED_URLS:
            f = stage / "public" / url
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"original owned resource")
        manifest = stage / "src/render/characters/manifest.ts"
        manifest.write_text("\n".join([
            "// HIGHFLY_P4_VISUAL_BRIDGE_START",
            "if (import.meta.env.VITE_HIGHFLY_P4 === '1') {",
            "const heroBase = VISUALS.player_warrior;",
            "animUrls: [...hfDonors, ...(heroBase.animUrls ?? [])],",
            "const skeletonBase = VISUALS.skel_minion;",
            "animUrls: [...hfDonors, ...(skeletonBase.animUrls ?? [])],",
            "}",
            "// HIGHFLY_P4_VISUAL_BRIDGE_END",
        ]), encoding="utf8")
        assets = stage / "src/render/characters/assets.ts"
        assets.write_text(
            "const allPreloadUrls = characterPreloadUrls(false);\n"
            "const inventoryUntouched = true;\n",
            encoding="utf8")
        main = stage / "src/main.ts"
        main.write_text(
            "const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);\n"
            "const mainGameUntouched = true;\n", encoding="utf8")
        sim = stage / "src/sim/items.ts"
        sim.parent.mkdir(parents=True)
        sim.write_text("REAL ITEM RULES", encoding="utf8")
        return stage, (root / ".workspace/reports/highfly-p11"), manifest, assets, main, sim

    def test_apply_stages_owned_character_only_and_preserves_sim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, manifest, assets, main, sim = self.fixture(root)
            with patch.object(p11, "ROOT", root), patch.object(p11, "STAGE", stage):
                planned = p11.plan(stage)
                result = p11.apply(planned, report)
                self.assertTrue(result["applied"])
                self.assertEqual(result["characterBootUrls"], 6)
                self.assertNotIn("...(heroBase.animUrls ?? [])", manifest.read_text())
                self.assertNotIn("...(skeletonBase.animUrls ?? [])", manifest.read_text())
                self.assertIn("highfly-private-p4/hero.glb", assets.read_text())
                self.assertIn("VITE_HIGHFLY_OFFLINE_LAB", main.read_text())
                self.assertEqual(sim.read_text(), "REAL ITEM RULES")
                planned_again = p11.plan(stage)
                second = p11.apply(planned_again, report)
                self.assertEqual(second["filesEdited"], [])
                self.assertEqual(json.loads((report / "HUNTER_PREVIEW_P11.json").read_text())["worldAssetsComplete"], False)

    def test_rejects_missing_owned_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, manifest, assets, main, sim = self.fixture(root)
            (stage / "public/highfly-private-p4/hero.glb").unlink()
            with patch.object(p11, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "OWNED_P4_MODEL_NOT_PRESENT"):
                    p11.plan(stage)
            self.assertFalse(report.exists())

    def test_original_not_touched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, manifest, assets, main, sim = self.fixture(root)
            reference = root / ".workspace/claudecraft-v0.44.7"
            reference.mkdir(parents=True)
            (reference / "src").mkdir()
            (reference / "src/untouchable.ts").write_text("upstream unchanged")
            with patch.object(p11, "ROOT", root), patch.object(p11, "STAGE", stage):
                p11.apply(p11.plan(stage), report)
            self.assertEqual((reference / "src/untouchable.ts").read_text(), "upstream unchanged")


if __name__ == "__main__":
    unittest.main()
