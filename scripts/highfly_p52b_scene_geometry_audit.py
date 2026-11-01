#!/usr/bin/env python3
"""HIGHFLY P52B — scan ACTUAL scene geometry around Eastbrook, not just town roots.

Default behaviour is unchanged. ?hf_audit_giants=1 shows a report of unusually
large meshes, including outside eastbrookTownView (props, world models, etc).
?hf_audit_giants=1&hf_hide_giant=INDEX hides only the selected render mesh,
never sim entities, collision, saves, or quests. This is a debug comparison,
not a permanent fix; renderer recreates the mesh on reload.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
TARGET=STAGE/"src/render/renderer.ts"
REPORT=ROOT/".workspace/reports/highfly-p52b"
MARK="HIGHFLY_P52B_GLOBAL_EASTBROOK_GEOMETRY_AUDIT"
ANCHOR="    bd('eastbrook-town');"
TS=r"""
    // HIGHFLY_P52B_GLOBAL_EASTBROOK_GEOMETRY_AUDIT
    // Includes buildProps, Grand Armoury, town buildings and static instancing.
    // Off by default; requires explicit ?hf_audit_giants=1 browser query.
    if (new URLSearchParams(window.location.search).get('hf_audit_giants') === '1') {
      this.scene.updateMatrixWorld(true);
      type HfGiant = {
        index: number; name: string; hierarchy: string; geometry: string;
        kind: string; material: string; x: number; y: number; z: number;
        width: number; height: number; depth: number; maxDim: number;
        source: string; renderMesh: THREE.Object3D;
      };
      const candidates: HfGiant[] = [];
      const area = new THREE.Box3(
        new THREE.Vector3(-145,-500,-240),
        new THREE.Vector3(155,700,70),
      );
      const bb=new THREE.Box3();
      const size=new THREE.Vector3();
      const center=new THREE.Vector3();
      this.scene.traverse((obj: THREE.Object3D) => {
        if (!(obj instanceof THREE.Mesh) && !(obj instanceof THREE.InstancedMesh)) return;
        const mesh=obj as THREE.Mesh;
        // Use the fully transformed geometry, not GLB *source* dimensions.
        bb.setFromObject(mesh);
        if (bb.isEmpty() || !bb.intersectsBox(area)) return;
        bb.getSize(size); bb.getCenter(center);
        const maxDim=Math.max(size.x,size.y,size.z);
        if (maxDim<12) return;
        // Group/world tree: global props vs replacement town vs terrain.
        const chain: string[] = [];
        let n: THREE.Object3D|null=mesh;
        while(n && chain.length<8) {
          chain.unshift(n.name||n.type);
          n=n.parent;
        }
        const material=Array.isArray(mesh.material)
          ? mesh.material.map(m=>m.name||m.type).slice(0,4).join(',')
          : (mesh.material?.name||mesh.material?.type||'?');
        const source=String(
          mesh.userData?.assetUrl??mesh.userData?.sourceUrl??
          mesh.parent?.userData?.assetUrl??mesh.parent?.userData?.assetId??''
        );
        candidates.push({
          index:-1,name:mesh.name||'(sin nombre)',hierarchy:chain.join(' > '),
          geometry:mesh.geometry?.type??'?',kind:mesh.isInstancedMesh?'INSTANCED':'MESH',
          material,x:+center.x.toFixed(1),y:+center.y.toFixed(1),
          z:+center.z.toFixed(1),
          width:+size.x.toFixed(1),height:+size.y.toFixed(1),
          depth:+size.z.toFixed(1),maxDim:+maxDim.toFixed(1),
          source,renderMesh:mesh,
        });
      });
      candidates.sort((a,b)=>b.maxDim-a.maxDim);
      candidates.forEach((r,i)=>r.index=i);
      // No permanent scene mutation: hide a single index only with explicit query.
      const probe=Number(new URLSearchParams(window.location.search).get('hf_hide_giant'));
      const hasProbe=new URLSearchParams(window.location.search).has('hf_hide_giant');
      if(hasProbe&&Number.isInteger(probe)&&probe>=0&&probe<candidates.length){
        candidates[probe].renderMesh.visible=false;
        console.warn('[HIGHFLY P52B] Ocultada SOLO la malla visual',candidates[probe]);
      }
      const plain=candidates.map(({renderMesh,...row})=>row);
      console.info('[HIGHFLY P52B] Escena global: mallas grandes alrededor de Eastbrook',plain);
      console.table(plain.slice(0,70));
      window.setTimeout(()=>{
        document.getElementById('highfly-p52b-giants')?.remove();
        const panel=document.createElement('details');
        panel.id='highfly-p52b-giants'; panel.open=true;
        Object.assign(panel.style,{
          position:'fixed',left:'10px',top:'12%',zIndex:'2147483643',
          width:'min(760px,91vw)',maxHeight:'68vh',
          overflow:'auto',color:'#dff6ff',background:'#071525f2',
          border:'1px solid #67d3fa',borderRadius:'9px',padding:'12px',
          font:'11px/1.45 Consolas,monospace',whiteSpace:'pre-wrap',
        });
        const header=document.createElement('summary');
        header.textContent='HIGHFLY · EASTBROOK · MALLAS GRANDES (ESCENA COMPLETA) · '+plain.length;
        panel.append(header);
        const button=document.createElement('button');
        button.type='button'; button.textContent='COPIAR INFORME COMPLETO';
        Object.assign(button.style,{padding:'7px',margin:'7px 0',cursor:'pointer'});
        button.onclick=()=>{void navigator.clipboard?.writeText(JSON.stringify(plain,null,2));};
        panel.append(button);
        const text=document.createElement('pre');
        text.style.whiteSpace='pre-wrap';text.style.overflowWrap='anywhere';
        text.textContent=plain.slice(0,100).map(r=>
          '#'+r.index+' '+r.name+' ['+r.kind+'/'+r.geometry+'] '+
          r.width+'×'+r.height+'×'+r.depth+
          ' x='+r.x+' z='+r.z+'\n    '+r.hierarchy+
          (r.source?'\n    source='+r.source:'')
        ).join('\n');
        panel.append(text);document.body.append(panel);
      },0);
    }
"""
def patch(s):
 if MARK in s:raise RuntimeError("P52B_ALREADY_APPLIED")
 count=s.count(ANCHOR)
 if count!=1:raise RuntimeError("P52B_RENDERER_ANCHOR_DRIFT "+str(count))
 return s.replace(ANCHOR,ANCHOR+"\n"+TS,1)
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 if not TARGET.is_file() or TARGET.is_symlink():raise RuntimeError("P52B_NO_RENDERER")
 source=TARGET.read_text(encoding="utf8")
 transformed=patch(source)
 output={"phase":"P52B_GLOBAL_EASTBROOK_GEOMETRY","mode":"DRY_RUN",
         "wholeScene":True,"actualTransformedMeshBounds":True,
         "debugOnly":"?hf_audit_giants=1",
         "hideOneReversible":"?hf_audit_giants=1&hf_hide_giant=N",
         "questsSavesTutorialUnchanged":True,"browserVerified":False}
 if not apply:
  print("[HIGHFLY] P52B "+json.dumps(output,ensure_ascii=False));return
 backup=REPORT/"backups/src/render/renderer.ts"
 if backup.exists():raise RuntimeError("P52B_BACKUP_EXISTS")
 backup.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(TARGET,backup)
 if hashlib.sha256(backup.read_bytes()).digest()!=hashlib.sha256(TARGET.read_bytes()).digest():
  raise RuntimeError("P52B_BACKUP_INTEGRITY_FAILED")
 try:
  if TARGET.read_text(encoding="utf8")!=source:raise RuntimeError("P52B_CONCURRENT_EDIT")
  TARGET.write_text(transformed,encoding="utf8")
  subprocess.run([sys.executable,str(ROOT/"scripts/highfly_p9_private_build_smoke.py")],
    cwd=str(ROOT),check=True)
 except BaseException:
  shutil.copy2(backup,TARGET)
  print("[HIGHFLY] P52B RED - RESTORED PREVIOUS STAGE",file=sys.stderr)
  raise
 output["mode"]="BUILD_GREEN_NOT_BROWSER_VERIFIED"
 (REPORT/"STATUS.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
 print("[HIGHFLY] P52B "+json.dumps(output,ensure_ascii=False))
if __name__=="__main__":
 cli=argparse.ArgumentParser()
 cli.add_argument("--apply",action="store_true")
 args=cli.parse_args()
 run(args.apply)
