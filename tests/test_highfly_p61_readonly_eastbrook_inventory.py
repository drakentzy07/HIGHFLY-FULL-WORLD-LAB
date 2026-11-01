"""P61 read-only inventory parses authorship without touching world files."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location(
    "highfly_p61_readonly_eastbrook_inventory",
    Path(__file__).resolve().parents[1]/"scripts/highfly_p61_readonly_eastbrook_inventory.py")
p61=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p61)


class TestP61(unittest.TestCase):
    def test_building_ids_and_asset_urls(self):
        rows=[]
        for k in range(11):
            rows.append("makeBuilding('eastbrook_id_%02d','/models/biome/hexb_home_a.glb',"
                        "'house',{x:%d,z:-108},6.9,9.4,5.6,0.2),"%(k,k))
        code="const BUILDINGS = [\n"+ "\n".join(rows)+"\n] as const;"
        parsed=p61.parse_buildings(code)
        self.assertEqual(len(parsed),11)
        self.assertEqual(parsed[0]["originalAssetUrl"],"/models/biome/hexb_home_a.glb")
        self.assertEqual(parsed[10]["x"],10.0)

    def test_two_official_market_stalls(self):
        code="""const MARKET_STALL_SPECS = [
        ['eastbrook_market_stall_world_market', 'gold', { x: -20.5, z: -94 }, 2.4805494847391065],
        ['eastbrook_market_stall_provisions', 'green', { x: -19, z: -108 }, 0.6610431688506869],
        ] as const;"""
        items=p61.parse_stalls(code)
        self.assertEqual(len(items),2)
        self.assertEqual(items[1]["id"],"eastbrook_market_stall_provisions")
        self.assertEqual(items[1]["z"],-108)
        self.assertEqual(items[1]["height"],2.7)

    def test_nested_calls_not_split_at_facing_toward(self):
        code="const NPCS = [\n"
        for k in range(10):
            code += ("makeNpc('npc_%02d', POSITION, facingToward(POSITION, CENTER), "
                     "'shop_%02d'),\n")%(k,k)
        code += "] as const;"
        rows=p61.parse_npcs(code)
        self.assertEqual(len(rows),10)
        self.assertIn("facingToward(POSITION, CENTER)", rows[0]["placementCode"])
        self.assertEqual(rows[0]["namedAnchorIds"],["shop_00"])

    def test_role_map_is_data_never_exec(self):
        src="ROLES={'weaver_ottilie':'druid','fisherman_brandt':'rogue'}\n"
        self.assertEqual(p61.assigned_roles_from_p44(src)["weaver_ottilie"],"druid")
        self.assertEqual(p61.role_from_base("npc_smith"),"barbarian")
        self.assertEqual(p61.role_from_base("npc_villager"),"rogue")

    def test_binary_provenance_no_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original=root/"original";stage=root/"stage"
            for home,data in ((original,b"real"),(stage,b"other")):
                file=home/"public/models/props/eastbrook_market_stall.glb"
                file.parent.mkdir(parents=True)
                file.write_bytes(data)
            with patch.object(p61,"ORIGINAL",original),patch.object(p61,"STAGE",stage):
                info=p61.local_asset_info("/models/props/eastbrook_market_stall.glb")
            self.assertTrue(info["original"]["present"])
            self.assertTrue(info["highflyStage"]["present"])
            self.assertFalse(info["matchingBytes"])
            self.assertIn("UNKNOWN",info["licenseDecision"])
            self.assertEqual((stage/"public/models/props/eastbrook_market_stall.glb").read_bytes(),b"other")

    def test_invalid_or_unknown_paths_fail_closed(self):
        self.assertEqual(p61.local_asset_info("/foo/../../../weird.glb")["status"],
                         "not_a_safe_glb_path")
        with self.assertRaisesRegex(RuntimeError,"P61_EXPECTED_TWO_MARKET_STALLS"):
            p61.parse_stalls("const MARKET_STALL_SPECS = [] as const;")


if __name__=="__main__":
    unittest.main()
