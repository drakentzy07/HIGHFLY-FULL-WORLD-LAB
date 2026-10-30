#!/usr/bin/env python3
"""Contract tests for P18's exact, user-owned KayKit spec import planner."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p18_exact_kaykit_spec_recovery as p18


class P18ExactSpecTests(unittest.TestCase):
    def test_accepts_only_private_model_destinations(self):
        self.assertTrue(p18.eligible_target("models/biome/hex_castle.glb"))
        self.assertTrue(p18.eligible_target("models/props/garden_arch.glb"))
        for bad in ("/models/biome/a.glb", "models/creatures/a.glb",
                    "models/biome/../props/a.glb", "models/props/a.png",
                    "models/props\\evil.glb", "textures/a.glb"):
            self.assertFalse(p18.eligible_target(bad), bad)

    def test_exact_path_import_and_stem_only_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "original"
            stage = root / "stage"
            for spec in p18.SPEC_PATHS:
                (original / spec).parent.mkdir(parents=True, exist_ok=True)
            (stage / "public").mkdir(parents=True)
            pack = "KayKit Medieval Hexagon Pack 1.0.1"
            source = ("Z Complete KayKit Collection v7/" + pack +
                      "/Assets/gltf/buildings/green/building_castle_green.gltf")
            alt = ("Z Complete KayKit Collection v7/" + pack +
                   "/Assets/gltf/other/building_tavern_green.gltf")
            files = [
                {"src": "user/" + pack +
                 "/Assets/gltf/buildings/green/building_castle_green.gltf",
                 "out": "models/biome/hex_castle.glb"},
                {"src": "user/" + pack +
                 "/Assets/gltf/buildings/green/building_tavern_green.gltf",
                 "out": "models/biome/hex_tavern.glb"},
                {"src": "tmp/proprietary/blade.glb",
                 "out": "models/biome/unlicensed.glb"},
            ]
            (original / p18.SPEC_PATHS[0]).write_text(json.dumps({"items": files}))
            (original / p18.SPEC_PATHS[1]).write_text(json.dumps({"items": []}))
            plan = p18.inventory(original, stage, {source: object(), alt: object()})
            self.assertEqual(len(plan["exactImportCandidates"]), 1)
            self.assertEqual(plan["exactImportCandidates"][0]["target"],
                             "models/biome/hex_castle.glb")
            self.assertEqual(plan["statusCounts"]["UNIQUE_STEM_REVIEW_ONLY"], 1)
            self.assertEqual(plan["statusCounts"]["skipped_non_supported_kit_source"], 1)

    def test_existing_asset_is_never_selected_for_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "original"
            stage = root / "stage"
            source = ("pack/KayKit Medieval Hexagon Pack 1.0.1"
                      "/Assets/gltf/buildings/green/building_castle_green.gltf")
            for spec in p18.SPEC_PATHS:
                (original / spec).parent.mkdir(parents=True, exist_ok=True)
                records = ([{"src": source, "out": "models/biome/hex_castle.glb"}]
                           if spec == p18.SPEC_PATHS[0] else [])
                (original / spec).write_text(json.dumps({"items": records}))
            target = stage / "public/models/biome/hex_castle.glb"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"existing")
            plan = p18.inventory(original, stage, {source: object()})
            self.assertEqual(len(plan["exactImportCandidates"]), 0)
            self.assertEqual(plan["statusCounts"]["ALREADY_PRESENT"], 1)


if __name__ == "__main__":
    unittest.main()
