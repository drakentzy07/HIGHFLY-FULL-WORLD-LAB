import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_p12_world_kaykit_batch.py"
SPEC = importlib.util.spec_from_file_location("highfly_p12", SCRIPT)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def fixture(root):
    original = root / ".workspace/claudecraft-v0.44.7"
    stage = root / ".workspace/highfly-origin-stage-p0"
    archive = root / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
    report = root / ".workspace/reports/highfly-p12"
    (original / ".git").mkdir(parents=True)
    stage.mkdir(parents=True)
    (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
        "sourceCommit": p.PIN, "originalPublicMediaCopied": False
    }), encoding="utf8")
    for rel in ("src/sim/eastbrook_layout.ts", "src/sim/items.ts",
                "src/sim/corpse_loot_state.ts", "src/sim/mob/lifecycle.ts"):
        for base in (stage, original):
            path = base / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("protected:" + rel, encoding="utf8")
    for rel in ("models/dungeon/chest.glb", "models/biome/hexr_townhall.glb",
                "models/biome/kcas_unknown.glb"):
        dest = original / "public" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"CLAUDECRAFT MEDIA -- DO NOT COPY")
    archive.parent.mkdir(parents=True)
    source = json.dumps({
        "asset": {"version": "2.0"},
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "buffers": [{"uri": "bin/model.bin", "byteLength": 4}],
        "images": [{"uri": "textures/color.png"}],
    })
    with zipfile.ZipFile(archive, "w") as z:
        rootpart = "The Complete KayKit Collection v7/"
        for pack, name in (
            ("KayKit Dungeon Pack 1.1", "Assets/gltf/chest.gltf"),
            ("KayKit Medieval Hexagon Pack 1.0.1", "Assets/gltf/buildings/red/building_townhall_red.gltf"),
        ):
            stem = rootpart + pack + "/" + name
            parent = stem.rsplit("/", 1)[0]
            z.writestr(stem, source)
            z.writestr(parent + "/bin/model.bin", b"1234")
            z.writestr(parent + "/textures/color.png", b"png")
    converter = original / "node_modules/.bin/gltf-transform"
    converter.parent.mkdir(parents=True)
    converter.write_text("fixture")
    return original, stage, archive, report


def tiny_glb(file):
    content = json.dumps({"asset": {"version": "2.0"}, "meshes": [{}]}).encode()
    content += b" " * (-len(content) % 4)
    file.write_bytes(struct.pack("<4sIII4s", b"glTF", 2,
                    20 + len(content), len(content), b"JSON") + content)


class WorldP12Tests(unittest.TestCase):
    def test_exact_match_inventory_and_no_original_media_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, stage, archive, report = fixture(root)
            with patch.object(p, "ROOT", root), patch.object(
                    p.subprocess, "check_output", return_value=p.PIN + "\n"):
                p.validate(original, stage, archive, report)
                with zipfile.ZipFile(archive) as z:
                    index = p.index_models(p.zip_members(z))
                result = p.source_manifest(original, stage, index)
            self.assertEqual(result["statuses"], {
                "EXACT_SOURCE_NAME": 2, "NO_EXACT_KAYKIT_SOURCE": 1
            })
            self.assertFalse((stage / "public").exists())
            self.assertEqual(len(result["exactMatches"]), 2)

    def test_bulk_converts_only_owned_sources_and_preserves_rpg(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, stage, archive, report = fixture(root)
            with patch.object(p, "ROOT", root):
                with zipfile.ZipFile(archive) as z:
                    index = p.index_models(p.zip_members(z))
                chosen = p.source_manifest(original, stage, index)["exactMatches"]
                report.mkdir(parents=True)
                def fake_convert(args, **kwargs):
                    tiny_glb(Path(args[-1]))
                    return type("Proc", (), {"returncode": 0, "stderr": ""})()
                with patch.object(p.subprocess, "run", side_effect=fake_convert):
                    converted = p.import_batch(original, stage, report, archive, chosen)
                self.assertEqual(len(converted), 2)
                self.assertTrue((stage / "public/models/dungeon/chest.glb").is_file())
                self.assertTrue((stage / "public/models/biome/hexr_townhall.glb").is_file())
                self.assertFalse((stage / "public/models/biome/kcas_unknown.glb").exists())
                self.assertNotEqual((stage / "public/models/dungeon/chest.glb").read_bytes(),
                                    (original / "public/models/dungeon/chest.glb").read_bytes())
                self.assertEqual((stage / "src/sim/items.ts").read_text(),
                                 (original / "src/sim/items.ts").read_text())

    def test_rejects_zip_dependency_path_escape(self):
        member = ("The Complete KayKit Collection v7/KayKit Dungeon Pack 1.1/"
                  "Assets/gltf/chest.gltf")
        with self.assertRaisesRegex(RuntimeError, "GLTF_DEPENDENCY_OUTSIDE_SOURCE_PACK"):
            p.safe_dependency(member, "../../../../../../elsewhere.bin", {})

    def test_refuses_replacing_any_existing_stage_resource(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, stage, archive, report = fixture(root)
            with patch.object(p, "ROOT", root):
                with zipfile.ZipFile(archive) as z:
                    index = p.index_models(p.zip_members(z))
                chosen = p.source_manifest(original, stage, index)["exactMatches"]
                existing = stage / "public/models/dungeon/chest.glb"
                existing.parent.mkdir(parents=True)
                existing.write_bytes(b"OTHER USER ASSET")
                report.mkdir(parents=True)
                with self.assertRaisesRegex(RuntimeError, "REFUSE_TO_OVERWRITE_EXISTING_MEDIA"):
                    p.import_batch(original, stage, report, archive, chosen)
                self.assertEqual(existing.read_bytes(), b"OTHER USER ASSET")


if __name__ == "__main__":
    unittest.main()
