import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_p13_private_knight_creator.py"
SPEC=importlib.util.spec_from_file_location("highfly_p13",SCRIPT)
p=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class P13PrivateCreatorTests(unittest.TestCase):
    def fixture(self,root):
        stage=root/".workspace/highfly-origin-stage-p0"
        report=root/".workspace/reports/highfly-p13"
        main=stage/"src/main.ts"
        main.parent.mkdir(parents=True)
        main.write_text(
            p.BEFORE+"\n  else characterPreview.setClass(cls);\n}\n\n"
            + "function syncAppearanceUi(panelId: string, cls: PlayerClass): void {\n"
            + "  const hostSel = APPEARANCE_HOSTS[panelId];\n"
            + "  if (!hostSel) return;\n"
            + "  const host = document.querySelector(hostSel) as HTMLElement | null;\n"
            + "  if (!host) return;\n"
            + "  appearancePanelClass.set(panelId, cls);\n"
            + p.EDITOR_BEFORE+"\n    host.hidden=true;\n  }\n}\n"
        )
        return stage,report,main

    def test_preview_uses_kaykit_visual_no_rpg_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            stage,report,main=self.fixture(root)
            original=main.read_text()
            with patch.object(p,"ROOT",root),patch.object(p.p9,"preflight",return_value={}):
                result=p.apply(stage,report)
                self.assertTrue(result["changed"])
                self.assertIn("characterPreview.setClass('warrior');",main.read_text())
                self.assertIn("host.hidden = true;",main.read_text())
                self.assertIn("const look = modularLookForClass(cls);",main.read_text())
                self.assertEqual((report/"MAIN_BEFORE_P13.ts").read_text(),original)
                again=p.apply(stage,report)
                self.assertFalse(again["changed"])
            self.assertFalse((stage/"public").exists())

    def test_refuses_unknown_source_no_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            stage,report,main=self.fixture(root)
            main.write_text("unrelated main.ts")
            with patch.object(p,"ROOT",root):
                with self.assertRaisesRegex(RuntimeError,"SOURCE_SIGNATURE_MISMATCH"):
                    p.plan(stage)
            self.assertFalse(report.exists())


if __name__=="__main__":
    unittest.main()
