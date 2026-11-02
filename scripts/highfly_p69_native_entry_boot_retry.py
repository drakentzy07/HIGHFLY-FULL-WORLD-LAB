#!/usr/bin/env python3
"""P69 isolated entry only: trial the proven P43 'retry import main.ts' rescue.

Adds an OPT-IN script ?hf_p69_boot=1. Preserves original main.ts module tag,
the entire game, HTML entry controls, loader styling, NPC/GLB/quest/Sim, FURY,
and P41 saves. Only P69's index.html changes + one JS asset. P64/P43 untouched.
No fake login, progress, or manufactured game state. Save exact index backup.
"""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p69-restore-lab'
HTML=LAB/'index.html'
JS=LAB/'public/highfly/p69_native_boot_retry.js'
BACKUP=LAB/'.hf-p69-before-native-boot-retry.html'
REPORT=WORK/'reports/highfly-world7/P69_ENTRY_NATIVE_BOOT_RETRY.json'
MARK='HIGHFLY_P69_ORIGINAL_ENTRY_IMPORT_RETRY'
ENTRY='<script type="module" src="/src/main.ts"></script>'
ADD='<script defer src="/highfly/p69_native_boot_retry.js"></script>'
CODE=r"""/* HIGHFLY_P69_ORIGINAL_ENTRY_IMPORT_RETRY
   Entry investigation from the observed P43 behavior: an automatic main.ts
   module script failed but import('/src/main.ts') later completed.
   Runs ONLY with ?hf_p69_boot=1. Does not spoof server mode or init game state.
   It invokes the SAME unchanged original main module once more when the native
   selector is still online after page load.
*/
(function(){
 'use strict';
 if(!new URLSearchParams(location.search).has('hf_p69_boot'))return;
 let pending=false;
 let reportElement=null;
 function getReport(){
   if(reportElement)return reportElement;
   reportElement=document.createElement('div');
   reportElement.id='hf-p69-entry-boot-status';
   reportElement.setAttribute('role','status');
   reportElement.style.cssText='position:fixed;left:10px;top:10px;z-index:2147483600;max-width:min(480px,90vw);padding:8px 12px;background:rgba(4,14,30,.96);color:#edfbff;border:1px solid #75c9e9;border-radius:8px;font:12px/1.4 system-ui;overflow-wrap:anywhere';
   document.body.appendChild(reportElement);
   return reportElement;
 }
 function status(line){getReport().textContent='HIGHFLY P69 — '+line;}
 function nativeInitialized(){
   return document.getElementById('server-select')?.dataset.mode==='offline';
 }
 async function tryBoot(reason){
   if(pending)return;
   if(nativeInitialized()){status('Motor nativo inicializado; Offline seleccionado.');return;}
   pending=true;
   status('Recuperando inicio original ('+reason+')…');
   try{
     // The imported module retains all original RPG, worlds, NPCs and controls.
     // Do not replace or simulate any app event or auth flow.
     await import('/src/main.ts');
     const selected=document.getElementById('server-select')?.dataset.mode||'desconocido';
     status('Importación completada. Selector nativo: '+selected+
       '. Si la pantalla de sesión sigue abierta, tocá Atrás y luego Jugar.');
   }catch(e){
     const reason=String(e&& (e.message||e.stack)||e).slice(0,350);
     status('El módulo sigue fallando: '+reason+'.');
     const button=document.createElement('button');
     button.type='button';
     button.textContent='REINTENTAR MOTOR';
     button.style.cssText='margin-left:10px;background:#254e6b;color:#fff;border:1px solid #8ed6ff;border-radius:6px;padding:7px';
     button.addEventListener('click',()=>{
       button.remove();
       pending=false;
       void tryBoot('reintento manual');
     },{once:true});
     getReport().append(button);
   }
 }
 function afterPageLoad(){
   // If the normal static module loaded, do nothing except report that fact.
   // If it didn't, reproduce the successful isolated P43 manual-import path.
   setTimeout(()=>void tryBoot('módulo automático no completó'),1200);
 }
 if(document.readyState==='complete')afterPageLoad();
 else window.addEventListener('load',afterPageLoad,{once:true});
})();
"""
def check_file(p:Path)->str:
 if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(LAB.resolve()):
  raise RuntimeError('P69_ENTRY_INVALID_PATH_'+str(p))
 return p.read_text('utf8')
def preflight():
 if LAB.is_symlink() or not LAB.is_dir() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('P69_ENTRY_LAB_MISSING')
 if JS.exists() or JS.is_symlink() or BACKUP.exists() or REPORT.exists():
  raise RuntimeError('P69_ENTRY_RETRY_ALREADY_INSTALLED_OR_BACKUP_EXISTS')
 if not (LAB/'public/highfly').is_dir() or (LAB/'public/highfly').is_symlink():
  raise RuntimeError('P69_ENTRY_PUBLIC_UNSAFE')
 old=check_file(HTML)
 if old.count(ENTRY)!=1:
  raise RuntimeError('P69_ENTRY_NATIVE_MODULE_TAG_DRIFT_'+str(old.count(ENTRY)))
 if old.count('</head>')!=1 or ADD in old:
  raise RuntimeError('P69_ENTRY_HEAD_DRIFT')
 for mark in ('HIGHFLY_P69_FURY_CORE','HIGHFLY_P69_NATIVE_LOADER_CLEAN',
              'id="server-select"','id="server-opt-offline"'):
  if mark not in old:raise RuntimeError('P69_ENTRY_ORIGINAL_MARK_MISSING_'+mark)
 # Do not re-enable Offline in production or break the real game. The
 # 9-class patch is required for the selected local experiment.
 src=check_file(LAB/'src/main.ts')
 if 'HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES' not in src:
  raise RuntimeError('P69_ENTRY_NINE_CLASS_OFFLINE_PATCH_NOT_INSTALLED')
 if 'HIGHFLY_P69_FURY_CORE' not in src:raise RuntimeError('P69_ENTRY_FURY_MISSING')
 updated=old.replace('</head>',
  '<!-- '+MARK+': diagnostic opt-in; native ESM tag remains unchanged -->\n'+
  ADD+'\n</head>',1)
 return old,updated
def run(apply=False):
 old,new=preflight()
 result={
   'phase':'P69_ORIGINAL_ENTRY_IMPORT_RECOVERY',
   'mode':'APPLY' if apply else 'DRY_RUN',
   'optInUrlParam':'?hf_p69_boot=1',
   'nativeStaticMainModulePreserved':True,
   'FURYWorldNpcGLBCodeUnchanged':True,
   'activeP64Modified':False,'P43Modified':False,
   'P69GameSourceModified':False,'localStorageModified':False,
   'browserVerified':False,
   'willEdit':['index.html'],
   'willCreate':['public/highfly/p69_native_boot_retry.js'],
   'backup':str(BACKUP)}
 if not apply:
  print('[P69 ENTRY BOOT RETRY] '+json.dumps(result,ensure_ascii=False,indent=2))
  return
 BACKUP.write_text(old,'utf8')
 if BACKUP.read_text('utf8')!=old:raise RuntimeError('P69_ENTRY_BACKUP_VERIFICATION_FAILED')
 created=False
 try:
  if check_file(HTML)!=old:raise RuntimeError('P69_ENTRY_CONCURRENT_HTML_EDIT')
  with JS.open('x',encoding='utf8') as f:f.write(CODE)
  created=True
  HTML.write_text(new,'utf8')
  result['sha256']={'before':hashlib.sha256(old.encode()).hexdigest(),
                    'after':hashlib.sha256(new.encode()).hexdigest()}
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 except BaseException:
  HTML.write_text(old,'utf8')
  if created and JS.is_file() and JS.read_text('utf8')==CODE:JS.unlink()
  raise
 print('[P69 ENTRY BOOT RETRY] '+json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true')
 run(a.parse_args().apply)
