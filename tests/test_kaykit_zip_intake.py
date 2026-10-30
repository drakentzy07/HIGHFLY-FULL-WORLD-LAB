import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts/highfly_kaykit_zip_intake.py"
SPEC = importlib.util.spec_from_file_location("highfly_kaykit_zip_intake", SOURCE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class KaykitZipTests(unittest.TestCase):
    def test_paths_reject_traversal_absolute_and_windows_drive(self):
        for value in ["../bad.gltf", "/tmp/danger", "C:/Windows/file", "KayKit/../bad", "KayKit//bad"]:
            with self.assertRaises(ValueError, msg=value):
                mod.canonical_name(value)
        self.assertEqual(mod.canonical_name("The Complete KayKit Collection v7/KayKit Adventurers 2.0/x.glb"),
                         "The Complete KayKit Collection v7/KayKit Adventurers 2.0/x.glb")

    def test_selects_only_approved_pack_and_extracts_private_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            inbox = root / "input.zip"
            one = "The Complete KayKit Collection v7/KayKit Adventurers 2.0/Assets/gltf/knight.glb"
            two = "The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/home.gltf"
            other = "The Complete KayKit Collection v7/KayKit Skeletons 1.1/bone.glb"
            with zipfile.ZipFile(inbox, "w") as z:
                z.writestr(one, b"gltf model placeholder")
                z.writestr(two, b"{}")
                z.writestr(other, b"skeleton")
            plan = mod.build_plan([inbox], mod.PACKS_DEFAULT)
            self.assertEqual(plan["fileCount"], 3)
            self.assertEqual(plan["selectedFileCount"], 2)
            with self.assertRaises(ValueError):
                mod.safe_extract([inbox], plan, root / "NOT_PRIVATE")
            output = root / ".workspace/private-imports/approved"
            self.assertEqual(mod.safe_extract([inbox], plan, output), 2)
            self.assertEqual((output / one).read_bytes(), b"gltf model placeholder")
            self.assertFalse((output / other).exists())
            with self.assertRaises(FileExistsError):
                mod.safe_extract([inbox], plan, output)

    def test_duplicate_or_oversize_entries_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "duplicate.zip"
            a = "KayKit Adventurers 2.0/one.glb"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr(a, "A")
                z.writestr(a, "B")
            with self.assertRaises(ValueError):
                mod.build_plan([p], mod.PACKS_DEFAULT)


if __name__ == "__main__":
    unittest.main()
