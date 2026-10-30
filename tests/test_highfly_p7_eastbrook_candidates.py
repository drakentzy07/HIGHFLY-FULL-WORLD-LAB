import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_p7_eastbrook_candidates.py"
SPEC = importlib.util.spec_from_file_location("highfly_p7", SCRIPT)
p7 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p7)


def write_glb(file: Path):
    file.parent.mkdir(parents=True, exist_ok=True)
    body = b"{}  "
    file.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(body)) +
                     struct.pack("<I4s", len(body), b"JSON") + body)


class HighflyP7Tests(unittest.TestCase):
    def fixture(self, root):
        original = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        library = root / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
        output = root / ".workspace/reports/highfly-p7"
        (original / ".git").mkdir(parents=True)
        (stage / "src/sim").mkdir(parents=True)
        (original / "src/sim").mkdir(parents=True)
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit": p7.SOURCE_COMMIT, "originalPublicMediaCopied": False,
        }), encoding="utf-8")
        # All 11 placements: original IDs must remain unchanged, no changes to scene.
        locations = [
            ("bank", "hexb_townhall"), ("smithy", "hexb_workshop"),
            ("inn", "hexb_tavern"), ("chapel", "hex_church"),
            ("weaver", "hexb_home_a"), ("toolworks", "hexb_home_b"),
            ("home_market", "hexb_home_a"), ("home_east", "hexb_home_b"),
            ("quayside_home", "hexb_home_b"), ("harbour_market", "hexb_market"),
            ("dock_home", "hexb_home_a"),
        ]
        data = "\n".join(
            f"makeBuilding('eastbrook_{ident}', '/models/biome/{name}.glb',"
            for ident, name in locations
        )
        for base in (stage, original):
            (base / "src/sim/eastbrook_layout.ts").write_text(data, encoding="utf-8")
        pack = library / p7.PACK_NAME
        write_glb(pack / "Assets/gltf/buildings/blue/building_home_A_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_home_B_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_townhall_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_workshop_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_tavern_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_church_blue.glb")
        write_glb(pack / "Assets/gltf/buildings/blue/building_market_blue.glb")
        return original, stage, library, output

    def test_eastbrook_preserved_and_candidates_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, library, output = self.fixture(root)
            before = (original / "src/sim/eastbrook_layout.ts").read_bytes()
            with patch.object(p7, "ROOT", root), patch.object(
                p7.subprocess, "check_output", return_value=p7.SOURCE_COMMIT + "\n"):
                r = p7.audit(stage, original, library, output)
            self.assertEqual(r["placements"], 11)
            self.assertEqual(r["placementsWithCandidate"], 11)
            self.assertEqual(r["uniqueCandidateGlbsChecked"], 7)
            self.assertEqual(r["assetsCopiedIntoGame"], 0)
            self.assertEqual((original / "src/sim/eastbrook_layout.ts").read_bytes(), before)
            self.assertFalse((stage / "public").exists())
            self.assertTrue((output / "EASTBROOK_KAYKIT_CANDIDATES_P7.md").exists())

    def test_rejects_wrong_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, library, output = self.fixture(root)
            with patch.object(p7, "ROOT", root), patch.object(
                p7.subprocess, "check_output", return_value="wrong-sha\n"):
                with self.assertRaisesRegex(RuntimeError, "REFERENCE_PIN_MISMATCH"):
                    p7.audit(stage, original, library, output)
            self.assertFalse(output.exists())

    def test_unknown_building_gets_zero_candidates_without_fake_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, stage, library, output = self.fixture(root)
            for base in (stage, original):
                path = base / "src/sim/eastbrook_layout.ts"
                path.write_text(path.read_text(encoding="utf-8").replace(
                    "/models/biome/hexb_market.glb", "/models/biome/hexb_unknown.glb"),
                    encoding="utf-8")
            with patch.object(p7, "ROOT", root), patch.object(
                p7.subprocess, "check_output", return_value=p7.SOURCE_COMMIT + "\n"):
                r = p7.audit(stage, original, library, output)
            self.assertEqual(r["placementsWithCandidate"], 10)
            self.assertEqual(r["buildings"][9]["candidateCount"], 0)


if __name__ == "__main__":
    unittest.main()
