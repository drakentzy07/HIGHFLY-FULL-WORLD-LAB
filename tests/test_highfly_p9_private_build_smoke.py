import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hashlib

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_p9_private_build_smoke.py"
SPEC=importlib.util.spec_from_file_location("highfly_p9",SCRIPT)
p=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class P9Tests(unittest.TestCase):
    def fixture(self,root):
        original=root/".workspace/claudecraft-v0.44.7"
        stage=root/".workspace/highfly-origin-stage-p0"
        report=root/".workspace/reports/highfly-p9"
        (original/".git").mkdir(parents=True)
        (stage/"public/models/biome").mkdir(parents=True)
        (stage/"src/render/characters").mkdir(parents=True)
        (stage/"HIGHFLY_STAGE_STATUS.json").write_text(
            json.dumps({"sourceCommit":p.SHA,"originalPublicMediaCopied":False}),encoding="utf8")
        (stage/"src/render/characters/manifest.ts").write_text(
            "// HIGHFLY_P4_VISUAL_BRIDGE_START",encoding="utf8")
        for relative in ("src/sim/eastbrook_layout.ts", "src/sim/items.ts",
                         "src/sim/corpse_loot_state.ts", "src/sim/mob/lifecycle.ts"):
            for parent in (original,stage):
                path=parent/relative
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text("protected code "+relative,encoding="utf8")
        rows=[]
        for name in p.BUILDING_NAMES:
            path=stage/"public/models/biome"/name
            path.write_bytes(b"private KayKit GLB mock "+name.encode())
            rows.append({
                "publicUrl":"/models/biome/"+name,
                "glbSha256":hashlib.sha256(path.read_bytes()).hexdigest()
            })
        p8=root/".workspace/reports/highfly-p8/EASTBROOK_OWNED_BUILDINGS_P8.json"
        p8.parent.mkdir(parents=True)
        p8.write_text(json.dumps({
            "sourceCommit":p.SHA,"noClaudeCraftMediaCopied":True,"buildings":rows
        }),encoding="utf8")
        for name in p.REQUIRED_BUILD_TEXT:
            (original/name).write_text("build config "+name,encoding="utf8")
        vite=original/"node_modules/vite/bin/vite.js"
        vite.parent.mkdir(parents=True)
        vite.write_text("// vite mock")
        return original,stage,report

    def test_preflight_reports_missing_text_without_changing_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original,stage,report=self.fixture(root)
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.SHA+"\n"):
                data=p.preflight(original,stage,report)
            self.assertEqual(len(data["textFiles"]),4)
            self.assertFalse((stage/".browserslistrc").exists())
            self.assertFalse((stage/"node_modules").exists())
            self.assertFalse((original/"public").exists())

    def test_build_attempt_is_private_and_preserves_sim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original,stage,report=self.fixture(root)
            def fake_run(args,**kwargs):
                self.assertEqual(kwargs["cwd"],str(stage))
                self.assertEqual(kwargs["env"]["VITE_HIGHFLY_P4"],"1")
                self.assertEqual(kwargs["env"]["VITE_HIGHFLY_OFFLINE_LAB"],"1")
                return type("Outcome",(),{"returncode":0,"stdout":"vite complete","stderr":""})()
            before=(stage/"src/sim/items.ts").read_bytes()
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.SHA+"\n"),patch.object(p.subprocess,"run",side_effect=fake_run):
                result=p.smoke(original,stage,report)
            self.assertEqual(result["result"],"BUNDLE_BUILT_NOT_PLAYABLE_VERIFIED")
            self.assertEqual((stage/"src/sim/items.ts").read_bytes(),before)
            self.assertEqual((original/"src/sim/items.ts").read_bytes(),before)
            self.assertFalse((original/"public").exists())
            self.assertTrue((report/"VITE_BUILD_P9.json").is_file())

    def test_protects_modified_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original,stage,report=self.fixture(root)
            (stage/"public/models/biome/hexb_tavern.glb").write_bytes(b"different")
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.SHA+"\n"):
                with self.assertRaisesRegex(RuntimeError,"P8_PRIVATE_BUILDING_HASH_CHANGED"):
                    p.preflight(original,stage,report)
            self.assertFalse((stage/"node_modules").exists())


if __name__=="__main__":
    unittest.main()
