#!/usr/bin/env python3
"""Unit tests for the P17 private, read-only asset inventory."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p17_asset_inventory as p17


class P17InventoryTests(unittest.TestCase):
    def test_tracks_missing_present_and_unbundled_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory) / "stage"
            (stage / "src").mkdir(parents=True)
            (stage / "public/models/props").mkdir(parents=True)
            (stage / "dist").mkdir()
            (stage / "src/world.ts").write_text(
                "const a = '/models/props/missing.glb';\n"
                "const b = '/models/props/owned.glb';\n",
                encoding="utf8",
            )
            (stage / "public/models/props/owned.glb").write_bytes(b"test")
            result = p17.audit(stage, Path(directory) / "not-found.json")
            self.assertEqual(result["absentFromPublicCount"], 1)
            self.assertEqual(result["presentInPublicButAbsentFromDistCount"], 1)
            self.assertEqual(result["missingPublic"][0]["path"],
                             "models/props/missing.glb")

    def test_includes_p16_dynamic_references_and_detects_case_only_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory) / "stage"
            (stage / "src").mkdir(parents=True)
            (stage / "public/models/biome").mkdir(parents=True)
            (stage / "public/models/biome/Keep.GLB").write_bytes(b"test")
            p16 = Path(directory) / "p16.json"
            p16.write_text(json.dumps({
                "runtimeMissing": {
                    "firstMissing": ["models/biome/keep.glb",
                                     "models/dungeon/delve_entrance_2.glb"]
                }
            }), encoding="utf8")
            result = p17.audit(stage, p16)
            self.assertEqual(result["caseOnlyMismatchesCount"], 1)
            self.assertEqual(result["absentFromPublicCount"], 1)
            self.assertEqual(result["p16MissingImportedForCoverage"], 2)

    def test_does_not_need_vite_log(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "src").mkdir()
            (stage / "public").mkdir()
            report = p17.audit(stage, stage / "missing-report.json")
            self.assertEqual(report["staticAndP16PathsFound"], 0)
            self.assertFalse(report["distPresent"])


if __name__ == "__main__":
    unittest.main()
