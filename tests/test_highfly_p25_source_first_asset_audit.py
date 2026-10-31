#!/usr/bin/env python3
"""P25 tests: upstream src/out exact mapping, safe source names and source archive priority."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p25_source_first_asset_audit as p25


class P25ProvenanceTests(unittest.TestCase):
    def test_real_p20_p21_probes_are_independent_and_have_316_union_urls(self):
        from pathlib import Path
        project=Path(__file__).resolve().parents[1]
        first=p25.from_capture(
            project/"reports/highfly_p20_runtime_missing_paths.json",314)
        second=p25.from_capture(
            project/"reports/highfly_p21_fresh_missing_266.json",266)
        outcome=p25.compare_browser_captures(first,second)
        self.assertEqual(outcome["overlapCount"],264)
        self.assertEqual(outcome["firstOnlyCount"],50)
        self.assertEqual(outcome["newInSecondCount"],2)
        self.assertEqual(outcome["uniqueCount"],316)
        self.assertEqual(set(outcome["newInSecondPaths"]),{
            "/textures/loading/eastbrook-mine-duel.webp",
            "/textures/loading/crystal-delve.webp"})

    def test_browser_capture_merge_does_not_count_duplicate_urls_as_fixes(self):
        result=p25.compare_browser_captures(["/models/a.glb","/models/b.glb"],
                                            ["/models/b.glb","/models/c.glb"])
        self.assertEqual(result["union"],[
            "/models/a.glb","/models/b.glb","/models/c.glb"])
        self.assertEqual(result["newInSecondCount"],1)
        with self.assertRaises(RuntimeError):
            p25.compare_browser_captures(["/models/a.glb","/models/a.glb"],[])

    def test_provider_identification_from_actual_raw_source_path(self):
        values={
            "tmp/asset_src/quaternius_village/Fantasy_House_1.glb":"Quaternius",
            "tmp/asset_src/poly_pirate/dock.glb":"Quaternius",
            "tmp/asset_src/kenney_watercraft/boat.glb":"Kenney",
            "tmp/asset_src/kaykit/KayKit-Dungeon/foo.gltf.glb":"KayKit",
            "tmp/asset_src/polyhaven/rust_coarse_01.hdr":"Poly Haven",
            "tmp/asset_src/ambientcg/Ground023.jpg":"ambientCG",
            "tmp/asset_src/loafbrr_mines/rail.glb":"loafbrr",
            "tmp/asset_src/world_project/unique_boss.glb":"UNATTRIBUTED_OR_PROJECT_ART"
        }
        for src,expect in values.items():
            self.assertEqual(p25.provider(src),expect,src)

    def test_source_stem_normalizes_double_extension_and_original_name(self):
        self.assertEqual(p25.source_stem("tmp/asset_src/kaykit/floor_tile_large.gltf.glb"),
                         "floor_tile_large")
        self.assertEqual(p25.source_stem("tmp/asset_src/quaternius_village/Fantasy_House_1.glb"),
                         "fantasy_house_1")

    def test_upstream_specs_provide_unambiguous_out_src_links(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            folder=base/"scripts/assets/specs"
            folder.mkdir(parents=True)
            (folder/"real.json").write_text(json.dumps({"items":[
                {"src":"tmp/asset_src/poly_pirate/dock.glb",
                 "out":"models/biome/beach_dock.glb"},
                {"src":"tmp/asset_src/kaykit/floor_tile_large.gltf.glb",
                 "out":"models/dungeon/floor_tile_large.glb"},
                {"src":"../../BAD_SOURCE","out":"../../unsafe.glb"}
            ]}))
            rows=p25.outspec_index(base)
            self.assertIn("/models/biome/beach_dock.glb",rows)
            self.assertEqual(rows["/models/biome/beach_dock.glb"][0]["sourceProvider"],
                             "Quaternius")
            self.assertEqual(rows["/models/dungeon/floor_tile_large.glb"][0]["sourceProvider"],
                             "KayKit")
            self.assertNotIn("/../../unsafe.glb",rows)

    def test_cannot_count_legacy_free_kaykit_as_new_v7_source(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            owned=base/"KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
            with zipfile.ZipFile(owned,"w") as zip:
                zip.writestr("KayKit Complete V7/KayKit Dungeon Pack 1.1/Assets/gltf/true_source.gltf","{}")
                zip.writestr("KayKit Complete V7/KayKit Dungeon FREE/Assets/gltf/old_free.gltf","{}")
                zip.writestr("KayKit Complete V7/Unknown Unlicensed/Assets/gltf/nope.gltf","{}")
            index,count,providers=p25.source_candidate_index(base/"external",owned)
            self.assertEqual(count,1)
            self.assertIn("true_source",index)
            self.assertNotIn("old_free",index)
            self.assertNotIn("nope",index)

    def test_unknown_local_pack_name_is_not_license_confirmation(self):
        entry={"exactRawSource":"tmp/asset_src/unknown/strange.glb",
               "sourceProvider":"UNATTRIBUTED_OR_PROJECT_ART"}
        row=p25.match_sources([entry],"/models/props/strange.glb",
                              {"strange":[{"file":"strange.glb",
                                           "location":"other.zip",
                                           "providerHint":"UNATTRIBUTED_OR_PROJECT_ART"}]},
                              {"Quaternius":True})
        self.assertEqual(row["match"],"PROJECT_ART_OR_LICENSE_REVIEW")

    def test_identical_basename_matches_proven_source_but_requires_review(self):
        source=[{"exactRawSource":"tmp/asset_src/poly_pirate/dock.glb",
                 "sourceProvider":"Quaternius"}]
        index={"dock":[{"file":"models/dock.glb","location":"quaternius-pirate.zip",
                        "providerHint":"Quaternius"}]}
        result=p25.match_sources(source,"/models/biome/beach_dock.glb",index,
                                 {"Quaternius":True})
        self.assertEqual(result["match"],"LOCAL_EXACT_SOURCE_BASENAME_CANDIDATE_REVIEW")
        self.assertEqual(len(result["matched"]),1)


if __name__=="__main__":
    unittest.main()
