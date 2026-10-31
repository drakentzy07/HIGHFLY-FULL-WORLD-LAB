#!/usr/bin/env python3
"""P45C: FURY mobile visuals + pure deterministic combat core; no fake attacks.

Leverages ClaudeCraft's native touch router / ring / camera / jump. Does NOT
install a second joystick, break existing actions, alter damage, or claim the
four-hit combo is playable before wiring to sim/render in the next phase.
Audits missing item icon references and mobile hook readiness.
"""
import argparse,csv,hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p45-fury"
FILE="src/game/highfly_fury_core.ts"
CSS_FILE="public/highfly_fury_mobile.css"
MARK="HIGHFLY_P45_FURY_FOUNDATION"
TS="""
// HIGHFLY_P45_FURY_FOUNDATION: pure deterministic future combat pipeline.
// No DOM, no class bonuses, no fake visual steps or actual sim damage yet.
// The next phase will wire this to existing Input, Sim and Animation dispatch.
export const FURY_COMBO_RESET_MS = 780;
export const FURY_COMBO_MIN_MS = 85;
export const FURY_DASH_COOLDOWN_MS = 1200;
export const FURY_DASH_RANGE = 5.2;
export type FuryStep = 1 | 2 | 3 | 4;
export interface FuryCombo {
  step: FuryStep | 0;
  lastAttackMs: number;
  finisher: boolean;
}
export interface FuryDash {
  x: number;
  z: number;
  allowed: boolean;
  nextReadyMs: number;
}
export type FuryResource = 'mp' | 'energy';
export interface FurySkill {
  cooldownMs: number;
  resource: FuryResource;
  cost: number;
}
export function furyAdvanceCombo(prev: FuryCombo, nowMs: number): FuryCombo {
  const elapsed = nowMs - prev.lastAttackMs;
  const chained = prev.step !== 0 &&
    elapsed >= FURY_COMBO_MIN_MS &&
    elapsed <= FURY_COMBO_RESET_MS;
  const next: FuryStep = chained ? ((prev.step % 4) + 1) as FuryStep : 1;
  return {step: next, lastAttackMs: nowMs, finisher: next === 4};
}
export function furyDirectionalDash(
  moveX: number, moveZ: number, facingX: number, facingZ: number,
  nowMs: number, readyAtMs: number,
): FuryDash {
  if (nowMs < readyAtMs) return {x:0,z:0,allowed:false,nextReadyMs:readyAtMs};
  const mx = Number.isFinite(moveX) ? moveX : 0;
  const mz = Number.isFinite(moveZ) ? moveZ : 0;
  let x = mx, z = mz;
  if (Math.hypot(x,z) < 0.15) {x=facingX;z=facingZ;}
  const len = Math.hypot(x,z);
  if (!Number.isFinite(len) || len < 0.0001) {x=0;z=1;}
  else {x/=len;z/=len;}
  return {x:x*FURY_DASH_RANGE,z:z*FURY_DASH_RANGE,allowed:true,
    nextReadyMs:nowMs+FURY_DASH_COOLDOWN_MS};
}
export function furyCanUseSkill(
  spec:FurySkill,readyAtMs:number,nowMs:number,mp:number,energy:number,
): boolean {
  if (nowMs<readyAtMs || !Number.isFinite(spec.cost)) return false;
  return spec.resource==='mp' ? mp>=spec.cost : energy>=spec.cost;
}
export function furySkillReadyAt(spec:FurySkill,nowMs:number):number {
  return nowMs+Math.max(0,spec.cooldownMs);
}
""".strip()+"\n"
CSS="""
/* HIGHFLY_P45_FURY_FOUNDATION: styling the EXISTING mobile controls only.
   Never override their position or touch routing. Keep two-thumb gestures. */
@media (pointer:coarse) and (orientation:landscape) {
  #mobile-action-attack {
    border:2px solid #7ddfff !important;
    box-shadow:0 0 14px #16befc80, inset 0 0 11px #175da270 !important;
    background-color:#052b53b8 !important;
  }
  #mobile-action-ring .mobile-action-slot {
    border:1px solid #a37aff !important;
    box-shadow:inset 0 0 8px #4245d450 !important;
  }
  #mobile-jump {
    border:1px solid #56e6ef !important;
    box-shadow:0 0 9px #0db8dd55 !important;
  }
  #mobile-move-joystick, #mobile-camera-joystick {
    border-color:#499effbb !important;
  }
  #mobile-action-radial-cancel {
    border-color:#ff7796 !important;
  }
}
"""
def icons_report():
 pattern=re.compile(r"""(?<![a-zA-Z0-9])(?:/)?ui/items/[a-zA-Z0-9_./-]+\.(?:webp|png|svg)""")
 rows={}
 source=STAGE/"src"
 for file in source.rglob("*.ts"):
  if not file.is_file() or file.is_symlink():continue
  try:t=file.read_text(encoding="utf8")
  except UnicodeDecodeError:continue
  for found in pattern.findall(t):
   path=found.lstrip("/")
   if path not in rows:
    dest=STAGE/"public"/path
    rows[path]={"path":path,"inPublic":dest.is_file(),
                "sourceExample":str(file.relative_to(STAGE))}
 return list(rows.values())
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 h=STAGE/"index.html"
 original=h.read_text(encoding="utf8")
 if MARK in original or (STAGE/FILE).exists() or (STAGE/CSS_FILE).exists():
  raise RuntimeError("P45C_ALREADY_APPLIED")
 if original.count("</head>")!=1:raise RuntimeError("P45C_HEAD_DRIFT")
 required={
  "nativeJoystick":"src/game/mobile_controls.ts",
  "touchOwnerRouting":"src/game/touch_router.ts",
  "fourNativeSkillSlots":"src/ui/hud/action_bar/mobile_action_ring_controller.ts",
  "nativeSimulation":"src/sim/sim.ts",
 }
 for key,rel in required.items():
  if not (STAGE/rel).is_file():raise RuntimeError("P45C_MISSING_TOUCH_DEPENDENCY "+key+" "+rel)
 html=original.replace("</head>",
    '<link rel="stylesheet" href="/highfly_fury_mobile.css" />\n'
    '<!-- '+MARK+': cosmetic native HUD + pure combo module, not full integration -->\n'
    '</head>',1)
 rows=icons_report()
 if apply:
  backup=OUT/"backups/index.html"
  if backup.exists() or backup.is_symlink():raise RuntimeError("P45C_BACKUP_EXISTS")
  backup.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(h,backup)
  if hashlib.sha256(h.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
   raise RuntimeError("P45C_BAD_BACKUP")
  for rel,t in ((FILE,TS),(CSS_FILE,CSS)):
   target=STAGE/rel;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open("x",encoding="utf8") as file:file.write(t)
  h.write_text(html,encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 if rows:
  with (OUT/"P45C_ITEM_ICON_REFERENCE_AUDIT.csv").open("w",encoding="utf8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=["path","inPublic","sourceExample"])
   w.writeheader();w.writerows(rows)
 summary={"phase":"P45C_FURY_NATIVE_ANDROID_FOUNDATION","mode":"APPLY" if apply else "DRY_RUN",
  "nativeMobileHooks":list(required),"pureComboAndDashMath":True,
  "mobileHUDTheme":True,"actualCombatWired":False,
  "missingIconLiteralPaths":len([x for x in rows if not x["inPublic"]]),
  "referencesInspected":len(rows),
  "actorCombatModified":False,"simulationModified":False,
  "offlineSaveUnchanged":True,
  "browserAndroidVerified":False}
 (OUT/"P45C_REPORT.json").write_text(json.dumps(summary,indent=2)+"\n")
 print("[HIGHFLY] P45C FURY: "+json.dumps(summary))
 return summary
if __name__=="__main__":
 cli=argparse.ArgumentParser();cli.add_argument("--apply",action="store_true")
 run(cli.parse_args().apply)
