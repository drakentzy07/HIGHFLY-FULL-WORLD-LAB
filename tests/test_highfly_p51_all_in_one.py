import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p51_all_in_one as p

class P51Tests(unittest.TestCase):
    def test_probe_only_one_monument(self):
        source=p.ANCHOR
        result=p.patch(source)
        self.assertIn("hf_probe_monument", result)
        self.assertIn("monumentBody.group.scale.setScalar(0)",result)
        self.assertIn("monumentFx.group.scale.setScalar(0)",result)
        self.assertNotIn("sim.remove",result)
    def test_already_applied_is_blocked(self):
        with self.assertRaisesRegex(RuntimeError,"P51_ALREADY_APPLIED"):
            p.patch(p.patch(p.ANCHOR))
    def test_missing_anchor_is_blocked(self):
        with self.assertRaisesRegex(RuntimeError,"P51_EASTBROOK_MONUMENT_ANCHOR_DRIFT"):
            p.patch("other")
    def test_all_known_problems_audited(self):
        self.assertEqual(len(p.TOPICS),9)
        for cat in ("02_LOG_Y_BADGE_P35","04_JOYSTICK_GIRO_Y_FURY",
                    "05_JABALIES_Y_MONSTRUOS","06_EASTBROOK_BLOQUE_GIGANTE",
                    "07_NATACION_Y_BARCOS","08_BOLSA_LOOT_Y_MISIONES"):
            self.assertIn(cat,p.TOPICS)
    def test_no_private_kaykit_extraction(self):
        src=Path(p.__file__).read_text()
        self.assertIn("archive.namelist()",src)
        self.assertNotIn("extractall",src)
        self.assertNotIn("archive.extract(",src)
if __name__=="__main__":
    unittest.main()
