#!/usr/bin/env python3
"""P26 regression safety tests for exact original CC0 model restoration."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p22_owned_asset_rebuilder as p22
import highfly_p26_restore_original_non_kaykit_cc0 as p26


class ExactNonKaykitCC0Tests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.stage=self.root/"stage"
        self.reference=self.root/"original"
        self.stage.mkdir()
        self.reference.mkdir()
        self.targets=[]
        for name in ("pine_2","floor_tile_large","ignivar_prop_beam","forge","mystery"):
            file=self.stage/"public/models/foliage"/(name+".glb")
            file.parent.mkdir(parents=True,exist_ok=True)
            p22.build_model("/models/foliage/"+name+".glb",file)
            up=self.reference/"public/models/foliage"/(name+".glb")
            up.parent.mkdir(parents=True,exist_ok=True)
            p22.build_model("/models/foliage/"+name+".glb",up)
            self.targets.append((name,p26.p12.digest(file)))

    def evaluate(self,name,specs,credit):
        url="/models/foliage/"+name+".glb"
        sha=next(h for n,h in self.targets if n==name)
        with patch.object(p26,"STAGE",self.stage),patch.object(p26,"REFERENCE",self.reference):
            return p26.evaluate(url,specs,credit,sha)

    def test_exact_quaternius_cc0_can_recover_original(self):
        url="/models/foliage/pine_2.glb"
        row=self.evaluate("pine_2",{url:[{
            "exactRawSource":"tmp/asset_src/quaternius_nature/extracted/glTF/Pine_2.gltf",
            "sourceProvider":"Quaternius","upstreamSpec":"scripts/assets/specs/foliage.json"
        }]},{"Quaternius":True})
        self.assertEqual(row["decision"],"EXACT_CC0_ORIGINAL_READY")
        self.assertEqual(row["sourceProvider"],"Quaternius")
        self.assertTrue(row["upstreamSha256"])

    def test_old_kaykit_explicitly_rejected_even_if_cc0(self):
        url="/models/foliage/floor_tile_large.glb"
        row=self.evaluate("floor_tile_large",{url:[{
            "exactRawSource":"tmp/asset_src/kaykit/KayKit-Dungeon-Remastered-1.0/floor_tile_large.gltf",
            "sourceProvider":"KayKit","upstreamSpec":"scripts/assets/specs/dungeon.json"
        }]},{"KayKit":True})
        self.assertEqual(row["decision"],"EXCLUDE_OLD_KAYKIT_USE_OWNED_V7")

    def test_project_art_explicitly_rejected(self):
        url="/models/foliage/ignivar_prop_beam.glb"
        row=self.evaluate("ignivar_prop_beam",{url:[{
            "exactRawSource":"tmp/asset_src/ignivar/beam.glb",
            "sourceProvider":"UNATTRIBUTED_OR_PROJECT_ART",
            "upstreamSpec":"scripts/assets/specs/ignivar.json"
        }]},{})
        self.assertEqual(row["decision"],"RESTRICTED_OR_UNKNOWN_OR_PROJECT_ART")

    def test_no_spec_is_not_a_license(self):
        row=self.evaluate("mystery",{},{"Quaternius":True})
        self.assertEqual(row["decision"],"NO_EXACT_SOURCE_CONVERSION_SPEC")

    def test_cc0_credit_not_automatic_without_matching_credits(self):
        url="/models/foliage/forge.glb"
        specs={url:[{
            "exactRawSource":"tmp/asset_src/kenney/forge.glb",
            "sourceProvider":"Kenney","upstreamSpec":"scripts/assets/specs/props.json"
        }]}
        row=self.evaluate("forge",specs,{"Kenney":False})
        self.assertEqual(row["decision"],"CC0_CREDITS_MISSING")

    def test_disagreeing_source_specs_fail_closed(self):
        url="/models/foliage/forge.glb"
        specs={url:[
            {"exactRawSource":"tmp/asset_src/kenney/forge_1.glb","sourceProvider":"Kenney","upstreamSpec":"a.json"},
            {"exactRawSource":"tmp/asset_src/kenney/forge_2.glb","sourceProvider":"Kenney","upstreamSpec":"b.json"}]}
        row=self.evaluate("forge",specs,{"Kenney":True})
        self.assertEqual(row["decision"],"MULTIPLE_OR_AMBIGUOUS_SOURCE_SPECS")


if __name__=="__main__":
    unittest.main()
