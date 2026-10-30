import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/highfly_p7b_multiformat_buildings.py"
SPEC = importlib.util.spec_from_file_location("highfly_p7b", SOURCE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class HighflyP7bTests(unittest.TestCase):
    def fixtures(self, root):
        reference = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        library = root / ".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
        report = root / ".workspace/reports/highfly-p7b"
        (reference / ".git").mkdir(parents=True)
        (stage / "src/sim").mkdir(parents=True)
        (reference / "src/sim").mkdir(parents=True)
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit": p.PIN, "originalPublicMediaCopied": False
        }), encoding="utf8")
        ids = [
            ("bank","hexb_townhall"),("smithy","hexb_workshop"),
            ("inn","hexb_tavern"),("chapel","hex_church"),
            ("weaving_workshop","hexb_home_a"),("toolworks","hexb_home_b"),
            ("home_market","hexb_home_a"),("home_east","hexb_home_b"),
            ("quayside_home","hexb_home_b"),("harbour_market","hexb_market"),
            ("dock_home","hexb_home_a")
        ]
        source = "\n".join(f"makeBuilding('eastbrook_{name}','/models/biome/{model}.glb'," for name,model in ids)
        for base in (stage, reference):
            (base / "src/sim/eastbrook_layout.ts").write_text(source,encoding="utf8")
        pack=library/p.PACK/"Assets/fbx/buildings/blue"
        pack.mkdir(parents=True)
        for b in ("townhall","workshop","tavern","church","home_A","home_B","market"):
            (pack/f"building_{b}_blue.fbx").write_bytes(b"Kaydara FBX Binary  \x00")
        return reference,stage,library,report

    def test_detects_actual_fbx_only_pack_without_altering_eastbrook(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ref,stage,lib,out=self.fixtures(root)
            before=(stage/"src/sim/eastbrook_layout.ts").read_bytes()
            with patch.object(p,"ROOT",root), patch.object(p.subprocess,"check_output",return_value=p.PIN+"\n"):
                report=p.audit(stage,ref,lib,out)
            self.assertEqual(report["placements"],11)
            self.assertEqual(report["placementsWithCandidate"],11)
            self.assertEqual(report["sourceFormats"],{".fbx":7})
            self.assertEqual(report["filesCopiedToGame"],0)
            self.assertTrue(all(row["previewCandidates"][0]["requiresConversion"] for row in report["buildings"]))
            self.assertEqual((stage/"src/sim/eastbrook_layout.ts").read_bytes(),before)
            self.assertFalse((stage/"public").exists())
            self.assertTrue((out/"EASTBROOK_KAYKIT_MULTIFORMAT_P7B.json").is_file())

    def test_rejects_wrong_original_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ref,stage,lib,out=self.fixtures(root)
            with patch.object(p,"ROOT",root), patch.object(p.subprocess,"check_output",return_value="wrong\n"):
                with self.assertRaisesRegex(RuntimeError,"REFERENCE_NOT_PINNED"):
                    p.audit(stage,ref,lib,out)
            self.assertFalse(out.exists())

    def test_unsupported_name_does_not_invent_matches(self):
        self.assertIsNone(p.building_variant(Path("building_magic_castle_blue.fbx")))
        self.assertEqual(p.building_variant(Path("building_home_A_blue.fbx")),("home_a","blue"))
        self.assertEqual(p.source_kind("/models/biome/hex_church.glb"),"church")


if __name__ == "__main__":
    unittest.main()
