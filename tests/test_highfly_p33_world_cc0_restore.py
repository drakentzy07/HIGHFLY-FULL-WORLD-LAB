#!/usr/bin/env python3
"""P33: test CC0 evidence and no-overwrite rules without user private data."""
import sys
import struct
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p33_world_cc0_restore as p33

class P33Tests(unittest.TestCase):
    def test_exact_source_and_single_license(self):
        path = "models/creatures/wolf.glb"
        ok = {"/" + path: [{"sourceDescription":"tmp/asset_src/quaternius_creatures/Wolf.glb","provenance":"CC0_QUATERNIUS"}]}
        self.assertEqual(p33.exact_cc0_provenance(path, ok), "CC0_QUATERNIUS")
        ok["/" + path].append({"sourceDescription":"project/wolf.glb","provenance":"CC0_QUATERNIUS"})
        self.assertIsNone(p33.exact_cc0_provenance(path, ok))
        self.assertIsNone(p33.exact_cc0_provenance(path, {}))
        self.assertFalse(p33.safe_path("../public/models/wolf.glb"))

    def test_known_project_asset_never_authorized(self):
        x = {"/models/chars/modular/warrior_modular.glb":
             [{"sourceDescription":"tmp/modular/warrior.glb","provenance":"UNVERIFIED_OR_PROJECT_ONLY"}]}
        self.assertIsNone(p33.exact_cc0_provenance("models/chars/modular/warrior_modular.glb",x))

    def test_copy_missing_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            old_stage = p33.STAGE
            try:
                p33.STAGE = p
                src = p / "source"
                dst = p / "public/models/creatures/wolf.glb"
                src.write_bytes(struct.pack("<4sII", b"glTF",2,20) + b"12345678")
                p33.stage_copy(src, dst, False, None)
                self.assertEqual(p33.sha(src),p33.sha(dst))
                with self.assertRaises(FileExistsError):
                    p33.stage_copy(src,dst,False,None)
                self.assertEqual(p33.sha(src),p33.sha(dst))
            finally:
                p33.STAGE = old_stage

if __name__ == "__main__":
    unittest.main()
