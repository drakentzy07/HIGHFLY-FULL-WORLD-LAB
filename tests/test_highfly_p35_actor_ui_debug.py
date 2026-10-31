#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import highfly_p35_actor_ui_debug as mod
class TestP35(unittest.TestCase):
    def sample(self):
        return {'index.html':'<html><head></head></html>',
            'src/render/renderer.ts':'    const view = this.views.get(e.id);\n    if (!view) return;\n    const kind = viewBuildClass',
            'src/render/characters/index.ts':'    const detail = err instanceof Error ? err.message : String(err);\n    logAssetMissOnce('}
    def test_inserts_hooks(self):
        p=mod.prepare(self.sample())
        self.assertIn('highfly_p35_actor_ui.js',p['index.html'])
        self.assertIn('npc_view_attempt',p['src/render/renderer.ts'])
        self.assertIn('actor_visual_error',p['src/render/characters/index.ts'])
    def test_rejects_source_change(self):
        s=self.sample();s['src/render/renderer.ts']='altered'
        with self.assertRaisesRegex(RuntimeError,'P35_EXPECTED_SOURCE_ANCHOR'):
            mod.prepare(s)
    def test_bag_inventory_diagnostics(self):
        self.assertIn('inventoryOrBag',mod.JS)
        self.assertIn('brokenImages()',mod.JS)
if __name__=='__main__':unittest.main()
