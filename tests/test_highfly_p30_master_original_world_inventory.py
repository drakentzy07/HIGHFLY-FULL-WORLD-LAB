#!/usr/bin/env python3
"""HIGHFLY P30 master audit regression tests (no private pack required)."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p30_master_original_world_inventory as p30

class P30MasterAuditTests(unittest.TestCase):
    def test_all_required_categories_have_classification(self):
        expected={
           "models/chars/players/paladin.glb":"CHARACTERS",
           "models/chars/npc_gear/smith_apron.glb":"NPC",
           "models/creatures/wolf.glb":"MONSTERS",
           "models/weapons/longsword.glb":"WEAPONS",
           "models/props/castle_gate.glb":"STRUCTURES",
           "models/props/medieval_house.glb":"BUILDINGS",
           "models/foliage/pine_1.glb":"FLORA_FAUNA_VEGETATION",
           "models/biome/beach_dock.glb":"SHIPS",
           "textures/terrain/Grass001.webp":"WATER_LAVA_TERRAIN_WEATHER",
           "vfx/spell_fire.png":"SKILLS_VFX",
           "ui/items/loot_chest.webp":"LOOT",
           "ui/skills/fireball.webp":"MENUES_HUD",
           "audio/sfx/sword_hit.ogg":"AUDIO",
           "models/tools/axe.glb":"INTERACTIONS_MOVEMENT",
        }
        for path,category in expected.items():
            self.assertIn(category,p30.categories(path),path)

    def test_same_paladin_npc_uses_player_npc_rig_path_without_class_propagation(self):
        code=("const NPC_KEYS: Record<string, string> = {\n"
              "  brother_halven: 'npc_reliquary_keeper',\n"
              "};\n")
        self.assertEqual(dict(p30.NPC_KEY.findall(p30.ts_table(
            code,r"const NPC_KEYS:\s*Record<string,\s*string>"))),
            {"brother_halven":"npc_reliquary_keeper"})
        self.assertEqual(p30.expand("models/chars/players/paladin.glb"),
                         "/models/chars/players/paladin.glb")
        self.assertEqual(p30.expand("models/chars/" +
            chr(36)+"{PLAYERS}/paladin.glb"),
            "/models/chars/models/chars/players/paladin.glb")

    def test_typed_simulation_id_name_position_and_quests(self):
        raw=("export const RIVER_NPCS: Record<string, NpcDef> = {\n"
             "  ferryman_odo: {\n"
             "    id: 'ferryman_odo',\n"
             "    name: 'Ferryman Odo',\n"
             "    title: 'Keeper of the Crossing',\n"
             "    pos: { x: -356, z: 214 },\n"
             "    questIds: ['q_one', 'q_two'],\n"
             "  },\n"
             "};\n"
             "export const RIVER_MOBS: Record<string, MobTemplate> = {\n"
             "  coastal_wolf: {\n"
             "    name: 'Coastal Wolf',\n"
             "    family: 'beast',\n"
             "  },\n"
             "};\n")
        rows=p30.content_records_from_source(raw,"src/sim/content/river.ts")
        self.assertEqual(len(rows),2)
        npc,mob=rows
        self.assertEqual(npc["kind"],"NPC")
        self.assertEqual(npc["id"],"ferryman_odo")
        self.assertEqual(npc["displayName"],"Ferryman Odo")
        self.assertEqual(npc["positionX"],"-356")
        self.assertEqual(npc["positionZ"],"214")
        self.assertEqual(npc["questIds"],["q_one","q_two"])
        self.assertEqual(mob["family"],"beast")

    def test_item_equipment_role_is_lead_not_auto_gameplay_rewrite(self):
        row={"id":"sword_oak", "displayName":"Oak Sword","kind":"ITEMS_LOOT_EQUIPMENT"}
        roles=p30.content_classification(row)
        self.assertIn("WEAPONS",roles)
        self.assertIn("ITEMS",roles)
        self.assertIn("LOOT",roles)
        row["id"]="ancient_robe"
        self.assertIn("ARMOR",p30.content_classification(row))

    def test_source_literal_matches_full_url_not_generic_name(self):
        terms={m.group(1) for m in p30.TOKENS.finditer(
            'const x="/models/chars/players/paladin.glb"; const y="paladin.glb";')}
        self.assertIn("models/chars/players/paladin.glb",terms)
        self.assertNotIn("paladin.glb",terms)

if __name__=="__main__":
    unittest.main()
