"""P62 contracts: licensed CC0 market replacement and no generic warrior NPC fallback."""
from __future__ import annotations
import importlib.util,json,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

DIR=Path(__file__).resolve().parents[1]/'scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,DIR/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

p36=load('highfly_p36_npc_visible_fallback')
p62=load('highfly_p62_closeout_market_npc')

class P62Tests(unittest.TestCase):
    def test_exact_p36_fallback_source(self):
        src='// other program code\n'+p36.PATCH
        output=p62.patch_index(src)
        self.assertIn('HIGHFLY_P62_ROLE_PRESERVING_FALLBACK',output)
        self.assertIn("highflyP62Role ?? roleRig",output)
        self.assertIn("key.slice('highfly_npc_'.length)",output)
        self.assertIn("highfly_npc_(knight|mage|rogue|barbarian|paladin|druid)",output)
        self.assertIn("'player_warrior'",output)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p62.patch_index(output)

    def test_fail_closed_on_incompatible_visual_factory(self):
        with self.assertRaisesRegex(RuntimeError,'P36_ORIGINAL_FALLBACK_MISSING'):
            p62.patch_index("no fallback")
        with self.assertRaisesRegex(RuntimeError,'FALLBACK_ANCHOR_DRIFT'):
            p62.patch_index("// HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK")

    def test_licensed_market_exact_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            specs=root/'scripts/assets/specs/props.json'
            specs.parent.mkdir(parents=True)
            spec={'items':[{'src':'tmp/asset_src/quaternius_village/Market_Stand_1.glb',
                            'out':'models/props/market_stand_1.glb','type':'static'}]}
            specs.write_text(json.dumps(spec))
            credits=root/'CREDITS.md'
            credits.write_text('| Medieval Village Pack (houses, inn, blacksmith, well, market, cart) | Quaternius | link | CC0 1.0 | Yes |\n')
            source=root/p62.SRC
            source.parent.mkdir(parents=True)
            source.write_bytes(struct.pack('<4sII',b'glTF',2,12))
            with patch.object(p62,'ORIGINAL',root):
                result=p62.licensed_quaternius_source()
            self.assertEqual(result['license'],'CC0 1.0')
            self.assertEqual(result['provider'],'Quaternius')
            self.assertEqual(result['sizeBytes'],12)
            self.assertTrue(source.is_file())

    def test_unlisted_project_asset_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            specs=root/'scripts/assets/specs/props.json'
            specs.parent.mkdir(parents=True)
            specs.write_text(json.dumps({'items':[{'src':'tmp/asset_src/eastbrook_town/market_stall-final.glb',
                                  'out':'models/props/market_stand_1.glb','type':'static'}]}))
            (root/'CREDITS.md').write_text('Project asset | With the project only')
            with patch.object(p62,'ORIGINAL',root):
                with self.assertRaisesRegex(RuntimeError,'P62_CC0_MARKET_SOURCE_SPEC_CHANGED'):
                    p62.licensed_quaternius_source()

    def test_protected_game_files_never_edited(self):
        src=(DIR/'highfly_p62_closeout_market_npc.py').read_text()
        self.assertIn("INDEX='src/render/characters/index.ts'",src)
        self.assertIn("DST='public/models/props/eastbrook_market_stall.glb'",src)
        self.assertNotIn("(STAGE/'src/sim/",src)
        self.assertNotIn("ORIGINAL/SRC,dst",src.replace("shutil.copy2(ORIGINAL/SRC,dst)",""))  # source copy is intentional
        self.assertTrue(p62.ALLOWED_OLD_SHA)
        self.assertEqual(len(p62.ALLOWED_OLD_SHA),1)

if __name__=='__main__':
    unittest.main()
