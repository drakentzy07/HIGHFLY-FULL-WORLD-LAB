"""P43 9-class native editor, offline routing and fullscreen tests.

These fixtures verify no synthetic class picker, no replacing native loader,
no touching 4174 stage, and reversible per-lab backups. No browser claim.
"""
import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hf_p43_nine",ROOT/"scripts/highfly_p43_native_editor_offline.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def fixture_html():
    def classes():
        return "\n".join(
            f'<button type="button" class="mini-class" data-class="{klass}">{klass}</button>'
            for klass in p.CLASSES)
    return (
        '<html><head><style id="highfly-p42-hunter-styles">'
        '#offline-select .mini-class[data-class]:not([data-class="warrior"])'
        '{display:none!important}</style>\n'
        '<script defer src="/highfly_p42_hunter.js"></script></head>'
        '<body><div id="charcreate-panel">'+classes()+'</div>'
        '<div id="offline-select">'+classes()+'</div>'
        '<div id="server-opt-offline"></div></body></html>'
    )

def fixture_main():
    return (
        '/* HIGHFLY_P41_OFFLINE_SAVE */\n'
        'const foo=readHighflySave(name);\n'
        'const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);\n'
        "const offlineOption = $('#server-opt-offline');\n"
        'const choose = handleOfflineSelect;\n'
        'function request(){ requestMobileFullscreenLandscape(); }\n'
        "    applyServerMode('online');\n"
    )

class NativeEditorTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.old_work=p.WORK
        self.old_report=p.REPORT
        self.work=Path(self.t.name)/".workspace"
        self.lab=self.work/"highfly-p43-restore-lab"
        (self.lab/"src").mkdir(parents=True)
        (self.lab/"public").mkdir()
        (self.lab/"index.html").write_text(fixture_html(),"utf8")
        (self.lab/"src/main.ts").write_text(fixture_main(),"utf8")
        p.WORK=self.work
        p.REPORT=self.work/"reports/P43_NATIVE_EDITOR_OFFLINE.json"
        self.addCleanup(lambda: setattr(p,"WORK",self.old_work))
        self.addCleanup(lambda: setattr(p,"REPORT",self.old_report))

    def test_nine_classes_in_native_editor_and_offline(self):
        result=p.patch_html(fixture_html())
        self.assertEqual(result.count('class="mini-class"'),18)
        self.assertIn('id="offline-select"',result)
        self.assertIn('id="charcreate-panel"',result)
        self.assertNotIn('highfly_p42_hunter.js',result)
        self.assertNotIn('highfly-p42-hunter-styles',result)
        self.assertIn('highfly_p43_native_fullscreen.js',result)
        self.assertNotIn('highfly_splash.png',result)
        self.assertNotIn('highfly-p46',result)

    def test_native_offline_routing_only_dev(self):
        result=p.patch_main(fixture_main())
        self.assertIn("applyServerMode(offlineAvailable ? 'offline' : 'online')",result)
        self.assertIn('const offlineAvailable = import.meta.env.DEV;',result)
        self.assertIn('handleOfflineSelect',result)
        self.assertIn('server-opt-offline',result)
        self.assertNotIn('navigator.serviceWorker',result)

    def test_p43_gate_variant_without_original_expression(self):
        src=fixture_main().replace(
            'isOfflineModeAvailable(import.meta.env.DEV)',
            'import.meta.env.DEV && import.meta.env.VITE_HIGHFLY_OFFLINE_LAB === "1"')
        result=p.patch_main(src)
        self.assertIn('const offlineAvailable = import.meta.env.DEV;',result)
        self.assertIn("applyServerMode(offlineAvailable ? 'offline' : 'online')",result)

    def test_p43_false_gate_still_enabled_only_in_dev(self):
        src=fixture_main().replace('isOfflineModeAvailable(import.meta.env.DEV)','false')
        result=p.patch_main(src)
        self.assertIn('const offlineAvailable = import.meta.env.DEV;',result)
        self.assertNotIn('const offlineAvailable = false;',result)

    def test_p43_multiline_gate(self):
        src=fixture_main().replace(
            'const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);',
            'const offlineAvailable = isOfflineModeAvailable(\n  import.meta.env.DEV\n);')
        result=p.patch_main(src)
        self.assertIn('const offlineAvailable = import.meta.env.DEV;',result)

    def test_p43_unknown_gate_fails_before_modification(self):
        src=fixture_main().replace('offlineAvailable =','canUseLocalMode =')
        with self.assertRaisesRegex(RuntimeError,'P43_NATIVE_OFFLINE_GATE_DECLARATION_UNRECOGNIZED'):
            p.patch_main(src)

    def test_p43_original_handlers_required(self):
        src=fixture_main().replace('handleOfflineSelect','unexpected')
        with self.assertRaisesRegex(RuntimeError,'P43_NATIVE_OFFLINE_ROUTING_MISSING'):
            p.patch_main(src)

    def test_reject_missing_ninth_class(self):
        s=fixture_html().replace('data-class="druid"','data-class="warrior"')
        with self.assertRaisesRegex(RuntimeError,'P43_NATIVE_NINE_CLASS_CONTROLS_MISSING'):
            p.patch_html(s)

    def test_reject_unknown_legacy_p42_css(self):
        s=fixture_html().replace('highfly-p42-hunter-styles','wrong-name')
        with self.assertRaisesRegex(RuntimeError,'P43_P42_CLASS_HIDER_MISSING'):
            p.patch_html(s)

    def test_in_lab_backup_and_no_active_stage_changes(self):
        active=self.work/"highfly-origin-stage-p0"
        active.mkdir()
        (active/"index.html").write_text("ACTIVE P64 DO NOT TOUCH","utf8")
        result=p.apply(self.lab)
        self.assertEqual(result['mode'],"APPLY")
        self.assertEqual(len(result['classes']),9)
        self.assertFalse(result['browserVerified'])
        self.assertEqual((active/"index.html").read_text(),"ACTIVE P64 DO NOT TOUCH")
        self.assertEqual((self.lab/".hf-p43-native-editor-backup/index.html").read_text(),fixture_html())
        self.assertEqual((self.lab/".hf-p43-native-editor-backup/src/main.ts").read_text(),fixture_main())
        self.assertIn("PANTALLA COMPLETA",(self.lab/"public/highfly_p43_native_fullscreen.js").read_text())
        self.assertTrue(p.REPORT.is_file())

    def test_refuse_overwrite_existing_lab_backup(self):
        p.apply(self.lab)
        with self.assertRaisesRegex(RuntimeError,'P43_PREVIOUS_RUN_PRESENT'):
            p.apply(self.lab)

    def test_fullscreen_needs_direct_click(self):
        js=p.FULLSCREEN_JS
        self.assertIn("button.addEventListener('click'",js)
        self.assertIn("requestFullscreen",js)
        self.assertIn("screen.orientation",js)
        self.assertNotIn("MutationObserver",js)
        self.assertNotIn("ls-fill",js)

if __name__=="__main__":unittest.main()
