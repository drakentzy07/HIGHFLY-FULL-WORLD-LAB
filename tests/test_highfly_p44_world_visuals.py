import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p44_world_visuals as p
class Tests(unittest.TestCase):
 def sample(self):
  wolf=chr(36)+"{CREATURES}"
  return {
   p.FILES[0]:"  mob_wolf: {\n    url: "+chr(96)+wolf+"/wolf_basic.glb"+chr(96)+",\n    authoredAtlas: true,\n    clips: WOLF_BAKED,\n  },\n"
       "  form_ghost_wolf: {\n    url: "+chr(96)+wolf+"/wolf_basic.glb"+chr(96)+",\n    clips: WOLF_BAKED,\n  },\n"
       "  const npcBaseKey = NPC_KEYS[e.templateId] ?? 'npc_villager';",
   p.FILES[1]:"export async function preloadHighflyCrabAssets(): Promise<void> {",
   p.FILES[2]:("const HIGHFLY_P38_DIRECT_CC0_MEDIA = new Set([\n"
    "  'models/creatures/crab_ability_anims.glb',\n"
    "  // HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD: approved mob paths\n"
    "  'models/creatures/crab_ability_anims.glb',\n"
    "]);"),
   p.FILES[3]:"  preloadHighflyCrabAssets,\n  await preloadHighflyCrabAssets();",
   p.FILES[4]:"const art=Object.freeze({",
  }
 def test_wolf_and_icons(self):
  x=p.patch(self.sample())
  self.assertEqual(x[p.FILES[0]].count("wolf_basic.glb"),0)
  self.assertIn("preloadHighflyWolf",x[p.FILES[1]])
  self.assertIn("await preloadHighflyWolf()",x[p.FILES[3]])
  self.assertIn("ui/items/mother_of_pearl.webp",x[p.FILES[4]])
  self.assertEqual(x[p.FILES[2]].count("'models/creatures/crab_ability_anims.glb',"),2)
  self.assertEqual(x[p.FILES[2]].count("'models/creatures/wolf.glb',"),1)
  self.assertIn("HIGHFLY_P38_DIRECT_CC0_MEDIA",x[p.FILES[2]])
 def test_npc_roles_without_sim_changes(self):
  x=p.patch(self.sample())[p.FILES[0]]
  self.assertIn("NPC_KEYS[e.templateId]",x)
  self.assertIn("marshal_redbrook",x)
 def test_double_application_blocked(self):
  x=p.patch(self.sample())
  with self.assertRaisesRegex(RuntimeError,"P44_ALREADY_APPLIED"):p.patch(x)
 def test_source_drift_blocked(self):
  x=self.sample();x[p.FILES[1]]="other"
  with self.assertRaisesRegex(RuntimeError,"P44_ANCHOR_DRIFT"):p.patch(x)
 def test_original_icons(self):
  for value in p.ICONS.values():self.assertIn("<svg",p.icon(value))
if __name__=="__main__":unittest.main()
