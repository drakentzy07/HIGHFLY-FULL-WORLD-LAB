import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/highfly_p10_game_first.py"
SPEC = importlib.util.spec_from_file_location("highfly_p10", SOURCE)
p10 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p10)


def vite_config():
    rows = [
        ("main", "index.html"), ("admin", "admin.html"),
        ("play", "play.html"), ("guide", "guide.html"),
        ("editor", "editor.html"), ("walletHandoff", "wallet-handoff.html"),
    ]
    return (
        "export default { build: { rollupOptions: {\n  input: {\n"
        + "".join(
            f"    {key}: fileURLToPath(new URL('{page}', import.meta.url)),\n"
            for key, page in rows
        )
        + "  },\n  output: { }\n} } };\n"
    )


class HighflyP10Tests(unittest.TestCase):
    def fixture(self, root):
        original = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        report = root / ".workspace/reports/highfly-p10"
        (original / "src/admin/components").mkdir(parents=True)
        (original / "src/admin/App.svelte").write_text("<script>let x=1</script>")
        (original / "src/admin/components/Nav.svelte").write_text("<div>Nav</div>")
        (original / "svelte.config.js").write_text("export default {};")
        (stage / "src/sim").mkdir(parents=True)
        (stage / "src/sim/items.ts").write_text("PRESERVED INVENTORY")
        for page in ("index.html", "play.html", "editor.html", "admin.html", "guide.html", "wallet-handoff.html"):
            (stage / page).write_text("<html/>")
        (stage / "vite.config.ts").write_text(vite_config())
        return original, stage, report

    def test_restores_missing_source_and_focuses_game_without_deleting_admin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, report = self.fixture(root)
            with patch.object(p10, "ROOT", root):
                plan = p10.plan(original, stage, report)
                self.assertEqual(len(plan["missingSourceCode"]), 3)
                self.assertEqual(plan["removedFromBuildOnly"], [
                    "admin.html", "guide.html", "wallet-handoff.html"
                ])
                result = p10.apply(plan, report)
                self.assertEqual(result["missingSourceComponentsRecovered"], 3)
                repeat = p10.plan(original, stage, report)
                self.assertEqual(len(repeat["missingSourceCode"]), 0)
                self.assertEqual(repeat["removedFromBuildOnly"], [])
                self.assertEqual((stage / "src/sim/items.ts").read_text(), "PRESERVED INVENTORY")
                self.assertEqual((original / "src/admin/App.svelte").read_text(), "<script>let x=1</script>")
                self.assertNotIn("admin.html", (stage / "vite.config.ts").read_text())
                self.assertTrue((stage / "src/admin/App.svelte").exists())
                self.assertTrue((stage / "admin.html").exists())
                self.assertTrue((report / "VITE_BEFORE_P10.ts").is_file())

    def test_missing_game_entry_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, report = self.fixture(root)
            (stage / "play.html").unlink()
            with patch.object(p10, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "GAME_ENTRY_MISSING"):
                    p10.plan(original, stage, report)
            self.assertFalse(report.exists())

    def test_does_not_copy_original_artwork(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, report = self.fixture(root)
            (original / "src/admin/components/restricted.glb").write_bytes(b"DO NOT COPY")
            with patch.object(p10, "ROOT", root):
                p10.apply(p10.plan(original, stage, report), report)
            self.assertFalse((stage / "src/admin/components/restricted.glb").exists())


if __name__ == "__main__":
    unittest.main()
