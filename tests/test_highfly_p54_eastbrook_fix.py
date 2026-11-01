import importlib.util
from pathlib import Path
import sys
import types
import unittest

# The standalone tests also run outside a private Codespace.
try:
    import highfly_p9_private_build_smoke
except ImportError:
    stub = types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE = Path('/tmp/highfly-stage')
    stub.ORIGINAL = Path('/tmp/claudecraft-source')
    stub.REPORT = Path('/tmp/p9-report')
    sys.modules['highfly_p9_private_build_smoke'] = stub

MODULE = Path(__file__).with_name('highfly_p54_eastbrook_fix.py')
if not MODULE.is_file():
    MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'highfly_p54_eastbrook_fix.py'
spec = importlib.util.spec_from_file_location('highfly_p54', MODULE)
p54 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p54)

class P54SourceTests(unittest.TestCase):
    def test_decor_one_source_only(self):
        beginning = p54.INVENTORY_ANCHOR + '\n' + p54.PROPS_NEAR_OLD
        original = 'export function collectBuildingImpostors(seed: number): {\n' + p54.PROPS_FAR_OLD + '\n' + p54.FAR_IMPOSTOR_ASSET + '\n' + p54.FAR_IMPOSTOR_SCALES
        source = beginning + '\n' + original
        edited = p54.patch_props(source)
        self.assertIn('hexbWorkshop',edited)
        self.assertIn('Math.abs(d.x - 2)',edited)
        self.assertIn('Math.abs(d.z + 112)',edited)
        self.assertIn('8.4 / Math.max',edited)
        self.assertIn('hfP54Key',edited)
        self.assertNotIn(p54.PROPS_NEAR_OLD,edited)
        self.assertNotIn(p54.PROPS_FAR_OLD,edited)
        with self.assertRaisesRegex(RuntimeError,'ALREADY_APPLIED'):
            p54.patch_props(edited)

    def test_fail_closed_if_anchor_drifted(self):
        with self.assertRaisesRegex(RuntimeError,'ANCHOR_DRIFT'):
            p54.patch_props('export function collectBuildingImpostors(seed: number): {')

    def test_monument_has_no_visual_mutation(self):
        source = p54.TOWN_ANCHOR + '\n// HIGHFLY_P51_MONUMENT_VISUAL_PROBE'
        changed = p54.patch_town(source)
        self.assertIn('AUDIT ONLY',changed)
        self.assertNotIn('setScalar(0)',changed)
        self.assertIn('group.add(monumentFx.group);',changed)

    def test_html_natively_tracks_loading(self):
        source = '<html><head></head><!-- HIGHFLY_P50_SHELL_CLEANUP --></html>'
        changed = p54.patch_html(source)
        self.assertIn('/highfly/p54_eastbrook_ui.css',changed)
        self.assertIn('hf_debug_ui',p54.JS)
        self.assertIn('#ls-fill',p54.CSS)
        self.assertNotIn('ls-fill.style.width',p54.JS)
        self.assertEqual(changed.count('p54_eastbrook_ui.css'),1)

if __name__=='__main__': unittest.main()
