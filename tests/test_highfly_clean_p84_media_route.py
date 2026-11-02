"""P84 regression checks: confirm original Vite /media mismatch fix is scoped."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p84_media',ROOT/'scripts/highfly_clean_p84_fix_private_media_routes.py')
p84=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p84)
class P84Tests(unittest.TestCase):
 def test_exact_original_asset_url_branch(self):
  original="function assetUrl(url){const logical=url; if (import.meta.env.DEV) return '/'+logical;}"
  modified=original.replace(p84.MEDIA_OLD,p84.MEDIA_NEW,1)
  self.assertIn("import.meta.env.MODE === 'highfly-clean-private-offline'",modified)
  self.assertNotIn('manifest.generated.ts',p84.MEDIA_NEW)
  self.assertIn('import.meta.env.DEV ||',modified)
 def test_private_only_no_retries_timing(self):
  self.assertEqual(p84.RETRY_OLD,'export const MAX_LOAD_ATTEMPTS = 3;')
  self.assertIn("? 1 : 3",p84.RETRY_NEW)
  self.assertIn('highfly-clean-private-offline',p84.RETRY_NEW)
 def test_models_proof_and_existing_4182_backup(self):
  self.assertIn('models/chars/players/knight.glb',p84.SAMPLES)
  self.assertIn('models/biome/hexb_townhall.glb',p84.SAMPLES)
  self.assertNotEqual(p84.PREV,p84.DIST)
  self.assertNotEqual(p84.TMP_DIST,p84.DIST)
  text=(ROOT/'scripts/highfly_clean_p84_fix_private_media_routes.py').read_text('utf8')
  self.assertIn('hashfile(target)!=hashfile(LAB/',text)
  self.assertIn('DIST.rename(PREV)',text)
  self.assertIn('TMP_DIST.rename(DIST)',text)
  self.assertNotIn('shutil.copytree',text)
  self.assertIn("'unlicensedModelsCopied':0",text)
  self.assertIn("'browserVerified':False",text)
 def test_probe_requires_lab(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as root:
   with patch.object(p84,'LAB',Path(root)/'missing'):
    with self.assertRaisesRegex(RuntimeError,'P84_CLEAN_LAB_MISSING'):
     p84.check()
if __name__=='__main__':unittest.main()
