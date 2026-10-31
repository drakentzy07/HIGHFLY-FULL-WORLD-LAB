#!/usr/bin/env python3
"""HIGHFLY P28 original texture creator tests without external dependencies."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p28_original_runtime_textures as p28

class P28FirstPartyImageTests(unittest.TestCase):
    def test_all_9_blocking_textures_and_2_lazy_loading_images(self):
        self.assertEqual(len(p28.URLS),11)
        self.assertEqual(sum(x.startswith("/textures/loading/") for x in p28.URLS),2)
        self.assertIn("/vfx/fel_meteor_impact.png",p28.URLS)
        self.assertIn("/textures/props/eastbrook_realm_builder_impostor.webp",p28.URLS)

    def test_every_generated_texture_is_original_valid_svg_source(self):
        for url in p28.URLS:
            with self.subTest(url=url):
                image=p28.original_svg(url)
                w,h,_=p28.URLS[url]
                self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"',image)
                self.assertIn('width="%d" height="%d"'%(w,h),image)
                self.assertTrue(image.endswith("</svg>"))
                self.assertNotIn("ClaudeCraft",image)

    def test_both_material_atlases_have_16_distinct_texture_cells(self):
        for fen in (True,False):
            content=p28.make_atlas(fen)
            self.assertEqual(content.count('width="128" height="128"'),16)

    def test_roughness_uses_correct_packed_metalness(self):
        content=p28.make_rough(True)
        self.assertIn('fill="rgb(132,132,183)"',content)
        self.assertEqual(content.count('width="128" height="128"'),16)
        east=p28.make_rough(False)
        self.assertIn('fill="rgb(204,204,204)"',east)

    def test_normal_map_has_correct_tangent_space_neutral_blue(self):
        self.assertIn('rgb(128,128,255)',p28.original_svg(
            "/textures/eastbrook_surface_normal.webp"))

    def test_generated_monument_and_meteor_have_transparency(self):
        for url in ("/textures/props/eastbrook_realm_builder_impostor.webp",
                    "/vfx/fel_meteor_impact.png"):
            image=p28.original_svg(url)
            self.assertNotIn('<rect width="512" height="512"',image)

if __name__=="__main__":
    unittest.main()
