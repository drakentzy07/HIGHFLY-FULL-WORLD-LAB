#!/usr/bin/env python3
"""P23 safety + semantic-replacement tests (do not require the user's private ZIP)."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p22_owned_asset_rebuilder as p22
import highfly_p23_real_kaykit_upgrade as p23


def fake_zip(path):
    with zipfile.ZipFile(path,"w") as archive:
        for pack,stem in (
            ("KayKit Dungeon Pack 1.1","anvil"),
            ("KayKit Dungeon Pack 1.1","chain"),
            ("KayKit Dungeon Pack 1.1","chest"),
            ("KayKit Furniture Bits 1.0","chest"),
            ("KayKit Medieval Hexagon Pack 1.0.1","building_windmill"),
            ("KayKit Halloween Bits 1.0","gravestone_B"),
            ("KayKit Resource Bits 1.0","ore_vein"),
            ("KayKit Forest Nature Pack 1.0","willow"),
            ("Unknown Unlicensed Pack","castle"),
        ):
            archive.writestr(
                "KayKit Complete V7/"+pack+"/Assets/gltf/"+stem+".gltf",
                '{"asset":{"version":"2.0"},"meshes":[{"primitives":[{}]}]}')


class P23OwnedArtTests(unittest.TestCase):
    def test_user_owned_complete_archive_pack_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"kaykit.zip"
            fake_zip(path)
            with zipfile.ZipFile(path) as archive:
                table,index=p23.zip_index(archive)
                self.assertGreater(len(table),6)
                self.assertEqual(len(index["anvil"]),1)
                self.assertNotIn("castle",index)
                self.assertIn("building_windmill",index)
                r=p23.match_archive("/models/biome/hex_windmill.glb",index)
                self.assertEqual(r["method"],"REPLACE_WITH_OWNED_KAYKIT")
                self.assertIn("Medieval Hexagon",r["sourcePack"])
                r=p23.match_archive("/models/dungeon/ignivar_prop_anvil.glb",index)
                self.assertEqual(r["sourceStem"],"anvil")
                r=p23.match_archive("/models/props/banker_chest.glb",index)
                self.assertEqual(r["sourceStem"],"chest")
                self.assertIn("Furniture",r["sourcePack"])
                r=p23.match_archive("/models/resources/gather_ore_vein.glb",index)
                self.assertEqual(r["sourceStem"],"ore_vein")

    def test_wrapper_is_not_pack_and_pack_at_archive_root_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"mixed-sources.zip"
            with zipfile.ZipFile(path,"w") as archive:
                archive.writestr(
                    "KayKit Complete V7/Unknown Unlicensed Pack/Assets/gltf/unlicensed.gltf",
                    "{}")
                archive.writestr(
                    "KayKit Complete V7/Assets/gltf/wrapper_only.gltf",
                    "{}")
                archive.writestr(
                    "KayKit Dungeon Pack 1.1/Assets/gltf/valid_asset.gltf",
                    "{}")
                archive.writestr(
                    "KayKit Complete V7/KayKit Dungeon Pack 1.1/Assets/gltf/valid_nested.gltf",
                    "{}")
            with zipfile.ZipFile(path) as archive:
                table,index=p23.zip_index(archive)
            self.assertEqual(len(table),4)
            self.assertNotIn("unlicensed",index)
            self.assertNotIn("wrapper_only",index)
            self.assertEqual(index["valid_asset"][0]["pack"],"KayKit Dungeon Pack 1.1")
            self.assertEqual(index["valid_nested"][0]["pack"],"KayKit Dungeon Pack 1.1")

    def test_only_source_archive_models_no_free_variants_or_legacy_stage_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"Kaykit_CompleteV7_source.zip"
            with zipfile.ZipFile(path,"w") as archive:
                archive.writestr("KayKit Complete V7/KayKit Dungeon Pack 1.1/Assets/gltf/anvil.gltf","{}")
                archive.writestr("KayKit Complete V7/KayKit Dungeon FREE/Assets/gltf/anvil_free.gltf","{}")
                archive.writestr("KayKit Complete V7/KayKit Halloween Demo/Assets/gltf/gravestone.gltf","{}")
                archive.writestr("KayKit Complete V7/Unknown Unlicensed Pack/Assets/gltf/sword.gltf","{}")
                archive.writestr("KayKit Complete V7/KayKit Dungeon Pack 1.1/Some/Other/gltf/invalid.gltf","{}")
            with zipfile.ZipFile(path) as archive:
                table,index=p23.zip_index(archive)
            self.assertEqual(len(table),5)
            self.assertEqual(sum(len(x) for x in index.values()),1)
            self.assertIn("anvil",index)
            self.assertNotIn("anvil_free",index)
            self.assertNotIn("gravestone",index)
            self.assertNotIn("sword",index)
            self.assertNotIn("invalid",index)
            self.assertEqual(index["anvil"][0]["source"],"USER_OWNED_KAYKIT_COMPLETE_SOURCE_V7")
            model=p23.match_archive("/models/dungeon/ignivar_prop_anvil.glb",index)
            self.assertEqual(model["method"],"REPLACE_WITH_OWNED_KAYKIT")
            self.assertEqual(model["sourceZipMember"],index["anvil"][0]["member"])

    def test_preserve_proven_quaternius_but_do_not_copy_old_kaykit(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            private=Path(temp)
            public=private/"public/models"
            (public/"foliage").mkdir(parents=True)
            (public/"dungeon").mkdir(parents=True)
            a=public/"foliage/fern.glb"
            b=public/"dungeon/wall.glb"
            p22.build_model("/models/foliage/fern.glb",a)
            p22.build_model("/models/dungeon/wall.glb",b)
            report=private/"P21.json"
            report.write_text(json.dumps({"installed":[
                {"path":"/models/foliage/fern.glb",
                 "sha256":p23.fingerprint(a),"provenance":"CC0_QUATERNIUS"},
                {"path":"/models/dungeon/wall.glb",
                 "sha256":p23.fingerprint(b),"provenance":"CC0_KAYKIT"}
            ]}))
            with patch.object(p23,"STAGE",private), patch.object(p23,"P21_REPORT",report):
                proof=p23.staged_proof()
            self.assertIn("/models/foliage/fern.glb",proof)
            self.assertNotIn("/models/dungeon/wall.glb",proof)
            self.assertEqual(proof["/models/foliage/fern.glb"]["origin"],"CC0_QUATERNIUS")

    def test_never_replace_structural_contracts(self):
        paths=(
            "/models/mounts/valorsteed.glb",
            "/models/creatures/leaping_fish.glb",
            "/models/props/kmed_home_A_hollow.glb",
            "/models/props/eastbrook_ferry.glb",
            "/models/props/wickharbor_harbor.glb",
            "/models/props/fenbridge_crooked_reed_inn.glb",
            "/models/props/delve_module_exit.glb",
            "/models/props/streetlamp_wraithwood_ghost.glb",
            "/models/dungeon/ignivar_prop_bridge_floor.glb",
            "/models/dungeon/ignivar_prop_lift_arch_beam.glb",
            "/models/battleground/rune_damage.glb",
        )
        for url in paths:
            self.assertTrue(p23.is_structural(url),url)
            self.assertEqual(p23.match_archive(url,{})["method"],
                             "KEEP_P22_CONTRACT_REVIEW")

    def test_exact_stems_and_curated_aliases_only(self):
        self.assertEqual(p23.model_stems("/models/props/fallback_crate.glb"),
                         ["fallback_crate","crate"])
        self.assertEqual(p23.model_stems("/models/dungeon/ignivar_prop_anvil.glb"),
                         ["ignivar_prop_anvil","anvil"])
        self.assertNotIn("crate",p23.model_stems("/models/props/fenbridge_hesk_tannery.glb"))
        self.assertNotIn("house",p23.model_stems("/models/props/dragon_hoard.glb"))

    def test_provenance_guard_rejects_any_tampered_provisional_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"owned.glb"
            p22.build_model("/models/props/fallback_crate.glb",target)
            good=p23.fingerprint(target)
            self.assertTrue(p23.is_p22_file(target,good))
            target.write_bytes(target.read_bytes()+b"NOT_ORIGINAL")
            self.assertFalse(p23.is_p22_file(target,good))

    def test_loading_screen_art_is_original_and_semantically_named(self):
        for url,title in (
            ("/textures/loading/fenbridge-rain-skiff.webp","FENBRIDGE"),
            ("/textures/loading/hollow-crypt-empty.webp","HOLLOW CRYPT"),
        ):
            svg=p23.loading_svg(url)
            self.assertIn("<svg ",svg)
            self.assertIn(title,svg)
            self.assertIn("HIGHFLY ORIGIN",svg)
            self.assertNotIn("ClaudeCraft",svg)

    def test_ambiguity_does_not_pick_random_file(self):
        entries={"anvil":[
            {"member":"a","pack":"KayKit Dungeon Pack 1.1","stem":"anvil"},
            {"member":"b","pack":"KayKit Dungeon Pack 1.1","stem":"anvil"},
        ]}
        row=p23.match_archive("/models/dungeon/ignivar_prop_anvil.glb",entries)
        self.assertEqual(row["method"],"AMBIGUOUS_KAYKIT_VARIANTS")


if __name__=="__main__":
    unittest.main()
