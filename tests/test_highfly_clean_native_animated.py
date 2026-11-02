"""Animated character pipeline P0 regression safety checks (no user archive access)."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("hfnativeanimated",ROOT/"scripts/highfly_clean_v0447_rebuild_animated_characters.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CleanAnimatedTest(unittest.TestCase):
 def test_unique_source_alias_and_animation_donor_only(self):
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w') as z:
   z.writestr("KayKit Complete V7/KayKit Adventurers 2.0/Characters/gltf/Knight.glb",b"glTF")
   z.writestr("KayKit Complete V7/KayKit Character Animations 1.1/Animations/gltf/Rig_Medium/Rig_Medium_General.glb",b"glTF")
   z.writestr("Random Pack/Characters/gltf/Knight.glb",b"glTF")
  buf.seek(0)
  with zipfile.ZipFile(buf) as z:
   tab=mod.p12.zip_members(z)
   m,p=mod.match_exact_member(tab,
    "tmp/asset_src/kaykit/KayKit Adventurers 2.0/Characters/gltf/Knight.glb","body")
   self.assertIsNone(p)
   self.assertEqual(len(m),1)
   self.assertTrue(m[0].endswith("/Characters/gltf/Knight.glb"))
   donors,_=mod.match_exact_member(tab,
    "tmp/asset_src/kaykit/KayKit Character Animations 1.1/Animations/gltf/Rig_Medium/Rig_Medium_General.glb","donor")
   self.assertEqual(len(donors),1)
   self.assertIn("Character Animations",donors[0])
 def test_paladin_source_must_be_helmet_variant(self):
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w') as z:
   z.writestr("KayKit Complete V7/KayKit Paladin/characters/gltf/Paladin.glb",b"glTF")
   z.writestr("KayKit Complete V7/KayKit Paladin/characters/gltf/Paladin_with_Helmet.glb",b"glTF")
  buf.seek(0)
  with zipfile.ZipFile(buf) as z:
   tab=mod.p12.zip_members(z)
   m,_=mod.match_exact_member(tab,
    "tmp/asset_src/kaykit/Paladin/characters/gltf/Paladin_with_Helmet.glb","body")
   self.assertEqual(len(m),1)
   self.assertIn("with_Helmet",m[0])
 def test_no_pretend_source_when_absent(self):
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w') as z:
   z.writestr("KayKit Complete V7/KayKit Adventurers 2.0/Characters/gltf/Knight.glb",b"glTF")
  buf.seek(0)
  with zipfile.ZipFile(buf) as z:
   tab=mod.p12.zip_members(z)
   hits,_=mod.match_exact_member(tab,
    "tmp/asset_src/kaykit/KayKit Character Animations 1.1/Animations/gltf/Rig_Medium/Rig_Medium_General.glb","donor")
   self.assertEqual(hits,[])

if __name__=="__main__":
 unittest.main()
