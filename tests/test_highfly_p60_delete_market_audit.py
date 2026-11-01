"""P60: Delete-key studio draft and safe market GLB provenance audit."""
from __future__ import annotations
import importlib.util,sys,types,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE=Path('/tmp/stage');stub.ORIGINAL=Path('/tmp/original');stub.REPORT=Path('/tmp/report')
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
p59=load('highfly_p59_minihouse_trace')
p60=load('highfly_p60_delete_market_audit')

def generated():
    return p59.patch_studio(p58.patch_studio(p57.patch_studio(p55.STUDIO_TS)))

class P60Tests(unittest.TestCase):
    def test_exact_p59_to_p60(self):
        output=p60.patch_studio(generated())
        for token in ["HIGHFLY_P60_STABLE_DELETE",
                      "ev.key!=='Delete'&&ev.key!=='Backspace'",
                      "e.kind==='mesh'",
                      "this.removeVisual()",
                      "this.selected=null;this.selectedRoot=null",
                      "window.addEventListener('keydown',this.onStudioDeleteKey,true)",
                      "window.removeEventListener('keydown',this.onStudioDeleteKey,true)",
                      "const sourceId=exact?.userData?.highflyMicroId"]:
            if token.startswith('const sourceId='):
                self.assertIn("const sourceId=exact?.userData?.highflyMicroId",output)
            else:
                self.assertIn(token,output)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_INSTALLED'):
            p60.patch_studio(output)
    def test_fail_closed_on_wrong_stage(self):
        with self.assertRaisesRegex(RuntimeError,'P60_REQUIRES_P59'):
            p60.patch_studio(p55.STUDIO_TS)
    def test_not_editing_game_source(self):
        output=p60.patch_studio(generated())
        self.assertIn('remove_visual_proposal',output)
        self.assertIn('requiresColliderReview:true',output)
        self.assertNotIn('deletePhysics',output)
    def test_market_binary_hash_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            origin=root/'orig';stage=root/'stage'
            a=origin/'public/models/props/eastbrook_market_stall.glb'
            b=stage/'public/models/props/eastbrook_market_stall.glb'
            a.parent.mkdir(parents=True);b.parent.mkdir(parents=True)
            a.write_bytes(b'original geometry');b.write_bytes(b'different replacement geometry')
            with patch.object(p60,'ORIGINAL',origin),patch.object(p60,'STAGE',stage):
                report=p60.market_audit()
            self.assertFalse(report['sameGeometryBytes'])
            self.assertEqual(report['meshes']['original_reference'][0]['bytes'],len(b'original geometry'))
            self.assertEqual(report['meshes']['highfly_private_stage'][0]['bytes'],len(b'different replacement geometry'))
            self.assertEqual(a.read_bytes(),b'original geometry')
            self.assertEqual(b.read_bytes(),b'different replacement geometry')
    def test_no_assets_means_unverified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with patch.object(p60,'ORIGINAL',root/'missing'),patch.object(p60,'STAGE',root/'missing2'):
                report=p60.market_audit()
            self.assertFalse(report['sameGeometryBytes'])
            self.assertEqual(report['meshes']['original_reference'],[])

if __name__=='__main__':unittest.main()
