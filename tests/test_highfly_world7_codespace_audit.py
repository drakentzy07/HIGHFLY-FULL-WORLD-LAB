"""Read-only P70 doctor regression checks. No private assets needed."""
from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_world7_codespace_audit.py"
spec = importlib.util.spec_from_file_location("p70_doctor", SCRIPT)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class CodespaceAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / ".workspace"
        self.stage = self.ws / "highfly-origin-stage-p0"
        self.original = self.ws / "claudecraft-v0.44.7"
        self.out = self.ws / "reports/highfly-world7"
        self.patch = mock.patch.multiple(
            doctor, ROOT=self.root, WORKSPACE=self.ws, STAGE=self.stage,
            ORIGINAL=self.original, OUT=self.out)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def put(self, relative, content):
        path = self.stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf8")
        return path

    def test_absent_stage_reports_blockers_without_creating_game(self):
        result = doctor.run()
        self.assertFalse(result["privateStageFound"])
        self.assertIn("PRIVATE_STAGE_NOT_FOUND", result["blockers"])
        doctor.write_report(result)
        self.assertTrue((self.out / "P70_CODESPACE_AUDIT.json").is_file())
        self.assertFalse(self.stage.exists())

    def test_markers_and_legacy_references_are_source_audit_only(self):
        main = self.put("src/main.ts",
                        "// HIGHFLY_P68_FURY_GOLDEN_RECOVERY\n"
                        "// HIGHFLY_P69_FURY_CORE\n"
                        "characterPreview.setClass('warrior');\n")
        self.put("src/sim/types.ts",
                 "export type PlayerClass = 'warrior';")
        self.put("src/render/characters/manifest.ts", "export const chars = {};")
        self.put("src/game/highfly_fury_skill_touch.ts",
                 "if (a.def.targetMode !== 'position') return;")
        self.put("HIGHFLY_STAGE_STATUS.json",
                 '{"sourceCommit":"493c35a108cef6c8aa290e8793107b1cd117886e",'
                 '"originalPublicMediaCopied":false}')
        before = main.read_bytes()
        result = doctor.run()
        self.assertTrue(result["privateStageFound"])
        self.assertEqual(result["files"]["src/main.ts"]["legacyWarriorReferences"], 1)
        self.assertIn("legacyPreviewWarrior", result["files"]["src/main.ts"]["anchors"])
        self.assertIn("aimPositionGate", result["files"]["src/game/highfly_fury_skill_touch.ts"]["anchors"])
        self.assertNotIn("P69_NOT_CONFIRMED_IN_SCANNED_SOURCES", result["blockers"])
        doctor.write_report(result)
        self.assertEqual(main.read_bytes(), before)
        self.assertTrue(result["readOnlyGameplay"])

    def test_glb_header_exposes_clips_without_copying_model(self):
        self.put("src/main.ts", "/* world */")
        self.put("src/sim/types.ts", "type PlayerClass = 'warrior'")
        self.put("src/render/characters/manifest.ts", "export const clips = [];")
        model = self.stage / "public/models/chars/hero.glb"
        model.parent.mkdir(parents=True)
        doc = json.dumps({"asset":{"version":"2.0"},
                          "skins":[{}], "animations":[{"name":"Run"}, {"name":"Jump"}]})
        encoded = doc.encode("utf8")
        encoded += b" " * ((-len(encoded)) % 4)
        chunk = struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
        model.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk)
        before = model.read_bytes()
        result = doctor.run()
        self.assertEqual(result["modelsWithAnimation"], 1)
        self.assertEqual(result["modelAnimationHeaders"][0]["animationNames"], ["Run", "Jump"])
        self.assertEqual(result["modelAnimationHeaders"][0]["skinningCount"], 1)
        self.assertEqual(model.read_bytes(), before)

    def test_unsafe_stage_symlink_fails_closed(self):
        outside = self.root / "external"
        outside.mkdir()
        self.ws.mkdir()
        self.stage.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_STAGE"):
            doctor.run()


if __name__ == "__main__":
    unittest.main()
