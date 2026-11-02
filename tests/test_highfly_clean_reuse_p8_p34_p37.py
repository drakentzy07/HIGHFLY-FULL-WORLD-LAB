"""Regression checks for reuse of ORIGINAL P8/P34/P36/P37 on CLEAN, port 4182."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_reuse_p8p37",ROOT/"scripts/highfly_clean_reuse_p8_p34_p37_private_build.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class P8P34P37ReuseTests(unittest.TestCase):
 def test_seven_p8_building_names_unchanged(self):
  self.assertEqual(len(m.p8.BUILDINGS),7)
  self.assertEqual(m.p8.BUILDINGS['townhall'],'hexb_townhall.glb')
  self.assertEqual(m.p8.BUILDINGS['church'],'hex_church.glb')
 def test_generated_private_preview_config_is_valid(self):
  conf=m.makeconfig()
  self.assertIn('highfly-reuse-p8-p37-dist',conf)
  self.assertIn("port:4182",conf)
  self.assertIn("isOfflineModeAvailable",conf)
  with tempfile.TemporaryDirectory() as d:
   cfg=Path(d)/'vite.config.mjs';cfg.write_text(conf,'utf8')
   p=subprocess.run(['node','--check',str(cfg)],text=True,capture_output=True)
   self.assertEqual(p.returncode,0,p.stderr)
 def test_reuses_original_p34_p36_p37_transforms(self):
  index=m.ORIG/'src/render/characters/index.ts'
  manifest=m.ORIG/'src/render/characters/manifest.ts'
  if not index.is_file() or not manifest.is_file():
   self.skipTest('Pinned original ClaudeCraft checkout not mounted')
  before_idx=index.read_text('utf8')
  before_manifest=manifest.read_text('utf8')
  modified=m.p34.prepare(before_idx,before_manifest,True,True)
  self.assertIn(m.p34.MARK,modified[m.FILES[0]])
  next_idx=m.apply_p36(modified[m.FILES[0]])
  self.assertIn(m.p36.MARK,next_idx)
  after=m.p37.patch_manifest(modified[m.FILES[1]])
  self.assertIn(m.p37.MARK,after)
  self.assertIn("wayfarer_bryn",after)
  self.assertIn("npc_reliquary_keeper",after)
  # The native class definitions are not redefined.
  self.assertEqual(before_manifest.count('const MOB_KEYS: Record<string, string> = {'),
   after.count('const MOB_KEYS: Record<string, string> = {'))
  self.assertIn("if (def.modular) continue;",after)
 def test_no_mass_import_or_unlicensed_copy(self):
  txt=(ROOT/'scripts/highfly_clean_reuse_p8_p34_p37_private_build.py').read_text('utf8')
  self.assertIn('sha(old)!=x.get',txt)
  self.assertIn('p34.prepare',txt)
  self.assertIn('p37.patch_manifest',txt)
  self.assertIn('p36.PATCH',txt)
  self.assertIn("'publicReleaseApproved':False",txt)
  self.assertNotIn('shutil.copytree(ORIG',txt)

if __name__=='__main__':unittest.main()
