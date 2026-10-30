import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

FILE = Path(__file__).resolve().parents[1] / "scripts/highfly_p6_rpg_and_world_packs.py"
SPEC = importlib.util.spec_from_file_location("highfly_p6", FILE)
p6 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p6)


class P6WorldTests(unittest.TestCase):
    def setup_fixture(self, root: Path):
        original = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        archive = root / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
        output = root / ".workspace/reports/highfly-p6"
        (original / ".git").mkdir(parents=True)
        for files in p6.MODULES.values():
            for name in files:
                a, b = original / name, stage / name
                a.parent.mkdir(parents=True, exist_ok=True)
                b.parent.mkdir(parents=True, exist_ok=True)
                a.write_text("original protected system " + name, encoding="utf8")
                b.write_text("original protected system " + name, encoding="utf8")
        layout = original / "src/sim/eastbrook_layout.ts"
        layout.write_text("makeBuilding('eastbrook_inn','/models/biome/hexb_tavern.glb',", encoding="utf8")
        (stage / "src/sim/eastbrook_layout.ts").write_text(layout.read_text(encoding="utf8"), encoding="utf8")
        p4 = stage / "src/render/characters/manifest.ts"
        p4.parent.mkdir(parents=True, exist_ok=True)
        p4.write_text("/* // HIGHFLY_P4_VISUAL_BRIDGE_START */", encoding="utf8")
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit": p6.PIN, "originalPublicMediaCopied": False,
        }), encoding="utf8")
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/Tavern.glb", b"GLB")
            z.writestr("The Complete KayKit Collection v7/KayKit Fantasy Weapons Bits 1.0/Assets/gltf/Sword.glb", b"GLB")
        return original, stage, archive, output

    def test_preservation_green_does_not_copy_or_modify_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_fixture(root)
            with patch.object(p6, "ROOT", root), patch.object(p6.subprocess, "check_output", return_value=p6.PIN + "\n"):
                report = p6.audit(ref, stage, archive, out)
            self.assertTrue(report["coreRpgCodeIdentical"])
            self.assertTrue(report["p4VisualBridgePresent"])
            self.assertEqual(report["eastbrook"]["buildingPlacements"], 1)
            self.assertEqual(report["kaykit"]["worldPacks"]["construcciones"]["modelFormatFiles"], 1)
            self.assertEqual(report["kaykit"]["worldPacks"]["armas_y_loot"]["files"], 1)
            self.assertFalse((stage / "public").exists())
            self.assertTrue((out / "RPG_AND_WORLD_P6.md").is_file())

    def test_changed_loot_code_is_detected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_fixture(root)
            mod = stage / "src/sim/corpse_loot_state.ts"
            mod.write_text("CHANGED", encoding="utf8")
            with patch.object(p6, "ROOT", root), patch.object(p6.subprocess, "check_output", return_value=p6.PIN + "\n"):
                report = p6.audit(ref, stage, archive, out)
            self.assertFalse(report["coreRpgCodeIdentical"])
            self.assertEqual(report["systems"]["loot_cadaveres"]["status"], "REVIEW_NEEDED")
            self.assertEqual(mod.read_text(encoding="utf8"), "CHANGED")

    def test_missing_p4_manifest_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_fixture(root)
            (stage / "src/render/characters/manifest.ts").unlink()
            with patch.object(p6, "ROOT", root), patch.object(p6.subprocess, "check_output", return_value=p6.PIN + "\n"):
                report = p6.audit(ref, stage, archive, out)
            self.assertFalse(report["p4VisualBridgePresent"])


if __name__ == "__main__":
    unittest.main()
