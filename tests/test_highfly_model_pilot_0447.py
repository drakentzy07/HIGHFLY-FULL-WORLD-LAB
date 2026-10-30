import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

FILE=Path(__file__).resolve().parents[1]/"scripts/highfly_install_model_pilot_0447.py"
SPEC=importlib.util.spec_from_file_location("highfly_model_pilot",FILE)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def glb(filename,extra=b"\x00"*8):
    size=12+len(extra)
    filename.parent.mkdir(parents=True,exist_ok=True)
    filename.write_bytes(b"glTF"+(2).to_bytes(4,"little")+size.to_bytes(4,"little")+extra)

class HighflyModelPilotTests(unittest.TestCase):
    def test_real_gltf_header_and_corrupt_file_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            f=root/"knight.glb"
            glb(f)
            self.assertTrue(mod.glb_valid(f))
            f.write_bytes(b"BAD!" + f.read_bytes()[4:])
            self.assertFalse(mod.glb_valid(f))

    def test_selects_hero_from_glb_assets_and_skeleton_without_source_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            hero=root/"KayKit Adventurers 2.0"
            enemy=root/"KayKit Skeletons 1.1"
            glb(hero/"Assets/gltf/knight.glb")
            glb(hero/"Animations/gltf/Rig_Medium/Rig_Medium_General.glb")
            glb(enemy/"Assets/gltf/skeleton_minion.glb")
            self.assertEqual(mod.choose_model(hero,"hero").name,"knight.glb")
            self.assertEqual(mod.choose_model(enemy,"skeleton").name,"skeleton_minion.glb")
            self.assertTrue(mod.donor_animation(hero))
            self.assertFalse((root/"public").exists())

    def test_existing_pilot_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a=root/"a.glb";b=root/"b.glb"
            a.write_bytes(b"ABCD")
            b.write_bytes(b"EFGH")
            with self.assertRaises(FileExistsError):
                mod.put_unmodified(a,b)
            self.assertEqual(b.read_bytes(),b"EFGH")
            mod.put_unmodified(a,root/"new.glb")
            self.assertEqual((root/"new.glb").read_bytes(),b"ABCD")
            mod.put_unmodified(a,root/"new.glb")

if __name__=="__main__":
    unittest.main()
