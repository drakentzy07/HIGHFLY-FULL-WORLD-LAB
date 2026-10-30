import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_reassemble_kaykit_v7.py"
SPEC=importlib.util.spec_from_file_location("highfly_reassemble",SCRIPT)
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class ReassembleKayKitTests(unittest.TestCase):
    def zip_bytes(self):
        content=io.BytesIO()
        with zipfile.ZipFile(content,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("The Complete KayKit Collection v7/KayKit Adventurers 2.0/Assets/gltf/hero.glb",b"GLB_MODEL_1")
            z.writestr("The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/house.gltf",b'{"asset":{"version":"2.0"}}')
        return content.getvalue()

    def wrap(self, filename, innername, payload):
        with zipfile.ZipFile(filename,'w',compression=zipfile.ZIP_STORED) as z:
            z.writestr(innername,payload)

    def prepare(self, root):
        source=self.zip_bytes()
        mid=len(source)//2
        p1,p2=root/"KIT_COMPLETO_PARTE_01.zip",root/"KIT_COMPLETO_PARTE_02.zip"
        self.wrap(p1,"fragmento_01.bin",source[:mid])
        self.wrap(p2,"fragmento_02.bin",source[mid:])
        expected=(("KIT_COMPLETO_PARTE_01.zip","fragmento_01.bin",mid),
                  ("KIT_COMPLETO_PARTE_02.zip","fragmento_02.bin",len(source)-mid))
        return (p1,p2),source,expected

    def test_rebuilds_original_zip_byte_for_byte_without_unpacking(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            parts,original,expected=self.prepare(root)
            dest=root/".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
            report=root/"reports/index.json"
            with mock.patch.object(module,"EXPECTED",expected):
                result=module.reconstruct(parts,dest,report,True)
            self.assertEqual(dest.read_bytes(),original)
            self.assertEqual(result["sha256"],hashlib.sha256(original).hexdigest())
            self.assertEqual(result["archiveFiles"],2)
            self.assertEqual(result["modelFiles"],2)
            self.assertEqual(len(result["packCounts"]),2)
            self.assertTrue(result["deepCrcVerified"])
            self.assertTrue(report.is_file())
            self.assertFalse((root/"public").exists())
            with mock.patch.object(module,"EXPECTED",expected):
                with self.assertRaises(FileExistsError):
                    module.reconstruct(parts,dest,report,False)

    def test_invalid_order_or_edited_fragment_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            parts,original,expected=self.prepare(root)
            dest=root/".workspace/private-imports/full.zip"
            with mock.patch.object(module,"EXPECTED",expected):
                with self.assertRaises(ValueError):
                    module.reconstruct((parts[1],parts[0]),dest,root/"report.json")
            self.assertFalse(dest.exists())
            # A bad member in an outer wrapper must not silently reconstruct.
            self.wrap(parts[1],"wrong_filename.bin",original[:10])
            with mock.patch.object(module,"EXPECTED",expected):
                with self.assertRaises(ValueError):
                    module.reconstruct(parts,dest,root/"report.json")
            self.assertFalse(dest.exists())

    def test_private_path_guard_and_bad_member_names(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                module.check_private_path(root/"public/model.glb")
            for item in ("../x","a/../x","C:/win","/abs","a\\evil","a//b"):
                self.assertFalse(module.safe_archive_name(item),item)
            self.assertTrue(module.safe_archive_name("KayKit Adventurers 2.0/Assets/hero.glb"))


if __name__=="__main__":
    unittest.main()
