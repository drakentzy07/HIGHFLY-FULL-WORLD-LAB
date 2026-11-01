#!/usr/bin/env python3
"""P56: extend P55's EXISTING editor. Source-specific, scene-only edit previews.
Requires P55. Backups and rollback on P9 private-build failure. No media copied.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p56"
STUDIO="src/editor/highfly_eastbrook_studio.ts"
CSS="src/editor/highfly_eastbrook_studio.css"
PROPS="src/render/props.ts"
MARK="HIGHFLY_P56_EDITABLE_STUDIO"

def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P56_ANCHOR_{label}: {n}")
    return s.replace(a,b,1)

def patch_studio(s):
    if MARK in s:raise RuntimeError("P56_ALREADY_APPLIED")
    s=once(s,
      "type Kind='building'|'vault'|'monument'|'decor';",
      "type Kind='building'|'vault'|'monument'|'fx'|'decor'|'mesh';\n// "+MARK+" - standalone per-scene visual overrides.",
      'KIND')
    s=once(s,"  action:'hide_visual_preview'; requiresColliderReview:true;",
      "  action:'hide_visual_preview'|'transform_preview'; requiresColliderReview:true;\n  offsetX?:number; offsetZ?:number; yawDeg?:number; sizeMultiplier?:number; provisional?:boolean;",
      "DRAFT")
    s=once(s,
      "  const v=EASTBROOK_LAYOUT.weeklyVault;",
      """  // Additional built-in non-layout buildings: these were absent from P55's
  // 11 official-building shortlist. Never equate proximity with identity.
  for(const b of BUILTIN_WORLD.props.buildings) {
    if(b.x<MIN_X || b.x>MAX_X || b.z<MIN_Z || b.z>MAX_Z)continue;
    if(EASTBROOK_LAYOUT.buildings.some(v=>v.id===b.id) ||
       b.id==='eastbrook_weekly_vault')continue;
    records.push({
      id:b.id??('free-house@'+format(b.x)+','+format(b.z)),
      kind:'building',model:String(b.assetId ?? b.kind),
      x:b.x,z:b.z,width:b.w,depth:b.d,height:b.height,
      details:'Origen BUILTIN_WORLD.props.buildings; escala/colisión revisar',
    });
  }
  const v=EASTBROOK_LAYOUT.weeklyVault;""","EXTRA_BUILDINGS")
    s=once(s,
      "  let n=0;",
      """  records.push({id:'eastbrook_monument_fx',kind:'fx',
    model:'realm_builder_monument_fx.ts (holograma y haces)',
    x:m.position.x,z:m.position.z,height:m.height,
    details:'FX separado del monumento. Tu nombre aquí = placeholder original sin ganador.'});
  let n=0;""","FX_ENTRY")
    s=once(s,
      "  private readonly hidden=new Map<string,THREE.Object3D[]>();",
      """  private readonly hidden=new Map<string,THREE.Object3D[]>();
  private readonly previewMatrix=new Map<string,{
    root:THREE.Object3D; matrix:THREE.Matrix4; worldCenter:THREE.Vector3;
    previousWorldAuto:boolean;
  }>();
  private readonly shifts=new Map<string,{x:number;z:number;rotation:number;scale:number}>();
  private readonly xInput:HTMLInputElement;
  private readonly zInput:HTMLInputElement;
  private readonly rotInput:HTMLInputElement;
  private readonly scaleInput:HTMLInputElement;
  private readonly btnTransform:HTMLButtonElement;
  private readonly btnReset:HTMLButtonElement;
  private readonly meshEntry=new Map<string,Entry>();""","FIELDS")
    s=once(s,
      "    const ctr=document.createElement('div');ctr.className='hf-studio-actions';",
      """    const edits=document.createElement('div');edits.className='hf-p56-edits';
    const heading=document.createElement('strong');heading.textContent='TRANSFORMAR VISTA · NO GUARDA EL MUNDO';
    edits.appendChild(heading);
    const make=(name:string,value:string):HTMLInputElement=>{
      const wrapper=document.createElement('label');wrapper.textContent=name;
      const input=document.createElement('input');input.type='number';input.step='0.1';
      input.value=value;wrapper.appendChild(input);edits.appendChild(wrapper);return input;
    };
    this.xInput=make('X','0');this.zInput=make('Z','0');
    this.rotInput=make('Giro °','0');this.scaleInput=make('Escala','1');
    this.scaleInput.min='0.1';this.scaleInput.max='5';
    this.btnTransform=this.button('Aplicar posición/escala',()=>this.transform());
    this.btnReset=this.button('Revertir transformación',()=>this.resetTransform());
    edits.append(this.btnTransform,this.btnReset);
    this.panel.appendChild(edits);
    const ctr=document.createElement('div');ctr.className='hf-studio-actions';""","INPUT_UI")
    s=once(s,
      "    if(e.kind==='building') return scene.getObjectByName('eastbrookBuilding:'+e.id) ?? null;",
      """    if(e.kind==='building') return scene.getObjectByName('eastbrookBuilding:'+e.id)
      ?? scene.getObjectByName('highflyFreeBuilding:'+e.id) ?? null;""","BUILDING_PICK")
    s=once(s,
      "    if(e.kind==='monument') return scene.getObjectByName('eastbrookRealmBuilderMonumentFxBody') ?? null;",
      """    if(e.kind==='monument') return scene.getObjectByName('eastbrookRealmBuilderMonumentFxBody') ?? null;
    if(e.kind==='fx') return scene.getObjectByName('eastbrookRealmBuilderMonumentFx') ?? null;""","FX_FIND")
    s=once(s,
      "    if(e.kind==='decor') return scene.getObjectByName('highflyDecor:'+e.model+'@'+format(e.x)+','+format(e.z)) ?? null;",
      """    if(e.kind==='decor') return scene.getObjectByName('highflyDecor:'+e.model+'@'+format(e.x)+','+format(e.z)) ?? null;
    if(e.kind==='mesh') return this.meshEntry.has(e.id) ?
      this.renderer.scene.getObjectByProperty('uuid',e.id.slice(5)) ?? null : null;""","MESH_FIND")
    s=once(s,
      "      if(cursor.userData?.eastbrookBuildingId || cursor.name.startsWith('highflyDecor:')) return cursor;",
      """      if(cursor.userData?.eastbrookBuildingId || cursor.name.startsWith('highflyDecor:') ||
         cursor.name.startsWith('highflyFreeBuilding:')) return cursor;""","ROOT_TAG")
    s=once(s,
      """    if(e.kind==='monument') {
      const fx=this.renderer.scene.getObjectByName('eastbrookRealmBuilderMonumentFx');
      return fx && fx!==root ? [root,fx] : [root];
    }
    return [root];""",
      """    // P56: FX and monument body are *different* source identities.
    // No longer hide both with one click: small golden shaft may be just FX.
    return [root];""","SPLIT_BODY_FX")
    s=once(s,
      """    const matches=this.entries.filter(e=>
      (e.id+' '+e.model+' '+e.kind).toLowerCase().includes(query));""",
      """    const matches=[...this.entries,...this.meshEntry.values()].filter(e=>
      (e.id+' '+e.model+' '+e.kind).toLowerCase().includes(query));""","LIST_MESH")
    s=once(s,
      """    this.renderList();
    this.showInfo();
  }
  pick(clientX:number,clientY:number):void {""",
      """    this.populateTransform();
    this.renderList();
    this.showInfo();
  }
  private populateTransform():void {
    const e=this.selected;
    const v=e?this.shifts.get(e.id):null;
    this.xInput.value=String(v?.x??e?.x??0);
    this.zInput.value=String(v?.z??e?.z??0);
    this.rotInput.value=String(v?.rotation??0);
    this.scaleInput.value=String(v?.scale??1);
  }
  pick(clientX:number,clientY:number):void {""","POPULATE")
    s=once(s,
      """      if(o.name.startsWith('highflyDecor:'))decorRoots.push(o);""",
      """      if(o.name.startsWith('highflyDecor:') ||
         o.name.startsWith('highflyFreeBuilding:'))decorRoots.push(o);""","FREE_RAY")
    s=once(s,
      """        const id=String(tagged.userData?.eastbrookBuildingId??'');
        const kind=tagged.name.includes('RealmBuilder')?'monument':'building';
        const found=this.entries.find(e=>e.id===(kind==='monument'?
          'eastbrook_realm_builder_monument':id));""",
      """        const id=String(tagged.userData?.eastbrookBuildingId??
          tagged.userData?.highflySourceBuilding?.id??'');
        const kind=tagged.name==='eastbrookRealmBuilderMonumentFx'?'fx':
          tagged.name.includes('RealmBuilder')?'monument':'building';
        const found=this.entries.find(e=>e.id===(kind==='fx'?'eastbrook_monument_fx':
          kind==='monument'?'eastbrook_realm_builder_monument':id));""","PICK_KIND")
    s=once(s,
      """    const hits=this.ray.intersectObjects(town?[town,...decorRoots]:decorRoots,true);""",
      """    // Raycast actual editor scene so a mini-house drawn by another
    // renderer system is selectable; only on click, not in frame loop.
    const hits=this.ray.intersectObjects(this.renderer.scene.children,true);""","SCENE_RAY")
    s=once(s,
      """      // Unknown/batched mesh: report geometry but forbid unsafe deletion.
      const mat=h.object instanceof THREE.Mesh""",
      """      // Untagged, standalone small mesh: runtime-only inspection/edit. A
      // large batch cannot be hidden or moved safely without provenance.
      let propRoot:THREE.Object3D|null=h.object;
      let isProp=false;
      while(propRoot){
        if(propRoot.userData?.renderCategory==='props'){isProp=true;break;}
        propRoot=propRoot.parent;
      }
      if(isProp && h.object instanceof THREE.Mesh &&
         !(h.object instanceof THREE.InstancedMesh) &&
         !h.object.name.startsWith('far-bake:')) {
        const bounds=new THREE.Box3().setFromObject(h.object);
        const sz=bounds.getSize(new THREE.Vector3());
        const c=bounds.getCenter(new THREE.Vector3());
        if(!bounds.isEmpty() && Math.max(sz.x,sz.y,sz.z)<18 &&
           Math.min(sz.x,sz.y,sz.z)>0.01 &&
           Math.hypot(c.x-h.point.x,c.z-h.point.z)<8) {
          const m=h.object;
          const id='mesh:'+m.uuid;
          const mat=Array.isArray(m.material)?m.material.map(x=>x.name).join(','):m.material.name;
          const entry:Entry={id,kind:'mesh',model:mat||m.name||'unknown mesh',
            x:c.x,z:c.z,width:sz.x,height:sz.y,depth:sz.z,
            details:'Malla sin origen identificado; sólo borrador de la sesión. NO persistir sin auditoría.'};
          this.meshEntry.set(id,entry);
          this.select(entry,m,m);
          return;
        }
      }
      // Unknown/batched mesh: report geometry but forbid unsafe deletion.
      const mat=h.object instanceof THREE.Mesh""","RUNTIME_PICK")
    s=once(s,
      """    this.hideButton.disabled=!(e && this.selectedRoot);
    this.restoreButton.disabled=!(e && this.hidden.has(e.id));
  }
  private hide():void {""",
      """    this.hideButton.disabled=!(e && this.selectedRoot);
    this.restoreButton.disabled=!(e && this.hidden.has(e.id));
    this.btnTransform.disabled=!(e && this.selectedRoot);
    this.btnReset.disabled=!(e && this.previewMatrix.has(e.id));
  }
  private transform():void {
    const e=this.selected,root=this.selectedRoot;
    if(!e || !root)return;
    const x=Number(this.xInput.value),z=Number(this.zInput.value);
    const rotation=Number(this.rotInput.value),scale=Number(this.scaleInput.value);
    if(![x,z,rotation,scale].every(Number.isFinite) || scale<0.1 || scale>5 ||
      Math.abs(x-e.x)>80 || Math.abs(z-e.z)>80 || Math.abs(rotation)>360) {
      this.selectedGroupInfo='Transformación fuera de límites (máximo 80 unidades, escala 0.1–5, giro ±360°)';
      this.showInfo();return;
    }
    let base=this.previewMatrix.get(e.id);
    if(!base){
      const box=new THREE.Box3().setFromObject(root);
      if(box.isEmpty())return;
      base={root,matrix:root.matrix.clone(),
        worldCenter:box.getCenter(new THREE.Vector3()),
        previousWorldAuto:root.matrixWorldAutoUpdate};
      this.previewMatrix.set(e.id,base);
    }
    const parentWorld=root.parent?.matrixWorld.clone()??new THREE.Matrix4();
    const worldDelta=new THREE.Matrix4().makeTranslation(x-e.x,0,z-e.z);
    const center=base.worldCenter;
    worldDelta.multiply(new THREE.Matrix4().makeTranslation(center.x,center.y,center.z));
    worldDelta.multiply(new THREE.Matrix4().makeRotationY(rotation*Math.PI/180));
    worldDelta.multiply(new THREE.Matrix4().makeScale(scale,scale,scale));
    worldDelta.multiply(new THREE.Matrix4().makeTranslation(-center.x,-center.y,-center.z));
    const localDelta=parentWorld.clone().invert().multiply(worldDelta).multiply(parentWorld);
    root.matrix.copy(localDelta.multiply(base.matrix));
    root.matrixAutoUpdate=false;
    root.matrixWorldAutoUpdate=true;
    root.matrixWorldNeedsUpdate=true;
    root.updateMatrixWorld(true);
    this.shifts.set(e.id,{x,z,rotation,scale});
    this.drafts.set(e.id,{id:e.id,kind:e.kind,model:e.model,
      x:e.x,z:e.z,action:'transform_preview',requiresColliderReview:true,
      offsetX:x-e.x,offsetZ:z-e.z,yawDeg:rotation,sizeMultiplier:scale,
      provisional:e.kind==='mesh'});
    this.showInfo();
  }
  private resetTransform():void {
    const e=this.selected;
    if(!e)return;
    const base=this.previewMatrix.get(e.id);
    if(base){
      base.root.matrix.copy(base.matrix);
      base.root.matrixWorldAutoUpdate=base.previousWorldAuto;
      base.root.matrixWorldNeedsUpdate=true;
      if(!base.previousWorldAuto)base.root.matrixWorldAutoUpdate=true;
      base.root.updateMatrixWorld(true);
      base.root.matrixWorldAutoUpdate=base.previousWorldAuto;
      this.previewMatrix.delete(e.id);
    }
    this.shifts.delete(e.id);
    this.drafts.delete(e.id);this.populateTransform();this.showInfo();
  }
  private hide():void {""","TRANSFORM")
    s=once(s,
      """    this.hideButton.disabled=!(e && this.selectedRoot);
    this.restoreButton.disabled=!(e && this.hidden.has(e.id));""",
      """    this.hideButton.disabled=!(e && this.selectedRoot);
    this.restoreButton.disabled=!(e && this.hidden.has(e.id));""","DUP_NO_CHANGE") if False else s
    s=once(s,
      """  dispose():void {this.panel.remove();this.hidden.clear();this.drafts.clear();}""",
      """  dispose():void {
    for(const id of [...this.previewMatrix.keys()]){
      const e=this.entries.find(e=>e.id===id)??this.meshEntry.get(id);
      if(e){this.selected=e;this.resetTransform();}
    }
    for(const roots of this.hidden.values())for(const root of roots)root.visible=true;
    this.panel.remove();this.hidden.clear();this.drafts.clear();
  }""","DISPOSE")
    s=once(s,'      this.showInfo();this.renderList();return;',
      '      this.showInfo();this.renderList();continue;','SKIP_UNKNOWN_BATCH')
    return s

def patch_props(s):
    if MARK in s:raise RuntimeError("P56_ALREADY_APPLIED_PROPS")
    anchor="""    g.rotation.y = b.rot;
    group.add(shadowed(g));
    registerHideable(g, obbFootprint(b.x, b.z, b.w / 2, b.d / 2, b.rot, roofY));"""
    modified="""    g.rotation.y = b.rot;
    // HIGHFLY_P56_EDITABLE_STUDIO: native non-layout building source tag.
    // Only in the private editor; regular game keeps its batching unchanged.
    if(typeof window !== 'undefined' &&
       new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1' &&
       b.x >= -120 && b.x <= 50 && b.z >= -160 && b.z <= -48) {
      g.name='highflyFreeBuilding:'+(b.id??('free-house@'+Number(b.x.toFixed(2))+','+Number(b.z.toFixed(2))));
      g.userData.highflySourceBuilding={id:b.id??('free-house@'+Number(b.x.toFixed(2))+','+Number(b.z.toFixed(2))),x:b.x,z:b.z};
      g.traverse(o=>{if(o instanceof THREE.Mesh)keepFromMerge.add(o);});
    }
    group.add(shadowed(g));
    registerHideable(g, obbFootprint(b.x, b.z, b.w / 2, b.d / 2, b.rot, roofY));"""
    return once(s,anchor,modified,"FREE_BUILDING")

STYLE=r"""
/* HIGHFLY_P56_EDITABLE_STUDIO, reversible in-memory transform controls */
#hf-studio-p55 .hf-p56-edits{
 display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:5px;background:#11132b;border:1px solid #4c4674;border-radius:7px;padding:7px;margin:6px 0;
}
#hf-studio-p55 .hf-p56-edits strong{grid-column:span 2;font-size:10px;color:#e4b3ff}
#hf-studio-p55 .hf-p56-edits label{display:flex;flex-direction:column;gap:3px;font-size:10px}
#hf-studio-p55 .hf-p56-edits input{width:100%;min-width:0;padding:5px;font-size:12px}
#hf-studio-p55 .hf-p56-edits button{font-size:11px;min-height:28px;padding:4px}
#hf-studio-p55{width:min(380px,35vw)}
@media(max-width:1050px){#hf-studio-p55{width:min(340px,47vw)}}
""".strip()+"\n"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    old={}
    for rel in (STUDIO,CSS,PROPS):
        f=STAGE/rel
        if not f.is_file() or f.is_symlink():raise RuntimeError('P56_STAGE_MISSING '+rel)
        old[rel]=f.read_text(encoding='utf8')
    if 'HIGHFLY_P55_EXISTING_EDITOR_STUDIO' not in old[STUDIO]:
        raise RuntimeError('P56_REQUIRES_P55')
    updates={STUDIO:patch_studio(old[STUDIO]),CSS:old[CSS]+"\n"+STYLE,
             PROPS:patch_props(old[PROPS])}
    result={'phase':'P56_EASTBROOK_EDITOR_EDITABLE','mode':'DRY_RUN',
       'source':'P55 installed existing editor',
       'features':'original houses, free buildings, decor, monument body/FX separately, safe standalone meshes',
       'tools':'click, hide, restore, X/Z, yaw, scale, revert, export diagnostic JSON',
       'worldSimulationSaveQuestCollidersChanged':False,
       'batchDeletionEnabled':False,'runtimeBrowserVerified':False}
    if not apply:
       print('[HIGHFLY P56] '+json.dumps(result,ensure_ascii=False,indent=2));return result
    backups=[]
    try:
      for rel in old:
        source=STAGE/rel;dest=OUT/'backups'/rel
        if dest.exists() or dest.is_symlink():raise RuntimeError('P56_ALREADY_APPLIED_OR_BACKUP_EXISTS '+rel)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        if sha(source)!=sha(dest):raise RuntimeError('P56_BACKUP_BAD '+rel)
        backups.append((source,dest))
      for rel,c in updates.items():
        if (STAGE/rel).read_text(encoding='utf8')!=old[rel]:raise RuntimeError('P56_CONCURRENT_EDIT '+rel)
        (STAGE/rel).write_text(c,encoding='utf8')
      subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=str(ROOT),check=True)
    except BaseException:
      for file,backup in backups:
        if backup.is_file():shutil.copy2(backup,file)
      print('[HIGHFLY P56] RED - ROLLED BACK',file=sys.stderr)
      raise
    OUT.mkdir(parents=True,exist_ok=True)
    result['mode']='PRIVATE_BUNDLE_GREEN_BROWSER_PENDING'
    (OUT/'P56_STATUS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('[HIGHFLY P56] '+json.dumps(result,ensure_ascii=False,indent=2))
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    run(parser.parse_args().apply)
