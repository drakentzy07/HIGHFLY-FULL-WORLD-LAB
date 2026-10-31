#!/usr/bin/env python3
"""P31 regression tests: no private files required, no mutation outside temp."""
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/highfly_p31_cc0_wolf_restore.py'
spec = importlib.util.spec_from_file_location('highfly_p31_cc0_wolf_restore', SCRIPT)
p31 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p31)


class P31Tests(unittest.TestCase):
    def test_requires_exact_source_and_cc0_credit(self):
        correct = {'items': [{'out': p31.WOLF, 'src': p31.RAW_SOURCE}]}
        credits = '| Animated creatures (wolf, bull) | Quaternius | https://quaternius.com | CC0 1.0 | Yes |'
        self.assertTrue(p31.source_has_verified_credits(correct, credits))
        wrong = {'items': [{'out': p31.WOLF, 'src': 'project_art/wolf.glb'}]}
        self.assertFalse(p31.source_has_verified_credits(wrong, credits))
        self.assertFalse(p31.source_has_verified_credits(correct, credits.replace('CC0 1.0', 'With the project only')))
        self.assertFalse(p31.source_has_verified_credits(correct, ''))

    def test_rejects_invalid_glb_and_accepts_valid_header(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'wolf.glb'
            f.write_bytes(b'not a GLB' * 4)
            with self.assertRaisesRegex(ValueError, 'GLB_HEADER_INVALID'):
                p31.glb_size(f)
            f.write_bytes(struct.pack('<4sII', b'glTF', 2, 20) + b'12345678')
            self.assertEqual(p31.glb_size(f), 20)

    def test_copy_is_exact_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / 'src.glb'
            dst = root / 'public' / p31.WOLF
            src.write_bytes(struct.pack('<4sII', b'glTF', 2, 20) + b'12345678')
            p31.verify_no_symlink_ancestors(dst, root)
            p31.restore_atomically(src, dst)
            self.assertEqual(p31.digest(src), p31.digest(dst))
            with self.assertRaises(FileExistsError):
                p31.restore_atomically(src, dst)
            self.assertEqual(p31.digest(src), p31.digest(dst))


if __name__ == '__main__':
    unittest.main()
