"""P58 tests: P57 exact generated studio -> named micro sources."""
from __future__ import annotations
import importlib.util,sys,types,unittest
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE=Path('/tmp/hf-stage');stub.ORIGINAL=Path('/tmp/hf-original');stub.REPORT=Path('/tmp/hf-report')
    sys.modules['highfly_p9_private_build_smoke']=stub
def load(name):
    spec=importlib.util.spec_from_file_location(name,S/(name+'.py'))
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m
p55=load('highfly_p55_private_editor_studio')
p56=load('highfly_p56_editor_transform')
p57=load('highfly_p57_quick_editor')
p58=load('highfly_p58_individual_micro_editor')

TOWN_FIXTURE="""interface MicroBatchBuild {
  batches: THREE.Mesh[];
}
function buildMicroBatches() {
  const opaque: THREE.BufferGeometry[] = [];
  const emissive: THREE.BufferGeometry[] = [];
  const add = (url: string, matrix: THREE.Matrix4): void => {
    const template = templates.get(url);
    if (!template) throw new Error(`Eastbrook town template is missing: ${url}`);
    addPlacedGeometry(opaque, template.opaque, matrix);
    addPlacedGeometry(emissive, template.emissive, matrix);
  };
  for (const bench of EASTBROOK_LAYOUT.civic.benches) {
    const template = templates.get(bench.assetId);
  }
  for (const stall of EASTBROOK_LAYOUT.market.stalls) {
    const template = templates.get(stall.assetId);
  }
  for (const fence of EASTBROOK_LAYOUT.fences) {
    const template = templates.get(fence.assetId);
  }
  const batches: THREE.Mesh[] = [];
  const opaqueGeometry = mergeParts(opaque, 'micro opaque batch');
}"""

class P58Tests(unittest.TestCase):
    def test_exact_p57_studio_patch(self):
        result=p58.patch_studio(p57.patch_studio(p55.STUDIO_TS))
        for needle in ["kind:'micro'","highflyMicro:","highflyMicroId","Quitar (borrador)",
                       "remove_visual_proposal","if(d.action==='remove_visual_proposal')this.removeVisual()"]:
            self.assertIn(needle,result)
        self.assertIn('requiresColliderReview:true',result)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_INSTALLED_STUDIO'):p58.patch_studio(result)

    def test_original_town_micro_batch_source_fixture(self):
        result=p58.patch_town(TOWN_FIXTURE)
        for needle in ["HIGHFLY_P58_SELECTABLE_MICRO_PROPS","highflyMicroId",
                       "if(studioMode)return {batches:studioPieces}",
                       "activeSource={id:bench.id","activeSource={id:stall.id",
                       "activeSource={id:fence.id","addPlacedGeometry(opaque, template.opaque, matrix)"]:
            self.assertIn(needle,result)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_INSTALLED_TOWN'):p58.patch_town(result)

    def test_fail_closed_on_unknown_source(self):
        with self.assertRaisesRegex(RuntimeError,'P58_ANCHOR'):p58.patch_town('wrong source')
        with self.assertRaisesRegex(RuntimeError,'P58_REQUIRES_P57'):p58.patch_studio(p55.STUDIO_TS)

    def test_isolated_to_editor(self):
        result=p58.patch_town(TOWN_FIXTURE)
        self.assertIn("new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1'",result)
        self.assertIn("if(studioMode && activeSource)",result)
        self.assertIn("const batches: THREE.Mesh[] = [];",result)
        self.assertIn("mergeParts(opaque, 'micro opaque batch')",result)

if __name__=='__main__':unittest.main()
