"""HIGHFLY P69 FURY core integration contract tests; synthetic stage anchors.
The real private game must still compile via P9 and be tested on Android.
"""
import importlib.util,sys,types,unittest,math
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_p69_fury_core.py"
if "highfly_p9_private_build_smoke" not in sys.modules:
    stub=types.ModuleType("highfly_p9_private_build_smoke")
    stub.STAGE=Path("/missing/stage");stub.ORIGINAL=Path("/missing/original")
    sys.modules["highfly_p9_private_build_smoke"]=stub
spec=importlib.util.spec_from_file_location("p69",SCRIPT)
p69=importlib.util.module_from_spec(spec)
sys.modules["p69"]=p69
spec.loader.exec_module(p69)

class FuryTests(unittest.TestCase):
    def main(self):
        return (
            "import { AutoLoot } from './game/autoloot';\n"
            "  hud.onMobileAttackNearest = () => attackNearest();\n"
            "      world.targetEntity(enemy.id);\n"
            "      world.startAutoAttack();\n"
            "      highflyApproachEnemy(enemy.id);\n"
            "      return true;\n"
            "  mobileControls.start();\n"
            "        const worldX=vertical*Math.sin(yaw)+horizontal*Math.cos(yaw);\n"
            "        const worldZ=vertical*Math.cos(yaw)-horizontal*Math.sin(yaw);\n"
            "  function attackNearest(): void {\n"
        )
    def hud(self):
        return (
            "  onMobileAttackNearest: (() => void) | null = null;\n"
            "  private mobileSourceSlotForButton(\n"
            "      attackNearest: this.onMobileAttackNearest,\n"
        )
    def ring(self):
        return (
            "  attackNearest: (() => void) | null;\n"
            "    const hfTap=deps.attackTapState();\n"
        )
    def sim(self):
        return (
            "} from './combat/auto_attack';\n"
            "  startAutoAttack(pid?: number): void {\n"
        )
    def auto(self):
        return (
            "import { meleeReachActor } from './feral_reach';\n"
            "export function updatePlayerAutoAttack(ctx: SimContext, p: Entity, meta: PlayerMeta): void {\n"
            "  p.swingTimer = Math.max(0, p.swingTimer - DT);\n"
        )
    def test_joystick_native_screen_right_sign(self):
        s=p69.patch_main(self.main())
        self.assertIn("worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw)",s)
        self.assertIn("worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw)",s)
        def bearing(x,y,yaw):
            return math.atan2(y*math.sin(yaw)-x*math.cos(yaw),
                              y*math.cos(yaw)+x*math.sin(yaw))
        self.assertAlmostEqual(bearing(1,0,0),-math.pi/2)
        self.assertAlmostEqual(bearing(-1,0,0),math.pi/2)
        self.assertAlmostEqual(bearing(.4,.9,0),math.atan2(-.4,.9))
        self.assertNotAlmostEqual(bearing(.4,.9,0),-math.pi/4)
    def test_manual_button_is_one_physical_request(self):
        main=p69.patch_main(self.main())
        ring=p69.patch_ring(self.ring())
        hud=p69.patch_hud(self.hud())
        sim=p69.patch_sim(self.sim())
        self.assertIn("hud.onHighflyBasicTap = () => highflyBasicTap();",main)
        self.assertIn("if(offlineSim) offlineSim.highflyTapBasicAttack();",main)
        self.assertIn("highflyBasicTap(enemy.id);",main)
        self.assertIn("if(deps.onHighflyBasicTap)",ring)
        self.assertIn("onHighflyBasicTap: this.onHighflyBasicTap",hud)
        self.assertIn("queueHighflyTap(this.player,this.tickCount)",sim)
    def test_soft_target_works_across_all_angles(self):
        main=p69.patch_main(self.main())
        self.assertIn("for(const enemy of world.entities.values())",main)
        self.assertIn("dist2d(p.pos,enemy.pos)",main)
        self.assertIn("world.targetEntity(picked.id)",main)
        self.assertIn("isAttackableEntity(enemy,world.playerId,activePvpOpponentIds(world))",main)
        self.assertIn("highflyApproachEnemy(picked.id)",main)
    def test_manual_hit_retains_native_damage_gates(self):
        s=p69.patch_auto(self.auto())
        for piece in ("claimHighflyTap", "tryPlayerSwing(ctx,p,meta)",
                      "!ctx.isHostileTo(p,t)", "p.castingAbility",
                      "isStunned(p)", "isDisarmed(p)",
                      "dist2d(p.pos,t.pos)>MELEE_RANGE",
                      "p.autoAttack=false"):
            self.assertIn(piece,s)
        self.assertNotIn("dealDamage(",s)
    def test_one_slot_bounded_combo_pacing_no_adrenaline_gcd(self):
        s=p69.TAPS_CODE
        self.assertIn("HIGHFLY_TAP_MIN_TICKS=5",s)
        self.assertIn("HIGHFLY_TAP_QUEUE_TICKS=32",s)
        self.assertIn("existing.pending=true",s)
        self.assertIn("nextAllowed=tick+HIGHFLY_TAP_MIN_TICKS",s)
        self.assertNotIn("castAbility(",s)
        self.assertNotIn("gainRage",s)
        self.assertNotIn("dealDamage",s)
    def test_mobile_legends_style_real_ground_reticle_drag_and_release(self):
        s=p69.TOUCH_CODE
        for piece in ("pointerdown","pointermove","pointerup",
                      "pointercancel","hooks.begin(spec.slot)",
                      "hooks.update(target)","hooks.commit(target)",
                      "hooks.cancel()","setPointerCapture",
                      "e.stopImmediatePropagation()", "holder.value"):
            self.assertIn(piece,s)
        main=p69.patch_main(self.main())
        self.assertIn("hud.isGroundAimActive()",main)
        self.assertIn("hud.commitGroundAimAt(p)",main)
        self.assertIn("hud.updateGroundAimPoint(p)",main)
        self.assertIn("cameraYaw:()=>input.camYaw",main)
    def test_no_second_skill_system_no_empower_override(self):
        s=p69.patch_hud(self.hud())
        self.assertIn("a.def.targetMode!=='position'",s)
        self.assertIn("a.def.selfCentered",s)
        self.assertIn("!!a.def.empowerStages",s)
        self.assertNotIn("furyDirectDamage",s)
    def test_fury_thumb_does_not_touch_joystick_camera(self):
        s=p69.TOUCH_CODE
        self.assertIn("Math.atan2(-dx,-dy)",s)
        self.assertNotIn("input.setTouchMove",s)
        self.assertNotIn("input.camYaw =",s)
        self.assertNotIn("triggerTouchDash",s)
    def test_cancel_button_follows_pointer_real_native_cancel(self):
        s=p69.TOUCH_CODE
        self.assertIn("isCancel(e.clientX,e.clientY)",s)
        self.assertIn("drop(true);return;",s)
        self.assertIn("window.addEventListener('blur',blur)",s)
        self.assertIn("window.removeEventListener('blur',blur)",s)
        self.assertIn("cancel.remove()",s)
        self.assertIn("pointer-events:none",p69.CSS_CODE)
    def test_fail_closed_on_drift(self):
        with self.assertRaisesRegex(RuntimeError,"P69_ANCHOR_NATIVE_360_SIGN_COUNT_0"):
            p69.patch_main(self.main().replace("Math.cos(yaw)+horizontal", "Math.cos(yaw)-horizontal"))
        with self.assertRaisesRegex(RuntimeError,"P69_ANCHOR_RING_MANUAL_ATK_COUNT_0"):
            p69.patch_ring(self.ring().replace("const hfTap", "const tapChanged"))
        with self.assertRaisesRegex(RuntimeError,"P69_ANCHOR_SIM_REQUEST_COUNT_0"):
            p69.patch_sim(self.sim().replace("startAutoAttack", "someAttack"))
    def test_p69_does_not_claim_fake_curved_fireball_or_aerial_combo(self):
        code=SCRIPT.read_text("utf8")
        self.assertIn('"fireballCurved":"pending',code)
        self.assertIn('"aerialCombo":"pending',code)
        self.assertIn('"onlineMode":"legacy server-authorized autoattack',code)
    def test_private_stage_backups_protected_files(self):
        code=SCRIPT.read_text("utf8")
        for fragment in ("p9.preflight(ORIGINAL,STAGE,p9.REPORT)",
                         "P69_REQUIRES_P68","P69_REQUIRES_P63_COMBO",
                         "P69_REQUIRES_P64_BOAR", "except BaseException:",
                         "shutil.copy2(source,dest)", "BUILD_GREEN_BROWSER_PENDING"):
            self.assertIn(fragment,code)
        self.assertNotIn("git push",code)
        self.assertNotIn("src/sim/content/zone1.ts",code)
    def test_full_stage_patch_does_not_modify_broken_downloader_assets(self):
        self.assertNotIn("download",SCRIPT.read_text("utf8"))
        self.assertNotIn("kaykit",SCRIPT.read_text("utf8").lower())
        self.assertNotIn("craftpix",SCRIPT.read_text("utf8").lower())
if __name__=="__main__":unittest.main()
