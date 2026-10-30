import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FILE = Path(__file__).resolve().parents[1] / "scripts/highfly_p16_kaykit_spec_repair.py"
SPEC = importlib.util.spec_from_file_location("highfly_p16_kaykit_spec_repair", FILE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)

def dummy_source(root, stage):
    for name in p.SPECS:
        src = root / name
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text('{"items":[]}', encoding="utf8")
    return root

class KayKitOriginalSpecMappingTests(unittest.TestCase):
    def test_castle_kcas_alias_and_red_hex_rebuilt_from_specs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = dummy_source(root / "reference", root / "stage")
            stage = root / "stage"
            source_spec = reference / p.SPECS[0]
            source_spec.write_text(json.dumps({"items": [
                {"out": "models/biome/kcas_wall_window.glb",
                 "src": "Complete KayKit Collection v5/KayKit Dungeon Remastered 1.1/Assets/gltf/wall_window_open.gltf"},
                {"out": "models/biome/hexr_townhall.glb",
                 "src": "Complete KayKit Collection v5/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/buildings/red/building_townhall_red.gltf"},
            ]}))
            a = "The Complete KayKit Collection v7/KayKit Dungeon Pack 1.1/Assets/gltf/wall_window_open.gltf"
            b = "The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/buildings/red/building_townhall_red.gltf"
            chosen = p.inventory(reference, stage, {a: None, b: None})
            self.assertEqual(len(chosen["candidates"]), 2)
            self.assertEqual([r["target"] for r in chosen["candidates"]],
                             ["models/biome/kcas_wall_window.glb",
                              "models/biome/hexr_townhall.glb"])
            self.assertTrue(all(r["status"] == "EXACT_SOURCE_SPEC_PATH"
                                for r in chosen["candidates"]))

    def test_dungeon_double_extension_and_halloween_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = dummy_source(root / "reference", root / "stage")
            stage = root / "stage"
            (reference / p.SPECS[2]).write_text(json.dumps({"items": [
                {"out": "models/dungeon/banner_green.glb",
                 "src": "tmp/asset_src/kaykit/KayKit-Dungeon-Remastered-1.0/addons/kaykit_dungeon_remastered/Assets/gltf/banner_green.gltf.glb"},
                {"out": "models/dungeon/coffin.glb",
                 "src": "tmp/asset_src/kaykit/KayKit-Halloween-Bits-1.0/addons/kaykit_halloween_bits/Assets/gltf/coffin.gltf.glb"},
            ]}))
            a = "Collection/KayKit Dungeon Pack 1.1/Assets/gltf/banner_green.gltf"
            b = "Collection/KayKit Halloween Bits 1.0/Assets/gltf/coffin.gltf"
            result = p.inventory(reference, stage, {a: None, b: None})
            self.assertEqual(len(result["candidates"]), 2)

    def test_ambiguous_zip_source_does_not_select_random_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = dummy_source(root / "reference", root / "stage")
            stage = root / "stage"
            (reference / p.SPECS[1]).write_text(json.dumps({"items": [
                {"out": "models/biome/hexr_tavern.glb",
                 "src": "Complete KayKit Collection v5/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/buildings/red/building_tavern_red.gltf"},
            ]}))
            table = {f"{prefix}/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/buildings/red/building_tavern_red.gltf": None
                     for prefix in ("CollectionA", "CollectionB")}
            result = p.inventory(reference, stage, table)
            self.assertEqual(len(result["candidates"]), 0)
            self.assertEqual(result["unmatched"][0]["status"],
                             "AMBIGUOUS_KAYKIT_SOURCE")

    def test_preview_uses_owned_hero_without_original_attached_weapons(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            manifest = stage / "src/render/characters/manifest.ts"
            main = stage / "src/main.ts"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("""// HIGHFLY_P4_VISUAL_BRIDGE_START
  const heroBase = VISUALS.player_warrior;
  if (heroBase) VISUALS.player_warrior = {
    ...heroBase,
    url: "highfly-private-p4/hero.glb",
// HIGHFLY_P4_VISUAL_BRIDGE_END
""")
            main.write_text("""// HIGHFLY_P13_OWNED_KNIGHT_PREVIEW
    characterPreview.setClass('warrior');
    return;
""")
            patches = p.preview_patches(stage)
            self.assertEqual(len(patches), 2)
            self.assertIn("attach: []", patches[0][2])
            self.assertIn("weaponSlots: []", patches[0][2])
            self.assertIn("setClass('warrior', null, null)", patches[1][2])
            manifest.write_text(patches[0][2])
            main.write_text(patches[1][2])
            again = p.preview_patches(stage)
            self.assertTrue(all(a == b for _, a, b in again))
            self.assertEqual(patches[0][0].read_text(), again[0][1])

    def test_does_not_copy_original_media_or_change_sim(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            (stage / "src/render").mkdir(parents=True)
            for file in ("props.ts", "dungeon.ts", "eastbrook_town.ts"):
                (stage / "src/render" / file).write_text(
                    "const p = '/models/biome/kcas_wall_window.glb';")
            output = p.runtime_missing(stage)
            self.assertGreater(output["worldModelReferencesStillMissing"], 0)
            (stage / "public/models/biome").mkdir(parents=True)
            (stage / "public/models/biome/kcas_wall_window.glb").write_bytes(b"owned model")
            self.assertEqual(p.runtime_missing(stage)["worldModelReferencesStillMissing"], 0)

if __name__ == "__main__":
    unittest.main()
