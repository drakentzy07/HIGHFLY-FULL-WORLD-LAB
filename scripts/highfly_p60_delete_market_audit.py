#!/usr/bin/env python3
"""P60: keyboard Delete/Backspace for individually identified editor items;
and read-only binary provenance of Eastbrook's market stall, without copying.

P59 required. Never removes simulation entries/colliders/interactions.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
ORIGINAL=p9.ORIGINAL
OUT=ROOT/'.workspace/reports/highfly-p60'
STUDIO='src/editor/highfly_eastbrook_studio.ts'
MARK='HIGHFLY_P60_STABLE_DELETE'
ASSET='eastbrook_market_stall.glb'

def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f'P60_ANCHOR_DRIFT_{label}_{n}')
    return s.replace(a,b,1)

def patch_studio(s):
    if MARK in s:raise RuntimeError('P60_ALREADY_INSTALLED')
    for marker in ('HIGHFLY_P59_RAW_SCENE_PICK_TRACE',
                   'HIGHFLY_P58_SELECTABLE_MICRO_PROPS','HIGHFLY_P57_QUICK_EDIT'):
        if marker not in s:raise RuntimeError('P60_REQUIRES_P59_'+marker)
    s=once(s,
      '  private probeArmed=false;',
      """  private probeArmed=false;
  // HIGHFLY_P60_STABLE_DELETE. Global capture only in the private editor.
  private onStudioDeleteKey=(ev:KeyboardEvent):void=>{
    if(ev.key!=='Delete'&&ev.key!=='Backspace')return;
    if(ev.ctrlKey||ev.metaKey||ev.altKey)return;
    const target=ev.target as HTMLElement|null;
    if(target?.isContentEditable||target?.closest('input,textarea,select,[contenteditable="true"]'))
      return;
    const e=this.selected;
    if(!e||!this.selectedRoot)return;
    // An opaque mesh uuid from a diagnostic is not an authored world ID.
    if(e.kind==='mesh'){
      this.selectedGroupInfo='No se permite borrar una malla provisional. Elegí el registro de origen por ID.';
      this.showInfo();return;
    }
    ev.preventDefault();ev.stopImmediatePropagation();
    this.removeVisual();
    // The deleted visual is removed from selection. Next click selects
    // another object; the source catalog keeps an undo/restore entry.
    this.selected=null;this.selectedRoot=null;this.selectedHit=null;
    this.selectedGroupInfo='Quitado visualmente: '+e.id+
      ' · cambio guardado como propuesta. Se puede restaurar desde el catálogo.';
    this.populateTransform();
    this.renderList();
    this.showInfo();
  };""",
      'DELETE_CALLBACK')
    s=once(s,
      """    this.panel.append(header,intro,this.search,this.list,this.info,this.probePanel,ctr);
    this.parent.appendChild(this.panel);""",
      """    this.panel.append(header,intro,this.search,this.list,this.info,this.probePanel,ctr);
    this.parent.appendChild(this.panel);
    // Studio intercepts Delete before the classic custom-map editor does.
    window.addEventListener('keydown',this.onStudioDeleteKey,true);""",
      'KEY_INSTALL')
    s=once(s,
      """        if(!item.safe)return;
        const obj=item.object;
        const id='mesh:'+obj.uuid;""",
      """        if(!item.safe)return;
        const obj=item.object;
        // A named official source takes precedence over a transient mesh
        // uuid. Selecting a single part of a stall must select WHOLE stall.
        const exact=this.rootForHit(obj);
        const sourceId=exact?.userData?.highflyMicroId as string|undefined;
        if(sourceId){
          const entry=this.entries.find(e=>e.id===sourceId&&e.kind==='micro');
          if(entry){this.select(entry,exact,obj);return;}
        }
        const id='mesh:'+obj.uuid;""",
      'PROBE_PICK_STABLE_ID')
    s=once(s,
      """    this.panel.remove();this.hidden.clear();this.drafts.clear();""",
      """    window.removeEventListener('keydown',this.onStudioDeleteKey,true);
    this.panel.remove();this.hidden.clear();this.drafts.clear();""",
      'KEY_TEARDOWN')
    return s

def fingerprint(path:Path)->dict:
    data={'exists':path.is_file() and not path.is_symlink()}
    if data['exists']:
        data.update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return data

def market_audit()->dict:
    """Local file provenance only; do NOT copy any model into the public repo."""
    out={}
    for name,root in [('original_reference',ORIGINAL),('highfly_private_stage',STAGE)]:
        # Finds both ordinary model paths and Vite hashed media aliases.
        matches=[]
        pub=root/'public'
        if pub.is_dir() and not pub.is_symlink():
            for p in pub.rglob('*eastbrook_market_stall*'):
                if len(matches)>=16:break
                if p.is_file() and not p.is_symlink() and p.suffix.lower()=='.glb':
                    meta=fingerprint(p)
                    meta['path']=str(p.relative_to(root))
                    matches.append(meta)
        out[name]=matches
    origHashes={v['sha256'] for v in out['original_reference'] if 'sha256' in v}
    stageHashes={v['sha256'] for v in out['highfly_private_stage'] if 'sha256' in v}
    result={'sourceModel':'/models/props/eastbrook_market_stall.glb',
       'sourceCode':'scripts/assets/eastbrook_town/furniture.js -> buildMarketStall',
       'expectedLook':'4 timber posts, striped cloth canopy, market counter and goods',
       'meshes':out,
       'sameGeometryBytes':bool(origHashes and stageHashes and origHashes.intersection(stageHashes)),
       'conclusion':'Exact file comparison only; when files missing, inspect effective manifest URL. Never infer licensed status from a path alone.',
       'userAssetSourceNotPublished':True}
    return result

def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(apply=False):
    p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
    editor=STAGE/STUDIO
    if not editor.is_file() or editor.is_symlink():
        raise RuntimeError('P60_EDITOR_NOT_FOUND')
    before=editor.read_text(encoding='utf8')
    patch=patch_studio(before)
    audit=market_audit()
    status={'phase':'P60_EDITOR_DELETE_MARKET_ASSET_AUDIT','mode':'DRY_RUN',
       'editorOnly':True,'keyboard':'Delete/Backspace = remove visual draft for stable IDs only',
       'afterDelete':'selection cleared, next click picks a different object; restoration available',
       'market':audit,'worldGameDataChanged':False,'browserVerified':False}
    if not apply:
        print('[HIGHFLY P60] '+json.dumps(status,indent=2,ensure_ascii=False));return
    if OUT.exists() or OUT.is_symlink():
        if OUT.is_symlink() or not OUT.is_dir():
            raise RuntimeError('P60_UNSAFE_BACKUP_PATH')
        if (OUT/'P60_STATUS.json').exists():
            raise RuntimeError('P60_ALREADY_BUILT')
        history=OUT.parent/'highfly-p60-preserved-attempts'
        if history.is_symlink():raise RuntimeError('P60_ARCHIVE_UNSAFE')
        history.mkdir(parents=True,exist_ok=True)
        dest=history/('attempt-'+str(time.time_ns()))
        if dest.exists():raise RuntimeError('P60_BACKUP_COLLISION')
        OUT.rename(dest)
        print('[HIGHFLY P60] Previous failed backups preserved: '+str(dest))
    backup=OUT/'backups'/STUDIO
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(editor,backup)
    if sha(editor)!=sha(backup):raise RuntimeError('P60_BACKUP_MISMATCH')
    try:
        if editor.read_text(encoding='utf8')!=before:raise RuntimeError('P60_CONCURRENT_EDITOR_CHANGE')
        editor.write_text(patch,encoding='utf8')
        subprocess.run([sys.executable,str(ROOT/'scripts/highfly_p9_private_build_smoke.py')],cwd=ROOT,check=True)
    except BaseException:
        shutil.copy2(backup,editor)
        print('[HIGHFLY P60] RED — restored original P59 editor',file=sys.stderr)
        raise
    OUT.mkdir(parents=True,exist_ok=True)
    status['mode']='BUILD_GREEN_BROWSER_PENDING'
    (OUT/'P60_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    (OUT/'MARKET_ASSET_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print('[HIGHFLY P60] '+json.dumps(status,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    run(parser.parse_args().apply)
