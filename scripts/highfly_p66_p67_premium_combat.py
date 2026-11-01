#!/usr/bin/env python3
"""HIGHFLY WORLD RPG FITNESS P66+P67:
One guarded stage-only pass: bespoke HUD / integrated loading composition,
independent free-look and combat move-to-target/facing. No fake hits, no sim edits.
Requires P65. Backups and rollback on Vite failure. No external assets.
"""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
MARK='HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM'
HTML='index.html'
MAIN='src/main.ts'
CSS_PATH='public/highfly/p66_p67_premium.css'
FILES=(HTML,MAIN)
OUT=ROOT/'.workspace/reports/highfly-p66-p67-combat-premium'

CSS=r"""/* HIGHFLY WORLD RPG FITNESS | authored touch skin | P66-P67
   Uses native engine icons, cooldowns, health, targeting and buttons.
   All game actions remain inside the original native interaction system. */
:root{--hf66-void:#080d24;--hf66-panel:#10132e;--hf66-edge:#a57cfc;
 --hf66-glow:#48daf5;--hf66-gold:#ebc482;--hf66-ink:#f6f1ff}
/* The spectacular HIGHFLY splash is the art; reserve a dedicated dark footer
   for progress/copy, so those elements no longer float on the brand logo. */
#loading-screen .ls-progress{
  position:absolute!important;z-index:12!important;
  inset:auto auto max(4px,env(safe-area-inset-bottom)) 50%!important;
  transform:translateX(-50%)!important;
  width:min(760px,94vw)!important;height:76px!important;max-height:none!important;
  box-sizing:border-box!important;margin:0!important;
  padding:7px 18px!important;display:block!important;
  border:1px solid rgba(180,125,255,.66)!important;
  border-radius:14px!important;
  background:linear-gradient(110deg,rgba(5,9,28,.94),rgba(25,10,47,.91),rgba(5,9,28,.94))!important;
  box-shadow:0 0 1px #b49fff inset,0 0 16px rgba(99,38,191,.34),0 12px 22px rgba(0,0,0,.42)!important;
  backdrop-filter:blur(10px)!important;-webkit-backdrop-filter:blur(10px)!important;
  overflow:hidden!important;
}
#loading-screen #ls-status{
  position:absolute!important;top:6px!important;left:12px!important;
  right:12px!important;width:auto!important;height:19px!important;
  display:block!important;text-align:center!important;
  font:700 12px/19px system-ui,sans-serif!important;letter-spacing:.08em!important;
  color:#f4ebff!important;background:none!important;
  text-shadow:0 0 8px rgba(145,87,245,.8)!important;
}
#loading-screen .ls-bar{
  position:absolute!important;top:29px!important;
  left:18px!important;right:18px!important;
  width:calc(100% - 36px)!important;height:11px!important;
  border:1px solid rgba(174,145,255,.9)!important;border-radius:8px!important;
  background:rgba(4,8,28,.95)!important;
  box-shadow:0 0 8px rgba(125,68,224,.35),inset 0 0 6px #050d1e!important;
  overflow:hidden!important;
}
#loading-screen #ls-fill{
  height:100%!important;min-height:0!important;border-radius:7px!important;
  background:linear-gradient(90deg,#5550d6,#8e5ce8,#e2afea)!important;
  box-shadow:0 0 9px rgba(222,164,255,.75)!important;
}
#loading-screen #ls-tip{
  position:absolute!important;top:44px!important;
  left:12px!important;right:12px!important;width:auto!important;
  height:25px!important;min-height:0!important;max-height:25px!important;
  margin:0!important;padding:0!important;
  background:none!important;border:0!important;display:block!important;
  overflow:hidden!important;text-overflow:ellipsis!important;
  color:#d7ceea!important;text-align:center!important;
  font:10px/13px system-ui,sans-serif!important;
  text-shadow:0 1px 3px #04050c!important;
}
#loading-screen #ls-slow-hint{display:none!important}
@media(max-height:430px) and (orientation:landscape){
 #loading-screen .ls-progress{height:65px!important;border-radius:11px!important;padding:5px 13px!important}
 #loading-screen #ls-status{top:4px!important;height:15px!important;font-size:11px!important;line-height:15px!important}
 #loading-screen .ls-bar{top:22px!important;height:10px!important}
 #loading-screen #ls-tip{top:36px!important;height:22px!important;max-height:22px!important;font-size:9px!important}
}
/* Premium action panel. Size, glyph, border and rhythm shared across controls. */
body.mobile-touch.game-active{
 --hf66-control:clamp(43px,5.1vw,54px);
 --hf66-gap:clamp(8px,1.25vw,13px);
 --hf66-edge:rgba(170,134,250,.89);
 --hf66-ink:#eee8ff;
}
body.mobile-touch.game-active #mobile-action-ring > button,
body.mobile-touch.game-active #mobile-menu-anchor{
  border:1.5px solid var(--hf66-edge)!important;
  background:radial-gradient(circle at 35% 23%,rgba(71,47,121,.94),rgba(19,18,53,.97) 63%,rgba(8,10,27,.99) 100%)!important;
  color:var(--hf66-ink)!important;
  box-shadow:0 0 0 2px rgba(6,12,31,.85) inset,
   0 0 0 1px rgba(187,148,255,.19),
   0 3px 13px rgba(0,0,0,.57),0 0 12px rgba(116,68,190,.3)!important;
  font-family:system-ui,sans-serif!important;
  text-shadow:0 1px 3px #000,0 0 8px rgba(166,116,255,.5)!important;
}
body.mobile-touch.game-active #mobile-action-ring > button:not([hidden]){
  touch-action:none!important;-webkit-tap-highlight-color:transparent;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive,
body.mobile-touch.game-active #mobile-action-ring #mobile-jump,
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge,
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{
  width:var(--hf66-control)!important;
  height:var(--hf66-control)!important;
  display:flex!important;
  justify-content:center!important;align-items:center!important;
  bottom:calc(var(--mobile-ring-attack-size)/2 - var(--hf66-control)/2)!important;
  border-radius:50%!important;
}
/* Control row, from left to right PASIVA | SALTAR | EVADIR | S1.
   Right-aligned relative to ATK: consistent step and centerline. */
body.mobile-touch.game-active #mobile-action-ring #mobile-passive{
  right:calc(var(--hf66-control)*3 + var(--hf66-gap)*3 + 141px)!important;
  font-size:0!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive::after{
  content:"PAS";position:static;color:#e7d4ff;font-size:10px;letter-spacing:.05em;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-jump{
  right:calc(var(--hf66-control)*2 + var(--hf66-gap)*2 + 141px)!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge{
  position:absolute!important;right:calc(var(--hf66-control) + var(--hf66-gap) + 141px)!important;
  font-size:0!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge::before{
  content:"↠";display:block;font:750 24px/1 system-ui;color:#b4f7ff;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge::after{
  content:"DASH";position:absolute;bottom:1px;left:50%;transform:translateX(-50%);
  font:700 7px/1 system-ui;letter-spacing:.03em;color:#ccffff;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{
  right:141px!important;
  border-color:rgba(94,219,255,.94)!important;
  box-shadow:0 0 0 2px #061122 inset,0 0 13px rgba(31,208,243,.38)!important;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]::after{
  content:"S1";position:absolute;bottom:-13px;left:50%;transform:translateX(-50%);
  font:700 10px/1 system-ui;color:#a7f4ff;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-jump .mobile-label{
  margin-top:1px!important;font-size:8px!important;color:#e8dbff!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive .ui-icon{display:none!important}
body.mobile-touch.game-active #mobile-action-ring #mobile-action-attack{
  border:2px solid rgba(94,219,255,.94)!important;
  background:radial-gradient(circle at 28% 20%,#314b82 0%,#17234d 55%,#0a112c 95%)!important;
  box-shadow:0 0 0 2px #0c1028 inset,0 0 18px rgba(54,212,237,.42),0 5px 12px #030819!important;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="1"],
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="2"],
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="3"],
body.mobile-touch.game-active #mobile-action-ring #mobile-consumable-seat{
  opacity:.88!important;filter:saturate(.78)!important;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot:active,
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge:active,
body.mobile-touch.game-active #mobile-action-ring #mobile-jump:active{
  filter:brightness(1.35)!important;
  border-color:#96faff!important;
}
body.mobile-touch.game-active #mobile-menu-anchor{
  background:linear-gradient(140deg,#261a50,#0d1736)!important;
  border:1.5px solid #b78ef4!important;
  border-radius:12px!important;box-shadow:0 0 14px rgba(121,72,201,.33)!important;
}
body.mobile-touch.game-active #mobile-menu-anchor::after{
  content:"•••";font-size:18px;color:#e7d1ff;
  letter-spacing:2px;
}
/* Solid square fantasy popup, not a generic blue dashboard grid. */
body.mobile-touch.game-active #mobile-extra-controls{
  width:min(480px,calc(100vw - 24px))!important;
  height:min(380px,calc(100dvh - 20px))!important;
  border-radius:14px!important;
  border:2px solid rgba(185,139,251,.83)!important;
  background:
    linear-gradient(145deg,rgba(101,54,150,.15),transparent 28%),
    linear-gradient(165deg,#100f2f,#10142d 60%,#0b0925)!important;
  box-shadow:0 0 0 3px #080a1c inset,0 0 18px rgba(171,105,237,.22),0 14px 35px #01030b!important;
}
body.mobile-touch.game-active #mobile-extra-controls .panel-title{
  min-height:44px!important;
  letter-spacing:.09em!important;font:800 16px/1.2 Georgia,serif!important;
  color:#f3deff!important;text-shadow:0 0 10px rgba(193,114,245,.5)!important;
}
body.mobile-touch.game-active #mobile-extra-grid{
  display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:8px!important;padding:5px!important;
}
body.mobile-touch.game-active #mobile-extra-grid .mobile-btn{
  border-radius:10px!important;min-height:47px!important;
  background:linear-gradient(165deg,rgba(47,33,96,.95),rgba(15,19,52,.96))!important;
  border:1px solid rgba(158,127,229,.65)!important;
  color:#e9ddff!important;
  box-shadow:0 0 0 1px rgba(22,16,56,.85) inset,0 3px 8px rgba(0,0,0,.34)!important;
  font-weight:700!important;text-shadow:0 1px 3px #050916!important;
}
body.mobile-touch.game-active #mobile-extra-grid .mobile-btn .mobile-label{
  font-size:10px!important;color:#eeeaff!important;
}
body.mobile-touch.game-active #mobile-extra-grid .mobile-btn:is(:focus-visible,:active){
  border-color:#87f2ff!important;
  background:linear-gradient(160deg,#343974,#18214d)!important;
}
@media(max-height:460px) and (orientation:landscape){
 body.mobile-touch.game-active{--hf66-control:clamp(39px,5.0vw,49px);--hf66-gap:8px}
 body.mobile-touch.game-active #mobile-extra-controls{height:calc(100dvh - 14px)!important}
 body.mobile-touch.game-active #mobile-extra-grid .mobile-btn{min-height:41px!important}
}
@media(prefers-reduced-motion:reduce){
 body.mobile-touch.game-active #mobile-action-ring button{transition:none!important}
}
""".strip()+'\n'

def once(s,old,new,tag):
    n=s.count(old)
    if n!=1:raise RuntimeError('P66_P67_ANCHOR_'+tag+'_'+str(n))
    return s.replace(old,new,1)

def patch_html(s):
    # Append after P65 style without depending on historical P48 link paths.
    return once(s,'</head>',
        '<!-- '+MARK+': new premium HIGHFLY mobile skin -->\n'
        '<link rel="stylesheet" href="/highfly/p66_p67_premium.css" />\n</head>',
        'HEAD')

def patch_main(s):
    # Camera follows the FREE LOOK, not the player rotation generated by
    # the left thumb. Right-hand swipe and double-tap recenter still work.
    s=once(s,
      '    const next = updateFollowCameraYaw({',
      """    // HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM: manual camera and movement
    // are independent on touch. Follow-body yaw made LEFT joystick
    // movement rotate the whole camera, which is not an action RPG feel.
    if (document.body.classList.contains('mobile-touch') &&
        document.body.classList.contains('game-active')) {
      lastInterpFacing = interpFacing;
      return;
    }
    const next = updateFollowCameraYaw({""",
      'FREE_CAMERA')
    s=once(s,
      '  let lastInterpFacing: number | null = null;',
      """  let lastInterpFacing: number | null = null;
  // HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM: limited attack-approach initiated
  // ONLY by the player's own touch ATK or an explicit enemy tap.
  let highflyApproachId: number | null = null;""",
      'APPROACH_STATE')
    s=once(s,
      '      world.targetEntity(enemy.id);\n      world.startAutoAttack();\n      return true;',
      """      world.targetEntity(enemy.id);
      world.startAutoAttack();
      highflyApproachEnemy(enemy.id);
      return true;""",
      'TAP_TARGET_CHASE')
    s=once(s,
      '    world.targetEntity(best);\n    world.startAutoAttack();\n  }\n\n  function clickMovePathTo(',
      """    world.targetEntity(best);
    world.startAutoAttack();
    highflyApproachEnemy(best);
  }

  // HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM: reuse collision-aware
  // click-to-move path for a short automatic approach, NEVER teleport.
  // The native click-move cancels immediately if a manual joystick
  // direction is held. Outside 15m we only target, not autowalk.
  function highflyApproachEnemy(targetId: number): void {
    if (!document.body.classList.contains('mobile-touch') ||
        input.suspendMovement || input.isMouselookActive()) return;
    const target=world.entities.get(targetId);
    if (!target || target.dead || !isAttackableEntity(target,world.playerId,activePvpOpponentIds(world))) return;
    const d=dist2d(world.player.pos,target.pos);
    if (d<=3.0 || d>15) return;
    const current=input.readMoveInput();
    if (current.forward || current.back || current.strafeLeft || current.strafeRight) return;
    const goal=resolvedClickMoveTarget({x:target.pos.x,z:target.pos.z});
    highflyApproachId=targetId;
    input.setClickMoveTarget(goal,2.6,targetId,clickMovePathTo(goal),false);
  }

  function clickMovePathTo(""",
      'NATIVE_CHASE')
    s=once(s,
      "        enabled: settings.get('clickToMove') > 0 || settings.get('attackMove'),",
      """        enabled: settings.get('clickToMove') > 0 || settings.get('attackMove') ||
          (document.body.classList.contains('mobile-touch') &&
           highflyApproachId!==null && input.clickMoveEntityId===highflyApproachId),""",
      'CHOOSE_BOUNDED_CHASE')
    s=once(s,
      '        mi.strafeLeft=false;mi.strafeRight=false;\n      }\n    }',
      """        mi.strafeLeft=false;mi.strafeRight=false;
      }
    }
    // HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM: when the player is
    // standing and ATK is armed, face the live hostile target. Manual
    // movement and a running path retain control of the character.
    if (document.body.classList.contains('mobile-touch') &&
        !input.clickMoveTarget && !input.isMouselookActive() &&
        !mi.forward && !mi.back && !mi.strafeLeft && !mi.strafeRight &&
        world.player.autoAttack && world.player.targetId!==null) {
      const target=world.entities.get(world.player.targetId);
      if (target && !target.dead &&
          isAttackableEntity(target,world.playerId,activePvpOpponentIds(world)) &&
          dist2d(playerPos,target.pos)<16) {
        facing=Math.atan2(target.pos.x-playerPos.x,target.pos.z-playerPos.z);
      }
    }""",
      'ATTACK_TURN')
    return s

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()

def validate():
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    orig={}
    for rel in FILES:
        f=STAGE/rel
        if f.is_symlink() or not f.is_file():raise RuntimeError('P66_P67_MISSING_'+rel)
        orig[rel]=f.read_text('utf8')
        if MARK in orig[rel]:raise RuntimeError('P66_P67_ALREADY_'+rel)
    if (STAGE/CSS_PATH).exists() or (STAGE/CSS_PATH).is_symlink():
        raise RuntimeError('P66_P67_CSS_EXISTS')
    if 'HIGHFLY_P65_MOBILE_COMBAT_HUD_C2' not in orig[MAIN] or \
       'HIGHFLY_P65_MOBILE_COMBAT_HUD_C2' not in orig[HTML]:
        raise RuntimeError('P66_P67_REQUIRES_P65')
    if 'HIGHFLY_P64_REAL_BOAR_CC0' not in (STAGE/'src/render/characters/manifest.ts').read_text('utf8'):
        raise RuntimeError('P66_P67_REQUIRES_P64_BOAR')
    changes={HTML:patch_html(orig[HTML]),MAIN:patch_main(orig[MAIN]),CSS_PATH:CSS}
    return orig,changes

def run(apply=False):
    orig,changes=validate()
    state={
      'phase':'P66_P67_HIGHFLY_PREMIUM_HUD_AND_COMBAT_FEEL',
      'mode':'DRY_RUN',
      'loading':'progress and tips in lower glass panel, real engine percent',
      'hud':'single violet and cyan circular family, native S1/cooldown and jump/dodge',
      'menu':'native HIGHFLY 3-dot square menu, fully styled',
      'camera':'left stick moves only; camera yaw unchanged by movement or target turning',
      'attack':'native attack faces target at rest and path-approaches within 15m on touch',
      'manualMoveCancelsChase':True,
      'backwardsMotion':'P65 camera-relative 360 preserved',
      'realSimDamage':'P63 and P64 unchanged',
      'editor':'P58 is draft-only; NOT a permanent world writer',
      'browserVerified':False,'fullActionCombatComplete':False,
    }
    if not apply:
        print('[HIGHFLY P66+P67] '+json.dumps(state,ensure_ascii=False,indent=2));return
    if OUT.is_symlink():raise RuntimeError('P66_P67_BACKUP_UNSAFE')
    if OUT.exists():
        if not OUT.is_dir():raise RuntimeError('P66_P67_BACKUP_BAD')
        if (OUT/'P66_P67_STATUS.json').exists():raise RuntimeError('P66_P67_ALREADY_INSTALLED')
        archive=OUT.parent/'highfly-p66-p67-attempts'
        if archive.is_symlink():raise RuntimeError('P66_P67_ARCHIVE_UNSAFE')
        archive.mkdir(parents=True,exist_ok=True)
        OUT.rename(archive/('attempt-'+str(time.time_ns())))
    backup=[];created=[]
    try:
        for rel in FILES:
            src=STAGE/rel;dst=OUT/'backups'/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            if sha(src)!=sha(dst):raise RuntimeError('P66_P67_BACKUP_MISMATCH')
            backup.append((src,dst))
        for rel,data in changes.items():
            dest=STAGE/rel
            if rel in orig:
                if dest.read_text('utf8')!=orig[rel]:
                    raise RuntimeError('P66_P67_CONCURRENT_CHANGE_'+rel)
                dest.write_text(data,encoding='utf8')
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('x',encoding='utf8') as w:w.write(data)
                created.append(dest)
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],
                        cwd=ROOT,check=True)
    except BaseException:
        for src,bak in backup:
            if bak.is_file():shutil.copy2(bak,src)
        for f in created:
            if f.is_file():f.unlink()
        print('[HIGHFLY P66+P67] Build failed; restored previous P65 stage',file=sys.stderr)
        raise
    state['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P66_P67_STATUS.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('[HIGHFLY P66+P67] '+json.dumps(state,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    run(parser.parse_args().apply)
