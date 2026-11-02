"""Validate owned SOURCE V7 character alias handling without touching the game."""
import importlib.util
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('hf_owned_v7',ROOT/'scripts/highfly_clean_v0447_owned_characters.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class OwnedV7AliasTests(unittest.TestCase):
 def test_characters_folder_is_not_weapon_folder(self):
  buff=io.BytesIO()
  with zipfile.ZipFile(buff,'w') as zipout:
   zipout.writestr('KayKit Complete V7/KayKit Adventurers/Characters/gltf/Knight.glb',b'glTF')
   zipout.writestr('KayKit Complete V7/KayKit Adventurers/Characters/gltf/Mage.glb',b'glTF')
   zipout.writestr('KayKit Complete V7/KayKit Adventurers/Assets/gltf/sword_1handed.gltf',
    '{"asset":{"version":"2.0"},"meshes":[{"primitives":[]}]}')
  buff.seek(0)
  with zipfile.ZipFile(buff) as z:
   bodies,weapons=mod.build_catalog(z)
  self.assertEqual(len(bodies['knight']),1)
  self.assertTrue(bodies['knight'][0]['member'].endswith('/Characters/gltf/Knight.glb'))
  self.assertEqual(len(bodies['mage']),1)
  self.assertEqual(len(weapons['sword_1handed']),1)
 def test_untrusted_top_level_source_not_accepted(self):
  buff=io.BytesIO()
  with zipfile.ZipFile(buff,'w') as z:
   z.writestr('Random Pack/Characters/gltf/Knight.glb',b'glTF')
   z.writestr('KayKit Complete V7/Characters/gltf/Knight.glb',b'glTF')
  buff.seek(0)
  with zipfile.ZipFile(buff) as z:
   bodies,_=mod.build_catalog(z)
  self.assertNotIn('knight',bodies)
 def test_output_paths_and_source_stems_are_distinct(self):
  self.assertEqual(mod.BODIES['models/chars/players/knight.glb'],'knight')
  self.assertEqual(len(mod.BODIES),7)
  self.assertIn('models/weapons/sword_1handed.glb',mod.WEAPONS)

if __name__=='__main__':
 unittest.main()
