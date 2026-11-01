"""P64 unit tests: exact Gobkit source provenance, distinct real boar animations,
fail-closed GLB validation, stage source anchors, no server/world edits.
No download, no runtime stage mutation in unit tests.
"""
import importlib.util,json,struct,sys,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'scripts'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.ORIGINAL=Path('/missing/original');stub.STAGE=Path('/missing/stage')
    sys.modules['highfly_p9_private_build_smoke']=stub
spec=importlib.util.spec_from_file_location('p64',D/'highfly_p64_real_boar_cc0.py')
p64=importlib.util.module_from_spec(spec);sys.modules['p64']=p64;spec.loader.exec_module(p64)

def catalog(license='CC0 1.0 public domain',url=None,clips=('idle','walk','attack','dead')):
    uri=url or p64.URL
    return json.dumps({'glbs':[uri],
      'packs':[{'models':[{'id':'boar','name':'Boar','url':uri,
        'format':'glb','rigged':True,'license':license,
        'animations':[{'name':x} for x in clips]}]}]}).encode()

def glb(clips=('idle','walk','attack','dead')):
    data={'asset':{'version':'2.0'},'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],
          'skins':[{'joints':[0]}],
          'animations':[{'name':a} for a in clips],
          'nodes':[{'mesh':0}]}
    js=json.dumps(data).encode('utf8');js+=b' ' *((4-len(js)%4)%4)
    payload=struct.pack('<I4s',len(js),b'JSON')+js
    return struct.pack('<4sII',b'glTF',2,12+len(payload))+payload

class P64Tests(unittest.TestCase):
    def test_manifest_requires_actual_named_boar_cc0(self):
        p=p64.provider_metadata(catalog())
        self.assertEqual(p['provider'],'Gobkit Free Animal Pack Vol.2')
        self.assertIn('attack',p['animations'])
        self.assertIn('CC0',p['license'])
    def test_denies_non_cc0_or_wrong_species(self):
        with self.assertRaisesRegex(RuntimeError,'LICENSE_NOT_CC0'):
            p64.provider_metadata(catalog(license='noncommercial'))
        with self.assertRaisesRegex(RuntimeError,'NOT_IN_FREE_CATALOG'):
            p64.provider_metadata(catalog(url='https://gobkit.com/fakes/Fox.glb'))
    def test_actual_glb_must_have_four_distinct_rigged_animations(self):
        x=p64.inspect_glb(glb())
        self.assertEqual(x['clips'],['attack','dead','idle','walk'])
        self.assertEqual(x['skins'],1)
        with self.assertRaisesRegex(RuntimeError,'SEPARATE_ANIMATIONS'):
            p64.inspect_glb(glb(('Idle','Attack')))
        with self.assertRaisesRegex(RuntimeError,'INVALID_GLB_HEADER'):
            p64.inspect_glb(b'badbyte'*30)
    def test_real_stable_source_repairs_only_visuals(self):
        s=("  mob_boar: {\n"
           '    url: '+chr(96)+'$'+'{CREATURES}/wild_boar.glb'+chr(96)+',\n'
           '    height: 1.45,\n'
           '    clips: WILD_BOAR,\n'
           "    tint: 'entity',\n"
           '    tintStrength: 0.4,\n'
           '  },')
        changed=p64.edit_manifest(s)
        self.assertIn('highfly_gobkit_boar_cc0.glb',changed)
        self.assertIn('HIGHFLY_P64_REAL_BOAR_CC0',changed)
        self.assertNotIn('wild_boar.glb',changed)
        with self.assertRaisesRegex(RuntimeError,'P64_ALREADY_APPLIED_MANIFEST'):
            p64.edit_manifest(changed)
    def test_media_and_lazy_load_once(self):
        # P39A and P39B each legitimately include the SAME crab GLB.
        # The old P64 installer failed with count=2, before modifying stage.
        fixture=(
          "export const MEDIA=[\n"
          "  'models/creatures/crab_ability_anims.glb',\n"
          "  // HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD: CC0 VERIFIED stage assets referenced by mob visuals.\n"
          "  'models/creatures/crab_ability_anims.glb',\n"
          "];\n"
        )
        a=p64.edit_media(fixture)
        b=p64.edit_assets("const HIGHFLY_P39B_MOB_CC0_URLS = new Set<string>([")
        self.assertEqual(a.count('models/creatures/crab_ability_anims.glb'),2)
        self.assertIn('highfly_gobkit_boar_cc0.glb',a)
        self.assertIn('highfly_gobkit_boar_cc0.glb',b)
        self.assertEqual(a.count('highfly_gobkit_boar_cc0.glb'),1)
        self.assertIn('HIGHFLY_P64_REAL_BOAR_CC0',a)
        with self.assertRaisesRegex(RuntimeError,'P64_ALREADY_APPLIED_MEDIA'):
            p64.edit_media(a)
        with self.assertRaisesRegex(RuntimeError,'P64_ALREADY_APPLIED_ASSETS'):
            p64.edit_assets(b)
    def test_rejects_existing_asset_without_marker(self):
        fixture=(
          "  // HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD: CC0 VERIFIED stage assets referenced by mob visuals.\n"
          "  'models/creatures/highfly_gobkit_boar_cc0.glb',\n"
        )
        with self.assertRaisesRegex(RuntimeError,'P64_ALREADY_APPLIED_MEDIA'):
            p64.edit_media(fixture)
    def test_media_without_p39b_provenance_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'DIRECT_MEDIA_ALLOWLIST_0'):
            p64.edit_media("  'models/creatures/crab_ability_anims.glb',")

    def test_no_changes_to_gameplay_and_assets_unpublished(self):
        source=(D/'highfly_p64_real_boar_cc0.py').read_text('utf8')
        self.assertIn('for rel in (MEDIA,ASSETS,MANIFEST):',source)
        self.assertNotIn('source.write_text(',source)
        self.assertIn("DEST='public/models/creatures/highfly_gobkit_boar_cc0.glb'",source)
        self.assertIn('P64_SOURCE_ANCHOR_',source)
        self.assertIn('P64_ALREADY_APPLIED',source)
        self.assertIn('except BaseException:',source)
if __name__=='__main__':unittest.main()
