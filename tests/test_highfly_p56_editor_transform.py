"""P56 tests use the exact P55-generated editor; no private GLB needed."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys,types,unittest

if 'highfly_p9_private_build_smoke' not in sys.modules:
    p9=types.ModuleType('highfly_p9_private_build_smoke')
    p9.STAGE=Path('/tmp/highfly-stage')
    p9.ORIGINAL=Path('/tmp/original')
    p9.REPORT=Path('/tmp/report')
    sys.modules['highfly_p9_private_build_smoke']=p9
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
p55=load('highfly_p55_private_editor_studio')
p56=load('highfly_p56_editor_transform')

class P56EditorTests(unittest.TestCase):
    def test_exact_p55_studio_fixture(self):
        source=p55.STUDIO_TS
        out=p56.patch_studio(source)
        self.assertIn('TRANSFORMAR VISTA',out)
        self.assertIn('offsetX:x-e.x',out)
        self.assertIn('resetTransform()',out)
        self.assertIn("kind:'fx'",out)
        self.assertIn('this.ray.intersectObjects(this.renderer.scene.children,true)',out)
        self.assertIn("continue;",out)
        self.assertIn('highflyFreeBuilding:',out)
        self.assertIn('requiresColliderReview:true',out)
        self.assertNotIn('deleteColliders',out)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p56.patch_studio(out)

    def test_style(self):
        self.assertIn('.hf-p56-edits',p56.STYLE)
        self.assertIn('#hf-studio-p55',p56.STYLE)

    def test_fail_closed_on_missing_source(self):
        with self.assertRaisesRegex(RuntimeError,'P56_ANCHOR'):
            p56.patch_studio('random string')
        with self.assertRaisesRegex(RuntimeError,'P56_ANCHOR'):
            p56.patch_town('not source')
        with self.assertRaisesRegex(RuntimeError,'P56_ANCHOR'):
            p56.patch_fx('bad')

    def test_nonlayout_prop_source_tag(self):
        old="""    g.rotation.y = b.rot;
    group.add(shadowed(g));
    registerHideable(g, obbFootprint(b.x, b.z, b.w / 2, b.d / 2, b.rot, roofY));"""
        out=p56.patch_props(old)
        self.assertIn('highflyFreeBuilding:',out)
        self.assertIn('keepFromMerge.add(o)',out)
        self.assertIn('hf_eastbrook_studio',out)

    def test_monument_size_gate_only_visual(self):
        old="""  const monumentBody = buildRealmBuilderMonumentBody(monumentTemplate.raw, monumentSeat);
  group.add(monumentBody.group);"""
        changed=p56.patch_town(old)
        self.assertIn('size.y > monumentSeat.nativeHeight * 1.5',changed)
        self.assertIn('p56Body.scale.multiplyScalar(k)',changed)
        self.assertIn('monumentSeat.groundY-after.min.y',changed)
        self.assertNotIn('EASTBROOK_LAYOUT.civic.monument.height =',changed)

    def test_offline_placeholder_hides_only_hologram(self):
        old="""import { currentRealmBuilder } from '../sim/content/realm_builders';
  let honoureeName = initialHonoureeName;
    beam.name = \`\${GROUP_NAME}Beam\`;
    panel.name = \`\${GROUP_NAME}Name\`;
      honoureeName = name;
      // Re-bake rather than re-place:"""
        out=p56.patch_fx(old)
        self.assertIn('isPlaceholderRealmBuilder',out)
        self.assertIn('beam.visible = p56Named',out)
        self.assertIn('panel.visible = p56Named',out)
        self.assertIn('p56Named = true',out)
        self.assertNotIn('group.visible = false',out)

if __name__=='__main__': unittest.main()
