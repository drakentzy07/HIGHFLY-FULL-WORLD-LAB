"""HIGHFLY CLEAN read-only reuse audit safety: P8/P33/P34/P37 mapping before copy."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hf_prior_reuse',ROOT/'scripts/highfly_clean_reuse_previous_solutions_audit.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class PreviousFixAuditTests(unittest.TestCase):
 def test_p8_seven_building_mapping_is_explicit(self):
  buildings=[p for p in m.PATHS if p.startswith('models/biome/')]
  self.assertEqual(len(buildings),7)
  self.assertIn('models/biome/hexb_townhall.glb',buildings)
  self.assertIn('models/biome/hex_church.glb',buildings)
 def test_warrior_modular_known_missing_and_npcrigs_are_distinct(self):
  self.assertIn('models/chars/modular/warrior_modular.glb',m.PATHS)
  self.assertIn('models/chars/players/knight.glb',m.PATHS)
  self.assertIn('models/chars/players/mage.glb',m.PATHS)
  self.assertNotEqual(m.PATHS.index('models/chars/modular/warrior_modular.glb'),
   m.PATHS.index('models/chars/players/knight.glb'))
 def test_bom_encoded_p30_csv_is_readable(self):
  with tempfile.TemporaryDirectory() as root:
   file=Path(root)/'P30_ALL_MEDIA_AND_USAGE.csv'
   file.write_text('path,status\\nmodels/props/fence.glb,CC0\\n',encoding='utf-8-sig')
   rows=m.rows_for_csv(file,'models/props/fence.glb')
   self.assertEqual(len(rows),1)
   self.assertEqual(rows[0]['path'],'models/props/fence.glb')

 def test_unsafe_paths_rejected_and_no_copy(self):
  self.assertTrue(m.safe_rel('models/props/fence.glb'))
  for value in ('../outside.glb','/models/props/fence.glb','models/../../secret.glb','bad&name.glb'):
   self.assertFalse(m.safe_rel(value))
  body=(ROOT/'scripts/highfly_clean_reuse_previous_solutions_audit.py').read_text('utf8')
  self.assertIn("'assetCopyCount':0",body)
  self.assertNotIn("shutil.copyfile",body)
  self.assertNotIn("shutil.copy2",body)
  self.assertNotIn("os.rename",body)

if __name__=='__main__':unittest.main()
