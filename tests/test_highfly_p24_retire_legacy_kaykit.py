#!/usr/bin/env python3
"""P24 tests: never delete or 'fix' old KayKit with unmatched models or other brands."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p24_retire_legacy_kaykit as p24


class P24LegacySourceTests(unittest.TestCase):
    def test_only_exact_hash_documented_old_kaykit_is_migration_candidate(self):
        old=[
            {"path":"/models/dungeon/anvil.glb","sha256":"abc",
             "status":"EXACT_OLD_KAYKIT_PRESENT","source":"CLAUDECRAFT_PREVIOUS_FREE_CC0"},
            {"path":"/models/props/chest.glb","sha256":"def",
             "status":"ALREADY_CHANGED_OR_ABSENT","source":"CLAUDECRAFT_PREVIOUS_FREE_CC0"},
        ]
        index={"anvil":[{"member":"KayKit Complete V7/KayKit Dungeon Pack 1.1/Assets/gltf/anvil.gltf",
                          "pack":"KayKit Dungeon Pack 1.1","stem":"anvil"}]}
        with patch.object(p24.p23,"legacy_kaykit_inventory",return_value={"items":old}):
            rows=p24.manifest(index)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["method"],"REPLACE_WITH_OWNED_KAYKIT")
        self.assertEqual(rows[1]["method"],"ALREADY_CHANGED_OR_ABSENT")
        self.assertEqual(len(p24.ready(rows)),1)

    def test_unmatched_old_kaykit_must_not_be_deleted(self):
        old=[{"path":"/models/dungeon/not_in_complete.glb","sha256":"abc",
              "status":"EXACT_OLD_KAYKIT_PRESENT"}]
        with patch.object(p24.p23,"legacy_kaykit_inventory",return_value={"items":old}):
            rows=p24.manifest({})
        self.assertEqual(rows[0]["method"],"NO_KAYKIT_SEMANTIC_MATCH")
        self.assertEqual(len(p24.ready(rows)),0)

    def test_non_kaykit_assets_never_part_of_legacy_p21_inventory(self):
        data=[{"path":"/models/foliage/pine_1.glb",
               "status":"EXACT_OLD_KAYKIT_PRESENT","sha256":"foo"}]
        with patch.object(p24.p23,"legacy_kaykit_inventory",return_value={"items":[]}):
            self.assertEqual(p24.manifest({}),[])


if __name__=="__main__":
    unittest.main()
