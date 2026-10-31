#!/usr/bin/env python3
"""P41: PRIVATE stage offline persistence. Does not change online or NPCs."""
import argparse,json,shutil,hashlib,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p41-offline"
FILES=("src/sim/types.ts","src/sim/sim.ts","src/game/offline_world_config.ts","src/main.ts")
NEW="src/game/highfly_offline_saves.ts"
MARK="HIGHFLY_P41_OFFLINE_SAVE"
TS="""
// HIGHFLY_P41_OFFLINE_SAVE — original Sim serialized state and restore path.
import type {CharacterState} from '../sim/character_state';
import type {PlayerClass} from '../sim/types';
import type {Sim} from '../sim/sim';
const KEY='highfly.origin.offline.v1';
const MAX_BYTES=3500000;
export interface HighflySave {
 version:1; name:string; cls:PlayerClass; state:CharacterState;
 appearance:Record<string,unknown>|null; helmHidden:boolean; at:number;
}
export function readHighflySave(name:string):HighflySave|null {
 try{
  const raw=localStorage.getItem(KEY);if(!raw||raw.length>MAX_BYTES)return null;
  const s=JSON.parse(raw) as HighflySave;
  if(s.version!==1||s.name!==name||!s.state||
     typeof s.state!=='object'||typeof s.cls!=='string')return null;
  return s;
 }catch(e){console.warn('[HIGHFLY P41] Error al leer la partida',e);return null;}
}
export function saveHighfly(sim:Sim,cls:PlayerClass,name:string):HighflySave|null {
 try{
  const state=sim.serializeCharacter(sim.playerId);
  if(!state)throw new Error('Personaje no disponible');
  const actor=sim.entities.get(sim.playerId);
  const s:HighflySave={version:1,name,cls,state,
   appearance:actor?.modularAppearance??null,
   helmHidden:actor?.helmHidden??false,at:Date.now()};
  const json=JSON.stringify(s);
  if(json.length>MAX_BYTES)throw new Error('Guardado demasiado grande');
  localStorage.setItem(KEY,json);return s;
 }catch(e){console.error('[HIGHFLY P41] NO SE GUARDO la partida',e);return null;}
}
export function startHighflyAutosave(sim:Sim,cls:PlayerClass,name:string):void {
 const save=()=>saveHighfly(sim,cls,name);
 window.setInterval(save,15000);
 document.addEventListener('visibilitychange',()=>{
   if(document.visibilityState==='hidden')save();
 });
 window.addEventListener('pagehide',save);
 const row=document.createElement('div');
 row.id='highfly-save-controls';
 row.style.cssText='position:fixed;top:69px;left:7px;z-index:2147483000;display:flex;gap:4px;';
 const css='background:#122a4d;border:1px solid #6bcbea;border-radius:5px;color:white;padding:6px;font:12px Arial;cursor:pointer';
 const a=document.createElement('button');a.textContent='GUARDAR';a.style.cssText=css;
 const b=document.createElement('button');b.textContent='EXPORTAR';b.style.cssText=css;
 const msg=document.createElement('span');msg.style.cssText='background:#122a4d;color:#fff;font:11px Arial;padding:6px';
 a.addEventListener('click',()=>{msg.textContent=save()?'Guardado OK':'ERROR AL GUARDAR';});
 b.addEventListener('click',()=>{
  const data=save();if(!data){msg.textContent='ERROR AL GUARDAR';return;}
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;
  link.download='HIGHFLY_PARTIDA_'+name+'.json';
  document.body.append(link);link.click();
  window.setTimeout(()=>{URL.revokeObjectURL(url);link.remove();},1000);
 });
 row.append(a,b,msg);document.body.append(row);
}
""".strip()+"\n"
def repl(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError("P41_ANCHOR_DRIFT "+label+" "+str(n))
 return s.replace(old,new,1)
def patch(x):
 if any(MARK in s for s in x.values()):raise RuntimeError("P41_ALREADY_APPLIED")
 a=repl(x[FILES[0]],"export interface SimConfig {\n  seed: number;",
  "export interface SimConfig {\n  // "+MARK+"\n  offlineRestoreState?: import('./character_state').CharacterState;\n  seed: number;","config")
 b=repl(x[FILES[1]],"        autoEquip: this.cfg.autoEquip,\n        // Carried through, never derived:",
  "        autoEquip: this.cfg.autoEquip,\n        // "+MARK+"\n        state: cfg.offlineRestoreState,\n        // Carried through, never derived:","addPlayer")
 b=repl(b,"      const ownPlayer = this.cfg.compulsoryTutorial\n",
  "      const ownPlayer = this.cfg.compulsoryTutorial && !cfg.offlineRestoreState\n","tutorial")
 c=repl(x[FILES[2]],"  readonly devCommands: boolean;\n}): SimConfig {",
  "  readonly devCommands: boolean;\n  // "+MARK+"\n  readonly offlineRestoreState?: import('../sim/character_state').CharacterState;\n}): SimConfig {","worldConfig")
 c=repl(c,"    playerName: options.name,\n    devCommands: options.devCommands,",
  "    playerName: options.name,\n    offlineRestoreState: options.offlineRestoreState,\n    devCommands: options.devCommands,","worldForward")
 d=repl(x[FILES[3]],"import { offlineWorldConfig } from './game/offline_world_config';",
  "import { offlineWorldConfig } from './game/offline_world_config';\n"
  "import { readHighflySave, startHighflyAutosave } from './game/highfly_offline_saves';","import")
 d=repl(d,"  stopShaderWarmup();\n  if (!(await prepareWorldEntry())) return;\n  resetLoadProfile();",
  "  // "+MARK+": resume character by name, skip brand-new tutorial reset.\n"
  "  const highflySaved = !world ? readHighflySave(name) : null;\n"
  "  const highflyClass = highflySaved?.cls ?? playerClass;\n"
  "  stopShaderWarmup();\n  if (!(await prepareWorldEntry())) return;\n  resetLoadProfile();","start")
 d=repl(d,"          playerClass,\n          name,\n          world,\n          seedOverride,",
  "          playerClass: highflyClass,\n          name,\n          world,\n          seedOverride,\n          offlineRestoreState: highflySaved?.state,","cfg")
 d=repl(d,"  sim.setPlayerSkin(sim.playerId, skin);",
  "  if (!highflySaved) sim.setPlayerSkin(sim.playerId, skin);","skin")
 d=repl(d,"    offlinePlayer.modularAppearance = modularAppearance as unknown as Record<string, unknown>;\n    offlinePlayer.helmHidden = !creationHelm;",
  "    offlinePlayer.modularAppearance = (highflySaved?.appearance ?? modularAppearance) as Record<string, unknown>;\n"
  "    offlinePlayer.helmHidden = highflySaved?.helmHidden ?? !creationHelm;","appearance")
 pat=r"(?m)^  // Offline characters are not persisted \(a fresh name is typed each session\),\n  // so the only stable handle is class \+ name\. Keybinds scope to that pair\.\n  void startGame\(sim, sim, null, .+?, true\);"
 if len(re.findall(pat,d))!=1:raise RuntimeError("P41_ANCHOR_DRIFT oldOfflineStart")
 d=re.sub(pat,"  // "+MARK+": persistent offline play with original CharacterState.\n"
   "  void startGame(sim, sim, null, 'offline:' + highflyClass + ':' + name, true);\n"
   "  if (!world) startHighflyAutosave(sim, highflyClass, name);",d,count=1)
 return dict(zip(FILES,(a,b,c,d)))
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 target=STAGE/NEW
 if target.exists() or target.is_symlink():raise RuntimeError("P41_NEW_FILE_EXISTS")
 inputs={}
 for rel in FILES:
  f=STAGE/rel
  if not f.is_file() or f.is_symlink():raise RuntimeError("P41_MISSING_SOURCE "+rel)
  inputs[rel]=f.read_text(encoding="utf8")
 changes=patch(inputs)
 if apply:
  for rel in FILES:
   b=OUT/"backups"/rel
   if b.exists() or b.is_symlink():raise RuntimeError("P41_BACKUP_EXISTS "+rel)
  for rel in FILES:
   f=STAGE/rel;b=OUT/"backups"/rel;b.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(f,b)
   if hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest():
    raise RuntimeError("P41_BACKUP_HASH_MISMATCH "+rel)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(TS,encoding="utf8")
  for rel in FILES:
   if (STAGE/rel).read_text(encoding="utf8")!=inputs[rel]:
    raise RuntimeError("P41_SOURCE_CHANGED "+rel)
   (STAGE/rel).write_text(changes[rel],encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 result={"phase":"P41_OFFLINE_SAVE","mode":"APPLY" if apply else "DRY_RUN",
  "sourceFiles":list(FILES)+[NEW],"completeCharacterState":True,
  "autosaveIntervalSeconds":15,"manualExport":True,"browserVerified":False}
 (OUT/"P41_STATUS.json").write_text(json.dumps(result,indent=2)+"\n")
 print("[HIGHFLY] P41 SAVE: "+json.dumps(result))
 return result
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--apply",action="store_true")
 run(ap.parse_args().apply)
