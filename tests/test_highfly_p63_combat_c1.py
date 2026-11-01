"""P63 first playable core contracts, all fixtures synthetic; never touches stage."""
from __future__ import annotations
import importlib.util,sys,types,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/highfly_p63_combat_c1.py'
if 'highfly_p9_private_build_smoke' not in sys.modules:
    stub=types.ModuleType('highfly_p9_private_build_smoke')
    stub.STAGE=Path('/missing/stage')
    stub.ORIGINAL=Path('/missing/original')
    sys.modules['highfly_p9_private_build_smoke']=stub
spec=importlib.util.spec_from_file_location('p63',SCRIPT)
p63=importlib.util.module_from_spec(spec)
sys.modules['p63']=p63
spec.loader.exec_module(p63)

class P63Tests(unittest.TestCase):
    def fixture(self):
        return {
          p63.TOWN:"""
for (const stall of EASTBROOK_LAYOUT.market.stalls){
      placementMatrix(template,stall.position.x,
        stall.width,
        stall.height,
        stall.depth,
      );
}
""",
          p63.RING:"""
    handleMobileAttackTap(deps.attackTapState(), {
      activateAttack: () => deps.activateFixedAttackSlot(),
      attackNearest: deps.attackNearest,
    });
    attackBtn.blur();
""",
          p63.AUTO:"""
import { meleeReachActor } from './feral_reach';
export function startAutoAttack(ctx: SimContext, pid?: number): void {}
    let weaponMult = 1;
    if (p.queuedOnSwing) {
}
      weaponMult,
      whiteDualWieldPenalty: dualWieldWhiteMissPenalty && abilityName === null,
      autoAttack: true,
    if (connected && abilityId) creditAbilityDrill(ctx, p, t, abilityId);
""",
          p63.VISUAL:"""
    const name = clips[this.attackIdx++ % clips.length];
    this.playOneShot(name, skinAttack?.timeScale ?? this.def.attackTimeScale ?? 1.3);
    this.currentOneShotIsAttack = true;
""",
        }
    def test_real_melee_and_fourth_hit(self):
        out=p63.transform(self.fixture())
        a=out[p63.AUTO]
        self.assertIn('nextHighflyHit(highflyCombo.get(p),ctx.tickCount,t.id)',a)
        self.assertIn('HF_FOURTH_DAMAGE_MULT',a)
        self.assertIn('if(connected&&abilityName===null&&hfHit)',a)
        self.assertIn('WeakMap<Entity,HfHit>',a)
        self.assertIn('HF_RESET_TICKS=90',out[p63.CORE])
        self.assertIn('HF_FOURTH_DAMAGE_MULT=1.28',out[p63.CORE])
        self.assertIn('step===4',out[p63.CORE])

    def test_native_attack_does_not_toggle_off(self):
        out=p63.transform(self.fixture())
        self.assertIn('if(!(hfTap.autoAttack&&hfTap.hasLiveHostileTarget))',out[p63.RING])
        self.assertIn('attackNearest:deps.attackNearest',out[p63.RING])
        self.assertNotIn('nextHighflyHit',out[p63.RING])

    def test_market_footprint_unchanged(self):
        town=p63.transform(self.fixture())[p63.TOWN]
        self.assertIn('stall.width,',town)
        self.assertIn('stall.depth,',town)
        self.assertIn('Math.max(stall.height, 3.2)',town)
        self.assertNotIn('stall.width *',town)

    def test_visual_plays_existing_authored_clips(self):
        src=p63.transform(self.fixture())[p63.VISUAL]
        self.assertIn('clips[hfStep%clips.length]',src)
        self.assertIn('this.playOneShot(name',src)
        self.assertNotIn('dealDamage',src)

    def test_guard_fails_on_anchor_drift(self):
        with self.assertRaisesRegex(RuntimeError,'P63_ANCHOR_MARKET_0'):
            p63.transform({**self.fixture(),p63.TOWN:'changed'})
        with self.assertRaisesRegex(RuntimeError,'P63_ANCHOR_TOUCH_ATK_0'):
            p63.transform({**self.fixture(),p63.RING:'changed'})

    def test_original_boar_identity_not_modified(self):
        self.assertNotIn('src/sim/content/zone1.ts',p63.transform(self.fixture()))
        self.assertNotIn(p63.CORE,self.fixture())
        self.assertIn('UNMODIFIED' if False else 'NOT_VERIFIED',SCRIPT.read_text())
        self.assertNotIn('shutil.copy2(O/',SCRIPT.read_text())

if __name__=='__main__':unittest.main()
