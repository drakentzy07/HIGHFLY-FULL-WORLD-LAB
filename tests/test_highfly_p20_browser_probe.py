#!/usr/bin/env python3
"""HIGHFLY P20 private probe installer unit tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p20_browser_probe as p20


class P20BrowserProbeTests(unittest.TestCase):
    def test_installs_once_and_never_changes_main_module(self):
        original = '<!doctype html><html><head><title>HIGHFLY</title></head><body><script type="module" src="/src/main.ts"></script></body></html>'
        changed = p20.inject_html(original)
        self.assertEqual(changed.count(p20.MARKUP), 1)
        self.assertIn('/src/main.ts', changed)
        self.assertEqual(p20.inject_html(changed), changed)

    def test_removal_restores_original_page_byte_for_byte(self):
        original = '<html><head>\n<link rel="icon" href="/a.svg"></head>\n<body>HIGHFLY</body></html>'
        changed = p20.inject_html(original)
        self.assertEqual(p20.remove_html(changed), original)

    def test_reject_unexpected_old_probe_fragment(self):
        with self.assertRaisesRegex(RuntimeError, "UNKNOWN_EXISTING"):
            p20.inject_html('<html><head><script data-highfly-p20="other"></script></head></html>')

    def test_no_html_head_is_hard_failure(self):
        with self.assertRaisesRegex(RuntimeError, "NO_HTML_HEAD"):
            p20.inject_html('<html><body>start</body></html>')

    def test_repo_owned_probe_source_and_script_scope(self):
        js = Path(p20.SOURCE_JS).read_text(encoding="utf8")
        self.assertIn("__HIGHFLY_P20_PROBE__", js)
        self.assertIn("new Blob(", js)
        self.assertIn("HTML_FALLBACK_OR_WRONG_MIME", js)
        self.assertIn("window.fetch =", js)
        self.assertIn("originalFetch.apply", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sendBeacon", js)
        self.assertNotIn("XMLHttpRequest", js)


if __name__ == "__main__":
    unittest.main()
