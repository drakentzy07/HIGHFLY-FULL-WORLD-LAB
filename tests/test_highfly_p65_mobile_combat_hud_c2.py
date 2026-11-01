"""P65 integration contract tests: real inputs and menu, no fake gameplay.
Tests use synthetic source fixtures; private P64 stage gets exact-anchor verification
before applying, then a real P9 Vite build with rollback on failure.
"""
import importlib.util,sys,types,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/highfly_p65_mobile_combat_hud_c2.py'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.ORIGINAL=Path('/missing/original')
    stub.STAGE=Path('/missing/stage')
    sys.modules['highfly_p9_private_build_smoke']=stub
spec=importlib.util.spec_from_file_location('p65',SCRIPT)
p65=importlib.util.module_from_spec(spec);sys.modules['p65']=p65
spec.loader.exec_module(p65)

class P65Tests(unittest.TestCase):
    def html(self):
        return (
         "<head>\n<link rel=\"stylesheet\" href=\"/highfly/p48.css\" />\n</head>\n"
         '<button type="button" id="mobile-jump" data-i18n-title="jump">Saltar</button>\n'
         '<span id="mobile-more-title" data-i18n="hud.core.mobileMore">More</span>\n'
        )
    def mobile(self):
        return ('''import { buildMobileMenuControl, type MobileMenuControl } from '../ui/hud/menu';
interface MobileControlCallbacks {
  onCycleTarget(): void;
}
function onSwipeLookEnd(){
    if (quickTap && isRecenterDoubleTap(this.lastSwipeTapAt, now, this.swipeLookActive)) {
    }
}
    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });
    this.menuControl = buildMobileMenuControl();
    if (target.closest('#mobile-extra-controls') || target.closest('#mobile-more')){}
''')
    def main(self):
        return ('''    onCycleTarget: () => world.tabTarget(),
    let facing: number | null = mouselook ? input.camYaw : null;
''')
    def test_html_reuses_real_native_slots(self):
        h=p65.patch_html(self.html())
        self.assertIn('id="mobile-passive"',h)
        self.assertIn('id="mobile-jump"',h)
        self.assertIn('/highfly/p65.css',h)
        self.assertIn('HIGHFLY · MENÚ',h)
        self.assertEqual(h.count('id="mobile-jump"'),1)
        self.assertEqual(h.count('id="mobile-passive"'),1)

    def test_stylesheet_uses_head_not_legacy_p48_link(self):
        # Reproduces P65_ANCHOR_STYLESHEET_COUNT_0 from the REAL P64
        # assembled stage. P48 marker may survive while its link changes.
        html=self.html().replace(
            '<link rel="stylesheet" href="/highfly/p48.css" />',
            '<link href="/highfly/p48.css?v=1" rel="stylesheet">'
        )
        html=html.replace(
            '<span id="mobile-more-title" data-i18n="hud.core.mobileMore">More</span>',
            '<span id="mobile-more-title" class="panel-text">Acciones</span>'
        )
        out=p65.patch_html(html)
        self.assertEqual(out.count('/highfly/p65.css'),1)
        self.assertEqual(out.count('id="mobile-more-title"'),1)
        self.assertIn('HIGHFLY · MENÚ',out)
        self.assertEqual(out.count('</head>'),1)

    def test_rejects_missing_or_duplicate_html_head(self):
        with self.assertRaisesRegex(RuntimeError,'P65_ANCHOR_HEAD_STYLESHEET_COUNT_0'):
            p65.patch_html(self.html().replace('</head>','</no-head>'))
        with self.assertRaisesRegex(RuntimeError,'P65_ANCHOR_HEAD_STYLESHEET_COUNT_2'):
            p65.patch_html(self.html().replace('</head>','</head></head>'))

    def test_menu_routes_to_actual_bound_modal(self):
        m=p65.patch_mobile(self.mobile())
        self.assertIn("this.bindButton('mobile-passive', () => this.callbacks.onSpellbook());",m)
        self.assertIn("this.bindButton('mobile-menu-anchor'",m)
        self.assertIn("document.body.classList.add('mobile-more-open');",m)
        self.assertIn("this.menuControl = null;",m)
        self.assertIn("import type { MobileMenuControl }",m)
        self.assertNotIn("buildMobileMenuControl, type",m)
        self.assertIn("target.closest('#mobile-menu-anchor')",m)

    def test_world_tap_uses_real_entity_and_sim(self):
        m=p65.patch_mobile(self.mobile())
        a=p65.patch_main(self.main())
        self.assertIn('onWorldTap?: (x:number,y:number) => boolean',m)
        self.assertIn("this.callbacks.onWorldTap?.(e.clientX,e.clientY)===true",m)
        self.assertIn('renderer.pick(x,y)',a)
        self.assertIn('isAttackableEntity(enemy,world.playerId,activePvpOpponentIds(world))',a)
        self.assertIn('world.targetEntity(enemy.id);',a)
        self.assertIn('world.startAutoAttack();',a)
        self.assertNotIn('dealDamage(',a)

    def test_movement_has_camera_relative_forward_and_back_turn(self):
        a=p65.patch_main(self.main())
        self.assertIn("document.body.classList.contains('mobile-touch')",a)
        self.assertIn("const vertical=Number(mi.forward)-Number(mi.back);",a)
        self.assertIn('const yaw=input.camYaw;',a)
        self.assertIn('facing=Math.atan2(worldX,worldZ);',a)
        self.assertIn('mi.forward=true;mi.back=false;',a)
        self.assertIn('mi.strafeLeft=false;mi.strafeRight=false;',a)
        self.assertIn('!input.clickMoveTarget',a)

    def test_passive_does_not_fake_active_cast(self):
        self.assertIn('PASIVA is a true spellbook entry',p65.patch_mobile(self.mobile()))
        self.assertNotIn('castAbility(',p65.patch_mobile(self.mobile()))
        self.assertIn("data-mobile-index",p65.CSS)  # S1 is native action slot
        self.assertIn('id="mobile-passive"',p65.patch_html(self.html()))

    def test_hud_safe_fullscreen_and_left_header(self):
        css=p65.CSS
        self.assertIn('100dvh',css)
        self.assertIn('#loading-screen',css)
        self.assertIn('#player-frame:not(.pf-detached)',css)
        self.assertIn('#mobile-menu-anchor::after',css)
        self.assertIn('mobile-extra-grid',css)
        self.assertIn('#mobile-dodge',css)
        self.assertIn('env(safe-area-inset-left)',css)

    def test_anchor_drift_stops_before_editing(self):
        with self.assertRaisesRegex(RuntimeError,'P65_ANCHOR_MENU_TITLE_COUNT_0'):
            p65.patch_html(self.html().replace('mobile-more-title','changed'))
        with self.assertRaisesRegex(RuntimeError,'P65_ANCHOR_WORLD_TAP_COMBAT_COUNT_0'):
            p65.patch_mobile(self.mobile().replace('isRecenterDoubleTap','differentFn'))
        with self.assertRaisesRegex(RuntimeError,'P65_ANCHOR_REAL_TAP_ON_MONSTER_COUNT_0'):
            p65.patch_main(self.main().replace('world.tabTarget','customTarget'))

    def test_isolated_stage_and_backups_contract(self):
        code=SCRIPT.read_text('utf8')
        self.assertIn('p9.preflight(O,S,p9.REPORT)',code)
        self.assertIn('P65_REQUIRES_REAL_BOAR_CCO',code)
        self.assertIn('subprocess.run([sys.executable,str(ROOT/',code)
        self.assertIn('except BaseException:',code)
        self.assertIn("status['mode']='BUILD_GREEN_BROWSER_PENDING'",code)
        self.assertNotIn('git push',code)
        self.assertNotIn('src/sim/content/zone1.ts',code)
        self.assertNotIn('public/models/creatures/highfly_gobkit_boar_cc0.glb',code)

if __name__=='__main__':unittest.main()
