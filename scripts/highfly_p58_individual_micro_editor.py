#!/usr/bin/env python3
"""HIGHFLY P58: editable Eastbrook micro props, safely without touching gameplay.

P57 built first. Only editor query ?hf_eastbrook_studio=1 unmerges benches,
market stalls and fences for per-source selection. Runtime game stays batched.
Draft removal only: it hides visual and exports source ID for later sim audit.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/'.workspace/reports/highfly-p58'
TOWN='src/render/eastbrook_town.ts'
STUDIO='src/editor/highfly_eastbrook_studio.ts'
MARK='HIGHFLY_P58_SELECTABLE_MICRO_PROPS'

def once(s,a,b,name):
    n=s.count(a)
    if n!=1:raise RuntimeError(f'P58_ANCHOR_{name}_{n}')
    return s.replace(a,b,1)

def patch_town(s):
    if MARK in s:raise RuntimeError('P58_ALREADY_INSTALLED_TOWN')
    s=once(s,
      """interface MicroBatchBuild {
  batches: THREE.Mesh[];
}""",
      """interface MicroBatchBuild {
  batches: THREE.Object3D[];
}""",'BATCH_TYPE')
    s=once(s,
      """  const opaque: THREE.BufferGeometry[] = [];
  const emissive: THREE.BufferGeometry[] = [];
  const add = (url: string, matrix: THREE.Matrix4): void => {
    const template = templates.get(url);
    if (!template) throw new Error(`Eastbrook town template is missing: ${url}`);
    addPlacedGeometry(opaque, template.opaque, matrix);
    addPlacedGeometry(emissive, template.emissive, matrix);
  };""",
      """  const opaque: THREE.BufferGeometry[] = [];
  const emissive: THREE.BufferGeometry[] = [];
  const studioMode = typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1';
  // HIGHFLY_P58_SELECTABLE_MICRO_PROPS: only the studio opts out of
  // immutable performance batches; game renderer retains the old pipeline.
  const studioPieces: THREE.Group[] = [];
  let activeSource: {id:string;kind:string;model:string;x:number;z:number}|null=null;
  const add = (url: string, matrix: THREE.Matrix4): void => {
    const template = templates.get(url);
    if (!template) throw new Error(`Eastbrook town template is missing: ${url}`);
    if(studioMode && activeSource){
      const source=activeSource;
      const g=new THREE.Group();
      g.name='highflyMicro:'+source.id;
      g.userData.highflyMicroId=source.id;
      g.userData.highflyMicroSource={...source};
      for(const [geometry,glow] of [
        [template.opaque,false],[template.emissive,true],
      ] as const){
        if(!geometry)continue;
        const clone=geometry.clone();
        clone.applyMatrix4(matrix);
        const mesh=new THREE.Mesh(clone,townMaterial(glow,atlas,glow));
        mesh.name=g.name+(glow?':glow':':solid');
        mesh.castShadow=!glow;
        mesh.receiveShadow=!glow;
        g.add(mesh);
      }
      studioPieces.push(g);
      return;
    }
    addPlacedGeometry(opaque, template.opaque, matrix);
    addPlacedGeometry(emissive, template.emissive, matrix);
  };""",'CREATE_EDITOR_GROUPS')
    # The original source spells the throw with a template literal.
    s=once(s,
      """  for (const bench of EASTBROOK_LAYOUT.civic.benches) {
    const template = templates.get(bench.assetId);""",
      """  for (const bench of EASTBROOK_LAYOUT.civic.benches) {
    activeSource={id:bench.id,kind:'bench',model:bench.assetId,
      x:bench.position.x,z:bench.position.z};
    const template = templates.get(bench.assetId);""",
      'BENCH_ORIGIN')
    s=once(s,
      """  for (const stall of EASTBROOK_LAYOUT.market.stalls) {
    const template = templates.get(stall.assetId);""",
      """  for (const stall of EASTBROOK_LAYOUT.market.stalls) {
    activeSource={id:stall.id,kind:'market_stall',model:stall.assetId,
      x:stall.position.x,z:stall.position.z};
    const template = templates.get(stall.assetId);""",
      'STALL_ORIGIN')
    s=once(s,
      """  for (const fence of EASTBROOK_LAYOUT.fences) {
    const template = templates.get(fence.assetId);""",
      """  for (const fence of EASTBROOK_LAYOUT.fences) {
    activeSource={id:fence.id,kind:'fence',model:fence.assetId,
      x:(fence.start.x+fence.end.x)/2,z:(fence.start.z+fence.end.z)/2};
    const template = templates.get(fence.assetId);""",
      'FENCE_ORIGIN')
    s=once(s,
      """  const batches: THREE.Mesh[] = [];
  const opaqueGeometry = mergeParts(opaque, 'micro opaque batch');""",
      """  if(studioMode)return {batches:studioPieces};
  const batches: THREE.Mesh[] = [];
  const opaqueGeometry = mergeParts(opaque, 'micro opaque batch');""",
      'EDITOR_ONLY_RETURN')
    return s

def patch_studio(s):
    if MARK in s:raise RuntimeError('P58_ALREADY_INSTALLED_STUDIO')
    if 'HIGHFLY_P57_QUICK_EDIT' not in s or 'HIGHFLY_P56_EDITABLE_STUDIO' not in s:
        raise RuntimeError('P58_REQUIRES_P57_PRIVATE_STAGE')
    s=once(s,
      "type Kind='building'|'vault'|'monument'|'fx'|'decor'|'mesh';",
      "type Kind='building'|'vault'|'monument'|'fx'|'decor'|'mesh'|'micro';\n// "+MARK,
      'MICRO_KIND')
    s=once(s,
      "  action:'hide_visual_preview'|'transform_preview'; requiresColliderReview:true;",
      "  action:'hide_visual_preview'|'transform_preview'|'remove_visual_proposal'; requiresColliderReview:true;",
      'DRAFT_ACTION')
    s=once(s,
      """  let n=0;
  for(const d of BUILTIN_WORLD.props.decorProps ?? []) {""",
      """  // Individual parts of ClaudeCraft's former static micro-batches:
  // these have REAL IDs rather than approximate scene mesh positions.
  for(const b of EASTBROOK_LAYOUT.civic.benches){
    records.push({id:b.id,kind:'micro',model:b.assetId,
      x:b.position.x,z:b.position.z,width:b.width,depth:b.depth,
      details:'Banco Eastbrook, geometría antes fusionada: mover/quitar solo borrador'});
  }
  for(const stall of EASTBROOK_LAYOUT.market.stalls){
    records.push({id:stall.id,kind:'micro',model:stall.assetId,
      x:stall.position.x,z:stall.position.z,
      width:stall.width,height:stall.height,depth:stall.depth,
      details:'Puesto de mercado real de ClaudeCraft; puede parecer mini casita'});
  }
  for(const f of EASTBROOK_LAYOUT.fences){
    records.push({id:f.id,kind:'micro',model:f.assetId,
      x:(f.start.x+f.end.x)/2,z:(f.start.z+f.end.z)/2,
      details:'Valla oficial de Eastbrook; preservar servicios/colisión al aplicar'});
  }
  let n=0;
  for(const d of BUILTIN_WORLD.props.decorProps ?? []) {""",
      'MICRO_ENTRIES')
    s=once(s,
      """    if(e.kind==='fx') return scene.getObjectByName('eastbrookRealmBuilderMonumentFx') ?? null;""",
      """    if(e.kind==='fx') return scene.getObjectByName('eastbrookRealmBuilderMonumentFx') ?? null;
    if(e.kind==='micro')return scene.getObjectByName('highflyMicro:'+e.id)??null;""",
      'FIND_MICRO')
    s=once(s,
      """         cursor.name.startsWith('highflyFreeBuilding:')) return cursor;""",
      """         cursor.name.startsWith('highflyFreeBuilding:') ||
         cursor.userData?.highflyMicroId) return cursor;""",
      'TAG_MICRO')
    s=once(s,
      """        const source=tagged.userData?.highflySourceDecor as
          {key:string;x:number;z:number}|undefined;""",
      """        const micro=tagged.userData?.highflyMicroId as string|undefined;
        if(micro){
          const item=this.entries.find(e=>e.id===micro&&e.kind==='micro');
          if(item){this.select(item,tagged,h.object);return;}
        }
        const source=tagged.userData?.highflySourceDecor as
          {key:string;x:number;z:number}|undefined;""",
      'CLICK_MICRO')
    s=once(s,
      """    const saveDraft=this.button('Guardar borrador + JSON',()=>this.saveDraft());
    ctr.append(this.hideButton,this.restoreButton,copy,exportButton,saveDraft);""",
      """    const saveDraft=this.button('Guardar borrador + JSON',()=>this.saveDraft());
    const removeVisual=this.button('Quitar (borrador)',()=>this.removeVisual());
    removeVisual.title='Quita únicamente la imagen en este editor; propuesta JSON con ID, nunca altera colisiones sin revisión';
    ctr.append(this.hideButton,this.restoreButton,removeVisual,copy,exportButton,saveDraft);""",
      'REMOVE_UI')
    s=once(s,
      """  private hide():void {
    const e=this.selected;""",
      """  private removeVisual():void {
    if(!this.selectedRoot||!this.selected)return;
    const e=this.selected;
    this.hide();
    this.drafts.set(e.id,{id:e.id,kind:e.kind,model:e.model,x:e.x,z:e.z,
      action:'remove_visual_proposal',requiresColliderReview:true,
      provisional:e.kind==='mesh'});
    this.showInfo();
  }
  private hide():void {
    const e=this.selected;""",
      'REMOVE_LOGIC')
    s=once(s,
      """        if(d.action==='hide_visual_preview')this.hide();""",
      """        if(d.action==='hide_visual_preview')this.hide();
        if(d.action==='remove_visual_proposal')this.removeVisual();""",
      'REMOVE_REPLAY')
    return s

def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()

def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    old={}
    for rel in (TOWN,STUDIO):
        file=STAGE/rel
        if not file.is_file() or file.is_symlink():raise RuntimeError('P58_STAGE_FILE_MISSING '+rel)
        old[rel]=file.read_text(encoding='utf8')
    if 'HIGHFLY_P57_QUICK_EDIT' not in old[STUDIO]:
        raise RuntimeError('P58_REQUIRES_P57_GREEN')
    if MARK in old[TOWN] or MARK in old[STUDIO]:
        raise RuntimeError('P58_ALREADY_APPLIED')
    updated={TOWN:patch_town(old[TOWN]),STUDIO:patch_studio(old[STUDIO])}
    status={
      'phase':'P58_INDIVIDUAL_EASTBROOK_MICRO_EDITOR','mode':'DRY_RUN',
      'originalGameRendering':'batched and unchanged',
      'editorOnly':'benches, market stalls, fences with IDs, click/drag/hide/remove preview',
      'removal':'JSON proposal, NOT permanent code deletion or sim collision change',
      'source':'ClaudeCraft v0.44.7 pinned and P57 private stage',
      'browserVerified':False
    }
    if not apply:
        print('[HIGHFLY P58] '+json.dumps(status,indent=2,ensure_ascii=False));return
    if OUT.exists() or OUT.is_symlink():
        raise RuntimeError('P58_BACKUP_EXISTS: do not overwrite; diagnose first')
    backups=[]
    try:
        for rel in old:
            src=STAGE/rel;dest=OUT/'backups'/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dest)
            if sha(src)!=sha(dest):raise RuntimeError('P58_BACKUP_HASH_BAD '+rel)
            backups.append((src,dest))
        for rel,content in updated.items():
            if (STAGE/rel).read_text(encoding='utf8')!=old[rel]:
                raise RuntimeError('P58_CONCURRENT_EDIT '+rel)
            (STAGE/rel).write_text(content,encoding='utf8')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        for original,backup in backups:
            if backup.is_file():shutil.copy2(backup,original)
        print('[HIGHFLY P58] ROLLBACK: preserved P57, no world-data changes',file=sys.stderr)
        raise
    status['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P58_STATUS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n')
    print('[HIGHFLY P58] '+json.dumps(status,indent=2,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--apply',action='store_true')
    cli=p.parse_args()
    run(cli.apply)
