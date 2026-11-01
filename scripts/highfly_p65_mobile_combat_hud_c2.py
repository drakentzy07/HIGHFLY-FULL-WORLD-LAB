#!/usr/bin/env python3
"""HIGHFLY P65 — one integrated MOBILE C2 pass on the PRIVATE stage.
Screen-wide loading, portrait HUD at top-left, 3-dot square real game menu,
connected PASSIVA (spellbook), SALTAR, EVADIR, S1, camera-relative 360° move
and tap-on-actual-monster soft targeting. Preserve P64, RPG data, all quests,
colliders and KayKit/Gobkit assets. Guard each edit and rollback on build errors.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
O=p9.ORIGINAL;S=p9.STAGE
OUT=ROOT/'.workspace/reports/highfly-p65-hud-combat-c2'
MARK="HIGHFLY_P65_MOBILE_COMBAT_HUD_C2"
HTML='index.html'
MOBILE='src/game/mobile_controls.ts'
MAIN='src/main.ts'
CSS_PATH='public/highfly/p65.css'
FILES=(HTML,MOBILE,MAIN)

CSS=r"""/* HIGHFLY_P65_MOBILE_COMBAT_HUD_C2: actual touch controls, not mockups.
   Responsive S23 Ultra landscape safe-area layout. */
body.mobile-touch {
  --hf-ink:#e8f9ff;--hf-cyan:#36d7ed;--hf-purple:#805be5;
}
body.mobile-touch #loading-screen {
  position:fixed!important;
  inset:0!important;
  width:100vw!important;height:100dvh!important;
  min-height:100dvh!important;max-height:none!important;
  padding:env(safe-area-inset-top) env(safe-area-inset-right)
    env(safe-area-inset-bottom) env(safe-area-inset-left)!important;
  overflow:hidden!important;
  background-position:center center!important;
  background-size:cover!important;
}
body.mobile-touch #loading-screen::before {
  inset:0!important;
  background-position:center center!important;
  background-size:cover!important;
}
/* Health, mana, stamina are still painted by native #player-frame. */
body.mobile-touch.game-active #player-frame:not(.pf-detached),
body.mobile-touch.game-active.operating-vehicle #player-frame:not(.pf-detached) {
  position:fixed!important;
  left:max(8px,env(safe-area-inset-left))!important;
  top:calc(7px + env(safe-area-inset-top))!important;
  right:auto!important;bottom:auto!important;
  margin:0!important;
  transform:scale(.78)!important;
  transform-origin:top left!important;
  z-index:83!important;
}
/* The THREE DOTS are under the player frame, not in the button row. */
body.mobile-touch.game-active #mobile-combat-controls,
body.mobile-touch.game-active.xhb-mode #mobile-combat-controls,
body.mobile-touch.game-active.xhb-mode.mobile-left-handed #mobile-combat-controls{
  position:absolute!important;
  top:calc(90px + env(safe-area-inset-top))!important;
  left:max(9px,env(safe-area-inset-left))!important;
  bottom:auto!important;right:auto!important;
  display:flex!important;flex-direction:column!important;
  width:50px!important;max-width:50px!important;z-index:35!important;
  pointer-events:none!important;
}
body.mobile-touch.game-active #mobile-menu-anchor{
  width:49px!important;height:47px!important;
  border-radius:12px!important;
  transform:none!important;
  border:1px solid rgba(54,215,237,.7)!important;
  background:linear-gradient(145deg,rgba(9,24,53,.95),rgba(21,10,45,.92))!important;
  color:var(--hf-ink)!important;
  box-shadow:0 0 0 1px rgba(128,91,229,.45),0 4px 15px rgba(0,0,0,.6)!important;
  pointer-events:auto!important;
}
body.mobile-touch.game-active #mobile-menu-anchor :is(.mobile-label,.ui-icon,.ui-icon-art){
  display:none!important;
}
body.mobile-touch.game-active #mobile-menu-anchor::after{
  content:"•••";
  font:800 22px/1 system-ui;
  letter-spacing:1px;color:var(--hf-cyan);
}
/* Existing mobile-extra-controls is a real, already bound native menu modal. */
body.mobile-touch.game-active #mobile-extra-controls{
  position:fixed!important;
  left:50%!important;top:50%!important;
  right:auto!important;bottom:auto!important;
  width:min(390px,calc(100vw - 32px))!important;
  height:min(340px,calc(100dvh - 26px))!important;
  max-width:calc(100vw - 32px)!important;
  max-height:calc(100dvh - 26px)!important;
  overflow-y:auto!important;
  transform:translate(-50%,-50%)!important;
  border:1px solid rgba(54,215,237,.65)!important;
  border-radius:15px!important;
  background:linear-gradient(150deg,rgba(7,18,38,.98),rgba(21,10,47,.98))!important;
  box-shadow:0 0 22px rgba(54,215,237,.18),0 18px 55px rgba(0,0,0,.82)!important;
  z-index:110!important;
}
body.mobile-touch.game-active #mobile-extra-controls .panel-title{
  color:var(--hf-ink)!important;
  font-weight:750!important;text-align:center!important;
}
body.mobile-touch.game-active #mobile-extra-grid{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  grid-auto-rows:minmax(42px,auto)!important;
  gap:7px!important;
}
body.mobile-touch.game-active #mobile-extra-grid .mobile-btn{
  min-height:42px!important;height:auto!important;
  border-radius:9px!important;
  border:1px solid rgba(128,91,229,.6)!important;
  background:rgba(17,33,66,.86)!important;
  color:var(--hf-ink)!important;
}
body.mobile-touch.game-active #mobile-extra-grid :is(#mobile-donate,#mobile-steam-wishlist,#mobile-wiki,#mobile-discord,#mobile-wocmarket,#mobile-daily-rewards){
  display:none!important;
}
/* Preserve the ring's own 4 actionable ability slots and all cooldown visuals.
   Rearrange only the lower row: PASIVA / SALTAR / EVADIR / S1 / ATK. */
body.mobile-touch.game-active #mobile-action-ring #mobile-passive{
  position:absolute!important;display:flex!important;
  right:calc(390px * var(--mobile-chrome-scale,1))!important;
  bottom:calc(var(--mobile-ring-attack-size)/2 - 24px)!important;
  width:50px!important;height:50px!important;
  border-radius:50%!important;z-index:35!important;
  border:2px solid rgba(128,91,229,.8)!important;
  background:radial-gradient(circle at 35% 25%,#213e70,#0b1738 75%)!important;
  color:#e8e5ff!important;
  font:800 10px/1 system-ui!important;
  box-shadow:0 0 10px rgba(128,91,229,.35)!important;
  text-align:center!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-jump{
  right:calc(328px * var(--mobile-chrome-scale,1))!important;
  bottom:calc(var(--mobile-ring-attack-size)/2 - var(--mobile-ring-secondary-size)/2)!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge{
  position:absolute!important;display:flex!important;
  right:calc(265px * var(--mobile-chrome-scale,1))!important;
  bottom:calc(var(--mobile-ring-attack-size)/2 - 27px)!important;
  width:54px!important;height:54px!important;
  border-radius:50%!important;
  border:2px solid rgba(54,215,237,.8)!important;
  background:linear-gradient(145deg,#122e59,#081633)!important;
  color:#e7fbff!important;
  box-shadow:0 0 10px rgba(54,215,237,.25)!important;
  font:800 9px/1 system-ui!important;
  z-index:35!important;pointer-events:auto!important;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{
  right:calc(205px * var(--mobile-chrome-scale,1))!important;
  bottom:calc(var(--mobile-ring-attack-size)/2 - var(--mobile-ring-action-size)/2)!important;
}
body.mobile-touch.game-active #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]::after{
  content:"S1";position:absolute;bottom:-13px;left:50%;transform:translateX(-50%);
  color:var(--hf-cyan);font:800 10px/1 system-ui;pointer-events:none;
}
body.mobile-touch.game-active #mobile-action-ring > button:focus-visible {
  outline:2px solid var(--hf-cyan);outline-offset:2px;
}
@media(max-height:420px) and (orientation:landscape){
 body.mobile-touch.game-active #mobile-extra-controls{height:calc(100dvh - 18px)!important}
 body.mobile-touch.game-active #mobile-action-ring #mobile-passive{
   right:calc(356px * var(--mobile-chrome-scale,1))!important;
 }
 body.mobile-touch.game-active #mobile-action-ring #mobile-jump{
   right:calc(300px * var(--mobile-chrome-scale,1))!important;
 }
 body.mobile-touch.game-active #mobile-action-ring #mobile-dodge{
   right:calc(250px * var(--mobile-chrome-scale,1))!important;
 }
}
@media(prefers-reduced-motion:reduce){
 body.mobile-touch #mobile-extra-controls,
 body.mobile-touch #mobile-action-ring button {transition:none!important}
}
""".strip()+"\n"

def once(src,old,new,label):
    count=src.count(old)
    if count!=1:raise RuntimeError('P65_ANCHOR_'+label+'_COUNT_'+str(count))
    return src.replace(old,new,1)

def patch_html(s):
    s=once(s,
      '<button type="button" id="mobile-jump" data-i18n-title=',
      '<button type="button" id="mobile-passive" title="Pasivas: abrir habilidades" aria-label="Pasivas: abrir habilidades" data-icon="spellbook">PASIVA</button>\n'
      '<button type="button" id="mobile-jump" data-i18n-title=',
      'REAL_PASSIVE_ENTRY')
    # HEAD is the structural HTML insertion point. P48's CSS may have
    # been re-authored/reordered in later HIGHFLY stages; don't require
    # a verbatim P48 <link> as an insertion anchor.
    s=once(s,'</head>',
      '<!-- '+MARK+': mobile controls use genuine game callbacks -->\n'
      '<link rel="stylesheet" href="/highfly/p65.css" />\n'
      '</head>',
      'HEAD_STYLESHEET')
    # Keep the official menu's stable ID but allow its text/i18n markup
    # to evolve. Remove the translation attribute so HIGHFLY remains branded.
    import re
    title_pattern=r'<span\\s+id="mobile-more-title"[^>]*>[^<]*</span>'
    s,count=re.subn(title_pattern,
      '<span id="mobile-more-title">HIGHFLY · MENÚ</span>',s,count=2)
    if count!=1:raise RuntimeError('P65_ANCHOR_MENU_TITLE_COUNT_'+str(count))
    return s

def patch_mobile(s):
    s=once(s,
      "import { buildMobileMenuControl, type MobileMenuControl } from '../ui/hud/menu';",
      "import type { MobileMenuControl } from '../ui/hud/menu';",
      'REMOVE_UNUSED_OLD_MENU_IMPORT')
    s=once(s,'  onCycleTarget(): void;',
      '  onCycleTarget(): void;\n'
      '  /** Tap on real enemy mesh; false keeps two-tap camera recenter. */\n'
      '  onWorldTap?: (x:number,y:number) => boolean;',
      'WORLD_TAP_INTERFACE')
    s=once(s,
       "    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });",
       "    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });\n"
       "    // "+MARK+": PASIVA is a true spellbook entry, not a fake active cast.\n"
       "    this.bindButton('mobile-passive', () => this.callbacks.onSpellbook());",
       'PASSIVE_ACTION_CALLBACK')
    s=once(s,'    this.menuControl = buildMobileMenuControl();',
"""    // HIGHFLY_P65_MOBILE_COMBAT_HUD_C2: route the top-left THREE DOTS
    // directly into the existing real square More menu and its callbacks.
    // Avoid the old gesture strip. Every modal item remains the native button
    // bound by bindButton() below (bags, skills, character, quests, map).
    this.menuControl = null;
    this.bindButton('mobile-menu-anchor', () => {
      const open = !document.body.classList.contains('mobile-more-open');
      if (!open) { this.closeMoreModal(); return; }
      this.root?.classList.add('expanded');
      document.body.classList.add('mobile-more-open');
      const modal=document.getElementById('mobile-extra-controls');
      if (modal) {
        modal.style.left='50%';modal.style.top='50%';
        modal.style.right='auto';modal.style.bottom='auto';
        modal.style.transform='translate(-50%, -50%)';
        delete modal.dataset.windowMoved;
      }
    });""",
       'SQUARE_MENU_REAL_CALLBACK')
    s=once(s,"target.closest('#mobile-extra-controls') || target.closest('#mobile-more')",
       "target.closest('#mobile-extra-controls') || target.closest('#mobile-more') ||\n"
       "          target.closest('#mobile-menu-anchor')",
       'MENU_OUTSIDE_GUARD')
    s=once(s,
"""    if (quickTap && isRecenterDoubleTap(this.lastSwipeTapAt, now, this.swipeLookActive)) {""",
"""    // HIGHFLY_P65_MOBILE_COMBAT_HUD_C2: tap directly on the actual
    // monster mesh for semi-automatic target+attack; drags remain camera.
    if (quickTap && this.callbacks.onWorldTap?.(e.clientX,e.clientY)===true) {
      this.lastSwipeTapAt=0;
      this.releaseSwipeLook();
      return;
    }
    if (quickTap && isRecenterDoubleTap(this.lastSwipeTapAt, now, this.swipeLookActive)) {""",
       'WORLD_TAP_COMBAT')
    return s

def patch_main(s):
    s=once(s,
      '    onCycleTarget: () => world.tabTarget(),',
"""    // HIGHFLY_P65_MOBILE_COMBAT_HUD_C2: real entity raycast on screen
    // tap. Never start a synthetic hit or use an invisible hot zone.
    onWorldTap: (x,y) => {
      const picked=renderer.pick(x,y);
      const enemy=picked===null?null:world.entities.get(picked);
      if (!enemy || !isAttackableEntity(enemy,world.playerId,activePvpOpponentIds(world)))
        return false;
      world.targetEntity(enemy.id);
      world.startAutoAttack();
      return true;
    },
    onCycleTarget: () => world.tabTarget(),""",
      'REAL_TAP_ON_MONSTER')
    s=once(s,
      "    let facing: number | null = mouselook ? input.camYaw : null;",
"""    let facing: number | null = mouselook ? input.camYaw : null;
    // HIGHFLY_P65_MOBILE_COMBAT_HUD_C2: camera-relative 360-degree
    // facing on mobile. A back joystick push now runs toward the back
    // camera vector and TURNs the character, not legacy backpedalling.
    // Do not change keyboard, PC, mob AI or autorun; click-move keeps
    // its own bearing later in resolveMove().
    if (document.body.classList.contains('mobile-touch') &&
        !input.clickMoveTarget && !input.autorun && !input.suspendMovement) {
      const horizontal=Number(mi.strafeRight)-Number(mi.strafeLeft);
      const vertical=Number(mi.forward)-Number(mi.back);
      if (horizontal!==0 || vertical!==0) {
        const yaw=input.camYaw;
        const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);
        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);
        facing=Math.atan2(worldX,worldZ);
        mi.forward=true;mi.back=false;
        mi.strafeLeft=false;mi.strafeRight=false;
      }
    }""",
      'CAMERA_RELATIVE_MOVEMENT_360')
    return s

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()

def validate():
    p9.preflight(O,S,p9.REPORT)
    source={}
    for rel in FILES:
        f=S/rel
        if not f.is_file() or f.is_symlink():raise RuntimeError('P65_STAGE_SOURCE_MISSING_'+rel)
        source[rel]=f.read_text('utf8')
        if MARK in source[rel]:raise RuntimeError('P65_ALREADY_APPLIED_'+rel)
    if (S/CSS_PATH).exists() or (S/CSS_PATH).is_symlink():
        raise RuntimeError('P65_CSS_ALREADY_EXISTS')
    required={
      HTML:('HIGHFLY_P48_FURY_MOBILE','mobile-dodge','mobile-jump'),
      MOBILE:('HIGHFLY_P48_FURY_MOBILE','buildMobileMenuControl','onGroundAimTap'),
      MAIN:('onCycleTarget: () => world.tabTarget(),','function resolveMove('),
    }
    for rel,items in required.items():
        for item in items:
            if item not in source[rel]:raise RuntimeError('P65_PREREQUISITE_MISSING_'+rel+'_'+item)
    if 'HIGHFLY_P63_COMBAT_C1' not in (S/'src/sim/combat/auto_attack.ts').read_text('utf8'):
        raise RuntimeError('P65_REQUIRES_COMBAT_C1')
    if 'HIGHFLY_P64_REAL_BOAR_CC0' not in (S/'src/render/characters/manifest.ts').read_text('utf8'):
        raise RuntimeError('P65_REQUIRES_REAL_BOAR_CCO')
    updated={HTML:patch_html(source[HTML]),
             MOBILE:patch_mobile(source[MOBILE]),
             MAIN:patch_main(source[MAIN]),CSS_PATH:CSS}
    return source,updated

def run(apply=False):
    original,updated=validate()
    status={'phase':'P65_HIGHFLY_MOBILE_COMBAT_HUD_C2','mode':'DRY_RUN',
       'loadingViewport':'100dvh cover (browser chrome can only hide after user gesture)',
       'playerBars':'native HP/MP/energy frame, top-left',
       'menu':'3 dots top-left -> existing real centered grid with bags/map/character/skills',
       'buttons':'PASIVA opens real spellbook; SALTAR native; EVADIR P48; S1 existing real slot 0',
       'combat':'tapping a visible attackable monster acquires and arms native Sim attack',
       'movement':'mobile camera-relative 360deg direction facing (no backpedal)',
       'boars':'P64 rig stays, no changes to AI/loot/quests',
       'protectedRPGFilesChanged':False,'browserVerified':False,
       'fullyPremiumFinalCompleted':False}
    if not apply:
        print('[HIGHFLY P65] '+json.dumps(status,ensure_ascii=False,indent=2));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():raise RuntimeError('P65_BACKUPS_UNSAFE')
        if (OUT/'P65_STATUS.json').exists():raise RuntimeError('P65_ALREADY_BUILT')
        past=OUT.parent/'highfly-p65-attempts'
        if past.is_symlink():raise RuntimeError('P65_ATTEMPT_ARCHIVE_UNSAFE')
        past.mkdir(parents=True,exist_ok=True)
        OUT.rename(past/('attempt-'+str(time.time_ns())))
    backup=[];created=[]
    try:
        for rel in FILES:
            f=S/rel;bak=OUT/'backups'/rel
            bak.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(f,bak)
            if sha(f)!=sha(bak):raise RuntimeError('P65_BACKUP_FAILED_'+rel)
            backup.append((f,bak))
        for rel,text in updated.items():
            p=S/rel
            if rel in original:
                if p.read_text('utf8')!=original[rel]:
                    raise RuntimeError('P65_CONCURRENT_CHANGE_'+rel)
                p.write_text(text,encoding='utf8')
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('x',encoding='utf8') as w:w.write(text)
                created.append(p)
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],
           cwd=ROOT,check=True)
    except BaseException:
        for p,bak in backup:
            if bak.is_file():shutil.copy2(bak,p)
        for p in created:
            if p.is_file():p.unlink()
        print('[HIGHFLY P65] RED — restored P64 stage from backups',file=sys.stderr)
        raise
    status['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P65_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    print('[HIGHFLY P65] '+json.dumps(status,indent=2,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true')
    run(p.parse_args().apply)
