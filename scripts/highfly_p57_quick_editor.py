#!/usr/bin/env python3
"""P57: ONE-STEP P55 -> intuitive HIGHFLY editor; supersedes P56 --apply.

Reuses P56 source corrections but never runs its installer or a second build.
Existing terrain tools and original editor remain intact outside ?hf_eastbrook_studio=1.
Transforms are local preview plus exported/stored proposal, NOT sim/physics edits.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p56_editor_transform as p56

STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p57"
STUDIO=p56.STUDIO
CSS=p56.CSS
VIEW="src/editor/3d/viewport.ts"
PROPS=p56.PROPS
TOWN=p56.TOWN
FX=p56.FX
TAG="HIGHFLY_P57_QUICK_EDIT"

def once(s,old,new,label):
    count=s.count(old)
    if count!=1:raise RuntimeError(f'P57_ANCHOR_DRIFT_{label}_{count}')
    return s.replace(old,new,1)

def patch_studio(s):
    s=p56.patch_studio(s)
    # Original P55 extension is being upgraded, not the legacy ClaudeCraft editor.
    s=once(s,
      "  private readonly meshEntry=new Map<string,Entry>();",
      """  private readonly meshEntry=new Map<string,Entry>();
  // HIGHFLY_P57_QUICK_EDIT: mouse drag and instant buttons.
  private dragStart: {px:number;pz:number;x:number;z:number;y:number}|null=null;
  private readonly DRAFT_KEY='HIGHFLY_EASTBROOK_EDITOR_P57_V1';""",
      "FIELDS")
    s=once(s,
      """    edits.append(this.btnTransform,this.btnReset);
    this.panel.appendChild(edits);
    const ctr=document.createElement('div');ctr.className='hf-studio-actions';""",
      """    edits.append(this.btnTransform,this.btnReset);
    // A quick-action pad like Sims is PRIMARY; numeric transforms are optional.
    const pad=document.createElement('section');pad.className='hf-p57-pad';
    const quickHeader=document.createElement('strong');
    quickHeader.textContent='MOVER · GIRAR · TAMAÑO';
    const note=document.createElement('span');
    note.textContent='Arrastrá con el mouse. Clic derecho para orbitar.';
    pad.append(quickHeader,note);
    const btn=(name:string,action:()=>void,tip:string)=>{
      const b=this.button(name,action);b.title=tip;b.className='hf-p57-action';pad.append(b);
    };
    btn('←',()=>this.quick('x',-1),'Mover 1 unidad a la izquierda');
    btn('↑',()=>this.quick('z',-1),'Mover 1 unidad hacia adelante');
    btn('↓',()=>this.quick('z',1),'Mover 1 unidad hacia atrás');
    btn('→',()=>this.quick('x',1),'Mover 1 unidad a la derecha');
    btn('↶ 15°',()=>this.quick('rotation',-15),'Girar 15 grados');
    btn('15° ↷',()=>this.quick('rotation',15),'Girar 15 grados');
    btn('− 10%',()=>this.quick('scale',-0.1),'Achicar un 10%');
    btn('+ 10%',()=>this.quick('scale',0.1),'Agrandar un 10%');
    btn('Escala sugerida',()=>this.suggestScale(),'Ajustar visual al tamaño físico del registro');
    const advanced=document.createElement('details');
    advanced.className='hf-p57-advanced';
    const summary=document.createElement('summary');summary.textContent='Ajustes precisos (opcional)';
    advanced.append(summary,edits);
    this.panel.append(pad,advanced);
    const ctr=document.createElement('div');ctr.className='hf-studio-actions';""",
      "QUICK_PAD")
    s=once(s,
      """    const ctr=document.createElement('div');ctr.className='hf-studio-actions';
    ctr.append(this.hideButton,this.restoreButton,copy,exportButton);""",
      """    const ctr=document.createElement('div');ctr.className='hf-studio-actions';
    const saveDraft=this.button('Guardar borrador + JSON',()=>this.saveDraft());
    ctr.append(this.hideButton,this.restoreButton,copy,exportButton,saveDraft);""",
      "SAVE_BUTTON")
    s=once(s,
      """    this.renderList();
    this.showInfo();
  }

  private button(label:string,onClick:()=>void):HTMLButtonElement {""",
      """    this.renderList();
    this.showInfo();
    this.replayDraft();
  }

  private button(label:string,onClick:()=>void):HTMLButtonElement {""",
      "RESTORE_ON_BOOT")
    s=once(s,
      "  private transform():void {",
      """  private quick(field:'x'|'z'|'rotation'|'scale',delta:number):void {
    if(!this.selectedRoot)return;
    const input=field==='x'?this.xInput:field==='z'?this.zInput:
      field==='rotation'?this.rotInput:this.scaleInput;
    const next=Number(input.value)+delta;
    input.value=String(field==='scale'?Number(Math.max(0.1,Math.min(5,next)).toFixed(3)):
      Number(next.toFixed(2)));
    this.transform();
  }
  private suggestScale():void {
    const e=this.selected,root=this.selectedRoot;
    if(!e || !root || !e.width || !e.height || !e.depth)return;
    const box=new THREE.Box3().setFromObject(root);
    const size=box.getSize(new THREE.Vector3());
    if(box.isEmpty()||size.x<0.01||size.y<0.01||size.z<0.01)return;
    const factor=Math.min(e.width/size.x,e.height/size.y,e.depth/size.z);
    if(!Number.isFinite(factor)||factor<=0)return;
    const current=Number(this.scaleInput.value);
    this.scaleInput.value=String(Math.max(0.1,Math.min(5,current*factor)).toFixed(3));
    this.transform();
  }
  private pointerGround(clientX:number,clientY:number,y:number):THREE.Vector3|null {
    const rect=this.canvas.getBoundingClientRect();
    this.ndc.set((clientX-rect.left)/Math.max(1,rect.width)*2-1,
      -(clientY-rect.top)/Math.max(1,rect.height)*2+1);
    this.ray.setFromCamera(this.ndc,this.renderer.camera);
    const plane=new THREE.Plane(new THREE.Vector3(0,1,0),-y);
    return this.ray.ray.intersectPlane(plane,new THREE.Vector3());
  }
  beginDrag(clientX:number,clientY:number):boolean {
    this.pick(clientX,clientY);
    if(!this.selectedRoot || !this.selected || this.selected.kind==='mesh')return false;
    const y=this.selectedRoot.getWorldPosition(new THREE.Vector3()).y;
    const point=this.pointerGround(clientX,clientY,y);
    if(!point)return false;
    this.dragStart={px:point.x,pz:point.z,
      x:Number(this.xInput.value),z:Number(this.zInput.value),y};
    return true;
  }
  drag(clientX:number,clientY:number):void {
    const start=this.dragStart;
    if(!start)return;
    const point=this.pointerGround(clientX,clientY,start.y);
    if(!point)return;
    this.xInput.value=String(Number((start.x+point.x-start.px).toFixed(2)));
    this.zInput.value=String(Number((start.z+point.z-start.pz).toFixed(2)));
    this.transform();
  }
  endDrag():void {this.dragStart=null;}
  private saveDraft():void {
    try {
      // Browser-only scratch persistence. This is NOT a write to code or server.
      localStorage.setItem(this.DRAFT_KEY,this.diagnosis());
      this.exportDraft();
    } catch {
      // Private browsing/storage policies can deny localStorage; still export.
      this.exportDraft();
      this.info.textContent+='\\nNo se pudo guardar en navegador; JSON exportado.';
    }
  }
  private replayDraft():void {
    try {
      const saved=localStorage.getItem(this.DRAFT_KEY);
      if(!saved)return;
      const data=JSON.parse(saved) as {changes?:Array<Draft>};
      if(!Array.isArray(data.changes))return;
      for(const d of data.changes.slice(0,150)) {
        const e=this.entries.find(v=>v.id===d.id && v.model===d.model);
        if(!e)continue;
        this.select(e);
        if(!this.selectedRoot)continue;
        if(d.action==='hide_visual_preview')this.hide();
        if(d.action==='transform_preview' &&
          [d.offsetX,d.offsetZ,d.yawDeg,d.sizeMultiplier].every(v=>typeof v==='number'&&Number.isFinite(v))) {
          this.xInput.value=String(e.x+(d.offsetX??0));
          this.zInput.value=String(e.z+(d.offsetZ??0));
          this.rotInput.value=String(d.yawDeg??0);
          this.scaleInput.value=String(d.sizeMultiplier??1);
          this.transform();
        }
      }
      this.selected=null;this.selectedRoot=null;this.showInfo();
    }catch(e){console.warn('[HIGHFLY P57] Borrador local inválido, se ignora',e);}
  }
  private transform():void {""",
      "DRAG_FUNCTIONS")
    s=once(s,
      """      height:d.h,details:'Decoración original; origen ZONE1_PROPS/decorProps por posición. Collider r='+""",
      """      width:d.hw?d.hw*2:undefined,depth:d.hd?d.hd*2:undefined,
      height:d.h,details:'Decoración original; origen ZONE1_PROPS/decorProps por posición. Collider r='+""",
      'DECOR_SUGGESTED_DIMENSIONS')
    return s

def patch_view(source):
    if 'HIGHFLY_P55_EXISTING_EDITOR_STUDIO' not in source:
      raise RuntimeError('P57_REQUIRES_P55_VIEW')
    if TAG in source:raise RuntimeError('P57_ALREADY_APPLIED_VIEW')
    source=once(source,
      "  private dragMode: 'none' | 'orbit' | 'pan' | 'edit' | 'moveplacement' = 'none';",
      "  private dragMode: 'none' | 'orbit' | 'pan' | 'edit' | 'moveplacement' | 'hfmove' = 'none';\n  // "+TAG+" drag bridge into existing editor viewport.",
      "DRAG_MODE")
    source=once(source,
      """    const wantsEdit = ev.button === 0 && this.hooks.toolActive();""",
      """    if(ev.button===0 && !ev.shiftKey && this.hfStudio?.beginDrag(ev.clientX,ev.clientY)){
      this.dragMode='hfmove';this.canvas.style.cursor='grabbing';
      this.canvas.setPointerCapture(ev.pointerId);return;
    }
    const wantsEdit = ev.button === 0 && this.hooks.toolActive();""",
      "DRAG_START")
    source=once(source,
      """    else if (this.dragMode === 'pan') this.cam.pan(dx, dy);""",
      """    else if (this.dragMode === 'pan') this.cam.pan(dx, dy);
    else if (this.dragMode === 'hfmove') this.hfStudio?.drag(ev.clientX,ev.clientY);""",
      "DRAG_MOVE")
    source=once(source,
      """    if (this.dragMode === 'edit') {
      this.hooks.onEditEnd(ev);""",
      """    if (this.dragMode === 'hfmove') {
      this.hfStudio?.endDrag();this.canvas.style.cursor='';
    } else if (this.dragMode === 'edit') {
      this.hooks.onEditEnd(ev);""",
      "DRAG_END")
    return source

QUICK_CSS=r"""
/* HIGHFLY_P57_QUICK_EDIT: Sims-like quick controls, expert input collapsible */
#hf-studio-p55 .hf-p57-pad{
 display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;
 margin:8px 0;background:#0c1330;border:1px solid #6550ab;
 padding:9px;border-radius:10px;
}
#hf-studio-p55 .hf-p57-pad strong,#hf-studio-p55 .hf-p57-pad span{
 grid-column:1/-1;
}
#hf-studio-p55 .hf-p57-pad strong{font-size:11px;color:#d7c0ff}
#hf-studio-p55 .hf-p57-pad span{font-size:10px;color:#aeb8d0}
#hf-studio-p55 .hf-p57-action{
 min-height:35px;min-width:0;padding:4px;font-weight:700;
 border:1px solid #6057a4;color:#f7f5ff;background:#211a43;
 border-radius:7px;white-space:nowrap;font-size:12px;
}
#hf-studio-p55 .hf-p57-action:nth-last-child(1){
 grid-column:1/-1;background:#31325d;border-color:#a399ed;
}
#hf-studio-p55 .hf-p57-advanced{margin:4px 0 7px}
#hf-studio-p55 .hf-p57-advanced summary{cursor:pointer;font-size:11px;padding:7px;color:#b5c9e9}
#hf-studio-p55 .hf-p56-edits{margin:0 0 6px}
#hf-studio-p55{width:min(410px,38vw)}
@media (max-width:1000px){#hf-studio-p55{width:min(335px,48vw)}}
""".strip()+"\n"

def checksum(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def archive_incomplete_previous_backup():
    """Keep failed P57 backup attempts; never delete or overwrite them.

    Caller has already checked that the private stage is genuinely still P55
    and all transform anchors are available. A successful P57 report is NOT a
    stale attempt, so refuse to touch it.
    """
    if not OUT.exists() and not OUT.is_symlink():
        return None
    if OUT.is_symlink() or not OUT.is_dir():
        raise RuntimeError('P57_REPORT_PATH_UNSAFE')
    if (OUT / 'P57_STATUS.json').exists() or (OUT / 'P57_STATUS.json').is_symlink():
        raise RuntimeError('P57_SUCCESS_REPORT_EXISTS_CHECK_STAGE_MANUALLY')
    archive_dir=OUT.parent/'highfly-p57-preserved-attempts'
    if archive_dir.is_symlink():
        raise RuntimeError('P57_ARCHIVE_SYMLINK_UNSAFE')
    archive_dir.mkdir(parents=True,exist_ok=True)
    candidate=archive_dir/('highfly-p57-'+str(time.time_ns()))
    if candidate.exists() or candidate.is_symlink():
        raise RuntimeError('P57_ARCHIVE_COLLISION')
    # An atomic directory rename on the same volume: NO files are deleted.
    OUT.rename(candidate)
    print('[HIGHFLY P57] Previous incomplete backup PRESERVED: '+str(candidate))
    return candidate

def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    originals={}
    for rel in (STUDIO,CSS,VIEW,PROPS,TOWN,FX):
        f=STAGE/rel
        if not f.is_file() or f.is_symlink():raise RuntimeError('P57_STAGE_FILE_MISSING '+rel)
        originals[rel]=f.read_text(encoding='utf8')
    if 'HIGHFLY_P55_EXISTING_EDITOR_STUDIO' not in originals[STUDIO]:
        raise RuntimeError('P57_REQUIRES_P55_APPLIED_NOT_P56')
    if 'HIGHFLY_P56_EDITABLE_STUDIO' in originals[STUDIO] or TAG in originals[STUDIO]:
        raise RuntimeError('P57_STAGE_ALREADY_CHANGED_DO_NOT_REPEAT')
    updates={
      STUDIO:patch_studio(originals[STUDIO]),
      CSS:originals[CSS]+'\n'+p56.STYLE+'\n'+QUICK_CSS,
      VIEW:patch_view(originals[VIEW]),
      PROPS:p56.patch_props(originals[PROPS]),
      TOWN:p56.patch_town(originals[TOWN]),
      FX:p56.patch_fx(originals[FX]),
    }
    result={
      'phase':'P57_HIGHFLY_EASTBROOK_SIMS_QUICK_EDITOR','mode':'DRY_RUN',
      'inputStage':'P55 private stage; P56 script reused as library ONLY, not applied',
      'controls':'click to select; mouse drag; arrow nudges; rotate 15 deg; scale +/-10%; suggested scale; advanced numeric optional',
      'persistence':'browser-local draft + JSON download; NOT applied to game source or physics',
      'gameplaySystemsChanged':False,
      'monument':'visual normalized to authored size; no fake-name beams',
      'fullGameplayAndBrowserVerified':False,
    }
    if not apply:
        print('[HIGHFLY P57] '+json.dumps(result,ensure_ascii=False,indent=2));return result
    archive_incomplete_previous_backup()
    backups=[]
    try:
        for rel in originals:
            file=STAGE/rel;dest=OUT/'backups'/rel
            if dest.exists() or dest.is_symlink():raise RuntimeError('P57_BACKUP_EXISTS '+rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,dest)
            if checksum(dest)!=checksum(file):raise RuntimeError('P57_BACKUP_BAD '+rel)
            backups.append((file,dest))
        for rel,content in updates.items():
            path=STAGE/rel
            if path.read_text(encoding='utf8')!=originals[rel]:
                raise RuntimeError('P57_CONCURRENT_STAGE_EDIT '+rel)
            path.write_text(content,encoding='utf8')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        for path,backup in backups:
            if backup.is_file():shutil.copy2(backup,path)
        print('[HIGHFLY P57] RED: saved stage files restored; previous backups preserved',file=sys.stderr)
        raise
    OUT.mkdir(parents=True,exist_ok=True)
    result['mode']='BUILD_GREEN_BROWSER_UNVERIFIED'
    (OUT/'P57_STATUS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('[HIGHFLY P57] '+json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--apply',action='store_true')
    run(cli.parse_args().apply)
