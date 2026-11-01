"""HIGHFLY P68 FURY GOLDEN mobile integration contracts.
Fixtures reproduce P65+P67 edits, including attack tap guard.
"""
import importlib.util,sys,types,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_p68_fury_golden_recovery.py"
if "highfly_p9_private_build_smoke" not in sys.modules:
    p9=types.ModuleType("highfly_p9_private_build_smoke")
    p9.STAGE=Path("/missing/stage");p9.ORIGINAL=Path("/missing/original")
    sys.modules["highfly_p9_private_build_smoke"]=p9
spec=importlib.util.spec_from_file_location("p68",SCRIPT)
p68=importlib.util.module_from_spec(spec);sys.modules["p68"]=p68
spec.loader.exec_module(p68)

class P68Tests(unittest.TestCase):
    def main(self):
        return (
          "    // HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM: free cam\n"
          "      const horizontal=Number(mi.strafeRight)-Number(mi.strafeLeft);\n"
          "      const vertical=Number(mi.forward)-Number(mi.back);\n"
          "      if (horizontal!==0 || vertical!==0) {\n"
          "        const yaw=input.camYaw;\n"
          "        const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);\n"
          "        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);\n"
          "        facing=Math.atan2(worldX,worldZ);\n"
          "        mi.forward=true;mi.back=false;\n"
          "        mi.strafeLeft=false;mi.strafeRight=false;\n"
          "      }\n"
          "    let bestD = 40;\n"
          "    for (const e of world.entities.values()) {\n"
        )
    def ring(self):
        return (
          "    // HIGHFLY_P63_COMBAT_C1\n"
          "    if(!(hfTap.autoAttack&&hfTap.hasLiveHostileTarget)){\n"
          "      handleMobileAttackTap(hfTap,{\n"
          "        activateAttack:()=>deps.activateFixedAttackSlot(),\n"
          "        attackNearest:deps.attackNearest,\n"
          "      });\n"
          "    }\n"
        )
    def test_analog_interface_and_accessor(self):
        s=p68.patch_input(
          "  strafeRight: boolean;\n}\n\nexport interface InputDebugState {\n"
          "  setTouchMove(move: TouchMoveInput): void {\n")
        self.assertIn("analogX?: number",s)
        self.assertIn("analogY?: number",s)
        self.assertIn("getHighflyTouchAnalog()",s)
        self.assertIn("this.suspendMovement",s)
        self.assertIn("Math.hypot(x,y)<0.18",s)
    def test_joystick_forwards_original_and_preserves_continuous_angle(self):
        s=p68.patch_mobile("    this.input.setTouchMove(move);")
        self.assertIn("{...move,analogX:x,analogY:-y}",s)
        self.assertNotIn("applyTouchLookDelta",s)
    def test_right_input_faces_right_at_yaw_zero(self):
        s=p68.patch_main(self.main())
        self.assertIn("const worldX=vertical*Math.sin(yaw)+horizontal*Math.cos(yaw);",s)
        self.assertIn("const worldZ=vertical*Math.cos(yaw)-horizontal*Math.sin(yaw);",s)
        self.assertIn("input.getHighflyTouchAnalog()",s)
        # Cardinal and diagonal directions: same mathematics as TS.
        import math
        def heading(x,y,yaw=0):
            return math.atan2(y*math.sin(yaw)+x*math.cos(yaw),
                              y*math.cos(yaw)-x*math.sin(yaw))
        self.assertAlmostEqual(heading(1,0),math.pi/2)
        self.assertAlmostEqual(heading(-1,0),-math.pi/2)
        self.assertAlmostEqual(heading(0,-1),math.pi)
        self.assertAlmostEqual(heading(0.4,0.9),math.atan2(.4,.9))
        self.assertNotAlmostEqual(heading(0.4,0.9),math.pi/4)
    def test_soft_attack_does_not_require_manual_lock(self):
        ring=p68.patch_ring(self.ring())
        main=p68.patch_main(self.main())
        self.assertIn("if(deps.attackNearest) deps.attackNearest()",ring)
        self.assertIn("let bestD = 15;",main)
        # The existing main.ts retains native hostility/death checks; P68
        # only narrows the previous 40-unit search to 15 units.
        self.assertNotIn("isAttackableEntity",p68.patch_main(self.main()))
        self.assertNotIn("dealDamage(",ring)
    def test_centered_loading_tips(self):
        c=p68.CSS
        self.assertIn("grid-template-rows:17px 11px",c)
        self.assertIn("#loading-screen .ls-progress #ls-tip",c)
        self.assertIn("justify-content:center!important",c)
        self.assertIn("text-align:center!important",c)
        self.assertIn("grid-row:3!important",c)
    def test_unified_skill_colors_and_native_icons(self):
        c=p68.CSS
        self.assertIn("#mobile-passive,#mobile-jump,#mobile-dodge",c)
        self.assertIn('data-mobile-index="0"',c)
        self.assertIn("border:2px solid #a888eb!important",c)
        self.assertNotIn("castSlot(",c)
    def test_head_append_once(self):
        a=p68.patch_html("<head></head>")
        self.assertEqual(a.count("/highfly/p68_fury_recovery.css"),1)
        with self.assertRaisesRegex(RuntimeError,"P68_SOURCE_DRIFT_HEAD_2"):
            p68.patch_html("<head></head></head>")
    def test_guard_drift(self):
        with self.assertRaisesRegex(RuntimeError,"P68_SOURCE_DRIFT_TRUE_360_VECTOR_0"):
            p68.patch_main(self.main().replace("const worldX","const WORLD_X"))
        with self.assertRaisesRegex(RuntimeError,"P68_SOURCE_DRIFT_MOBILE_ATK_ACQUIRE_0"):
            p68.patch_ring(self.ring().replace("handleMobileAttackTap","replacedHandler"))
    def test_private_stage_backup_rollback(self):
        code=SCRIPT.read_text("utf8")
        for anchor in ("p9.preflight(O,S,p9.REPORT)","shutil.copy2(src,dest)",
                       "except BaseException:","P68_REQUIRES_P67_STAGE",
                       "P68_REQUIRES_P64_BOAR","P68_REQUIRES_P63_RING",
                       "BUILD_GREEN_BROWSER_PENDING"):
            self.assertIn(anchor,code)
        self.assertNotIn("git push",code)
        self.assertNotIn("src/sim/content/zone1.ts",code)
    def test_does_not_claim_four_independent_hits_or_full_skill_aim(self):
        code=SCRIPT.read_text("utf8")
        self.assertIn('"fullFourTapComboCompleted":False',code)
        self.assertIn("FURY F1 gesture integration separately pending",code)
        self.assertNotIn("p.swingTimer = 0",code)

if __name__=="__main__":unittest.main()
