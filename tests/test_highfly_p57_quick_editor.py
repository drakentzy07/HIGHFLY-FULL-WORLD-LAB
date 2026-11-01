"""P57 contract tests: inject directly into P55, never apply P56 first."""
from __future__ import annotations
import importlib.util,sys,types,unittest,tempfile
from unittest.mock import patch
from pathlib import Path

S=Path(__file__).resolve().parents[1]/'scripts'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE=Path('/tmp/hf-stage');stub.ORIGINAL=Path('/tmp/original');stub.REPORT=Path('/tmp/report')
    sys.modules['highfly_p9_private_build_smoke']=stub

def module(name):
    spec=importlib.util.spec_from_file_location(name,S/(name+'.py'))
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m
p55=module('highfly_p55_private_editor_studio')
p56=module('highfly_p56_editor_transform')
p57=module('highfly_p57_quick_editor')

class P57QuickEditorTests(unittest.TestCase):
    def test_one_step_p55_to_p57(self):
        s=p57.patch_studio(p55.STUDIO_TS)
        for needle in ('beginDrag(clientX:number','drag(clientX:number','endDrag():void',
                       "quick(field:'x'","Escala sugerida","Guardar borrador + JSON",
                       'this.saveDraft()','this.replayDraft()','localStorage.setItem',
                       'HIGHFLY_P57_QUICK_EDIT','HIGHFLY_P56_EDITABLE_STUDIO'):
            self.assertIn(needle,s)
        self.assertEqual(s.count('class HighflyEastbrookStudio'),1)
        self.assertEqual(s.count('beginDrag(clientX:number'),1)
        with self.assertRaises(RuntimeError):p57.patch_studio(s)

    def test_editor_view_pointer_bridge(self):
        source="""// HIGHFLY_P55_EXISTING_EDITOR_STUDIO
  private dragMode: 'none' | 'orbit' | 'pan' | 'edit' | 'moveplacement' = 'none';
    const wantsEdit = ev.button === 0 && this.hooks.toolActive();
    else if (this.dragMode === 'pan') this.cam.pan(dx, dy);
    if (this.dragMode === 'edit') {
      this.hooks.onEditEnd(ev);"""
        r=p57.patch_view(source)
        for needle in ("'hfmove'","this.hfStudio?.beginDrag","this.hfStudio?.drag",
                       "this.hfStudio?.endDrag","HIGHFLY_P57_QUICK_EDIT"):
            self.assertIn(needle,r)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p57.patch_view(r)

    def test_quick_css_and_safe_persistence(self):
        self.assertIn('.hf-p57-pad',p57.QUICK_CSS)
        self.assertIn('localStorage.setItem',p57.patch_studio(p55.STUDIO_TS))
        self.assertNotIn('fetch(',p57.patch_studio(p55.STUDIO_TS))
        self.assertNotIn('deleteColliders',p57.patch_studio(p55.STUDIO_TS))

    def test_p56_source_patches_dependency_available(self):
        self.assertIn('highflyFreeBuilding:',p56.patch_props(
          """    g.rotation.y = b.rot;
    group.add(shadowed(g));
    registerHideable(g, obbFootprint(b.x, b.z, b.w / 2, b.d / 2, b.rot, roofY));"""))
        self.assertIn('p56Body.scale.multiplyScalar(k)',p56.patch_town(
          """  const monumentBody = buildRealmBuilderMonumentBody(monumentTemplate.raw, monumentSeat);
  group.add(monumentBody.group);"""))

    def test_failed_attempt_backup_archived_without_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=root/'highfly-p57'
            original=old/'backups/src/editor/highfly_eastbrook_studio.ts'
            original.parent.mkdir(parents=True)
            original.write_text('old protected P55 backup',encoding='utf8')
            with patch.object(p57,'OUT',old):
                archived=p57.archive_incomplete_previous_backup()
            self.assertIsNotNone(archived)
            self.assertFalse(old.exists())
            self.assertTrue(archived.is_dir())
            self.assertEqual(
                (archived/'backups/src/editor/highfly_eastbrook_studio.ts').read_text(),
                'old protected P55 backup')
            self.assertIn('highfly-p57-preserved-attempts',str(archived))

    def test_completed_report_is_never_archived(self):
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/'highfly-p57'
            old.mkdir()
            report=old/'P57_STATUS.json'
            report.write_text('{"mode":"BUILD_GREEN_BROWSER_UNVERIFIED"}')
            with patch.object(p57,'OUT',old):
                with self.assertRaisesRegex(RuntimeError,'P57_SUCCESS_REPORT_EXISTS'):
                    p57.archive_incomplete_previous_backup()
            self.assertTrue(report.is_file())

    def test_fail_closed(self):
        with self.assertRaises(RuntimeError):p57.patch_studio('not P55')
        with self.assertRaises(RuntimeError):p57.patch_view('not viewport')

if __name__=='__main__': unittest.main()
