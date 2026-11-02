"""P74 safety tests: unique licensed source, no project-only import, no stage writes."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("p74", ROOT/"scripts/highfly_p74_integral_cc0_nine_classes.py")
p74=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p74)

class P74Safety(unittest.TestCase):
 def test_exact_spec_and_credit_only(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   original=root/"reference"
   stage=root/"stage"
   for src in ("models/approved.glb","models/project_only.glb","models/ambiguous.glb"):
    f=original/"public"/src
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_bytes(b"glTFdummy")
   specs={
    "/models/approved.glb":[{"exactRawSource":"tmp/asset_src/quaternius/approved.glb",
      "sourceProvider":"Quaternius","upstreamSpec":"specs/a.json"}],
    "/models/project_only.glb":[{"exactRawSource":"tmp/asset_src/unknown_pack/project.glb",
      "sourceProvider":"UNATTRIBUTED_OR_PROJECT_ART","upstreamSpec":"specs/b.json"}],
    "/models/ambiguous.glb":[{"exactRawSource":"tmp/asset_src/quaternius/amb.glb",
      "sourceProvider":"Quaternius","upstreamSpec":"specs/c.json"},
     {"exactRawSource":"tmp/asset_src/craftpix/amb.glb",
      "sourceProvider":"UNATTRIBUTED_OR_PROJECT_ART","upstreamSpec":"specs/d.json"}]
   }
   with patch.object(p74,"ORIGINAL",original),patch.object(p74,"STAGE",stage),\
     patch.object(p74.p25,"outspec_index",return_value=specs),\
     patch.object(p74.p25,"credited",return_value={"Quaternius":True}),\
     patch.object(p74.p21,"check_binary",return_value=True):
    approved,blocked,_,_=p74.make_proof_index()
   self.assertEqual([r["url"] for r in approved],["/models/approved.glb"])
   self.assertEqual(blocked["AMBIGUOUS_CONVERSION_SPEC"],1)
   self.assertEqual(blocked["PROJECT_ONLY_OR_LICENSE_UNVERIFIED_OR_OWNED_SOURCE_REQUIRED"],1)

 def test_overlay_symlinks_keep_original_binary_untouched(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);source=root/"source";overlay=root/"overlay"
   f=source/"nested/knight.glb";f.parent.mkdir(parents=True);f.write_bytes(b"existing")
   p74.mirror_to_overlay(source,overlay)
   target=overlay/"nested/knight.glb"
   self.assertTrue(target.is_symlink())
   self.assertEqual(target.read_bytes(),b"existing")
   self.assertEqual(f.read_bytes(),b"existing")

 def test_overlay_rejects_nested_symlinks_not_verified(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);source=root/"source";source.mkdir()
   (source/"external.glb").symlink_to(root/"other")
   with self.assertRaisesRegex(RuntimeError,"SYMLINK"):
    p74.mirror_to_overlay(source,root/"overlay")

 def test_creator_uses_original_buttons_not_fake_controls(self):
  self.assertIn("body #offline-select .mini-class-row",p74.EXTRA_CSS)
  self.assertIn("state.classesVisible.length",p74.JS_TEXT)
  self.assertNotIn("createElement('button')",p74.JS_TEXT)
  self.assertEqual(len(p74.CLASSES),9)
  self.assertEqual(len(set(p74.CLASSES)),9)

if __name__=="__main__":
 unittest.main()
