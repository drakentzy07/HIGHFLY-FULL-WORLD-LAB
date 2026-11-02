"""HIGHFLY Classic restore: verify native selector, saved games, controls, rollback."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("classic_restore",
    ROOT/"scripts/highfly_world7_classic_restore.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

class RestoreTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.stage=self.root/".workspace/highfly-origin-stage-p0"
        self.out=self.root/".workspace/reports/highfly-world7/p71"
        self.stage.mkdir(parents=True)
        self.out.mkdir(parents=True)
        native=(
            "import './core';\n"
            "// HIGHFLY_P69_FURY_CORE\n"
            "// HIGHFLY_P41_OFFLINE_SAVE\n"
            "  const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);\n"
            "        const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);\n"
            "        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);\n"
            "  hud.onHighflyBasicTap = () => highflyBasicTap();\n"
            "      highflyBasicTap(enemy.id);\n      return true;\n"
        )
        self.native=native.encode()
        self.main_p71=(
            native+
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "currentClass: offlineSim.player.cls,\n"
        ).encode()
        self.current=(
            native+
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "// HIGHFLY_WORLD7_P71_DRAKENLAB\n"
            "currentClass: offlineSim.player.templateId as PlayerClass,\n"
        ).encode()
        modts=b"export const menu = 'DrakenLAB';"
        modcss=b".hf-lab {display:block}"
        index=b"<html><head><title>HIGHFLY</title></head><body>World</body></html>"
        save=(
            "// HIGHFLY_P41_OFFLINE_SAVE\n"
            "const KEY='highfly.origin.offline.v1';\n"
            "const raw=localStorage.getItem(KEY);\n"
            "localStorage.setItem(KEY,json);return s;\n"
        ).encode()
        self.sources={p.MAIN:self.current,p.INDEX:index,p.SAVE:save,
                      p.MODS[0]:modts,p.MODS[1]:modcss}
        for rel,data in self.sources.items():
            f=self.stage/rel
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(data)
        orig=self.out/p.BASE
        orig.parent.mkdir(parents=True,exist_ok=True)
        orig.write_bytes(self.native)
        prior=self.out/"backup/P71B_BEFORE_CLASS_FIELD_FIX.ts"
        prior.write_bytes(self.main_p71)
        (self.out/p.P71).write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "sourceHashes":{
                p.MAIN:sha(self.main_p71),
                p.MODS[0]:sha(modts),
                p.MODS[1]:sha(modcss),
            }}),"utf8")
        (self.out/p.P71B).write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "updatedSha256":sha(self.current)
        }),"utf8")
        self.patcher=patch.object(p.p9,"preflight",return_value={"okay":True})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def go(self,apply=False,build=None):
        return p.run(apply,stage=self.stage,out=self.out,repo=self.root,build=build)

    def test_dry_run_no_mutation(self):
        report=self.go(False)
        self.assertEqual(report["mode"],"DRY_RUN")
        for rel,data in self.sources.items():
            self.assertEqual((self.stage/rel).read_bytes(),data)
        self.assertFalse((self.stage/p.NEW_CSS).exists())

    def test_restore_native_selector_and_atk(self):
        status=self.go(True,build=lambda:{"exitCode":0})
        self.assertEqual(status["mode"],"BUILD_GREEN_BROWSER_PENDING")
        main=(self.stage/p.MAIN).read_text("utf8")
        self.assertNotIn("WORLD7_P71_DRAKENLAB",main)
        self.assertIn("VITE_HIGHFLY_OFFLINE_LAB === '1'",main)
        self.assertIn("world.targetEntity(enemy.id)",main)
        self.assertIn("hud.onHighflyBasicTap = null;",main)
        self.assertIn("worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw)",main)
        self.assertIn("worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw)",main)
        self.assertTrue((self.stage/p.NEW_CSS).exists())
        for rel in p.MODS:
            self.assertFalse((self.stage/rel).exists())
        save=(self.stage/p.SAVE).read_text("utf8")
        self.assertIn("slotKey(name)",save)
        self.assertIn("getItem(KEY)",save) # preserve legacy old save fallback
        self.assertTrue((self.out/p.RESTORE_BACKUP/p.MAIN).is_file())
        self.assertEqual((self.out/p.BASE).read_bytes(),self.native)
        self.assertEqual(self.go()["mode"],"BUILD_GREEN_BROWSER_PENDING")

    def test_red_build_rolls_back_everything(self):
        with self.assertRaisesRegex(RuntimeError,"BUILD_FAILED"):
            self.go(True,build=lambda:{"exitCode":1})
        for rel,data in self.sources.items():
            self.assertEqual((self.stage/rel).read_bytes(),data)
        self.assertFalse((self.stage/p.NEW_CSS).exists())
        self.assertFalse((self.out/p.STATUS).exists())

    def test_refuse_current_source_drift(self):
        (self.stage/p.MAIN).write_bytes(self.current+b"unrelated\n")
        with self.assertRaisesRegex(RuntimeError,"MAIN_HASH_CHANGED"):
            self.go(True,build=lambda:{"exitCode":0})
        self.assertFalse((self.out/p.RESTORE_BACKUP).exists())

    def test_missing_p41_fails_closed(self):
        (self.stage/p.SAVE).unlink()
        with self.assertRaisesRegex(RuntimeError,"P41_NAMED_SAVE"):
            self.go(False)

    def test_refuse_tampered_drakenlab_file(self):
        (self.stage/p.MODS[0]).write_bytes(b"MODIFIED")
        with self.assertRaisesRegex(RuntimeError,"MODULE_HASH_CHANGED"):
            self.go(True,build=lambda:{"exitCode":0})

    def test_refuse_incomplete_prior_backup(self):
        backup=self.out/p.RESTORE_BACKUP
        backup.mkdir()
        with self.assertRaisesRegex(RuntimeError,"REQUIRED_FILE_MISSING"):
            self.go(False)

    def test_retry_after_rolled_back_build_without_deleting_backup(self):
        with self.assertRaisesRegex(RuntimeError,"BUILD_FAILED"):
            self.go(True,build=lambda:{"exitCode":1})
        # Prior backup remains valuable. Retry only when all bytes still match.
        result=self.go(True,build=lambda:{"exitCode":0})
        self.assertEqual(result["mode"],"BUILD_GREEN_BROWSER_PENDING")
        self.assertEqual((self.out/p.RESTORE_BACKUP/p.MAIN).read_bytes(),self.current)

    def test_preserves_native_camera_right_basis(self):
        # The original stepPlayerMotion uses camera-right = (-cos, +sin).
        # P69 sign is correct; only stick/animation runtime QA remains.
        main = p.patch_original(
            self.native.decode("utf8"),
            self.sources[p.INDEX].decode("utf8"),
            self.sources[p.SAVE].decode("utf8"))[0]
        self.assertIn("worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw)", main)
        self.assertIn("worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw)", main)
        self.assertNotIn("worldX=vertical*Math.sin(yaw)+horizontal*Math.cos(yaw)", main)

if __name__=="__main__":
    unittest.main()
