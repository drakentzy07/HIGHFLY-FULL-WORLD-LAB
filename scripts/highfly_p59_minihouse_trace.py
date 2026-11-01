#!/usr/bin/env python3
"""P59: click-to-identify unknown mini house: ray hits + scene provenance.

Pure editor-only instrumentation on top of P58. No game source, sim, collider,
save, private assets, or micro-batching change. Backup + P9 rollback.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9

STAGE=p9.STAGE
OUT=ROOT/'.workspace/reports/highfly-p59'
STUDIO='src/editor/highfly_eastbrook_studio.ts'
CSS='src/editor/highfly_eastbrook_studio.css'
MARK='HIGHFLY_P59_RAW_SCENE_PICK_TRACE'

def once(s,a,b,name):
    count=s.count(a)
    if count!=1:raise RuntimeError(f'P59_ANCHOR_{name}_{count}')
    return s.replace(a,b,1)

def patch_studio(s):
    if MARK in s:raise RuntimeError('P59_ALREADY_APPLIED')
    for required in ('HIGHFLY_P58_SELECTABLE_MICRO_PROPS',
                     'HIGHFLY_P57_QUICK_EDIT','HIGHFLY_P56_EDITABLE_STUDIO'):
        if required not in s:raise RuntimeError('P59_REQUIRES_P58_'+required)
    s=once(s,
      '  private readonly meshEntry=new Map<string,Entry>();',
      """  private readonly meshEntry=new Map<string,Entry>();
  // HIGHFLY_P59_RAW_SCENE_PICK_TRACE. Debug only; never infer source IDs.
  private probeArmed=false;
  private readonly probePanel:HTMLDivElement;
  private probeReport:Record<string,unknown>|null=null;
  private probeHits:Array<{
    object:THREE.Object3D; center:THREE.Vector3; size:THREE.Vector3;
    safe:boolean;summary:Record<string,unknown>
  }> = [];""",
      'FIELDS')
    s=once(s,
      """    const saveDraft=this.button('Guardar borrador + JSON',()=>this.saveDraft());
    const removeVisual=this.button('Quitar (borrador)',()=>this.removeVisual());
    removeVisual.title='Quita únicamente la imagen en este editor; propuesta JSON con ID, nunca altera colisiones sin revisión';
    ctr.append(this.hideButton,this.restoreButton,removeVisual,copy,exportButton,saveDraft);""",
      """    const saveDraft=this.button('Guardar borrador + JSON',()=>this.saveDraft());
    const removeVisual=this.button('Quitar (borrador)',()=>this.removeVisual());
    removeVisual.title='Quita únicamente la imagen en este editor; propuesta JSON con ID, nunca altera colisiones sin revisión';
    this.probePanel=document.createElement('div');
    this.probePanel.className='hf-p59-probe';
    const probeButton=this.button('🔎 Identificar casita: siguiente clic',()=>{
      this.probeArmed=true;
      this.probePanel.textContent='Ahora HACÉ UN CLIC sobre la mini casita (no arrastres). Registraré todas las mallas bajo el cursor.';
    });
    const probeExport=this.button('Descargar diagnóstico de casita',()=>this.exportProbe());
    probeExport.title='Archivo JSON con mallas reales, jerarquía, posición, material y candidatos, para compartir en el chat';
    ctr.append(this.hideButton,this.restoreButton,removeVisual,probeButton,probeExport,copy,exportButton,saveDraft);""",
      'TRACE_UI')
    s=once(s,
      '    this.panel.append(header,intro,this.search,this.list,this.info,ctr);',
      '    this.panel.append(header,intro,this.search,this.list,this.info,this.probePanel,ctr);',
      'TRACE_PANEL')
    s=once(s,
      """  beginDrag(clientX:number,clientY:number):boolean {
    this.pick(clientX,clientY);""",
      """  beginDrag(clientX:number,clientY:number):boolean {
    if(this.probeArmed){
      this.probeArmed=false;
      this.traceAt(clientX,clientY);
      // Claim the click, so viewport does NOT orbit or move an unrelated
      // monument/model. No dragStart is set, so further drags are inert.
      return true;
    }
    this.pick(clientX,clientY);""",
      'TRACE_ACTIVATE')
    s=once(s,
      """  private saveDraft():void {
    try {""",
      """  private traceAt(clientX:number,clientY:number):void {
    const rect=this.canvas.getBoundingClientRect();
    const candidates=new Map<string,THREE.Object3D>();
    const sampleOffsets:[[number,number],...Array<[number,number]>]=[
      [0,0],[-4,0],[4,0],[0,-4],[0,4],[-7,-7],[7,-7],[-7,7],[7,7],
    ];
    let originalHits=0;
    for(const [ox,oy] of sampleOffsets){
      this.ndc.set(((clientX+ox)-rect.left)/Math.max(1,rect.width)*2-1,
        -((clientY+oy)-rect.top)/Math.max(1,rect.height)*2+1);
      this.ray.setFromCamera(this.ndc,this.renderer.camera);
      const hits=this.ray.intersectObjects(this.renderer.scene.children,true);
      if(ox===0 && oy===0)originalHits=hits.length;
      for(const hit of hits.slice(0,45)){
        // The most revealing information is EVERY actual intersected mesh,
        // even if tagged selection intercepted the user's earlier click.
        const o=hit.object;
        if(!candidates.has(o.uuid) && candidates.size<65)candidates.set(o.uuid,o);
      }
    }
    const records:Array<{
      object:THREE.Object3D; center:THREE.Vector3; size:THREE.Vector3;
      safe:boolean;summary:Record<string,unknown>
    }>=[];
    let index=0;
    for(const object of candidates.values()){
      const path:string[]=[];
      const parentMeta:Array<Record<string,unknown>>=[];
      let o:THREE.Object3D|null=object;
      let top='',category='';
      let effectivelyVisible=true;
      while(o){
        path.unshift(o.name||o.type);
        if(o.visible===false)effectivelyVisible=false;
        if(o.userData?.renderCategory)category=String(o.userData.renderCategory);
        if(o.parent===this.renderer.scene)top=o.name||o.type;
        const ud=o.userData;
        if(ud && Object.keys(ud).length && parentMeta.length<5)
          parentMeta.push({name:o.name||o.type,
            props:Object.fromEntries(Object.entries(ud).slice(0,12).map(([k,v])=>
              [k,typeof v==='string'||typeof v==='boolean'||typeof v==='number'?v:
                Array.isArray(v)?'[array '+v.length+']':'[object]']))});
        o=o.parent;
      }
      const box=new THREE.Box3().setFromObject(object);
      const size=box.isEmpty()?new THREE.Vector3():box.getSize(new THREE.Vector3());
      const center=box.isEmpty()?new THREE.Vector3():box.getCenter(new THREE.Vector3());
      const nearby=this.entries.map(e=>({id:e.id,kind:e.kind,
        distance:Number(Math.hypot(e.x-center.x,e.z-center.z).toFixed(2))}))
        .filter(x=>x.distance<18).sort((a,b)=>a.distance-b.distance).slice(0,5);
      const mesh=object as THREE.Mesh;
      const material=mesh.isMesh?
        (Array.isArray(mesh.material)?mesh.material.map(m=>m.name||m.type):
          [mesh.material?.name||mesh.material?.type||'unknown']):[];
      const merged=/batch|bake|terrain|wall|ground|water|foliage|particle/i.test(path.join('/'));
      const safe=effectivelyVisible && mesh.isMesh &&
        !(object instanceof THREE.InstancedMesh) && !merged &&
        size.x>0.05 && size.y>0.05 && size.z>0.05 &&
        Math.max(size.x,size.y,size.z)<16 &&
        (category==='props'||path.some(x=>x.startsWith('highfly')));
      const summary:Record<string,unknown>={
        rank:++index,name:object.name||'(sin nombre)',
        class:object.type,uuid:object.uuid,
        material,top,category,visible:effectivelyVisible,
        hierarchy:path.join(' > '),userData:parentMeta,
        center:[center.x,center.y,center.z].map(v=>Number(v.toFixed(3))),
        realSize:[size.x,size.y,size.z].map(v=>Number(v.toFixed(3))),
        nearestRecords:nearby,rawMeshPreviewAllowed:safe,
      };
      records.push({object,center,size,safe,summary});
    }
    this.probeHits=records;
    this.probeReport={
      phase:'HIGHFLY_P59_MINIHOUSE_SOURCE_DIAG',
      source:'P58 editor scene, original v0.44.7 + HIGHFLY stage',
      click:{clientX,clientY,canvasRect:{x:rect.left,y:rect.top,
        w:rect.width,h:rect.height}},
      centerRayHits:originalHits,scannedOffsets:sampleOffsets,
      meshCount:records.length,
      warning:'nearest source is PROXIMITY ONLY, never proof of identity',
      hits:records.map(r=>r.summary),
    };
    this.probePanel.replaceChildren();
    const title=document.createElement('strong');
    title.textContent='DIAGNÓSTICO CASITA: '+records.length+
      ' mallas detectadas · clic en candidata para probar ocultación';
    this.probePanel.append(title);
    const note=document.createElement('p');
    note.textContent='No borra el mapa. Las mallas grandes/fusionadas no se pueden seleccionar como objeto suelto.';
    this.probePanel.append(note);
    for(const item of records.slice(0,25)){
      const v=item.summary;
      const label='#'+v.rank+' '+String(v.name).slice(0,26)+
        ' · '+String(v.top).slice(0,18)+' · '+(v.realSize as number[]).join('×');
      const b=this.button(label,()=>{
        if(!item.safe)return;
        const obj=item.object;
        const id='mesh:'+obj.uuid;
        const e:Entry={id,kind:'mesh',
          model:String(v.material||v.name||'mesh'),x:item.center.x,z:item.center.z,
          width:item.size.x,height:item.size.y,depth:item.size.z,
          details:'P59 MALLA DESCONOCIDA: ID provisional de SESIÓN. Ocultar para probar, exportar log; NO modificar sim sin auditoría.'};
        this.meshEntry.set(id,e);
        this.select(e,obj,obj);
        this.selectedGroupInfo='P59 DIAGNÓSTICO: selección provisional; ver informe descargable';
        this.showInfo();
      });
      b.disabled=!item.safe;
      b.title=item.safe?'Seleccionar SOLO esta malla de prueba; no es un ID persistente':
        'No editable individualmente: fusionada, grande o sin origen seguro';
      this.probePanel.append(b);
    }
    this.probePanel.scrollIntoView({block:'nearest'});
    console.info('[HIGHFLY P59] Identificación mini casita (solo editor)',this.probeReport);
  }
  private exportProbe():void {
    if(!this.probeReport){
      this.probePanel.textContent='Primero pulsá «Identificar casita» y hacé clic SOBRE la casita.';
      return;
    }
    const data=JSON.stringify(this.probeReport,null,2);
    const blob=new Blob([data],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url;link.download='HIGHFLY_P59_CASITA_SOURCE_LOG.json';
    link.click();
    window.setTimeout(()=>URL.revokeObjectURL(url),1200);
  }
  private saveDraft():void {
    try {""",
      'TRACE_IMPL')
    return s

STYLE=r"""
/* HIGHFLY_P59_RAW_SCENE_PICK_TRACE */
#hf-studio-p55 .hf-p59-probe{
 display:flex;flex-direction:column;gap:4px;max-height:180px;overflow:auto;
 padding:7px;margin:6px 0;border:1px solid #517cb6;border-radius:7px;
 background:#111e33;font-size:10px;
}
#hf-studio-p55 .hf-p59-probe:empty{display:none}
#hf-studio-p55 .hf-p59-probe button{
 min-height:25px;font-size:10px;text-align:left;white-space:normal;
 background:#192e45;color:#f6f9ff;border:1px solid #5075a2;border-radius:5px;
}
#hf-studio-p55 .hf-p59-probe button:disabled{opacity:.36}
""".strip()+"\n"

def sha(file:Path):return hashlib.sha256(file.read_bytes()).hexdigest()
def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    originals={}
    for rel in (STUDIO,CSS):
        path=STAGE/rel
        if not path.is_file() or path.is_symlink():raise RuntimeError('P59_STAGE_MISSING '+rel)
        originals[rel]=path.read_text(encoding='utf8')
    if 'HIGHFLY_P58_SELECTABLE_MICRO_PROPS' not in originals[STUDIO]:
        raise RuntimeError('P59_REQUIRES_P58_PRIVATE_GREEN')
    if MARK in originals[STUDIO]:raise RuntimeError('P59_ALREADY_APPLIED')
    updated={STUDIO:patch_studio(originals[STUDIO]),CSS:originals[CSS]+'\n'+STYLE}
    info={'phase':'P59_MINIHOUSE_EXACT_MESH_INSPECTOR','mode':'DRY_RUN',
      'editorOnly':True,'requiresP58':True,
      'features':['next click captures all intersections','object path/material/world dimensions',
        'world record proximity but not mistaken for ID','individual safe temporary mesh hide',
        'download HIGHFLY_P59_CASITA_SOURCE_LOG.json'],
      'gameplayAndCollidersChanged':False,'browserVerified':False}
    if not apply:
        print('[HIGHFLY P59] '+json.dumps(info,indent=2,ensure_ascii=False));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():raise RuntimeError('P59_BACKUP_PATH_UNSAFE')
        if (OUT/'P59_STATUS.json').exists():raise RuntimeError('P59_SUCCESS_ALREADY_EXISTS')
        dest=OUT.parent/'highfly-p59-preserved-attempts'
        if dest.is_symlink():raise RuntimeError('P59_ARCHIVE_PATH_UNSAFE')
        dest.mkdir(parents=True,exist_ok=True)
        target=dest/('attempt-'+str(time.time_ns()))
        if target.exists():raise RuntimeError('P59_ARCHIVE_COLLISION')
        OUT.rename(target)
        print('[HIGHFLY P59] Preserved previous attempt: '+str(target))
    backs=[]
    try:
        for rel in originals:
            src=STAGE/rel;backup=OUT/'backups'/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,backup)
            if sha(src)!=sha(backup):raise RuntimeError('P59_BACKUP_HASH_BAD '+rel)
            backs.append((src,backup))
        for rel,content in updated.items():
            file=STAGE/rel
            if file.read_text(encoding='utf8')!=originals[rel]:
                raise RuntimeError('P59_STAGE_CONCURRENT_EDIT '+rel)
            file.write_text(content,encoding='utf8')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        for dest,backup in backs:
            if backup.is_file():shutil.copy2(backup,dest)
        print('[HIGHFLY P59] RED — rollback to P58; no game changes',file=sys.stderr)
        raise
    info['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P59_STATUS.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    print('[HIGHFLY P59] '+json.dumps(info,indent=2,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    run(parser.parse_args().apply)
