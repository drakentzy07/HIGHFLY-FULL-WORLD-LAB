import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "scripts/highfly_bridge_hunter_world_p4.py"
sys.path.insert(0, str(FILE.parent))
SPEC = importlib.util.spec_from_file_location("highfly_world_p4", FILE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def glb(path: Path, clips=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    names = [f"bone_{i}" for i in range(23)]
    metadata = {
        "nodes": [{"name": name} for name in names],
        "skins": [{"joints": list(range(23))}],
        "animations": [
            {"name": name, "channels": [{"target": {"node": i}} for i in range(23)]}
            for name in (clips or [])
        ],
    }
    contents = json.dumps(metadata).encode("utf8")
    contents += b" " * ((4 - len(contents) % 4) % 4)
    binary = struct.pack("<4sII", b"glTF", 2, len(contents) + 20)
    binary += struct.pack("<I4s", len(contents), b"JSON") + contents
    path.write_bytes(binary)


class WorldBridgeP4Tests(unittest.TestCase):
    def fixture(self, root: Path):
        stage = root / ".workspace/highfly-origin-stage-p0"
        lib = root / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
        ref = root / ".workspace/claudecraft-v0.44.7"
        (stage / "src/render/characters").mkdir(parents=True)
        (ref / "src/render/characters").mkdir(parents=True)
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit": p.PIN, "originalPublicMediaCopied": False
        }), encoding="utf8")
        marker = "\n// ---------------------------------------------------------------------------\n" + p.ANCHOR + "\n"
        contents = "export const VISUALS = {player_warrior:{},skel_minion:{}};\n" + marker
        (stage / "src/render/characters/manifest.ts").write_text(contents, encoding="utf8")
        (ref / "src/render/characters/manifest.ts").write_text(contents, encoding="utf8")
        glb(lib / "KayKit Adventurers 2.0/Characters/gltf/Knight.glb")
        glb(lib / "KayKit Skeletons 1.1/characters/gltf/Skeleton_Minion.glb")
        anim = lib / "KayKit Character Animations 1.1/Animations/gltf/Rig_Medium"
        glb(anim / "Rig_Medium_MovementBasic.glb", ["Idle", "Walking_A", "Running_A"])
        glb(anim / "Rig_Medium_General.glb", ["Hit_A", "Death_A"])
        glb(anim / "Rig_Medium_CombatMelee.glb", ["Melee_1H_Attack_Chop"])
        glb(anim / "Rig_Medium_CombatRanged.glb", ["Ranged_Magic_Spellcasting"])
        (lib / "KayKit Adventurers 2.0/Animations/gltf/Rig_Medium").mkdir(parents=True)
        return stage, lib, ref, contents

    def test_generates_reversible_mapping_and_keeps_reference_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage, lib, ref, contents = self.fixture(root)
            with patch.object(p, "ROOT", root):
                report = p.plan(stage, lib)
            self.assertEqual(report["report"]["clips"]["walk"], "Walking_A")
            self.assertEqual(report["report"]["clips"]["attack"], "Melee_1H_Attack_Chop")
            self.assertEqual(len(report["targets"]), 6)
            self.assertIn("VITE_HIGHFLY_P4 === '1'", report["updated"])
            self.assertEqual((ref / "src/render/characters/manifest.ts").read_text(encoding="utf8"), contents)
            self.assertFalse((stage / "public").exists())

    def test_rejects_missing_stage_without_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage, lib, ref, _ = self.fixture(root)
            (stage / "HIGHFLY_STAGE_STATUS.json").unlink()
            with patch.object(p, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "HIGHFLY_CODE_STAGE_MISSING"):
                    p.plan(stage, lib)
            self.assertFalse((stage / "public").exists())

    def test_does_not_overwrite_conflicting_private_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage, lib, ref, _ = self.fixture(root)
            forbidden = stage / "public/highfly-private-p4/hero.glb"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_bytes(b"existing unrelated model")
            with patch.object(p, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "P4_TARGET_CONFLICT"):
                    p.plan(stage, lib)
            self.assertEqual(forbidden.read_bytes(), b"existing unrelated model")


if __name__ == "__main__":
    unittest.main()
