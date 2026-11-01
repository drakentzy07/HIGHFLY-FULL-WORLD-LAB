#!/usr/bin/env python3
"""HIGHFLY P55: upgrade existing editor with private Eastbrook Studio inspection.

Does not create a second editor. ?hf_eastbrook_studio=1 makes the existing
editor preview the official BUILTIN_WORLD, rather than the custom-map world
which intentionally excludes Eastbrook buildings. Studio is read-only to
simulation; selection/hide are reversible visual previews and exported drafts.
No KayKit media, savegame, NPC, gameplay collision, or quest mutation.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p55"
MARK="HIGHFLY_P55_EXISTING_EDITOR_STUDIO"
APP="src/editor/app.ts"
VIEW="src/editor/3d/viewport.ts"
PROPS="src/render/props.ts"
STUDIO="src/editor/highfly_eastbrook_studio.ts"
STUDIO_CSS="src/editor/highfly_eastbrook_studio.css"
LOAD_CSS="public/highfly/p55_loading.css"
HTML="index.html"

STUDIO_TS=r"""
// HIGHFLY_P55_EXISTING_EDITOR_STUDIO
// Extension of ClaudeCraft's existing 3D map editor. Source records are read-only.
// Hiding is a scene-only diagnostic; never deletes sim, colliders or saved maps.
import * as THREE from 'three';
import type { Renderer } from '../render/renderer';
import { BUILTIN_WORLD } from '../sim/data';
import { EASTBROOK_LAYOUT } from '../sim/eastbrook_layout';
import { terrainHeight } from '../sim/world';
import { WORLD_SEED } from '../sim/world_seed';
import './highfly_eastbrook_studio.css';

type Kind='building'|'vault'|'monument'|'decor';
interface Entry {
  id:string; kind:Kind; model:string; x:number; z:number;
  width?:number; depth?:number; height?:number;
  details?:string;
}
interface Draft {
  id:string;kind:Kind;model:string;x:number;z:number;
  action:'hide_visual_preview'; requiresColliderReview:true;
}
const MIN_X=-120, MAX_X=50, MIN_Z=-160, MAX_Z=-48;
function format(n:number):string {return Number(n.toFixed(2)).toString();}
function modelName(e:Entry):string {return e.model.split('/').pop() || e.model;}
function makeEntries():Entry[] {
  const records:Entry[]=[];
  for(const b of EASTBROOK_LAYOUT.buildings) {
    records.push({
      id:b.id,kind:'building',model:b.assetId,x:b.position.x,z:b.position.z,
      width:b.nativeDimensions.width,depth:b.nativeDimensions.depth,
      height:b.nativeDimensions.height,details:'Edificio oficial: conservar ID y servicios',
    });
  }
  const v=EASTBROOK_LAYOUT.weeklyVault;
  records.push({id:v.id,kind:'vault',model:'eastbrook weekly vault',x:v.x,z:v.z,
    width:v.w,depth:v.d,height:v.height,details:'Bóveda semanal: conservar keeper y colisión'});
  const m=EASTBROOK_LAYOUT.civic.monument;
  records.push({id:m.id,kind:'monument',model:m.assetId,x:m.position.x,z:m.position.z,
    height:m.height,width:m.nativeDimensions.width,depth:m.nativeDimensions.depth,
    details:'Body y FX; confirmar el cono con ocultación visual reversible'});
  let n=0;
  for(const d of BUILTIN_WORLD.props.decorProps ?? []) {
    if(d.x<MIN_X || d.x>MAX_X || d.z<MIN_Z || d.z>MAX_Z) continue;
    const prefix='decor:'+d.key+'@'+format(d.x)+','+format(d.z);
    records.push({
      id:prefix+'#'+n++,kind:'decor',model:d.key,x:d.x,z:d.z,
      height:d.h,details:'Decoración original; origen ZONE1_PROPS/decorProps por posición. Collider r='+
        (d.r ?? 0)+'; escala declarada='+(d.scale ?? 1),
    });
  }
  return records;
}
export class HighflyEastbrookStudio {
  private readonly panel:HTMLDivElement;
  private readonly info:HTMLPreElement;
  private readonly search:HTMLInputElement;
  private readonly entries=makeEntries();
  private readonly ray=new THREE.Raycaster();
  private readonly ndc=new THREE.Vector2();
  private readonly drafts=new Map<string,Draft>();
  private readonly hidden=new Map<string,THREE.Object3D[]>();
  private selected:Entry|null=null;
  private selectedRoot:THREE.Object3D|null=null;
  private selectedHit:THREE.Object3D|null=null;
  private selectedGroupInfo='';
  private list:HTMLDivElement;
  private hideButton:HTMLButtonElement;
  private restoreButton:HTMLButtonElement;

  constructor(private readonly parent:HTMLElement,
              private readonly renderer:Renderer,
              private readonly canvas:HTMLCanvasElement) {
    this.panel=document.createElement('div');
    this.panel.id='hf-studio-p55';
    const header=document.createElement('div');header.className='hf-studio-title';
    header.textContent='HIGHFLY · EDITOR 2.0 / EASTBROOK';
    const intro=document.createElement('p');
    intro.textContent='Vista oficial de ClaudeCraft v0.44.7. Elegí una estructura o hacé clic en el mundo. Los cambios son ensayos visuales; no modifican NPC, misiones ni colisiones.';
    this.search=document.createElement('input');
    this.search.placeholder='Buscar por ID, modelo, tipo...';
    this.search.setAttribute('aria-label','Filtrar estructuras de Eastbrook');
    this.search.addEventListener('input',()=>this.renderList());
    this.list=document.createElement('div');
    this.list.className='hf-studio-list';
    this.info=document.createElement('pre');
    this.info.className='hf-studio-info';
    this.info.textContent='Seleccioná una casa, monumento o decoración. El catálogo incluye las 11 casas oficiales, bóveda y decorProps.';
    this.hideButton=this.button('Ocultar visualmente',()=>this.hide());
    this.restoreButton=this.button('Restaurar visual',()=>this.restore());
    const copy=this.button('Copiar diagnóstico',()=>this.copy());
    const exportButton=this.button('Exportar cambios JSON',()=>this.exportDraft());
    const ctr=document.createElement('div');ctr.className='hf-studio-actions';
    ctr.append(this.hideButton,this.restoreButton,copy,exportButton);
    this.panel.append(header,intro,this.search,this.list,this.info,ctr);
    this.parent.appendChild(this.panel);
    this.renderList();
    this.showInfo();
  }

  private button(label:string,onClick:()=>void):HTMLButtonElement {
    const b=document.createElement('button');b.type='button';
    b.textContent=label;b.addEventListener('click',onClick);return b;
  }
  private findRoot(e:Entry):THREE.Object3D|null {
    const scene=this.renderer.scene;
    if(e.kind==='building') return scene.getObjectByName('eastbrookBuilding:'+e.id) ?? null;
    if(e.kind==='monument') return scene.getObjectByName('eastbrookRealmBuilderMonumentFxBody') ?? null;
    // The weekly vault may be named differently in the renderer;
    // do not silently guess a root for a shared batch.
    if(e.kind==='vault') return scene.getObjectByName('eastbrookBuilding:'+e.id) ?? null;
    if(e.kind==='decor') return scene.getObjectByName('highflyDecor:'+e.model+'@'+format(e.x)+','+format(e.z)) ?? null;
    return null;
  }
  private rootForHit(obj:THREE.Object3D):THREE.Object3D|null {
    let cursor:THREE.Object3D|null=obj;
    while(cursor) {
      if(cursor.userData?.eastbrookBuildingId || cursor.name.startsWith('highflyDecor:')) return cursor;
      if(cursor.name==='eastbrookRealmBuilderMonumentFxBody' ||
         cursor.name==='eastbrookRealmBuilderMonumentFx') return cursor;
      if(cursor.name==='eastbrookTownRebuild') return null;
      cursor=cursor.parent;
    }
    return null;
  }
  private descendantsFor(e:Entry, root:THREE.Object3D):THREE.Object3D[] {
    if(e.kind==='monument') {
      const fx=this.renderer.scene.getObjectByName('eastbrookRealmBuilderMonumentFx');
      return fx && fx!==root ? [root,fx] : [root];
    }
    return [root];
  }
  private renderList():void {
    const query=this.search.value.toLowerCase().trim();
    const matches=this.entries.filter(e=>
      (e.id+' '+e.model+' '+e.kind).toLowerCase().includes(query));
    this.list.replaceChildren();
    for(const e of matches.slice(0,180)) {
      const btn=this.button(e.id+'  ('+format(e.x)+', '+format(e.z)+')',()=>this.select(e));
      btn.className='hf-studio-row';
      if(this.selected?.id===e.id)btn.classList.add('selected');
      this.list.appendChild(btn);
    }
  }
  private select(e:Entry, root?:THREE.Object3D|null, hit?:THREE.Object3D|null):void {
    this.selected=e;
    this.selectedRoot=root===undefined?this.findRoot(e):root;
    this.selectedHit=hit??null;
    this.selectedGroupInfo='';
    if(hit){
      const hierarchy:string[]=[];
      let cur:THREE.Object3D|null=hit;
      for(let i=0;i<10 && cur;i++,cur=cur.parent)hierarchy.unshift(cur.name||cur.type);
      this.selectedGroupInfo=hierarchy.join(' > ');
    }
    this.renderList();
    this.showInfo();
  }
  pick(clientX:number,clientY:number):void {
    const rect=this.canvas.getBoundingClientRect();
    this.ndc.set((clientX-rect.left)/Math.max(1,rect.width)*2-1,
      -(clientY-rect.top)/Math.max(1,rect.height)*2+1);
    this.ray.setFromCamera(this.ndc,this.renderer.camera);
    const town=this.renderer.scene.getObjectByName('eastbrookTownRebuild');
    const decorRoots:THREE.Object3D[]=[];
    this.renderer.scene.traverse(o=>{
      if(o.name.startsWith('highflyDecor:'))decorRoots.push(o);
    });
    const hits=this.ray.intersectObjects(town?[town,...decorRoots]:decorRoots,true);
    for(const h of hits) {
      const tagged=this.rootForHit(h.object);
      if(tagged) {
        const source=tagged.userData?.highflySourceDecor as
          {key:string;x:number;z:number}|undefined;
        if(source){
          const decor=this.entries.find(e=>e.kind==='decor'&&e.model===source.key&&
            Math.abs(e.x-source.x)<0.001&&Math.abs(e.z-source.z)<0.001);
          if(decor){this.select(decor,tagged,h.object);return;}
        }
        const id=String(tagged.userData?.eastbrookBuildingId??'');
        const kind=tagged.name.includes('RealmBuilder')?'monument':'building';
        const found=this.entries.find(e=>e.id===(kind==='monument'?
          'eastbrook_realm_builder_monument':id));
        if(found){this.select(found,tagged,h.object);return;}
      }
      // Unknown/batched mesh: report geometry but forbid unsafe deletion.
      const mat=h.object instanceof THREE.Mesh
        ?(Array.isArray(h.object.material)
            ?h.object.material.map(m=>m.name).join(',')
            :h.object.material.name):'';
      const near=this.entries
        .map(e=>({e,d:Math.hypot(e.x-h.point.x,e.z-h.point.z)}))
        .sort((a,b)=>a.d-b.d)[0];
      this.selected=near?.d<8?near.e:null;
      this.selectedRoot=null;
      this.selectedHit=h.object;
      this.selectedGroupInfo='MALLA AGRUPADA SIN ID INDIVIDUAL: '+
        (h.object.name||h.object.type)+' / mat='+mat+
        '\nCercanía a registro ≠ identidad demostrada. No habilitar borrado.';
      this.showInfo();this.renderList();return;
    }
    // A ray that misses individual town meshes may hit a prop from ZONE1:
    // match to source coordinates for audit, never claim exact object identity.
    const plane=new THREE.Plane(new THREE.Vector3(0,1,0),0);
    const pos=new THREE.Vector3();
    if(this.ray.ray.intersectPlane(plane,pos)){
      const near=this.entries.map(e=>({e,d:Math.hypot(e.x-pos.x,e.z-pos.z)}))
        .sort((a,b)=>a.d-b.d)[0];
      if(near && near.d<10){
        this.select(near.e,null);
        this.selectedGroupInfo='COINCIDENCIA ESPACIAL SOLAMENTE (no hubo raycast con ID).';
        this.showInfo();return;
      }
    }
    this.selected=null;this.selectedRoot=null;this.selectedHit=null;
    this.selectedGroupInfo='No se pudo atribuir esta geometría a una entidad individual.';
    this.showInfo();
  }
  private showInfo():void {
    const e=this.selected;
    if(!e){
      this.info.textContent=this.selectedGroupInfo ||
        'Seleccioná en la lista o hacé clic en el mapa. Los props fusionados requieren auditoría por ID antes de ocultarlos.';
    } else {
      const root=this.selectedRoot;
      const box=root?new THREE.Box3().setFromObject(root):null;
      const size=box && !box.isEmpty()?box.getSize(new THREE.Vector3()):null;
      this.info.textContent=[
        'ID: '+e.id,
        'Fuente: '+e.kind,
        'Modelo: '+modelName(e),
        'Posición: x='+format(e.x)+' z='+format(e.z),
        'Dimensión declarada: '+[e.width??'?',e.height??'?',e.depth??'?'].join(' × '),
        'Dimensión real: '+(size?size.toArray().map(format).join(' × '):'Sin root aislable'),
        'Escena: '+(root?.name??'no atribuida individualmente'),
        'Estado: '+(this.hidden.has(e.id)?'OCULTO SÓLO EN ESTE EDITOR':'visible'),
        e.details??'',this.selectedGroupInfo,
      ].filter(Boolean).join('\n');
    }
    this.hideButton.disabled=!(e && this.selectedRoot);
    this.restoreButton.disabled=!(e && this.hidden.has(e.id));
  }
  private hide():void {
    const e=this.selected;
    if(!e || !this.selectedRoot)return;
    const targets=this.descendantsFor(e,this.selectedRoot);
    this.hidden.set(e.id,targets);
    this.drafts.set(e.id,{id:e.id,kind:e.kind,model:e.model,x:e.x,z:e.z,
      action:'hide_visual_preview',requiresColliderReview:true});
    this.showInfo();
  }
  private restore():void {
    const id=this.selected?.id;
    if(!id)return;
    this.hidden.delete(id);this.drafts.delete(id);
    this.showInfo();
  }
  tick():void {
    // Renderer reveal/LOD can reset visibility on every sync. The editor's
    // preview is reapplied AFTER sync; the player's game scene is untouched.
    for(const roots of this.hidden.values())for(const root of roots)root.visible=false;
  }
  private diagnosis():string {
    return JSON.stringify({
      phase:'HIGHFLY_P55_EDITOR2_EASTBROOK',source:'World of ClaudeCraft v0.44.7',
      selected:this.selected,selectedMesh:this.selectedHit?.name??null,
      hierarchy:this.selectedGroupInfo,
      entryCount:this.entries.length,
      changes:[...this.drafts.values()],note:'visual-only proposals; not sim edits',
    },null,2);
  }
  private copy():void {
    void navigator.clipboard?.writeText(this.diagnosis());
  }
  private exportDraft():void {
    const data=this.diagnosis();
    const link=document.createElement('a');
    const uri=URL.createObjectURL(new Blob([data],{type:'application/json'}));
    link.href=uri;link.download='HIGHFLY_P55_EASTBROOK_EDITOR_DRAFT.json';
    link.click();window.setTimeout(()=>URL.revokeObjectURL(uri),1000);
  }
  dispose():void {this.panel.remove();this.hidden.clear();this.drafts.clear();}
}
""".strip()+"\n"

STUDIO_STYLE=r"""
/* HIGHFLY_P55_EXISTING_EDITOR_STUDIO - editor-only, no impact on game HUD */
.editor-3d-host {position:relative}
#hf-studio-p55 {
 position:absolute;top:12px;left:12px;z-index:120;width:min(355px,32vw);
 max-height:calc(100% - 24px);overflow:auto;padding:11px;
 color:#e8e4fc;background:#080f23ed;border:1px solid #aa6dff;
 border-radius:12px;box-shadow:0 8px 28px #0008;font:12px/1.4 "Segoe UI",sans-serif;
}
#hf-studio-p55 .hf-studio-title{font-weight:800;color:#f2c6ff;letter-spacing:.05em}
#hf-studio-p55 p{margin:6px 0 8px;font-size:11px;color:#b9c3df}
#hf-studio-p55 input{box-sizing:border-box;width:100%;padding:7px;
 color:#fff;background:#10142e;border:1px solid #66628f;border-radius:6px}
#hf-studio-p55 .hf-studio-list{max-height:min(22dvh,180px);overflow:auto;margin:7px 0}
#hf-studio-p55 button{cursor:pointer}
#hf-studio-p55 .hf-studio-row{display:block;width:100%;margin:2px 0;
 background:#14233c;color:#dbeaf9;text-align:left;border:1px solid #293950;
 padding:5px 8px;border-radius:5px;font-size:10px}
#hf-studio-p55 .hf-studio-row.selected{border-color:#f8c1ff;background:#38244b}
#hf-studio-p55 .hf-studio-info{min-height:95px;max-height:25dvh;overflow:auto;
 white-space:pre-wrap;overflow-wrap:anywhere;background:#050b19;padding:8px;
 border:1px solid #39445e;border-radius:6px;font:11px/1.5 Consolas,monospace}
#hf-studio-p55 .hf-studio-actions{display:flex;flex-wrap:wrap;gap:5px}
#hf-studio-p55 .hf-studio-actions button{flex:1 1 42%;font-size:11px;padding:7px}
#hf-studio-p55 button:disabled{opacity:.4;cursor:not-allowed}
@media (max-width:1100px){#hf-studio-p55{width:min(320px,48vw)}}
""".strip()+"\n"

LOADING_STYLE=r"""
/* HIGHFLY_P55_EXISTING_EDITOR_STUDIO: premium loading reflow; native progress. */
#loading-screen {
 background-color:#080719!important;
 background-image:url('/highfly/official/highfly_splash.png'),radial-gradient(ellipse at center,#27104b,#070815 85%)!important;
 background-size:auto 89dvh,cover!important;
 background-position:center 42%,center!important;
 background-repeat:no-repeat!important;
}
#loading-screen::before,#loading-screen::after{content:none!important;display:none!important}
#loading-screen .ls-progress{
 position:absolute!important;box-sizing:border-box!important;display:block!important;
 left:50%!important;right:auto!important;top:auto!important;
 transform:translateX(-50%)!important;bottom:max(6px,1.5dvh)!important;
 width:min(770px,78vw)!important;height:81px!important;min-height:0!important;
 max-height:81px!important;border:0!important;margin:0!important;padding:0!important;
 background:transparent!important;overflow:visible!important;z-index:20!important;
}
#loading-screen #ls-status{
 position:absolute!important;left:0!important;top:0!important;
 display:block!important;width:100%!important;height:21px!important;
 padding:0!important;margin:0!important;text-align:center!important;
 font:700 clamp(12px,1.55vw,17px)/21px Georgia,serif!important;
 color:#fff5ff!important;text-shadow:0 1px 6px #06031a,0 1px 10px #190333!important;
}
#loading-screen .ls-bar{
 position:absolute!important;top:24px!important;left:0!important;
 display:block!important;width:100%!important;height:13px!important;
 margin:0!important;padding:0!important;box-sizing:border-box!important;
 border:1px solid #edb8f7!important;border-radius:20px!important;
 background:#050b28c9!important;overflow:hidden!important;
}
#loading-screen #ls-fill{display:block!important;height:100%!important}
#loading-screen #ls-tip{
 position:absolute!important;top:42px!important;left:50%!important;right:auto!important;
 transform:translateX(-50%)!important;display:flex!important;
 align-items:center!important;justify-content:center!important;
 width:100%!important;min-height:30px!important;max-height:33px!important;
 height:33px!important;box-sizing:border-box!important;
 padding:2px 10px!important;margin:0!important;text-align:center!important;
 background:#05091ccb!important;border:1px solid #633b8a99!important;border-radius:7px!important;
 color:#eee6ff!important;font:clamp(10px,.93vw,12px)/14px Arial,sans-serif!important;
 white-space:normal!important;overflow:hidden!important;word-break:normal!important;
}
@media (pointer:coarse) and (orientation:landscape), (max-height:430px) and (orientation:landscape){
 #loading-screen{background-size:auto 88dvh,cover!important}
 #loading-screen .ls-progress{bottom:5px!important;height:65px!important;max-height:65px!important;width:79vw!important}
 #loading-screen #ls-status{top:0!important;height:17px!important;font-size:11px!important;line-height:17px!important}
 #loading-screen .ls-bar{top:19px!important;height:11px!important}
 #loading-screen #ls-tip{top:33px!important;height:29px!important;min-height:29px!important;max-height:29px!important;font-size:9px!important;line-height:12px!important}
}
""".strip()+"\n"

def replace(source, old, new, label):
    count=source.count(old)
    if count!=1:raise RuntimeError(f"P55_ANCHOR_DRIFT_{label}={count}")
    return source.replace(old,new,1)
def patch_app(source):
    if MARK in source:raise RuntimeError("P55_ALREADY_APPLIED_APP")
    source=replace(source,"  private rebuildActiveWorld(): void {\n    const map = this.map;",
      """  private rebuildActiveWorld(): void {
    // HIGHFLY_P55_EXISTING_EDITOR_STUDIO: studio renders the OFFICIAL
    // world, unlike the custom editor which strips Eastbrook from props.
    if (new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1') {
      this.activeWorld = BUILTIN_WORLD;
      setActiveWorldContent(BUILTIN_WORLD);
      return;
    }
    const map = this.map;""","ACTIVE_WORLD")
    source=replace(source,"  private setTool(tool: EditorTool): void {\n    this.tool = tool;",
      """  private setTool(tool: EditorTool): void {
    // Studio intentionally cannot modify sim/colliders or saved world records.
    if (new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1') {
      tool = 'select';
    }
    this.tool = tool;""","READ_ONLY")
    return source
def patch_view(source):
    if MARK in source:raise RuntimeError("P55_ALREADY_APPLIED_VIEW")
    source=replace(source,
      "import { Renderer } from '../../render/renderer';",
      "import { Renderer } from '../../render/renderer';\nimport { BUILTIN_WORLD } from '../../sim/data';\nimport { HighflyEastbrookStudio } from '../highfly_eastbrook_studio';","IMPORT")
    source=replace(source,"  private renderer: Renderer | null = null;",
      "  private renderer: Renderer | null = null;\n  private hfStudio: HighflyEastbrookStudio | null = null;","FIELD")
    source=replace(source,"    const world = customMapToWorldContent(this.map);",
      """    // HIGHFLY_P55_EXISTING_EDITOR_STUDIO: use full official world only
    // on the explicit private editor query; normal editor stays unchanged.
    const world = new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1'
      ? BUILTIN_WORLD : customMapToWorldContent(this.map);""","WORLD")
    source=replace(source,"    this.renderer.placedAssets.rebuildAll(placementsToRenderAssets(this.map.placements), true);",
      """    this.renderer.placedAssets.rebuildAll(placementsToRenderAssets(this.map.placements), true);
    if (new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1') {
      this.hfStudio = new HighflyEastbrookStudio(this.parent,this.renderer,this.canvas);
    }""","STUDIO_BOOT")
    source=replace(source,"    this.renderer = null;\n    this.sim = null;",
      "    this.hfStudio?.dispose();\n    this.hfStudio = null;\n    this.renderer = null;\n    this.sim = null;","TEARDOWN")
    source=replace(source,"    this.renderer.sync(1, DT, null);",
      "    this.renderer.sync(1, DT, null);\n    this.hfStudio?.tick();","TICK")
    source=replace(source,
      "      this.hooks.onTap(ev.clientX, ev.clientY, this.surfaceAt(ev.clientX, ev.clientY));",
      """      if (this.hfStudio) this.hfStudio.pick(ev.clientX, ev.clientY);
      else this.hooks.onTap(ev.clientX, ev.clientY, this.surfaceAt(ev.clientX, ev.clientY));""","PICK")
    return source
def patch_props(source):
    if MARK in source:raise RuntimeError("P55_ALREADY_APPLIED_PROPS")
    old="""    g.rotation.y = d.rot ?? 0;
    group.add(shadowed(g));
    if (d.r) {"""
    new="""    g.rotation.y = d.rot ?? 0;
    // HIGHFLY_P55_EXISTING_EDITOR_STUDIO: only private editor preview.
    // Keep Eastbrook decor separated from static batch so a click maps back
    // to the source model and exact authored x/z. No game build changes.
    if (typeof window !== 'undefined' &&
        new URLSearchParams(window.location.search).get('hf_eastbrook_studio') === '1' &&
        d.x >= -120 && d.x <= 50 && d.z >= -160 && d.z <= -48) {
      g.name = 'highflyDecor:' + d.key + '@' + Number(d.x.toFixed(2)) + ',' + Number(d.z.toFixed(2));
      g.userData.highflySourceDecor = { key: d.key, x: d.x, z: d.z };
      g.traverse((obj) => {
        if (obj instanceof THREE.Mesh) keepFromMerge.add(obj);
      });
    }
    group.add(shadowed(g));
    if (d.r) {"""
    return replace(source,old,new,'DECOR_SOURCE_TAGS')

def patch_html(source):
    if MARK in source:raise RuntimeError("P55_ALREADY_APPLIED_HTML")
    if 'HIGHFLY_P54_EASTBROOK_SOURCE_CORRECTION' not in source:
      raise RuntimeError('P55_REQUIRES_P54')
    return replace(source,'</head>',
      '<!-- '+MARK+' -->\n<link rel="stylesheet" href="/highfly/p55_loading.css" />\n</head>',
      'HTML')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    originals={}
    for rel in (APP,VIEW,PROPS,HTML):
      f=STAGE/rel
      if not f.is_file() or f.is_symlink():raise RuntimeError('P55_PRIVATE_EDITOR_FILE_MISSING '+rel)
      originals[rel]=f.read_text(encoding='utf8')
    changed={APP:patch_app(originals[APP]),VIEW:patch_view(originals[VIEW]),
             PROPS:patch_props(originals[PROPS]),HTML:patch_html(originals[HTML])}
    new={STUDIO:STUDIO_TS,STUDIO_CSS:STUDIO_STYLE,LOAD_CSS:LOADING_STYLE}
    for rel in new:
      if (STAGE/rel).exists() or (STAGE/rel).is_symlink():raise RuntimeError('P55_OUTPUT_EXISTS '+rel)
    status={'phase':'P55_EXISTING_EDITOR_EASTBROOK_STUDIO','mode':'DRY_RUN',
      'editor':'/editor.html?hf_eastbrook_studio=1','realOfficialWorld':True,
      'pick':'11 official buildings, weekly vault, monument, and individually tagged Eastbrook decorProps',
      'previewOnly':'hide identifiable render groups with restoration, export JSON',
      'unknownBatch':'never delete without stable ID',
      'loading':'small centered background + native bar in reserved bottom band',
      'private':'ensure Codespaces port visibility PRIVATE; query flag alone is not authentication',
      'gameplayQuestSaveCollidersChanged':False,'browserVerified':False}
    if not apply:
      print('[HIGHFLY P55] '+json.dumps(status,ensure_ascii=False,indent=2));return status
    backups=[];created=[]
    try:
      for rel in originals:
        source=STAGE/rel;dest=OUT/'backups'/rel
        if dest.exists() or dest.is_symlink():raise RuntimeError('P55_BACKUP_EXISTS '+rel)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        if sha(source)!=sha(dest):raise RuntimeError('P55_BACKUP_SHA_FAILED '+rel)
        backups.append((source,dest))
      for rel,value in new.items():
        dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('x',encoding='utf8') as out:out.write(value)
        created.append(dest)
      for rel,value in changed.items():
        dest=STAGE/rel
        if dest.read_text(encoding='utf8')!=originals[rel]:raise RuntimeError('P55_CONCURRENT_EDIT '+rel)
        dest.write_text(value,encoding='utf8')
      subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],
        cwd=str(ROOT),check=True)
    except BaseException:
      for source,backup in backups:
        if backup.is_file():shutil.copy2(backup,source)
      for dest in created:
        if dest.is_file():dest.unlink()
      print('[HIGHFLY P55] RED - rolled back to original P54 stage',file=sys.stderr)
      raise
    OUT.mkdir(parents=True,exist_ok=True)
    status['mode']='BUILD_GREEN_NOT_BROWSER_VERIFIED'
    (OUT/'P55_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('[HIGHFLY P55] '+json.dumps(status,ensure_ascii=False,indent=2))
    return status
if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--apply',action='store_true')
    run(cli.parse_args().apply)
