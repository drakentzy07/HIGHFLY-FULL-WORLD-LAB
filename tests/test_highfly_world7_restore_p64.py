"""HIGHFLY P64 cleanup: full backup-chain reconstruction on synthetic private stage.

No actual user assets, private stage or network used in CI. Patch-transform
functions are replaced with deterministic pure marker transforms: production
still verifies against the REAL P65/P66/P68/P69 unchanged installer code.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("restore_p64",ROOT/"scripts/highfly_world7_restore_p64.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

class RestoreP64Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo=Path(tmp.name)
        self.stage=self.repo/".workspace/highfly-origin-stage-p0"
        self.reports=self.repo/".workspace/reports"
        self.out=self.reports/"highfly-world7/p64-clean-recovery"
        self.stage.mkdir(parents=True)
        self.reports.mkdir(parents=True)
        self.patches=[]
        for module,methods,tag in [
            (p.p65,("patch_main","patch_html","patch_mobile"),"65"),
            (p.p66,("patch_main","patch_html"),"66"),
            (p.p68,("patch_main","patch_html","patch_mobile","patch_input","patch_ring"),"68"),
            (p.p69,("patch_main","patch_hud","patch_sim","patch_auto","patch_ring"),"69"),
        ]:
            for method in methods:
                # Marker suffix makes all transformations distinct and order-sensitive.
                patcher=patch.object(module,method,side_effect=
                    lambda src,t=tag,m=method: src+"|"+t+"."+m)
                patcher.start()
                self.patches.append(patcher)
        self.addCleanup(lambda:[a.stop() for a in reversed(self.patches)])

        def build_src(rel:str,txt:str):
            f=self.stage/rel
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text(txt,"utf8")
            return f

        def backup(label:str,rel:str,src:str):
            folder={
                "65":"highfly-p65-hud-combat-c2",
                "66":"highfly-p66-p67-combat-premium",
                "68":"highfly-p68-fury-golden-recovery",
                "69":"highfly-p69-fury-core",
            }[label]
            f=self.reports/folder/"backups"/rel
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text(src,"utf8")
            return f

        base_main="// HIGHFLY_P41_OFFLINE_SAVE\n"
        base_html="<head><title>HIGHFLY</title></head>"
        base_mobile="// native P64 mobile controls\n"
        base_ring="// P63 action bar\n"
        base_input="// P64 input\n"
        base_hud="// P64 HUD\n"
        base_sim="// P64 Sim\n"
        base_auto="// HIGHFLY_P63_COMBAT_C1\n"
        self.base={
            p.MAIN:base_main,p.HTML:base_html,p.MOBILE:base_mobile,p.RING:base_ring,
            p.INPUT:base_input,p.HUD:base_hud,p.SIM:base_sim,p.AUTO:base_auto,
        }
        # Installer snapshots: each next installer saved the prior exact bytes.
        main65=p.p65.patch_main(base_main)
        main66=p.p66.patch_main(main65)
        main68=p.p68.patch_main(main66)
        main69=p.p69.patch_main(main68)
        html65=p.p65.patch_html(base_html)
        html66=p.p66.patch_html(html65)
        html68=p.p68.patch_html(html66)
        html69=p.p69.once(
            html68,"</head>",
            "<!-- "+p.p69.MARK+": real skill gesture + manual basics -->\n"
            '<link rel="stylesheet" href="/highfly/p69_fury_core.css" />\n</head>',
            "INDEX_HEAD")
        mob65=p.p65.patch_mobile(base_mobile)
        mob68=p.p68.patch_mobile(mob65)
        ring68=p.p68.patch_ring(base_ring)
        ring69=p.p69.patch_ring(ring68)
        inp68=p.p68.patch_input(base_input)
        hud69=p.p69.patch_hud(base_hud)
        sim69=p.p69.patch_sim(base_sim)
        auto69=p.p69.patch_auto(base_auto)
        for phase,items in [
            ("65",{p.MAIN:base_main,p.HTML:base_html,p.MOBILE:base_mobile}),
            ("66",{p.MAIN:main65,p.HTML:html65}),
            ("68",{p.MAIN:main66,p.HTML:html66,p.MOBILE:mob65,
                   p.INPUT:base_input,p.RING:base_ring}),
            ("69",{p.MAIN:main68,p.HTML:html68,p.RING:ring68,
                   p.HUD:base_hud,p.SIM:base_sim,p.AUTO:base_auto}),
        ]:
            for rel,src in items.items():
                backup(phase,rel,src)
        original_p71=self.reports/"highfly-world7/p71/backup/src/main.ts"
        original_p71.parent.mkdir(parents=True,exist_ok=True)
        original_p71.write_text(main69,"utf8")
        pre_b=main69+"// HIGHFLY_WORLD7_P71_DRAKENLAB\nold class property\n"
        curr_b=main69+"// HIGHFLY_WORLD7_P71_DRAKENLAB\nnew class property\n"
        bkp=self.reports/"highfly-world7/p71/backup/P71B_BEFORE_CLASS_FIELD_FIX.ts"
        bkp.write_text(pre_b,"utf8")
        self.curr={}
        for rel,src in {
            p.MAIN:curr_b,p.HTML:html69,p.MOBILE:mob68,p.INPUT:inp68,
            p.RING:ring69,p.HUD:hud69,p.SIM:sim69,p.AUTO:auto69,
        }.items():
            build_src(rel,src)
            self.curr[rel]=src.encode()
        build_src("src/render/characters/manifest.ts",
                  "// HIGHFLY_P64_REAL_BOAR_CC0\n")
        for rel,src in p.CREATED.items():
            build_src(rel,src)
            self.curr[rel]=src.encode()
        self.modules={}
        for rel in p.P71_CREATED:
            raw=("// DRAKENLAB "+rel).encode()
            build_src(rel,raw.decode())
            self.curr[rel]=raw
            self.modules[rel]=digest(raw)
        old_status=self.reports/"highfly-world7/p71/P71_STATUS.json"
        old_status.write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "sourceHashes":{p.MAIN:digest(pre_b.encode()),**self.modules},
        }),"utf8")
        new_status=self.reports/"highfly-world7/p71/P71B_STATUS.json"
        new_status.write_text(json.dumps({
            "mode":"BUILD_GREEN_BROWSER_PENDING",
            "updatedSha256":digest(curr_b.encode()),
        }),"utf8")
        self.preflight_patch=patch.object(p.p9,"preflight",return_value={"okay":True})
        self.preflight_patch.start()
        self.addCleanup(self.preflight_patch.stop)

    def runit(self,apply=False,build=None):
        return p.run(apply,stage=self.stage,repo=self.repo,
                     reports=self.reports,out=self.out,build=build)

    def test_dry_run_never_modifies_stage(self):
        result=self.runit()
        self.assertEqual(result["mode"],"DRY_RUN")
        self.assertEqual(result["restoredBaseline"],"P64_SOURCE_SNAPSHOT_PRE_P65")
        for rel,data in self.curr.items():
            self.assertEqual((self.stage/rel).read_bytes(),data)
        self.assertFalse(self.out.exists())

    def test_green_restores_exact_p64_and_removes_only_known_overlays(self):
        result=self.runit(True,build=lambda:{"exitCode":0})
        self.assertEqual(result["mode"],"BUILD_GREEN_BROWSER_PENDING")
        for rel,src in self.base.items():
            self.assertEqual((self.stage/rel).read_text("utf8"),src)
        for rel in tuple(p.CREATED)+p.P71_CREATED:
            self.assertFalse((self.stage/rel).exists())
        self.assertIn("HIGHFLY_P64_REAL_BOAR_CC0",
            (self.stage/"src/render/characters/manifest.ts").read_text())
        self.assertTrue((self.out/"SNAPSHOT_MANIFEST.json").exists())
        for rel,raw in self.curr.items():
            self.assertEqual((self.out/"pre_restore_snapshot"/rel).read_bytes(),raw)
        self.assertEqual(self.runit()["mode"],"BUILD_GREEN_BROWSER_PENDING")

    def test_failed_build_restores_all_new_and_old_files(self):
        with self.assertRaisesRegex(RuntimeError,"P64_BUILD_FAILED"):
            self.runit(True,build=lambda:{"exitCode":1})
        for rel,raw in self.curr.items():
            self.assertEqual((self.stage/rel).read_bytes(),raw)
        self.assertFalse((self.out/"P64_CLEAN_STATUS.json").exists())
        self.assertTrue((self.out/"pre_restore_snapshot").is_dir())

    def test_refuse_staged_input_drift_without_creating_snapshot(self):
        (self.stage/p.INPUT).write_text("modified unrelated motion file","utf8")
        with self.assertRaisesRegex(RuntimeError,"P64_CHAIN_DRIFT_P68_INPUT_CURRENT"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_refuse_asset_overwrite_or_unauthorized_remove(self):
        (self.stage/p.p69.TOUCH).write_text("// someone has modified this file","utf8")
        with self.assertRaisesRegex(RuntimeError,"P64_CHAIN_DRIFT_CREATED_"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_refuse_corrupt_backup(self):
        path=self.reports/"highfly-p65-hud-combat-c2/backups/src/main.ts"
        path.write_text("BROKEN","utf8")
        with self.assertRaisesRegex(RuntimeError,"P64_CHAIN_DRIFT_P65_P66_MAIN"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertFalse(self.out.exists())

    def test_refuse_unrelated_change_to_p71b_main(self):
        (self.stage/p.MAIN).write_text("new experimental changes","utf8")
        with self.assertRaisesRegex(RuntimeError,"P71B_CURRENT_MAIN_SHA"):
            self.runit()
        self.assertFalse(self.out.exists())

    def test_refuse_existing_incomplete_snapshot(self):
        (self.out/"pre_restore_snapshot").mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError,"P64_PREVIOUS_SNAPSHOT_EXISTS"):
            self.runit()
        self.assertTrue((self.out/"pre_restore_snapshot").exists())

    def test_stage_symlink_not_modified(self):
        alternate=self.repo/"alternate_file.ts"
        alternate.write_bytes(self.curr[p.MAIN])
        old=self.stage/p.MAIN
        old.unlink()
        old.symlink_to(alternate)
        with self.assertRaisesRegex(RuntimeError,"P64_UNSAFE_stage_"):
            self.runit(True,build=lambda:{"exitCode":0})
        self.assertEqual(alternate.read_bytes(),self.curr[p.MAIN])

if __name__=="__main__":
    unittest.main()
