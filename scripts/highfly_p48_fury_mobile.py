#!/usr/bin/env python3
"""P48: mobile FURY gameplay first pass + loading/branding repair.

Actual offline Sim movement (double jump, collision-aware timed dash),
touch-button input and removal of joystick autorun. Avoids fake buttons.
Uses existing P46 official image assets and real engine loading counter.
Does not change NPC quests, saves, items, tutorials, or online server.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE;OUT=ROOT/".workspace/reports/highfly-p48"
MARK="HIGHFLY_P48_FURY_MOBILE"
FILES=("src/game/mobile_controls.ts","src/game/input.ts","src/sim/types.ts",
       "src/sim/player_motion.ts","src/render/characters/visual.ts","index.html")
CSS_PATH="public/highfly/p48.css"
JS_PATH="public/highfly/p48.js"
CSS=r"""
/* HIGHFLY_P48_FURY_MOBILE: the original loading background contains a baked
   black rectangle in its lower half. Cover that region with our own existing
   HIGHFLY splash landscape instead of pretending CSS can erase its pixels. */
#loading-screen::before {
 content:""!important;display:block!important;position:absolute!important;
 inset:48% 0 0!important;z-index:0!important;pointer-events:none!important;
 background:url('/highfly/official/highfly_splash.png') center 78%/cover no-repeat!important;
 -webkit-mask-image:linear-gradient(to bottom,transparent 0%,#000 33%,#000 100%)!important;
 mask-image:linear-gradient(to bottom,transparent 0%,#000 33%,#000 100%)!important;
}
#loading-screen .ls-progress {
 position:absolute!important;z-index:1!important;
 left:50%!important;right:auto!important;top:auto!important;bottom:3.5dvh!important;
 transform:translateX(-50%)!important;
 width:min(880px,80vw)!important;height:112px!important;
 padding:0!important;margin:0!important;gap:0!important;
 background:none!important;background-color:transparent!important;
 border:0!important;box-shadow:none!important;outline:0!important;
 backdrop-filter:none!important;
 display:block!important;overflow:visible!important;
}
#loading-screen #ls-status {
 display:block!important;position:absolute!important;top:0!important;left:0!important;
 width:100%!important;height:29px!important;margin:0!important;padding:0!important;
 text-align:center!important;background:none!important;
 color:#fff3ef!important;text-shadow:0 2px 8px #000,0 0 14px #c543fc!important;
 font:700 clamp(14px,2.2vw,25px)/29px Georgia,serif!important;
}
#loading-screen .ls-bar {
 display:block!important;position:absolute!important;top:34px!important;
 left:0!important;right:0!important;width:100%!important;height:19px!important;
 padding:0!important;margin:0!important;
 border:2px solid #ffca80!important;border-radius:20px!important;
 background:#100824b5!important;box-shadow:0 0 17px #ba51f988!important;
 overflow:hidden!important;
}
#loading-screen #ls-fill {
 display:block!important;height:100%!important;border-radius:20px!important;
 background:linear-gradient(90deg,#6023d7,#ad40ec,#ffade4)!important;
 transition:width .13s linear!important;
}
#loading-screen #ls-tip {
 display:block!important;position:absolute!important;top:61px!important;left:0!important;
 right:0!important;width:100%!important;max-height:43px!important;
 height:43px!important;min-height:43px!important;margin:0!important;
 padding:6px 10px!important;box-sizing:border-box!important;overflow:hidden!important;
 border:0!important;border-radius:0!important;background:none!important;
 color:#f5d9fc!important;text-shadow:0 2px 7px #000!important;
 text-align:center!important;font:clamp(11px,1.1vw,13px)/16px Arial,sans-serif!important;
}
#loading-screen #ls-slow-hint {
 display:none!important;
}
/* The persistent developer QA overlay is still available from the console,
   but not on top of players' final HUD/splash. */
#highfly-log-widget,
#highfly-log,
.highfly-log-badge,
#highfly-p35-diagnostics,
.highfly-p35-badge,
#highfly-debug-overlay {display:none!important}
/* A true tap-to-dash button, placed beside the existing skills and jump. */
@media (pointer:coarse) and (orientation:landscape){
 html,body,#game-canvas{touch-action:none!important;overscroll-behavior:none!important}
 #mobile-autorun-target{display:none!important;pointer-events:none!important}
 #mobile-dodge {
   position:fixed!important;z-index:2147482000!important;
   right:25.5vw!important;bottom:max(6.5dvh,35px)!important;
   width:clamp(45px,6.2vw,66px)!important;height:clamp(45px,6.2vw,66px)!important;
   padding:0!important;border-radius:50%!important;
   border:2px solid #7bd9ff!important;
   background:radial-gradient(circle at 35% 30%,#3856aaf0,#09142deb)!important;
   box-shadow:0 0 14px #439ffca3!important;
   color:#fff!important;font:700 9px Arial!important;
   touch-action:none!important;user-select:none!important;
 }
 #mobile-dodge::before{content:"➜";display:block;font:700 23px Arial;line-height:24px}
 #mobile-action-ring .mobile-action-slot{opacity:1!important;min-width:40px;min-height:40px}
 #mobile-action-attack{box-shadow:0 0 12px #348fffff!important}
 #mobile-move-zone,#mobile-move-joystick{touch-action:none!important}
}
@media (max-height:430px) and (orientation:landscape){
 #mobile-dodge{right:27vw!important;bottom:4dvh!important}
 #loading-screen .ls-progress{bottom:1.8dvh!important;height:90px!important}
 #loading-screen #ls-status{height:23px!important;line-height:23px!important;font-size:14px!important}
 #loading-screen .ls-bar{top:26px!important;height:14px!important}
 #loading-screen #ls-tip{top:48px!important;height:37px!important}
}
"""
JS=r"""
// HIGHFLY_P48_FURY_MOBILE: request fullscreen in the FIRST real gesture.
// Regular Chrome cannot force fullscreen before a user's tap; an installed
// Android PWA with display:fullscreen is the separate zero-chrome launch path.
(function(){
'use strict';
function fullScreenFromGesture(){
 const p=document.documentElement;
 if(document.fullscreenElement||!p.requestFullscreen)return;
 const answer=p.requestFullscreen({navigationUI:'hide'});
 if(answer&&typeof answer.catch==='function')answer.catch(()=>{});
}
const splash=document.getElementById('highfly-p46-landing');
if(splash) splash.addEventListener('pointerup',fullScreenFromGesture,{once:true,capture:true});
else document.addEventListener('pointerup',function first(e){
 if(e.target&&e.target.closest&&e.target.closest('#highfly-p46-landing button,#btn-play,#btn-start-offline')){
   document.removeEventListener('pointerup',first,true);fullScreenFromGesture();
 }
},true);
})();
"""
def once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError("P48_ANCHOR_DRIFT "+label+" count="+str(n))
 return s.replace(old,new,1)
def patch(data):
 if any(MARK in s for s in data.values()):raise RuntimeError("P48_ALREADY_APPLIED")
 m=data[FILES[0]]
 start="    const inAutorunTarget = isMoveAutorunPush(rawY);\n"
 end="    this.syncMoveAutorunTarget(isMoveAutorunNear(rawY) ? 'near' : 'hidden');"
 a=m.find(start);b=m.find(end,a)
 if a<0 or b<0 or m.count(start)!=1 or m.count(end)!=1 or b-a>2300:
  raise RuntimeError("P48_AUTORUN_SECTION_DRIFT")
 new="""    // HIGHFLY_P48_FURY_MOBILE: no autorun from joystick overshoot.
    // Always interpret thumb displacement as directional analog movement.
    this.moveAutorunLocked = false;
    this.input.setAutorun(false);
    this.input.setTouchMove(move);
    this.syncMoveAutorunTarget('hidden');"""
 m=m[:a]+new+m[b+len(end):]
 m=once(m,
  "    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });",
  "    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });\n"
  "    // "+MARK+": real sim dash via touch input latch.\n"
  "    this.bindButton('mobile-dodge', () => this.input.triggerTouchDash(), { pressFirst: true });",
  "mobile-dash-binding")
 inp=data[FILES[1]]
 inp=once(inp,"  autorun = false;\n  suspendMovement = false;",
  "  autorun = false;\n  // "+MARK+": one touch dash latch, shared with gamepad/keyboard movement.\n"
  "  private touchDashUntil = 0;\n  suspendMovement = false;","input-field")
 inp=once(inp,"  /** Touch/controller swim-down, held for as long as the control is pressed. */",
  "  // "+MARK+": buffered through input reads until a real sim tick can observe it.\n"
  "  triggerTouchDash(): void {\n    this.touchDashUntil = Math.max(this.touchDashUntil, performance.now() + 120);\n  }\n\n"
  "  /** Touch/controller swim-down, held for as long as the control is pressed. */","input-dash-method")
 inp=once(inp,"    this.touchJumpUntil = 0;\n    this.autorun = false;",
  "    this.touchJumpUntil = 0;\n    this.touchDashUntil = 0;\n    this.autorun = false;","input-reset")
 inp=once(inp,"      performance.now() <= this.keyJumpUntil;\n",
  "      performance.now() <= this.keyJumpUntil;\n"
  "    const dash = performance.now() <= this.touchDashUntil;\n","input-read-dash")
 inp=once(inp,"        jump,\n        dive,\n        surface,",
  "        jump,\n        dash,\n        dive,\n        surface,","input-return-mouselook")
 inp=once(inp,"      jump,\n      dive,\n      surface,",
  "      jump,\n      dash,\n      dive,\n      surface,","input-return-normal")
 ty=once(data[FILES[2]],"  jump: boolean;\n  /** Swim DOWN.",
  "  jump: boolean;\n  // "+MARK+": optional, absent in original online packets.\n"
  "  dash?: boolean;\n  /** Swim DOWN.","moveinput-optional-dash")
 motion=data[FILES[3]]
 motion=once(motion,"export const AIR_CONTROL_ACCEL = 20;",
  "export const AIR_CONTROL_ACCEL = 20;\n"
  "// "+MARK+": ephemeral state keyed to the original Entity, no save changes.\n"
  "const highflyAirJumps = new WeakSet<Entity>();\n"
  "const highflyJumpHeld = new WeakMap<Entity,boolean>();\n"
  "const highflyDashes = new WeakMap<Entity,{active:number;cooldown:number;x:number;z:number}>();",
  "motion-state")
 motion=once(motion,"  const movingOnGround = moving && (p.onGround || swimming);",
  """  // HIGHFLY_P48_FURY_MOBILE: real timed dash uses the existing swept
  // movement/collision kernel. No teleport and no bypass of walls.
  let furyDash = highflyDashes.get(p);
  if (!furyDash) {
    furyDash = {active:0,cooldown:0,x:0,z:0};
    highflyDashes.set(p,furyDash);
  }
  furyDash.cooldown = Math.max(0,furyDash.cooldown-DT);
  if (inp.dash && furyDash.cooldown<=0 && p.onGround &&
      !swimming && !isRooted(p) && !isStunned(p)) {
    const dir = Math.hypot(wishX,wishZ);
    furyDash.x = dir>0.01 ? wishX/dir : Math.sin(p.facing);
    furyDash.z = dir>0.01 ? wishZ/dir : Math.cos(p.facing);
    furyDash.active = 0.18;
    furyDash.cooldown = 1.15;
  }
  const furyDashing = furyDash.active>0 && p.onGround && !swimming &&
    !isRooted(p) && !isStunned(p);
  if (furyDashing) {
    wishX=furyDash.x;wishZ=furyDash.z;
    wishSpeed=RUN_SPEED * deps.moveSpeedMult(p)*2.6;
    furyDash.active=Math.max(0,furyDash.active-DT);
  } else furyDash.active=0;
  const movingOnGround = (moving || furyDashing) && (p.onGround || swimming);""",
  "motion-real-dash")
 motion=once(motion,
  "  if (inp.jump && (p.onGround || coyote) && !isRooted(p) && !steepGround && !mountLocked) {\n    p.vy = JUMP_VELOCITY * jumpMult(p);",
  """  // HIGHFLY_P48_FURY_MOBILE: second jump requires a *new tap* in the air.
  // A held jump may not consume both jumps on consecutive physics ticks.
  const previousJumpHeld = highflyJumpHeld.get(p) ?? false;
  const freshJump = inp.jump && !previousJumpHeld;
  highflyJumpHeld.set(p, inp.jump);
  if (p.onGround) highflyAirJumps.delete(p);
  const secondJump = freshJump && !p.onGround && p.jumping &&
    !highflyAirJumps.has(p);
  if (inp.jump && (p.onGround || coyote || secondJump) &&
      !isRooted(p) && !steepGround && !mountLocked) {
    if (secondJump) highflyAirJumps.add(p);
    else highflyAirJumps.delete(p);
    p.vy = JUMP_VELOCITY * jumpMult(p) * (secondJump ? 0.88 : 1);""",
  "motion-double-jump")
 visual=data[FILES[4]]
 visual=once(visual,
  "      (proneAngle + swimPitch) * this.swimBlend + this.lean + CLIMB_BODY_PITCH * climb * climbLevel;",
  "      Math.max(-0.55,Math.min(0.55,(proneAngle + swimPitch) * this.swimBlend + this.lean + CLIMB_BODY_PITCH * climb * climbLevel));\n"
  "    // "+MARK+": pitch clamp prevents a full forward somersault in ledge climbs.",
  "climb-pitch-safety")
 visual=once(visual,"        this.climbHeadBone.rotation.x += CLIMB_HEAD_TILT_RAD * look * this.climbBlend;",
  "        this.climbHeadBone.rotation.x = Math.max(-0.5,Math.min(0.5,\n"
  "          this.climbHeadBone.rotation.x + CLIMB_HEAD_TILT_RAD * look * this.climbBlend));",
  "climb-baked-head-clamp")
 visual=once(visual,"      this.climbHeadBone.rotation.x += CLIMB_HEAD_TILT_RAD * look * k;",
  "      this.climbHeadBone.rotation.x = Math.max(-0.5,Math.min(0.5,\n"
  "        this.climbHeadBone.rotation.x + CLIMB_HEAD_TILT_RAD * look * k));",
  "climb-manual-head-clamp")
 html=data[FILES[5]]
 html=once(html,
  '<button type="button" id="mobile-jump" data-i18n-title=',
  '<button type="button" id="mobile-dodge" aria-label="Evadir y desplazarse" title="Evadir" data-icon="dash">EVADIR</button>\n'
  '<button type="button" id="mobile-jump" data-i18n-title=',
  "dodge-button")
 html=once(html,"</head>",
  '<!-- '+MARK+': mobile gameplay and loading overlay, no fake bars -->\n'
  '<link rel="stylesheet" href="/highfly/p48.css" />\n'
  '<script defer src="/highfly/p48.js"></script>\n'
  '</head>',"head-link")
 return dict(zip(FILES,(m,inp,ty,motion,visual,html)))
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 original={}
 for rel in FILES:
  f=STAGE/rel
  if not f.is_file() or f.is_symlink():raise RuntimeError("P48_STAGE_FILE_MISSING "+rel)
  original[rel]=f.read_text(encoding="utf8")
 if "HIGHFLY_P47_UI_LOOT_REAL_EDITOR" not in original["index.html"]:
  raise RuntimeError("P48_REQUIRES_P47")
 changed=patch(original)
 for rel in (CSS_PATH,JS_PATH):
  if (STAGE/rel).exists() or (STAGE/rel).is_symlink():
   raise RuntimeError("P48_ALREADY_HAS_ASSET "+rel)
 result={"phase":"P48_FURY_MOBILE_FIRST_REAL_MOVEMENT","mode":"DRY_RUN",
  "mobileAutorunDisabled":True,"collisionAwareDodgeButton":True,
  "doubleJumpSecondNewTap":True,"climbRotationClamped":True,
  "loadingBarsUseNativeCounters":True,"loadingBakedBlackCoveredWithExistingArtwork":True,
  "originalMediaNotModified":True,"questsAndSavesUnchanged":True,
  "boarModelProvenanceUnresolved":True,"fullCombatFurySkillWiringDone":False,
  "androidBrowserVerified":False}
 if not apply:
  print("[HIGHFLY] P48 "+json.dumps(result));return result
 for rel in FILES:
  backup=OUT/"backup"/rel
  if backup.exists() or backup.is_symlink():raise RuntimeError("P48_BACKUP_EXISTS "+rel)
 for rel in FILES:
  f=STAGE/rel;backup=OUT/"backup"/rel
  backup.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(f,backup)
  if hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
   raise RuntimeError("P48_BACKUP_BAD "+rel)
 created=[]
 try:
  for rel,source in ((CSS_PATH,CSS),(JS_PATH,JS)):
   target=STAGE/rel
   target.parent.mkdir(parents=True,exist_ok=True)
   with target.open("x",encoding="utf8") as out:out.write(source)
   created.append(target)
  for rel in FILES:
   f=STAGE/rel
   if f.read_text(encoding="utf8")!=original[rel]:raise RuntimeError("P48_CONCURRENT_STAGE_EDIT "+rel)
   f.write_text(changed[rel],encoding="utf8")
  subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
    cwd=ROOT,check=True)
 except BaseException:
  for rel in FILES:
   backup=OUT/"backup"/rel
   if backup.is_file():shutil.copy2(backup,STAGE/rel)
  for f in created:
   if f.is_file() and not f.is_symlink():f.unlink()
  print("[HIGHFLY] P48: reverted to P47 stage",file=sys.stderr)
  raise
 result["mode"]="BUILD_GREEN_NOT_ANDROID_VERIFIED"
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"P48_STATUS.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("[HIGHFLY] P48 "+json.dumps(result))
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
