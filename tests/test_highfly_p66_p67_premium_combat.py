"""HIGHFLY WORLD RPG FITNESS P66/P67 regression tests (P65 stage preserved)."""
import importlib.util,sys,types,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/highfly_p66_p67_premium_combat.py'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    p9=types.ModuleType('highfly_p9_private_build_smoke')
    p9.STAGE=Path('/missing/stage')
    p9.ORIGINAL=Path('/missing/original')
    sys.modules['highfly_p9_private_build_smoke']=p9
spec=importlib.util.spec_from_file_location('p66_p67',SCRIPT)
mod=importlib.util.module_from_spec(spec)
sys.modules['p66_p67']=mod
spec.loader.exec_module(mod)

def main_fixture():
    return """  let lastInterpFacing: number | null = null;
    const next = updateFollowCameraYaw({
    // HIGHFLY_P65_MOBILE_COMBAT_HUD_C2
      world.targetEntity(enemy.id);
      world.startAutoAttack();
      return true;
    world.targetEntity(best);
    world.startAutoAttack();
  }

  function clickMovePathTo(
        enabled: settings.get('clickToMove') > 0 || settings.get('attackMove'),
        mi.strafeLeft=false;mi.strafeRight=false;
      }
    }
"""
class P66P67Tests(unittest.TestCase):
    def test_visual_loading_only_native_counters(self):
        c=mod.CSS
        for token in ('#loading-screen .ls-progress',
                      '#loading-screen #ls-status','#loading-screen .ls-bar',
                      '#loading-screen #ls-fill','#loading-screen #ls-tip'):
            self.assertIn(token,c)
        self.assertNotIn('width:50%!important',c)
        self.assertIn('background:linear-gradient',c)
        self.assertNotIn('setInterval',c)

    def test_real_buttons_equal_diameter_and_native_slots(self):
        c=mod.CSS
        for b in ('#mobile-passive','#mobile-jump','#mobile-dodge',
                  'data-mobile-index="0"','#mobile-action-attack'):
            self.assertIn(b,c)
        self.assertIn('width:var(--hf66-control)!important',c)
        self.assertIn('height:var(--hf66-control)!important',c)
        self.assertIn('content:"S1"',c)
        self.assertIn('var(--hf66-gap)',c)

    def test_menu_same_theme_as_ring(self):
        c=mod.CSS
        self.assertIn('#mobile-menu-anchor',c)
        self.assertIn('#mobile-extra-controls',c)
        self.assertIn('#mobile-extra-grid .mobile-btn',c)
        self.assertIn('rgba(185,139,251,.83)',c)

    def test_head_injection_single_no_legacy_p48_anchor(self):
        o=mod.patch_html('<html><head><title>HIGHFLY</title></head><body/></html>')
        self.assertEqual(o.count('/highfly/p66_p67_premium.css'),1)
        self.assertIn(mod.MARK,o)
        with self.assertRaisesRegex(RuntimeError,'P66_P67_ANCHOR_HEAD_0'):
            mod.patch_html('<html><body></body></html>')
        with self.assertRaisesRegex(RuntimeError,'P66_P67_ANCHOR_HEAD_2'):
            mod.patch_html('<head></head></head>')

    def test_facing_does_not_spin_mobile_camera(self):
        r=mod.patch_main(main_fixture())
        self.assertIn("if (document.body.classList.contains('mobile-touch')) {",r)
        self.assertIn('lastInterpFacing = interpFacing;',r)
        self.assertIn('return;\n    }\n    const next = updateFollowCameraYaw',r)

    def test_real_enemy_acquired_no_fake_hits(self):
        r=mod.patch_main(main_fixture())
        self.assertIn('highflyApproachEnemy(enemy.id)',r)
        self.assertIn('highflyApproachEnemy(best)',r)
        self.assertIn('input.setClickMoveTarget(goal,2.6,targetId,clickMovePathTo(goal),false);',r)
        self.assertIn('isAttackableEntity(target,world.playerId,activePvpOpponentIds(world))',r)
        self.assertNotIn('dealDamage(',r)

    def test_manual_joystick_cancels_assist(self):
        r=mod.patch_main(main_fixture())
        self.assertIn('if (current.forward || current.back || current.strafeLeft || current.strafeRight) return;',r)
        self.assertIn('highflyApproachId!==null && input.clickMoveEntityId===highflyApproachId',r)
        self.assertIn('const d=dist2d(world.player.pos,target.pos);',r)
        self.assertIn('if (d<=3.0 || d>15) return;',r)

    def test_real_attack_facing_doesnt_override_motion(self):
        r=mod.patch_main(main_fixture())
        self.assertIn('!mi.forward && !mi.back && !mi.strafeLeft && !mi.strafeRight',r)
        self.assertIn('world.player.autoAttack && world.player.targetId!==null',r)
        self.assertIn('facing=Math.atan2(target.pos.x-playerPos.x,target.pos.z-playerPos.z)',r)

    def test_cannot_repatch_or_build_over_existing_stage(self):
        r=mod.patch_main(main_fixture())
        with self.assertRaisesRegex(RuntimeError,'P66_P67_ANCHOR_FREE_CAMERA_2'):
            mod.patch_main(r)
        self.assertIn("if (STAGE/CSS_PATH).exists()",SCRIPT.read_text())
        self.assertIn('P66_P67_REQUIRES_P65',SCRIPT.read_text())
        self.assertIn('P66_P67_REQUIRES_P64_BOAR',SCRIPT.read_text())

    def test_backups_no_publish_and_private_stage(self):
        s=SCRIPT.read_text()
        for fragment in ('p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)',
                         'shutil.copy2(src,dst)','except BaseException:',
                         'subprocess.run([sys.executable',
                         'BUILD_GREEN_BROWSER_PENDING',
                         'P66_P67_CONCURRENT_CHANGE_'):
            self.assertIn(fragment,s)
        self.assertNotIn('git push',s)
        self.assertNotIn('src/sim/content/zone1.ts',s)
        self.assertNotIn('public/models/creatures/highfly_gobkit_boar_cc0.glb',s)

    def test_fail_closed_on_source_drift(self):
        with self.assertRaisesRegex(RuntimeError,'P66_P67_ANCHOR_TAP_TARGET_CHASE_0'):
            mod.patch_main(main_fixture().replace('world.targetEntity(enemy.id)','targetChanged()'))
        with self.assertRaisesRegex(RuntimeError,'P66_P67_ANCHOR_NATIVE_CHASE_0'):
            mod.patch_main(main_fixture().replace('world.targetEntity(best)','targetChanged()'))

if __name__=='__main__':unittest.main()
