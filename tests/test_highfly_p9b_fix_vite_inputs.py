import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_p9b_fix_vite_inputs.py"
SPEC = importlib.util.spec_from_file_location("highfly_p9b", SCRIPT)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)

ENTRIES = [
    ("main", "index.html"),
    ("admin", "admin.html"),
    ("play", "play.html"),
    ("guide", "guide.html"),
    ("editor", "editor.html"),
    ("walletHandoff", "wallet-handoff.html"),
]


def vite_config(entries):
    return ("// independent Vite config\n" +
            "export default defineConfig({build:{rollupOptions:{\n"
            "      input: {\n" +
            "".join("        %s: fileURLToPath(new URL('%s', import.meta.url)),\n" % (k, path)
                    for k, path in entries) +
            "      },\n      output: { manualChunks: {} }\n}}});\n")


class P9bTests(unittest.TestCase):
    def fixture(self, root, *, extras=None, missing_core=None):
        stage = root / ".workspace/highfly-origin-stage-p0"
        report = root / ".workspace/reports/highfly-p9b"
        stage.mkdir(parents=True)
        for _, page in ENTRIES:
            if page != missing_core:
                (stage / page).write_text("<html>game</html>", encoding="utf8")
        entries = ENTRIES + (extras or [])
        config = stage / "vite.config.ts"
        config.write_text(vite_config(entries), encoding="utf8")
        protected = stage / "src/sim/items.ts"
        protected.parent.mkdir(parents=True)
        protected.write_text("INVENTORY CODE", encoding="utf8")
        return stage, report, config, protected

    def test_removes_only_missing_pilot_entries_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extra = [("highflyPilot", "highfly-kaykit-pilot.html"),
                     ("highflyP3", "highfly-animation-lab-p3.html")]
            stage, report, config, protected = self.fixture(root, extras=extra)
            old = config.read_text(encoding="utf8")
            with patch.object(p, "ROOT", root):
                result = p.repair(stage, report, apply=True)
            self.assertEqual(result["removedPilotEntries"], [extra[0][1], extra[1][1]])
            self.assertNotIn("highfly-kaykit-pilot.html", config.read_text(encoding="utf8"))
            self.assertNotIn("highfly-animation-lab-p3.html", config.read_text(encoding="utf8"))
            for _, page in ENTRIES:
                self.assertIn(page, config.read_text(encoding="utf8"))
            self.assertEqual((report / "VITE_CONFIG_BEFORE_P9B.ts").read_text(encoding="utf8"), old)
            self.assertEqual(protected.read_text(encoding="utf8"), "INVENTORY CODE")
            with patch.object(p, "ROOT", root):
                second = p.repair(stage, report, apply=True)
            self.assertEqual(second["removedPilotEntries"], [])

    def test_preserves_existing_pilot_page(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, config, _ = self.fixture(
                root, extras=[("highflyPilot", "highfly-kaykit-pilot.html")]
            )
            (stage / "highfly-kaykit-pilot.html").write_text("<html>viewer</html>")
            original = config.read_text(encoding="utf8")
            with patch.object(p, "ROOT", root):
                result = p.repair(stage, report, apply=False)
            self.assertEqual(result["removedPilotEntries"], [])
            self.assertEqual(config.read_text(encoding="utf8"), original)
            self.assertFalse(report.exists())

    def test_rejects_unknown_missing_game_entry_without_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, config, protected = self.fixture(
                root, extras=[("mysteryPage", "other-game.html")]
            )
            old = config.read_text(encoding="utf8")
            with patch.object(p, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "REQUIRED_GAME_ENTRY_MISSING"):
                    p.repair(stage, report, apply=True)
            self.assertEqual(config.read_text(encoding="utf8"), old)
            self.assertFalse(report.exists())

    def test_missing_core_page_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage, report, config, _ = self.fixture(root, missing_core="guide.html")
            with patch.object(p, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "REQUIRED_GAME_ENTRY_MISSING"):
                    p.repair(stage, report, apply=True)
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
