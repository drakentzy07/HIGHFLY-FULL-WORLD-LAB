#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p40_icon_art as p
class Tests(unittest.TestCase):
 def test_complete_inventory_and_classes(self):
  self.assertEqual(len(p.ART),20)
  for n in ('ui/items/recruit_tunic.webp','ui/items/worn_sword.webp',
            'ui/items/eastbrook_buckler.webp','ui/classes/druid.webp'):
   self.assertIn(n,p.ART)
 def test_original_vector_art(self):
  for label,shape,color in p.ART.values():
   self.assertIn('<svg',p.svg(label,shape,color))
   self.assertIn('viewBox="0 0 100 100"',p.svg(label,shape,color))
 def test_fallback_only_known_missing_images(self):
  self.assertIn('Object.freeze',p.JS)
  self.assertIn('img.dataset.highflyP40Applied',p.JS)
if __name__=="__main__":unittest.main()
