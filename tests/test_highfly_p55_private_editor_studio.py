"""P55 isolated transformation tests; no private Codespace assets required."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import types
import unittest

try:
    import highfly_p9_private_build_smoke
except ImportError:
    fake=types.ModuleType('highfly_p9_private_build_smoke')
    fake.STAGE=Path('/tmp/highfly-stage')
    fake.ORIGINAL=Path('/tmp/claudecraft-source')
    fake.REPORT=Path('/tmp/p9-report')
    sys.modules['highfly_p9_private_build_smoke']=fake

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/highfly_p55_private_editor_studio.py'
spec=importlib.util.spec_from_file_location('highfly_p55',SCRIPT)
p55=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p55)

class P55StudioTests(unittest.TestCase):
    def test_new_studio_uses_original_editor(self):
        self.assertIn('import { EASTBROOK_LAYOUT }',p55.STUDIO_TS)
        self.assertIn('BUILTIN_WORLD.props.decorProps',p55.STUDIO_TS)
        self.assertIn('eastbrookBuilding:',p55.STUDIO_TS)
        self.assertIn('hide_visual_preview',p55.STUDIO_TS)
        self.assertIn('requiresColliderReview:true',p55.STUDIO_TS)
        self.assertNotIn('invalidateStaticColliders',p55.STUDIO_TS)

    def test_editor_studio_guard(self):
        fake=('  private rebuildActiveWorld(): void {\n    const map = this.map;\n'
              '  private setTool(tool: EditorTool): void {\n    this.tool = tool;')
        patched=p55.patch_app(fake)
        self.assertIn("this.activeWorld = BUILTIN_WORLD;",patched)
        self.assertIn("tool = 'select';",patched)
        self.assertIn('setActiveWorldContent(BUILTIN_WORLD)',patched)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p55.patch_app(patched)

    def test_viewport_bridge_and_cleanup(self):
        before=("\n".join([
          "import { Renderer } from '../../render/renderer';",
          "  private renderer: Renderer | null = null;",
          "    const world = customMapToWorldContent(this.map);",
          "    this.renderer.placedAssets.rebuildAll(placementsToRenderAssets(this.map.placements), true);",
          "    this.renderer = null;",
          "    this.sim = null;",
          "    this.renderer.sync(1, DT, null);",
          "      this.hooks.onTap(ev.clientX, ev.clientY, this.surfaceAt(ev.clientX, ev.clientY));",
        ]))
        result=p55.patch_view(before)
        self.assertIn("new HighflyEastbrookStudio",result)
        self.assertIn("this.hfStudio?.dispose()",result)
        self.assertIn("this.hfStudio?.tick()",result)

    def test_props_source_tagging_only_in_studio(self):
        before="""    g.rotation.y = d.rot ?? 0;
    group.add(shadowed(g));
    if (d.r) {"""
        result=p55.patch_props(before)
        self.assertIn("highflySourceDecor",result)
        self.assertIn("keepFromMerge.add",result)
        self.assertIn("hf_eastbrook_studio",result)
        self.assertIn("group.add(shadowed(g));",result)

    def test_loading_preserves_actual_progress(self):
        self.assertIn('#ls-fill',p55.LOADING_STYLE)
        self.assertIn('background-size:auto 89dvh',p55.LOADING_STYLE)
        self.assertNotIn('ls-fill.style.width',p55.STUDIO_TS)
        src='<head><!-- HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION --></head>'
        self.assertIn('p55_loading.css',p55.patch_html(src))
        with self.assertRaisesRegex(RuntimeError,'P55_REQUIRES_P54'):
            p55.patch_html('</head>')

if __name__=='__main__':
    unittest.main()
