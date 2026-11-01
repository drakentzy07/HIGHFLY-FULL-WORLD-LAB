#!/usr/bin/env python3
"""HIGHFLY P53: isolate the abnormally large KMED block around Eastbrook.

Adds only an opt-in scene visualization probe to the already installed P52B
scene-audit scope. No model deletions, no source license changes, and no
simulation, savegame, combat, loot, or collision edits. The probe is based on
P52B's exact observed render bounds and KMED materials, not arbitrary ids.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
TARGET=STAGE/"src/render/renderer.ts"
REPORT=ROOT/".workspace/reports/highfly-p53"
MARK="HIGHFLY_P53_EASTBROOK_KMED_CLUSTER_VISUAL_PROBE"
ANCHOR="      // No permanent scene mutation: hide a single index only with explicit query."
INSERT=r"""
      // HIGHFLY_P53_EASTBROOK_KMED_CLUSTER_VISUAL_PROBE
      // P52B real-scene result: 59-66 (+74/75/80/81) are KMED fragments
      // around (-3.9,-112), extending 39 x 32 x 59 world units. Their
      // far-bake duplicates mean hiding only one P52B index proves nothing.
      // Hide ALL KMED fragments inside that geographic box, test explicitly.
      // OFF without ?hf_probe_eastbrook_kmed=hide; nothing is deleted.
      if (new URLSearchParams(window.location.search).get('hf_probe_eastbrook_kmed') === 'hide') {
        const selected = candidates.filter(r =>
          r.material.startsWith('kmed:') &&
          r.x >= -29 && r.x <= 24 &&
          r.z >= -155 && r.z <= -68 &&
          Math.max(r.width,r.height,r.depth) >= 10
        );
        for (const r of selected) {
          r.renderMesh.visible = false;
        }
        console.warn('[HIGHFLY P53] Grupo KMED sospechoso oculto (solo visual, esta URL):',
          selected.map(({renderMesh,...row})=>row));
        window.setTimeout(()=>{
          const prev=document.getElementById('hf-p53-probe');
          if(prev)prev.remove();
          const div=document.createElement('div');
          div.id='hf-p53-probe';
          Object.assign(div.style,{
            position:'fixed',bottom:'8px',right:'8px',zIndex:'2147483645',
            background:'#0a162deb',color:'#fce9fb',padding:'8px 10px',
            border:'1px solid #a85aea',borderRadius:'8px',
            font:'12px/1.4 Arial,sans-serif'
          });
          div.textContent='P53: '+selected.length+' mallas KMED ocultas · prueba reversible';
          document.body.append(div);
        },0);
      }
"""
def patch(s):
 if MARK in s:raise RuntimeError("P53_ALREADY_APPLIED")
 if "HIGHFLY_P52B_GLOBAL_EASTBROOK_GEOMETRY_AUDIT" not in s:raise RuntimeError("P53_REQUIRES_P52B")
 n=s.count(ANCHOR)
 if n!=1:raise RuntimeError("P53_P52B_ANCHOR_DRIFT "+str(n))
 return s.replace(ANCHOR,INSERT+"\n"+ANCHOR,1)
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 if not TARGET.is_file() or TARGET.is_symlink():raise RuntimeError("P53_RENDERER_MISSING")
 old=TARGET.read_text(encoding="utf8")
 new=patch(old)
 state={"phase":"P53_KMED_EASTBROOK_VISUAL_ISOLATION","mode":"DRY_RUN",
        "target":"kmed: rendered fragments near x=-3.9 z=-112",
        "compareUrl":"?hf_audit_giants=1&hf_probe_eastbrook_kmed=hide",
        "reversible":True,"gameplaySavesQuestsCollisionsChanged":False,
        "giantWallFixed":False,"browserVerified":False}
 if not apply:
  print("[HIGHFLY] P53 "+json.dumps(state,ensure_ascii=False));return state
 backup=REPORT/"backups/src/render/renderer.ts"
 if backup.exists() or backup.is_symlink():raise RuntimeError("P53_BACKUP_EXISTS")
 backup.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(TARGET,backup)
 if hashlib.sha256(backup.read_bytes()).digest()!=hashlib.sha256(TARGET.read_bytes()).digest():
  raise RuntimeError("P53_BACKUP_INTEGRITY")
 try:
  if TARGET.read_text(encoding="utf8")!=old:raise RuntimeError("P53_CONCURRENT_CHANGE")
  TARGET.write_text(new,encoding="utf8")
  subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],cwd=ROOT,check=True)
 except BaseException:
  shutil.copy2(backup,TARGET)
  print("[HIGHFLY] P53 RED - rollback to P52B",file=sys.stderr)
  raise
 state["mode"]="BUILD_GREEN_NOT_BROWSER_VERIFIED"
 (REPORT/"P53_STATUS.json").write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("[HIGHFLY] P53 "+json.dumps(state,ensure_ascii=False))
 return state
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 args=p.parse_args()
 run(args.apply)
