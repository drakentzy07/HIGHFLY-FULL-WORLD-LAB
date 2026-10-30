import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_p8_import_eastbrook_gltf.py"
SPEC=importlib.util.spec_from_file_location("highfly_p8",SCRIPT)
p=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def tiny_glb(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps({"asset":{"version":"2.0"},"meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}]}).encode()
    payload+=b" "*((-len(payload))%4)
    path.write_bytes(struct.pack("<4sIII4s",b"glTF",2,20+len(payload),len(payload),b"JSON")+payload)


class P8Tests(unittest.TestCase):
    def fixtures(self,root):
        reference=root/".workspace/claudecraft-v0.44.7"
        stage=root/".workspace/highfly-origin-stage-p0"
        pack=root/".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7/KayKit Medieval Hexagon Pack 1.0.1"
        report=root/".workspace/reports/highfly-p8"
        (reference/".git").mkdir(parents=True)
        (stage/"HIGHFLY_STAGE_STATUS.json").parent.mkdir(parents=True)
        (stage/"HIGHFLY_STAGE_STATUS.json").write_text(json.dumps({
            "sourceCommit":p.PIN,"originalPublicMediaCopied":False
        }))
        for rel in ("src/sim/eastbrook_layout.ts","src/sim/items.ts",
                    "src/sim/corpse_loot_state.ts","src/sim/mob/lifecycle.ts"):
            for base in (reference,stage):
                file=base/rel
                file.parent.mkdir(parents=True,exist_ok=True)
                file.write_text("protected code "+rel)
        base=pack/"Assets/gltf/buildings/blue"
        base.mkdir(parents=True)
        for name in p.BUILDINGS:
            gltf=base/f"building_{name}_blue.gltf"
            gltf.write_text(json.dumps({
                "asset":{"version":"2.0"},
                "meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}],
                "buffers":[{"uri":"geometry.bin","byteLength":3}],
                "images":[{"uri":"palette.png"}]
            }))
        (base/"geometry.bin").write_bytes(b"123")
        (base/"palette.png").write_bytes(b"png")
        return reference,stage,pack,report

    def test_plan_uses_seven_exact_urls_without_game_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            reference,stage,pack,report=self.fixtures(root)
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.PIN+"\n"):
                rows=p.plan(reference,stage,pack,report)
            self.assertEqual(len(rows),7)
            self.assertEqual({x["kind"] for x in rows},set(p.BUILDINGS))
            self.assertEqual({x["publicUrl"] for x in rows},{
                "/models/biome/"+f for f in p.BUILDINGS.values()})
            self.assertEqual(len(rows[0]["externalDependencies"]),2)
            self.assertFalse((stage/"public").exists())
            self.assertFalse(report.exists())

    def test_refuses_remote_dependencies_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            reference,stage,pack,report=self.fixtures(root)
            gltf=pack/"Assets/gltf/buildings/blue/building_church_blue.gltf"
            content=json.loads(gltf.read_text())
            content["images"]=[{"uri":"https://elsewhere.invalid/texture.png"}]
            gltf.write_text(json.dumps(content))
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.PIN+"\n"):
                with self.assertRaisesRegex(RuntimeError,"GLTF_DEPENDENCY_NOT_LOCAL"):
                    p.plan(reference,stage,pack,report)
            self.assertFalse((stage/"public").exists())

    def test_import_only_seven_own_glbs_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            reference,stage,pack,report=self.fixtures(root)
            report.mkdir(parents=True)
            with patch.object(p,"ROOT",root),patch.object(p.subprocess,"check_output",return_value=p.PIN+"\n"),patch.object(p,"converter_path",return_value=Path("/mock/converter")):
                rows=p.plan(reference,stage,pack,report)
                def fake_converter(source,target,exe,cwd):
                    tiny_glb(target)
                with patch.object(p,"convert",side_effect=fake_converter):
                    result=p.install(rows,reference,stage,report)
                    again=p.install(rows,reference,stage,report)
                self.assertEqual(len(result["buildings"]),7)
                self.assertEqual(len(again["buildings"]),7)
                self.assertTrue((stage/"public/models/biome/hexb_tavern.glb").is_file())
                self.assertTrue((stage/"public/models/biome/hex_church.glb").is_file())
                self.assertFalse((reference/"public").exists())
                self.assertEqual((stage/"src/sim/items.ts").read_text(),"protected code src/sim/items.ts")

if __name__=="__main__":
    unittest.main()
