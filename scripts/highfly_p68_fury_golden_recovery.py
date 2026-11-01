#!/usr/bin/env python3
"""HIGHFLY P68 — FURY GOLDEN 360 precision and native soft-target stabilization.
One guarded private-stage pass on P66/P67. No fake skills, assets or hit tables.
"""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
S=p9.STAGE; O=p9.ORIGINAL
HTML="index.html"; MAIN="src/main.ts"; INPUT="src/game/input.ts"
MOBILE="src/game/mobile_controls.ts"; RING="src/ui/hud/action_bar/mobile_action_ring_controller.ts"
CSS_PATH="public/highfly/p68_fury_recovery.css"
MARK="HIGHFLY_P68_FURY_GOLDEN_RECOVERY"
OUT=ROOT/".workspace/reports/highfly-p68-fury-golden-recovery"
FILES=(HTML,MAIN,INPUT,MOBILE,RING)

CSS=r"""/* HIGHFLY P68 — fix actual problems visible in the 01/11 Android video.
   Real loading state, real native skill icons, real on-screen touch actions. */
body.mobile-touch #loading-screen .ls-progress,
#loading-screen .ls-progress {
  left:50%!important;right:auto!important;
  bottom:max(5px,env(safe-area-inset-bottom))!important;
  transform:translateX(-50%)!important;
  display:grid!important;grid-template-columns:1fr!important;
  grid-template-rows:17px 11px minmax(20px,1fr)!important;
  align-items:center!important;justify-items:stretch!important;
  row-gap:3px!important;
  width:min(780px,90vw)!important;height:76px!important;
  padding:7px 18px!important;
  box-sizing:border-box!important;overflow:hidden!important;
  border:1px solid rgba(199,153,247,.85)!important;
  background:linear-gradient(140deg,rgba(7,7,25,.97),rgba(30,13,55,.95))!important;
  border-radius:12px!important;
}
#loading-screen .ls-progress #ls-status,
#loading-screen .ls-progress .ls-bar,
#loading-screen .ls-progress #ls-tip {
  position:static!important;inset:auto!important;
  transform:none!important;max-width:100%!important;
  min-width:0!important;box-sizing:border-box!important;
}
#loading-screen .ls-progress #ls-status{
  grid-row:1!important;width:100%!important;height:17px!important;
  margin:0!important;padding:0!important;
  color:#faf0ff!important;font:700 12px/17px system-ui!important;
  text-align:center!important;white-space:nowrap!important;
}
#loading-screen .ls-progress .ls-bar{
  grid-row:2!important;width:100%!important;height:11px!important;
  margin:0!important;padding:0!important;
  border-radius:8px!important;overflow:hidden!important;
}
#loading-screen .ls-progress #ls-tip{
  grid-row:3!important;display:flex!important;align-items:center!important;
  justify-content:center!important;
  width:100%!important;max-height:25px!important;min-height:0!important;
  height:auto!important;margin:0!important;padding:0 8px!important;
  border:0!important;background:none!important;
  text-align:center!important;white-space:normal!important;
  font:10px/12px system-ui!important;color:#eee0fb!important;
}
body.mobile-touch.game-active #mobile-action-ring
:is(#mobile-passive,#mobile-jump,#mobile-dodge,.mobile-action-slot[data-mobile-index="0"]){
  background:radial-gradient(circle at 30% 20%,#49356c 0%,#23143c 60%,#0c0b26 100%)!important;
  border:2px solid #a888eb!important;
  color:#f8eaff!important;
  box-shadow:0 0 0 2px #090920 inset,0 0 12px rgba(155,102,244,.4)!important;
  filter:none!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-dodge::before{
  color:#f8eaff!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive{
  font-size:0!important;
}
body.mobile-touch.game-active #mobile-action-ring #mobile-passive::after{
  content:"PAS"!important;display:block!important;color:#f8eaff!important;
  font:700 10px/1 system-ui!important;
}
body.mobile-touch.game-active #mobile-extra-controls{
  border:2px solid #b090fa!important;
  background:linear-gradient(150deg,#241342,#110f30 65%,#090e23)!important;
  box-shadow:0 0 0 3px rgba(4,6,23,.85) inset,0 0 25px rgba(119,74,196,.25),0 15px 35px #04050d!important;
}
body.mobile-touch.game-active #mobile-extra-grid .mobile-btn{
  background:linear-gradient(145deg,#332354,#1b1741)!important;
  border:1px solid rgba(166,129,235,.75)!important;
  box-shadow:0 1px 8px rgba(0,0,0,.28)!important;
  border-radius:10px!important;
  color:#eee3ff!important;
}
@media(max-height:430px) and (orientation:landscape){
 #loading-screen .ls-progress{height:65px!important;
   grid-template-rows:14px 10px minmax(18px,1fr)!important;
   row-gap:2px!important;padding:5px 12px!important}
 #loading-screen .ls-progress #ls-status{height:14px!important;font-size:10px!important;line-height:14px!important}
 #loading-screen .ls-progress .ls-bar{height:10px!important}
 #loading-screen .ls-progress #ls-tip{font-size:9px!important;line-height:11px!important}
}
""".strip()+"\n"

def once(src,old,new,label):
    count=src.count(old)
    if count!=1:
        raise RuntimeError("P68_SOURCE_DRIFT_"+label+"_"+str(count))
    return src.replace(old,new,1)

def patch_html(s):
    return once(s,"</head>",
       "<!-- "+MARK+": loading tips and physical touch visual harmonization -->\n"
       '<link rel="stylesheet" href="/highfly/p68_fury_recovery.css" />\n'
       "</head>","HEAD")

def patch_input(s):
    s=once(s,"  strafeRight: boolean;\n}\n\nexport interface InputDebugState {",
      """  strafeRight: boolean;
  /** HIGHFLY GOLDEN 360: raw, normalized touch stick X, Y (Y=forward). */
  analogX?: number;
  analogY?: number;
}

export interface InputDebugState {""","ANALOG_INTERFACE")
    s=once(s,"  setTouchMove(move: TouchMoveInput): void {",
      """  // HIGHFLY_P68_FURY_GOLDEN_RECOVERY: use uninterrupted stick angle.
  // This is NOT a camera input. Zero vector on release/suspend.
  getHighflyTouchAnalog(): {x:number;y:number}|null {
    if(this.suspendMovement) return null;
    const m=this.touchMove;
    const x=m.analogX??0, y=m.analogY??0;
    if(!Number.isFinite(x)||!Number.isFinite(y)||Math.hypot(x,y)<0.18)
      return null;
    return {x,y};
  }

  setTouchMove(move: TouchMoveInput): void {""","STICK_GETTER")
    return s

def patch_mobile(s):
    return once(s,
      "    this.input.setTouchMove(move);",
      """    // HIGHFLY_P68_FURY_GOLDEN_RECOVERY: preserve exact circular
    // analog thumb vector; flags are still sent for native movement intent.
    this.input.setTouchMove({...move,analogX:x,analogY:-y});""",
      "MOVE_VECTOR")

def patch_main(s):
    old="""      const horizontal=Number(mi.strafeRight)-Number(mi.strafeLeft);
      const vertical=Number(mi.forward)-Number(mi.back);
      if (horizontal!==0 || vertical!==0) {
        const yaw=input.camYaw;
        const worldX=vertical*Math.sin(yaw)-horizontal*Math.cos(yaw);
        const worldZ=vertical*Math.cos(yaw)+horizontal*Math.sin(yaw);
        facing=Math.atan2(worldX,worldZ);
        mi.forward=true;mi.back=false;
        mi.strafeLeft=false;mi.strafeRight=false;
      }"""
    new="""      // HIGHFLY_P68_FURY_GOLDEN_RECOVERY: continuous analog 360°.
      // P65 used -horizontal*cos(yaw), +horizontal*sin(yaw):
      // a RIGHT thumb push walked LEFT; diagonals also collapsed to 8 sectors.
      const touch=input.getHighflyTouchAnalog();
      const horizontal=touch?.x??(Number(mi.strafeRight)-Number(mi.strafeLeft));
      const vertical=touch?.y??(Number(mi.forward)-Number(mi.back));
      if (horizontal!==0 || vertical!==0) {
        const yaw=input.camYaw;
        const worldX=vertical*Math.sin(yaw)+horizontal*Math.cos(yaw);
        const worldZ=vertical*Math.cos(yaw)-horizontal*Math.sin(yaw);
        facing=Math.atan2(worldX,worldZ);
        mi.forward=true;mi.back=false;
        mi.strafeLeft=false;mi.strafeRight=false;
      }"""
    s=once(s,old,new,"TRUE_360_VECTOR")
    # No 40-yard surprise aggro: soft pick the closest living hostile in
    # the 15yd approach window, regardless of which way the camera faces.
    s=once(s,"    let bestD = 40;\n    for (const e of world.entities.values()) {",
       """    // HIGHFLY_P68_FURY_GOLDEN_RECOVERY: 360 soft-target without
    // a forced manual lock. Nearest hostile in reasonable assist range.
    let bestD = 15;
    for (const e of world.entities.values()) {""","SOFT_TARGET_RANGE")
    return s

def patch_ring(s):
    old="""    if(!(hfTap.autoAttack&&hfTap.hasLiveHostileTarget)){
      handleMobileAttackTap(hfTap,{
        activateAttack:()=>deps.activateFixedAttackSlot(),
        attackNearest:deps.attackNearest,
      });
    }"""
    new="""    // HIGHFLY_P68_FURY_GOLDEN_RECOVERY: ATK should NEVER require
    // manually selecting a front-facing target beforehand. Native nearest
    // hostile acquisition handles mobile targetless/stale attacks.
    // Keep the P63 guard so repeated presses don't toggle combat off.
    if(!(hfTap.autoAttack&&hfTap.hasLiveHostileTarget)){
      if(deps.attackNearest) deps.attackNearest();
      else handleMobileAttackTap(hfTap,{
        activateAttack:()=>deps.activateFixedAttackSlot(),
        attackNearest:null,
      });
    }"""
    return once(s,old,new,"MOBILE_ATK_ACQUIRE")

def sha(f):
    h=hashlib.sha256()
    with f.open("rb") as stream:
        for b in iter(lambda:stream.read(1048576),b""):h.update(b)
    return h.hexdigest()

def validate():
    p9.preflight(O,S,p9.REPORT)
    d={}
    for rel in FILES:
        p=S/rel
        if p.is_symlink() or not p.is_file():
            raise RuntimeError("P68_MISSING_"+rel)
        d[rel]=p.read_text("utf8")
        if MARK in d[rel]:raise RuntimeError("P68_ALREADY_INSTALLED_"+rel)
    if (S/CSS_PATH).exists() or (S/CSS_PATH).is_symlink():
        raise RuntimeError("P68_CSS_ALREADY_INSTALLED")
    if "HIGHFLY_P66_P67_COMBAT_FEEL_PREMIUM" not in d[MAIN]:
        raise RuntimeError("P68_REQUIRES_P67_STAGE")
    if "HIGHFLY_P63_COMBAT_C1" not in d[RING]:
        raise RuntimeError("P68_REQUIRES_P63_RING")
    if "HIGHFLY_P64_REAL_BOAR_CC0" not in (S/"src/render/characters/manifest.ts").read_text("utf8"):
        raise RuntimeError("P68_REQUIRES_P64_BOAR")
    update={HTML:patch_html(d[HTML]),MAIN:patch_main(d[MAIN]),
            INPUT:patch_input(d[INPUT]),MOBILE:patch_mobile(d[MOBILE]),
            RING:patch_ring(d[RING]),CSS_PATH:CSS}
    return d,update

def run(apply=False):
    old,new=validate()
    state={"phase":"P68_FURY_GOLDEN_RECOVERY","mode":"DRY_RUN",
      "movement":"exact analog angle with corrected right-axis + camera-relative 360",
      "joystickCamera":"P67 keeps camera independent; this patch never writes yaw",
      "softTarget":"ATK acquires nearest real hostile <=15 units without manual marking",
      "combat":"P63 damage, fourth impact and P64 boar unchanged",
      "loading":"dedicated centered grid so tip cannot escape left of HUD",
      "hud":"passive jump dodge S1 share one violet theme",
      "skills":"native cooldown/aim remains; FURY F1 gesture integration separately pending",
      "p66P67Retained":True,"browserVerified":False,
      "fullFourTapComboCompleted":False,
      "noNewUnlicensedMedia":True}
    if not apply:
        print("[HIGHFLY P68] "+json.dumps(state,ensure_ascii=False,indent=2));return
    if OUT.is_symlink():raise RuntimeError("P68_BACKUP_UNSAFE")
    if OUT.exists():
        if not OUT.is_dir():raise RuntimeError("P68_BACKUP_BAD")
        if (OUT/"P68_STATUS.json").exists():raise RuntimeError("P68_ALREADY_SUCCESSFUL")
        archive=OUT.parent/"highfly-p68-preserved-attempts"
        if archive.is_symlink():raise RuntimeError("P68_ARCHIVE_UNSAFE")
        archive.mkdir(parents=True,exist_ok=True)
        OUT.rename(archive/("attempt-"+str(time.time_ns())))
    backups=[];created=[]
    try:
        for rel in FILES:
            src=S/rel; dest=OUT/"backups"/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dest)
            if sha(src)!=sha(dest):raise RuntimeError("P68_BAD_BACKUP_"+rel)
            backups.append((src,dest))
        for rel,code in new.items():
            dest=S/rel
            if rel in old:
                if dest.read_text("utf8")!=old[rel]:
                    raise RuntimeError("P68_CONCURRENT_SOURCE_"+rel)
                dest.write_text(code,"utf8")
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open("x",encoding="utf8") as w:w.write(code)
                created.append(dest)
        subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
                      cwd=ROOT,check=True)
    except BaseException:
        for src,bak in backups:
            if bak.is_file():shutil.copy2(bak,src)
        for dest in created:
            if dest.is_file():dest.unlink()
        print("[HIGHFLY P68] RED: restored P67 stage",file=sys.stderr)
        raise
    state["mode"]="BUILD_GREEN_BROWSER_PENDING"
    (OUT/"P68_STATUS.json").write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n","utf8")
    print("[HIGHFLY P68] "+json.dumps(state,ensure_ascii=False,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
    run(p.parse_args().apply)
