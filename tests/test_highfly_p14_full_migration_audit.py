import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts/highfly_p14_full_migration_audit.py"
SPEC = importlib.util.spec_from_file_location("highfly_p14", SOURCE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class FullMigrationAuditTests(unittest.TestCase):
    def setup_world(self, root):
        reference = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        archive = root / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
        report = root / ".workspace/reports/highfly-p14"
        (reference / ".git").mkdir(parents=True)
        stage.mkdir(parents=True)
        (stage / "HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit": p.p12.PIN, "originalPublicMediaCopied": False,
        }), encoding="utf8")
        for names in p.p6.MODULES.values():
            for name in names:
                for basedir in (reference, stage):
                    path = basedir / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("protected module " + name, encoding="utf8")
        for relative in ("src/render/characters/manifest.ts", "src/main.ts"):
            source = reference / relative
            target = stage / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("original code", encoding="utf8")
            target.write_text("HIGHFLY private change", encoding="utf8")
        (reference / "src/another.ts").write_text(
            "const u = '/models/dungeon/chest.glb'", encoding="utf8")
        (stage / "src/another.ts").write_text(
            "const u = '/models/dungeon/chest.glb'", encoding="utf8")
        (reference / "src/not_copied.ts").write_text("not included", encoding="utf8")
        for relative in ("models/dungeon/chest.glb",
                         "models/biome/kcas_wall.glb",
                         "ui/character_card.webp"):
            path = reference / "public" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"reference media not for copying")
        (stage / "public/models/biome").mkdir(parents=True)
        (stage / "public/models/biome/hexb_tavern.glb").write_bytes(
            b"independent owned test model")
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(
                "The Complete KayKit Collection v7/KayKit Dungeon Pack 1.1/Assets/gltf/chest.gltf",
                '{"asset":{"version":"2.0"},"meshes":[{}]}')
        return reference, stage, archive, report

    def test_global_audit_reports_preservation_and_missing_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_world(root)
            before = (stage / "src/sim/items.ts").read_bytes()
            with patch.object(p, "ROOT", root), patch.object(
                p.p12, "ROOT", root), patch.object(p.p5, "ROOT", root), patch.object(
                p.p12.subprocess, "check_output", return_value=p.p12.PIN+"\n"):
                result = p.audit(ref, stage, archive, out)
            self.assertTrue(result["coreRpgCodeIdentical"])
            self.assertIn("src/not_copied.ts", result["code"]["missingCodeFiles"])
            self.assertEqual(len(result["code"]["expectedModifiedCodeFiles"]), 2)
            self.assertEqual(result["media"]["referenceFiles"], 3)
            self.assertEqual(result["media"]["independentFiles"], 1)
            self.assertEqual(result["media"]["missingSamePath"], 3)
            self.assertEqual(result["ownedKayKitWorld"]["exactMatchModelsReadyToImport"], 1)
            self.assertTrue((out / "MIGRATION_AUDIT_P14.md").is_file())
            self.assertEqual((stage / "src/sim/items.ts").read_bytes(), before)
            self.assertEqual((ref / "public/models/dungeon/chest.glb").read_bytes(),
                             b"reference media not for copying")

    def test_media_category_preserves_distinction_between_original_and_own_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_world(root)
            with patch.object(p, "ROOT", root):
                result = p.media_inventory(ref, stage, {"models/dungeon/chest.glb"})
            dungeon = result["byCategory"]["models/dungeon"]
            self.assertEqual(dungeon["sourceSamePathStillMissing"], 1)
            self.assertEqual(dungeon["literalRefsNotInHighfly"], 1)
            self.assertEqual(result["byCategory"]["models/biome"]["highflyFiles"], 1)

    def test_identifies_unexpected_changes_without_overwriting_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref, stage, archive, out = self.setup_world(root)
            path = stage / "src/another.ts"
            path.write_text("unexpected modification", encoding="utf8")
            result = p.code_inventory(ref, stage)
            self.assertIn("src/another.ts", result["unexpectedModifiedCodeFiles"])
            self.assertEqual(path.read_text(), "unexpected modification")


if __name__ == "__main__":
    unittest.main()
