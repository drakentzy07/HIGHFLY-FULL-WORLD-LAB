#!/usr/bin/env python3
"""P63: real 1-2-3-4 native combat and market height, with boar provenance audit.
P62 PRIVATE stage only; backups and Vite rollback. No quest/AI/loot edits.
"""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
S=p9.STAGE;O=p9.ORIGINAL
OUT=ROOT/'.workspace/reports/highfly-p63-combat-c1'
TOWN='src/render/eastbrook_town.ts'
RING='src/ui/hud/action_bar/mobile_action_ring_controller.ts'
AUTO='src/sim/combat/auto_attack.ts'
VISUAL='src/render/characters/visual.ts'
CORE='src/sim/combat/highfly_melee_combo.ts'
MARK='HIGHFLY_P63_COMBAT_C1'
CORE_TS="""// HIGHFLY_P63_COMBAT_C1: real landed melee hits, no fake animation damage.
export type HfStep=0|1|2|3|4;
export interface HfHit {step:HfStep; lastTick:number; targetId:number; finisher:boolean}
export const HF_RESET_TICKS=90;
export const HF_FOURTH_DAMAGE_MULT=1.28;
export function nextHighflyHit(prev:HfHit|undefined,tick:number,targetId:number):HfHit {
  const chained=!!prev&&prev.step>0&&prev.targetId===targetId&&
    tick>=prev.lastTick&&tick-prev.lastTick<=HF_RESET_TICKS;
  const step=(chained?prev!.step%4+1:1) as HfStep;
  return {step,targetId,lastTick:tick,finisher:step===4};
}
""".strip()+'\n'
def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError('P63_ANCHOR_'+label+'_'+str(n))
    return s.replace(a,b,1)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def transform(d):
    town=once(d[TOWN],'        stall.width,\n        stall.height,\n        stall.depth,',
"""        stall.width,
        // HIGHFLY_P63_COMBAT_C1: raise stand/canopy clearance to 3.2.
        // Preserve exact horizontal footprint and all physics colliders.
        Math.max(stall.height, 3.2),
        stall.depth,""",'MARKET')
    ring=once(d[RING],
"""    handleMobileAttackTap(deps.attackTapState(), {
      activateAttack: () => deps.activateFixedAttackSlot(),
      attackNearest: deps.attackNearest,
    });
    attackBtn.blur();""",
"""    // HIGHFLY_P63_COMBAT_C1: no accidental disengage on rapid ATK tap.
    const hfTap=deps.attackTapState();
    if(!(hfTap.autoAttack&&hfTap.hasLiveHostileTarget)){
      handleMobileAttackTap(hfTap,{
        activateAttack:()=>deps.activateFixedAttackSlot(),
        attackNearest:deps.attackNearest,
      });
    }
    attackBtn.blur();""",'TOUCH_ATK')
    auto=once(d[AUTO],"import { meleeReachActor } from './feral_reach';",
"""import { meleeReachActor } from './feral_reach';
import { nextHighflyHit, HF_FOURTH_DAMAGE_MULT, type HfHit } from './highfly_melee_combo';""",'IMPORT')
    auto=once(auto,'export function startAutoAttack(ctx: SimContext, pid?: number): void {',
"""// HIGHFLY_P63_COMBAT_C1: per actor and non-persistent.
const highflyCombo=new WeakMap<Entity,HfHit>();
export function startAutoAttack(ctx: SimContext, pid?: number): void {""",'STATE')
    auto=once(auto,'    let weaponMult = 1;\n    if (p.queuedOnSwing) {',
"""    let weaponMult = 1;
    const hfHit=!p.queuedOnSwing
      ?nextHighflyHit(highflyCombo.get(p),ctx.tickCount,t.id):null;
    if (p.queuedOnSwing) {""",'NEXT')
    auto=once(auto,
"""      weaponMult,
      whiteDualWieldPenalty: dualWieldWhiteMissPenalty && abilityName === null,
      autoAttack: true,""",
"""      weaponMult: weaponMult*(abilityName===null&&hfHit?.finisher?HF_FOURTH_DAMAGE_MULT:1),
      whiteDualWieldPenalty: dualWieldWhiteMissPenalty && abilityName === null,
      autoAttack: true,""",'FINISHER')
    auto=once(auto,'    if (connected && abilityId) creditAbilityDrill(ctx, p, t, abilityId);',
"""    if(connected&&abilityName===null&&hfHit)highflyCombo.set(p,hfHit);
    if (connected && abilityId) creditAbilityDrill(ctx, p, t, abilityId);""",'CONNECTED')
    visual=once(d[VISUAL],
"""    const name = clips[this.attackIdx++ % clips.length];
    this.playOneShot(name, skinAttack?.timeScale ?? this.def.attackTimeScale ?? 1.3);
    this.currentOneShotIsAttack = true;""",
"""    // HIGHFLY_P63_COMBAT_C1: four genuine animation accents. The sim
    // alone decides whether and when a melee hit deals real damage.
    const hfStep=this.attackIdx++%4;
    const name=clips[hfStep%clips.length];
    const speed=[1,1.09,1.13,.94][hfStep];
    this.playOneShot(name,(skinAttack?.timeScale??this.def.attackTimeScale??1.3)*speed);
    this.currentOneShotIsAttack = true;""",'ANIMATION')
    return {TOWN:town,RING:ring,AUTO:auto,VISUAL:visual,CORE:CORE_TS}
def boars():
    zone=(S/'src/sim/content/zone1.ts').read_text('utf8')
    camps=[
      ("{ mobId: 'wild_boar', center: { x: 58, z: -72 }, radius: 26, count: 5 }",5),
      ("{ mobId: 'wild_boar', center: { x: 97, z: -43 }, radius: 23.5, count: 4 }",4)]
    if any(line not in zone for line,_ in camps):
        raise RuntimeError('P63_ORIGINAL_BOAR_SPAWNS_DRIFT')
    manifest=(S/'src/render/characters/manifest.ts').read_text('utf8')
    return {'campCount':2,'mobPopulation':sum(n for _,n in camps),
      'originalWildBoarStageExists':(S/'public/models/creatures/wild_boar.glb').is_file(),
      'quaterniusBullStageExists':(S/'public/models/creatures/bull.glb').is_file(),
      'originalBoarModelReferenced':'wild_boar.glb' in manifest,
      'customWildBoarLicense':'NOT_VERIFIED_DO_NOT_REDISTRIBUTE',
      'nextStep':'CC0 ANIMATED PIG/WARTHOG SOURCE OR LICENSED CC0 BULL PROXY'}
def run(apply=False):
    p9.preflight(O,S,p9.REPORT)
    data={}
    for rel in (TOWN,RING,AUTO,VISUAL):
        path=S/rel
        if not path.is_file() or path.is_symlink():raise RuntimeError('P63_STAGE_FILE_MISSING '+rel)
        data[rel]=path.read_text('utf8')
        if MARK in data[rel]:raise RuntimeError('P63_ALREADY_APPLIED')
    if (S/CORE).exists():raise RuntimeError('P63_CORE_ALREADY_EXISTS')
    if 'HIGHFLY_P62_ROLE_PRESERVING_FALLBACK' not in (S/'src/render/characters/index.ts').read_text('utf8'):
        raise RuntimeError('P63_REQUIRES_P62')
    if 'HIGHFLY_P58_SELECTABLE_MICRO_PROPS' not in data[TOWN] or 'HIGHFLY_P48_FURY_MOBILE' not in data[VISUAL]:
        raise RuntimeError('P63_REQUIRES_P58_AND_P48')
    audit=boars();changes=transform(data)
    report={'phase':'P63_COMBAT_C1','mode':'DRY_RUN',
      'market':'two official stands visual height 3.2, physics footprint unchanged',
      'attack':'real connected mainhand hits 1-2-3-4, fourth hit 1.28x',
      'touch':'repeated ATK taps never stop an already engaged attack',
      'movement':'P48 double jump and dash intact',
      'boarAudit':audit,'boarModelsChanged':False,
      'spawnAndLootChanged':False,'questsChanged':False,
      'fullActionCombatDone':False,'browserVerified':False}
    if not apply:
        print('[HIGHFLY P63] '+json.dumps(report,ensure_ascii=False,indent=2));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():raise RuntimeError('P63_UNSAFE_BACKUP_FOLDER')
        if (OUT/'P63_STATUS.json').exists():raise RuntimeError('P63_ALREADY_BUILT')
        prev=OUT.parent/'highfly-p63-attempts';prev.mkdir(parents=True,exist_ok=True)
        OUT.rename(prev/('attempt-'+str(time.time_ns())))
    backups=[];created=[]
    try:
        for rel in data:
            src=S/rel;backup=OUT/'backups'/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,backup)
            if sha(src)!=sha(backup):raise RuntimeError('P63_BAD_BACKUP')
            backups.append((src,backup))
        for rel,content in changes.items():
            dest=S/rel
            if rel in data:
                if dest.read_text('utf8')!=data[rel]:raise RuntimeError('P63_CONCURRENT_STAGE_CHANGE')
                dest.write_text(content,encoding='utf8')
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('x',encoding='utf8') as f:f.write(content)
                created.append(dest)
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        for src,backup in backups:
            if backup.is_file():shutil.copy2(backup,src)
        for dest in created:
            if dest.is_file():dest.unlink()
        print('[HIGHFLY P63] RED — rollback to P62',file=sys.stderr)
        raise
    report['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P63_STATUS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('[HIGHFLY P63] '+json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true')
    run(ap.parse_args().apply)
