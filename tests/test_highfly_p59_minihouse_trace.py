"""P59 exact P58 -> P59 editor instrumentation tests."""
from __future__ import annotations
import importlib.util,sys,types,unittest
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE=Path('/tmp/stage');stub.ORIGINAL=Path('/tmp/original');stub.REPORT=Path('/tmp/report')
    sys.modules['highfly_p9_private_build_smoke']=stub
def load(n):
    spec=importlib.util.spec_from_file_location(n,S/(n+'.py'))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[n]=mod
    spec.loader.exec_module(mod)
    return mod
p55=load('highfly_p55_private_editor_studio')
p56=load('highfly_p56_editor_transform')
p57=load('highfly_p57_quick_editor')
p58=load('highfly_p58_individual_micro_editor')
p59=load('highfly_p59_minihouse_trace')

class TestP59(unittest.TestCase):
    def test_precise_generated_studio(self):
        base=p58.patch_studio(p57.patch_studio(p55.STUDIO_TS))
        output=p59.patch_studio(base)
        for token in [
            'HIGHFLY_P59_RAW_SCENE_PICK_TRACE',
            'this.traceAt(clientX,clientY)',
            'this.probePanel',
            'this.ray.intersectObjects(this.renderer.scene.children,true)',
            'HIGHFLY_P59_CASITA_SOURCE_LOG.json',
            'nearestRecords:nearby',
            'rawMeshPreviewAllowed:safe',
        ]:
            self.assertIn(token,output)
        self.assertIn('provisional',output)
        self.assertIn('this.saveDraft()',output)
        self.assertNotIn('deletePhysics',output)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p59.patch_studio(output)

    def test_can_not_patch_original_uninstrumented_source(self):
        with self.assertRaisesRegex(RuntimeError,'P59_REQUIRES_P58'):
            p59.patch_studio(p55.STUDIO_TS)

    def test_trace_is_editor_only_not_sim(self):
        text=p59.patch_studio(p58.patch_studio(p57.patch_studio(p55.STUDIO_TS)))
        self.assertIn('this.probeArmed',text)
        self.assertIn('if(this.probeArmed)',text)
        self.assertIn("mesh.isMesh",text)
        self.assertIn('MALLA DESCONOCIDA: ID provisional',text)
        self.assertIn('No borra el mapa',text)
        self.assertIn('this.selectedGroupInfo',text)

    def test_visual_controls_and_no_world_mutation(self):
        self.assertIn('.hf-p59-probe',p59.STYLE)
        self.assertIn("STUDIO='src/editor/highfly_eastbrook_studio.ts'",p59.__file__ and (S/'highfly_p59_minihouse_trace.py').read_text())
        self.assertNotIn('src/sim/',p59.__file__ and (S/'highfly_p59_minihouse_trace.py').read_text())

if __name__=='__main__':unittest.main()
