#!/usr/bin/env python3
"""P69 HIGHFLY FURY CORE: native manual 4-tap (offline), position-skill
hold-drag-release (native target & cooldown), corrected 360 heading, dash
from existing movement vector. Single guarded private stage transaction.
No fabricated damage, extra assets, class changes or public deployment.
"""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
ORIGINAL=p9.ORIGINAL
OUT=ROOT/".workspace/reports/highfly-p69-fury-core"
MARK="HIGHFLY_P69_FURY_CORE"
MAIN="src/main.ts"
HUD="src/ui/hud.ts"
RING="src/ui/hud/action_bar/mobile_action_ring_controller.ts"
SIM="src/sim/sim.ts"
AUTO="src/sim/combat/auto_attack.ts"
TOUCH="src/game/highfly_fury_skill_touch.ts"
TAPS="src/sim/combat/highfly_manual_taps.ts"
CSS="public/highfly/p69_fury_core.css"
EXISTING=(MAIN,HUD,RING,SIM,AUTO)

TOUCH_CODE=r"""// HIGHFLY_P69_FURY_CORE: mobile-skill gesture on a REAL position ability.
// Drag does not rotate the camera; the sim owns actual cooldowns, cost and hit.
// Other spell types retain their native slot behavior and normal empowered hold.
export interface HighflyFuryPositionSkill { slot:number; abilityId:string; range:number }
export interface HighflyFuryAimPoint { x:number;z:number }
export interface HighflyFurySkillHooks {
  skill: (buttonIndex:number)=>HighflyFuryPositionSkill|null;
  begin: (slot:number)=>boolean;
  player: ()=>HighflyFuryAimPoint;
  cameraYaw: ()=>number;
  update: (point:HighflyFuryAimPoint)=>void;
  commit: (point:HighflyFuryAimPoint)=>boolean;
  cancel: ()=>void;
}
const cap=(v:number,lo:number,hi:number)=>Math.max(lo,Math.min(hi,v));
export function highflyFuryAimPoint(
  player:HighflyFuryAimPoint,yaw:number,dx:number,dy:number,range:number,
):HighflyFuryAimPoint {
  // LEFT in the world is camera-relative +90°; screen right is yaw -90°.
  const drag=Math.hypot(dx,dy);
  const angle=yaw+(drag<12?0:Math.atan2(-dx,-dy));
  const reach=Math.max(0,range)* (drag<12?.72:cap(.33+.67*drag/128,.33,1));
  return {x:player.x+Math.sin(angle)*reach,z:player.z+Math.cos(angle)*reach};
}
export function installHighflyFuryPositionAim(hooks:HighflyFurySkillHooks):()=>void {
  const buttons=[...document.querySelectorAll<HTMLButtonElement>(
    '#mobile-action-ring .mobile-action-slot[data-mobile-index]'
  )];
  interface ActiveAim {pointer:number;index:number;startX:number;startY:number;
    skill:HighflyFuryPositionSkill;btn:HTMLButtonElement}
  const holder:{value:ActiveAim|null}={value:null};
  const cancel=document.createElement('div');
  cancel.id='highfly-fury-aim-cancel';
  cancel.textContent='✕  CANCELAR';
  cancel.setAttribute('aria-hidden','true');
  document.body.appendChild(cancel);
  function drop(withNativeCancel:boolean):void {
    const a=holder.value;
    if(a) {
      try { if(a.btn.hasPointerCapture(a.pointer))
        a.btn.releasePointerCapture(a.pointer); } catch {}
    }
    holder.value=null;
    cancel.classList.remove('active');
    if(withNativeCancel) hooks.cancel();
  }
  function point(a:NonNullable<typeof holder.value>,x:number,y:number):HighflyFuryAimPoint {
    return highflyFuryAimPoint(hooks.player(),hooks.cameraYaw(),
      x-a.startX,y-a.startY,a.skill.range);
  }
  function isCancel(x:number,y:number):boolean {
    const rect=cancel.getBoundingClientRect();
    return x>=rect.left-10 && x<=rect.right+10 &&
      y>=rect.top-10 && y<=rect.bottom+10;
  }
  function down(e:PointerEvent,index:number,btn:HTMLButtonElement):void {
    if(!document.body.classList.contains('mobile-touch') ||
       document.body.classList.contains('mobile-window-open'))return;
    const spec=hooks.skill(index);
    if(!spec) return;
    e.preventDefault();e.stopImmediatePropagation();
    if(holder.value) return;
    if(!hooks.begin(spec.slot))return;
    holder.value={pointer:e.pointerId,index,startX:e.clientX,startY:e.clientY,skill:spec,btn};
    cancel.classList.add('active');
    try {btn.setPointerCapture(e.pointerId);}catch {}
    hooks.update(point(holder.value,e.clientX,e.clientY));
  }
  function move(e:PointerEvent):void {
    const a=holder.value;
    if(!a || a.pointer!==e.pointerId)return;
    e.preventDefault();e.stopImmediatePropagation();
    if(document.body.classList.contains('mobile-window-open')) { drop(true);return; }
    cancel.classList.toggle('hover',isCancel(e.clientX,e.clientY));
    if(!isCancel(e.clientX,e.clientY))hooks.update(point(a,e.clientX,e.clientY));
  }
  function up(e:PointerEvent):void {
    const a=holder.value;
    if(!a || a.pointer!==e.pointerId)return;
    e.preventDefault();e.stopImmediatePropagation();
    if(isCancel(e.clientX,e.clientY)) {drop(true);return;}
    const target=point(a,e.clientX,e.clientY);
    hooks.update(target);
    hooks.commit(target);
    drop(false);
  }
  function interrupted(e:PointerEvent):void {
    if(holder.value?.pointer===e.pointerId) {
      e.preventDefault();e.stopImmediatePropagation();drop(true);
    }
  }
  const listeners: Array<{el:HTMLButtonElement;down:(e:PointerEvent)=>void}>=[];
  buttons.forEach((btn)=>{
    const index=Number(btn.dataset.mobileIndex);
    if(!Number.isInteger(index)||index<0||index>3)return;
    const onDown=(e:PointerEvent)=>down(e,index,btn);
    btn.addEventListener('pointerdown',onDown,true);
    btn.addEventListener('pointermove',move,true);
    btn.addEventListener('pointerup',up,true);
    btn.addEventListener('pointercancel',interrupted,true);
    listeners.push({el:btn,down:onDown});
  });
  const blur=()=>drop(true);
  window.addEventListener('blur',blur);
  return ()=>{
    drop(true);
    window.removeEventListener('blur',blur);
    for(const a of listeners) {
      a.el.removeEventListener('pointerdown',a.down,true);
      a.el.removeEventListener('pointermove',move,true);
      a.el.removeEventListener('pointerup',up,true);
      a.el.removeEventListener('pointercancel',interrupted,true);
    }
    cancel.remove();
  };
}
"""
TAPS_CODE=r"""// HIGHFLY_P69_FURY_CORE: offline-only manual tap intent.
// No damage here. Attack remains authoritative in auto_attack.ts's native
// meleeSwing through the real hostility/range/LoS/status gates.
import type { Entity } from '../types';
interface ManualTapState {
  queuedUntil:number; nextAllowed:number; targetId:number|null;
  pending:boolean; enabled:boolean;
}
const states=new WeakMap<Entity,ManualTapState>();
export const HIGHFLY_TAP_MIN_TICKS=5; // 250ms at 20Hz
export const HIGHFLY_TAP_QUEUE_TICKS=32; // bounded approach buffer: 1.6sec
export function queueHighflyTap(player:Entity,tick:number):void {
  const existing=states.get(player);
  if(existing) {
    existing.enabled=true;
    existing.pending=true; // one queue slot, anti-spam
    existing.targetId=player.targetId;
    existing.queuedUntil=tick+HIGHFLY_TAP_QUEUE_TICKS;
    return;
  }
  states.set(player,{queuedUntil:tick+HIGHFLY_TAP_QUEUE_TICKS,
    nextAllowed:0,targetId:player.targetId,pending:true,enabled:true});
}
export function highflyManualState(player:Entity):ManualTapState|null {
  return states.get(player)??null;
}
export function expireHighflyTap(player:Entity):void {
  const s=states.get(player);if(s)s.pending=false;
}
export function claimHighflyTap(player:Entity,tick:number):boolean {
  const s=states.get(player);
  if(!s?.enabled||!s.pending)return false;
  if(tick>s.queuedUntil||player.targetId!==s.targetId) {
    s.pending=false;return false;
  }
  if(tick<s.nextAllowed)return false;
  s.pending=false;
  s.nextAllowed=tick+HIGHFLY_TAP_MIN_TICKS;
  return true;
}
"""

CSS_CODE=r"""/* HIGHFLY_P69_FURY_CORE: visual signal for a real native ground reticle.
   In S23 landscape, skill finger and joystick remain separate.
   No fake cooldowns, projectiles or damage. */
#highfly-fury-aim-cancel{
  position:fixed;top:max(16px,env(safe-area-inset-top));right:max(20px,env(safe-area-inset-right));
  z-index:2147482001;display:none;align-items:center;justify-content:center;
  width:clamp(90px,12vw,145px);height:48px;
  pointer-events:none;touch-action:none;user-select:none;
  border:2px solid rgba(230,118,174,.95);border-radius:13px;
  background:linear-gradient(145deg,rgba(75,23,64,.95),rgba(22,11,40,.96));
  color:#ffdfed;font:800 12px/1 system-ui;
  box-shadow:0 0 20px #9a3d7d66,0 3px 15px #000a;
}
#highfly-fury-aim-cancel.active{display:flex}
#highfly-fury-aim-cancel.hover{
  border-color:#fff;background:#b72865;box-shadow:0 0 26px #e957afaa
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot{
  touch-action:none!important;
}
"""

def once(text,old,new,tag):
    n=text.count(old)
    if n!=1:raise RuntimeError("P69_ANCHOR_"+tag+"_COUNT_"+str(n))
    return text.replace(old,new,1)

def patch_main(s):
    s=once(s,
      "import { AutoLoot } from './game/autoloot';",
      "import { AutoLoot } from './game/autoloot';\n"
      "import { installHighflyFuryPositionAim } from './game/highfly_fury_skill_touch';",
      "AIM_IMPORT")
    s=once(s,
      '  hud.onMobileAttackNearest = () => attackNearest();',
      """  // HIGHFLY_P69_FURY_CORE: 1 ATK tap means 1 authorized physical attempt.
  hud.onHighflyBasicTap = () => highflyBasicTap();
  hud.onMobileAttackNearest = () => attackNearest();""",
      "MANUAL_ATK_HUD")
    s=once(s,
      '      world.targetEntity(enemy.id);\n      world.startAutoAttack();\n'
      '      highflyApproachEnemy(enemy.id);\n      return true;',
      """      highflyBasicTap(enemy.id);
      return true;""",
      "WORLD_TAP_MANUAL")
    s=once(s,
      '  mobileControls.start();',
      """  mobileControls.start();
  // HIGHFLY_P69_FURY_CORE: one skill thumb owns press/drag/release on
  // real position spells, other spells keep original radial/empower UX.
  installHighflyFuryPositionAim({
    skill: i=>hud.highflyGroundSkillAtButton(i),
    begin: slot=>{hud.castSlot(slot);return hud.isGroundAimActive();},
    player: ()=>({x:world.player.pos.x,z:world.player.pos.z}),
    cameraYaw:()=>input.camYaw,
    update:p=>hud.updateGroundAimPoint(p),
    commit:p=>hud.commitGroundAimAt(p),
    cancel:()=>{hud.cancelGroundAim();}
  });""",
      "MOBILE_FURY_SKILL_BIND")
    # Fix P68 inverted right/left and diagonals (verified against actual
    # stepPlayerMotion convention: screen right = (-cos(facing), sin(facing))).
    s=once(s,
      "const worldX=vertical*Math.sin(yaw)+horizontal*Math.cos(yaw);\n"
      "        const worldZ=vertical*Math.cos(yaw)-horizontal*Math.sin(yaw);",
      "const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);\n"
      "        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);",
      "NATIVE_360_SIGN")
    s=once(s,'  function attackNearest(): void {',
      """  // HIGHFLY_P69_FURY_CORE: no cast bar or repeating MMO attacks.
  // Select existing valid enemy or soft-pick 360° within 15m. The native
  // collision-aware P67 approach is used only when stationary.
  function highflyBasicTap(explicitId:number|null=null):void {
    const p=world.player;
    let picked=explicitId!==null?world.entities.get(explicitId):null;
    if(!picked || picked.dead ||
       !isAttackableEntity(picked,world.playerId,activePvpOpponentIds(world)) ||
       dist2d(p.pos,picked.pos)>15) {
      const selected=p.targetId!==null?world.entities.get(p.targetId):null;
      picked=selected && !selected.dead &&
        isAttackableEntity(selected,world.playerId,activePvpOpponentIds(world)) &&
        dist2d(p.pos,selected.pos)<=15?selected:null;
    }
    if(!picked) {
      let best=15;
      for(const enemy of world.entities.values()) {
        if(!isAttackableEntity(enemy,world.playerId,activePvpOpponentIds(world)))continue;
        const d=dist2d(p.pos,enemy.pos);
        if(d<best){picked=enemy;best=d;}
      }
    }
    if(!picked){hud.showError(t('errors.noEnemyNearby'));return;}
    world.targetEntity(picked.id);
    if(offlineSim) offlineSim.highflyTapBasicAttack();
    else world.startAutoAttack(); // online must use server-authorized protocol
    highflyApproachEnemy(picked.id);
  }

  function attackNearest(): void {""",
      "MANUAL_ATK_FUNCTION")
    return s

def patch_hud(s):
    s=once(s,
      '  onMobileAttackNearest: (() => void) | null = null;',
      """  onMobileAttackNearest: (() => void) | null = null;
  // HIGHFLY_P69_FURY_CORE: offline mobile manual hit, not a recast.
  onHighflyBasicTap: (() => void) | null = null;""",
      "HUD_PROPERTY")
    s=once(s,
      '  private mobileSourceSlotForButton(',
      """  // Native only: area skill source slot, real range and cooldown.
  highflyGroundSkillAtButton(index:number):
    {slot:number;abilityId:string;range:number}|null {
    if(!Number.isInteger(index)||index<0||index>=4)return null;
    const slot=this.mobileSourceSlotForButton(index,'center');
    const a=this.abilityForSlot(slot);
    if(!a || a.def.targetMode!=='position' || a.def.selfCentered ||
       !!a.def.empowerStages)return null;
    return {slot,abilityId:a.def.id,range:Math.max(1,a.def.range)};
  }

  private mobileSourceSlotForButton(""",
      "HUD_SKILL_LOOKUP")
    s=once(s,
      '      attackNearest: this.onMobileAttackNearest,',
      '      attackNearest: this.onMobileAttackNearest,\n'
      '      onHighflyBasicTap: this.onHighflyBasicTap,',
      "HUD_RING_BIND")
    return s

def patch_ring(s):
    s=once(s,
      '  attackNearest: (() => void) | null;',
      '  attackNearest: (() => void) | null;\n'
      '  onHighflyBasicTap?: (() => void) | null;',
      "RING_CONTRACT")
    s=once(s,
      '    const hfTap=deps.attackTapState();',
      """    // HIGHFLY_P69_FURY_CORE: offline manual-tap combat bypasses the
    // old autoattack toggle. One gesture = one native Sim attempt.
    if(deps.onHighflyBasicTap) {
      deps.onHighflyBasicTap();
      attackBtn.blur();
      return;
    }
    const hfTap=deps.attackTapState();""",
      "RING_MANUAL_ATK")
    return s

def patch_sim(s):
    s=once(s,
      "} from './combat/auto_attack';",
      "} from './combat/auto_attack';\n"
      "import { queueHighflyTap } from './combat/highfly_manual_taps';",
      "SIM_IMPORT")
    s=once(s,
      '  startAutoAttack(pid?: number): void {',
      """  // HIGHFLY_P69_FURY_CORE: one touch-down requests one physical hit.
  // Only the browser's local Sim invokes this; server gameplay unchanged.
  highflyTapBasicAttack():void {
    if(this.player.dead)return;
    queueHighflyTap(this.player,this.tickCount);
  }

  startAutoAttack(pid?: number): void {""",
      "SIM_REQUEST")
    return s

def patch_auto(s):
    s=once(s,
      "import { meleeReachActor } from './feral_reach';",
      """import { meleeReachActor } from './feral_reach';
import { claimHighflyTap, expireHighflyTap, highflyManualState } from './highfly_manual_taps';""",
      "AUTO_IMPORT")
    s=once(s,
      """export function updatePlayerAutoAttack(ctx: SimContext, p: Entity, meta: PlayerMeta): void {
  p.swingTimer = Math.max(0, p.swingTimer - DT);""",
      """export function updatePlayerAutoAttack(ctx: SimContext, p: Entity, meta: PlayerMeta): void {
  // HIGHFLY_P69_FURY_CORE: manual touch attacks are separate from the
  // automatic cast/swing driver. No GCD, cast or channel on ATK basic.
  // The real native tryPlayerSwing validates hostility, LoS, range,
  // stun, disarm, defense and equipment before applying damage.
  const hf=highflyManualState(p);
  if(hf?.enabled) {
    p.autoAttack=false;
    if(!hf.pending)return;
    const t=p.targetId!==null?ctx.entities.get(p.targetId):null;
    if(!t || t.dead || !ctx.isHostileTo(p,t)) {
      expireHighflyTap(p);return;
    }
    if(ctx.tickCount>hf.queuedUntil) {expireHighflyTap(p);return;}
    if(p.dead || p.castingAbility || isStunned(p) || isDisarmed(p) ||
       dist2d(p.pos,t.pos)>MELEE_RANGE) return;
    if(!claimHighflyTap(p,ctx.tickCount))return;
    // Facing is a character action; P67 camera never follows this turn.
    p.facing=angleTo(p.pos,t.pos);
    p.swingTimer=0;
    p.autoAttack=true;
    try {
      tryPlayerSwing(ctx,p,meta); // genuine swing, P63 combo on landed hits
    } finally {
      p.autoAttack=false;
    }
    return;
  }
  p.swingTimer = Math.max(0, p.swingTimer - DT);""",
      "AUTO_TAP_GATE")
    return s

def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def validate():
    p9.preflight(ORIGINAL,STAGE,p9.REPORT)
    src={}
    for rel in EXISTING:
        p=STAGE/rel
        if p.is_symlink() or not p.is_file():raise RuntimeError("P69_SOURCE_MISSING_"+rel)
        src[rel]=p.read_text("utf8")
        if MARK in src[rel]:raise RuntimeError("P69_ALREADY_APPLIED_"+rel)
    for rel in (TOUCH,TAPS,CSS):
        if (STAGE/rel).exists() or (STAGE/rel).is_symlink():
            raise RuntimeError("P69_TARGET_EXISTS_"+rel)
    if "HIGHFLY_P68_FURY_GOLDEN_RECOVERY" not in src[MAIN]:
        raise RuntimeError("P69_REQUIRES_P68")
    if "HIGHFLY_P63_COMBAT_C1" not in src[AUTO] or \
       "HIGHFLY_P63_COMBAT_C1" not in src[RING]:
        raise RuntimeError("P69_REQUIRES_P63_COMBO")
    if "HIGHFLY_P64_REAL_BOAR_CC0" not in \
       (STAGE/"src/render/characters/manifest.ts").read_text("utf8"):
        raise RuntimeError("P69_REQUIRES_P64_BOAR")
    new={MAIN:patch_main(src[MAIN]),HUD:patch_hud(src[HUD]),
         RING:patch_ring(src[RING]),SIM:patch_sim(src[SIM]),
         AUTO:patch_auto(src[AUTO]),TOUCH:TOUCH_CODE,
         TAPS:TAPS_CODE,CSS:CSS_CODE}
    # CSS link added in HTML as late-stage authored skin.
    index=STAGE/"index.html"
    if index.is_symlink() or not index.is_file():raise RuntimeError("P69_INDEX_MISSING")
    original_html=index.read_text("utf8")
    if '<link rel="stylesheet" href="/highfly/p68_fury_recovery.css" />' not in original_html:
        raise RuntimeError("P69_REQUIRES_P68_CSS")
    new["index.html"]=once(original_html,'</head>',
       "<!-- "+MARK+": real skill gesture + manual basics -->\n"
       '<link rel="stylesheet" href="/highfly/p69_fury_core.css" />\n</head>',
       "INDEX_HEAD")
    src["index.html"]=original_html
    return src,new

def run(apply=False):
    originals,updated=validate()
    result={"phase":"P69_FURY_CORE_NATIVE_ACTION_INTEGRATION",
      "mode":"DRY_RUN",
      "movement":"P68 vector using native signed screen-right, no camera yaw writes",
      "dash":"P48 collision swept dash uses corrected facing and joystick, no duplicate engine",
      "basic":"offline Sim: one touch tap -> one native gated hit, short tap buffer and P63 landed combo",
      "skills":"native position-target skills: hold-drag-preview-release, top-right cancel, native cost and cooldown",
      "skillsOther":"non-position, empowered and unassigned slots retain native behavior",
      "onlineMode":"legacy server-authorized autoattack, no unsanctioned local damage",
      "fireballCurved":"pending asset/trajectory integration; no fake curved projectile",
      "aerialCombo":"pending, not falsely claimed",
      "saveNpcLootQuestsChanged":False,
      "visualBrowserVerified":False}
    if not apply:
        print("[HIGHFLY P69] "+json.dumps(result,indent=2,ensure_ascii=False));return
    if OUT.is_symlink():raise RuntimeError("P69_UNSAFE_BACKUP")
    if OUT.exists():
        if not OUT.is_dir():raise RuntimeError("P69_INVALID_BACKUP")
        if (OUT/"P69_STATUS.json").exists():raise RuntimeError("P69_INSTALLED_ALREADY")
        archives=OUT.parent/"highfly-p69-safekept-attempts"
        if archives.is_symlink():raise RuntimeError("P69_ARCHIVE_SYMLINK")
        archives.mkdir(exist_ok=True,parents=True)
        destination=archives/("attempt-"+str(time.time_ns()))
        if destination.exists():raise RuntimeError("P69_ARCHIVE_EXISTS")
        OUT.rename(destination)
    backups=[];created=[]
    try:
        for rel in originals:
            source=STAGE/rel;dest=OUT/"backups"/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,dest)
            if hash_file(source)!=hash_file(dest):
                raise RuntimeError("P69_BACKUP_HASH_"+rel)
            backups.append((source,dest))
        for rel,source in updated.items():
            path=STAGE/rel
            if rel in originals:
                if path.read_text("utf8")!=originals[rel]:
                    raise RuntimeError("P69_CONCURRENT_CHANGE_"+rel)
                path.write_text(source,"utf8")
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open("x",encoding="utf8") as f:f.write(source)
                created.append(path)
        subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
          cwd=ROOT,check=True)
    except BaseException:
        for path,backup in backups:
            if backup.is_file():shutil.copy2(backup,path)
        for p in created:
            if p.is_file():p.unlink()
        print("[HIGHFLY P69] RED -> recovered previous P68 stage",file=sys.stderr)
        raise
    result["mode"]="BUILD_GREEN_BROWSER_PENDING"
    (OUT/"P69_STATUS.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
    print("[HIGHFLY P69] "+json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    run(ap.parse_args().apply)
