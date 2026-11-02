#!/usr/bin/env python3
"""P69-only repair of the ORIGINAL offline creator's layout, not the RPG.

P46 messed up native editor layout; removing P47 UI filters removed its
creator layout repair too. Reintroduce just a clean creator-only CSS layer.
Keep P42/P45/P47 Hunter-only script/CSS disabled, do NOT modify any game
sources, NPCs, character model, GLBs, native Offline route, FURY, saves.
Back up index.html, preflight all original editor anchors, opt-in read-only
?hf_p69_creator_diag=1 for empty preview discovery. --apply is explicit.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p69-restore-lab'
HTML=LAB/'index.html'
MAIN=LAB/'src/main.ts'
CSS=LAB/'public/highfly/p69_native_creator_clean.css'
DIAG=LAB/'public/highfly/p69_native_creator_diagnostic.js'
BACKUP=LAB/'.hf-p69-native-creator-before.html'
REPORT=WORK/'reports/highfly-world7/P69_NATIVE_CREATOR_CLEAN.json'
MARK='HIGHFLY_P69_NATIVE_CREATOR_RESTORE'
CLASSES=('warrior','paladin','hunter','rogue','priest','shaman','mage','warlock','druid')
CSS_TEXT=r"""/* HIGHFLY_P69_NATIVE_CREATOR_RESTORE
   Selectors scoped ONLY to the original #offline-select panel.
   No logo, loading, gameplay, NPC, FURY, global CSS or media modifications. */
#offline-select:not([hidden]){
  position:fixed!important;left:50%!important;top:50%!important;
  right:auto!important;bottom:auto!important;
  transform:translate(-50%,-50%)!important;
  display:flex!important;flex-direction:column!important;
  box-sizing:border-box!important;
  width:min(1240px,95vw)!important;height:min(760px,91dvh)!important;
  max-height:91dvh!important;max-width:95vw!important;
  z-index:2147480000!important;
  margin:0!important;padding:clamp(10px,2vw,22px)!important;
  overflow-y:auto!important;overflow-x:hidden!important;
  background:linear-gradient(145deg,#080d21f7,#1a1033f8)!important;
  border:1px solid #a56ce1!important;border-radius:15px!important;
  box-shadow:0 14px 45px #000b!important;
}
#offline-select[hidden]{display:none!important}
#offline-select .auth-title{
  display:block!important;position:relative!important;
  width:100%!important;min-height:0!important;
  margin:0 0 12px!important;padding:0!important;
  text-align:center!important;
  color:#f7e3ff!important;font:700 clamp(18px,2vw,27px)/1.3 Georgia,serif!important;
}
#offline-select .charselect-layout{
  display:grid!important;
  grid-template-columns:minmax(0,1.06fr) minmax(0,.94fr)!important;
  align-items:start!important;gap:clamp(12px,2vw,24px)!important;
  position:relative!important;inset:auto!important;
  transform:none!important;width:100%!important;
  min-width:0!important;height:auto!important;
  overflow:visible!important;margin:0!important;padding:0!important;
}
#offline-select .charselect-col-left,
#offline-select .charselect-col-right,
#offline-select .char-create{
  position:relative!important;inset:auto!important;transform:none!important;
  display:flex!important;flex-direction:column!important;
  gap:9px!important;align-items:stretch!important;
  width:100%!important;min-width:0!important;max-width:100%!important;
  height:auto!important;max-height:none!important;
  margin:0!important;padding:0!important;overflow:visible!important;
}
#offline-select .charselect-col-left{order:1!important}
#offline-select .charselect-col-right{order:2!important}
#offline-select .char-create > .auth-label,
#offline-select .char-create > .char-input-group{
  position:relative!important;inset:auto!important;order:0!important;
  display:block!important;visibility:visible!important;
  transform:none!important;
  width:100%!important;max-width:100%!important;
  box-sizing:border-box!important;
  margin:0!important;padding:0!important;
}
#offline-select #char-name{
  position:relative!important;inset:auto!important;
  display:block!important;visibility:visible!important;
  transform:none!important;
  width:100%!important;max-width:100%!important;
  min-height:39px!important;box-sizing:border-box!important;
  font-size:14px!important;
}
#offline-select .char-create > .mini-class-row{
  position:relative!important;inset:auto!important;transform:none!important;
  order:1!important;display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:7px!important;align-items:stretch!important;
  width:100%!important;max-width:100%!important;
  margin:4px 0!important;padding:0!important;
}
#offline-select .char-create .mini-class-row > .mini-class[data-class]{
  display:flex!important;visibility:visible!important;opacity:1!important;
  position:relative!important;inset:auto!important;transform:none!important;
  justify-content:center!important;align-items:center!important;
  box-sizing:border-box!important;
  width:100%!important;min-width:0!important;max-width:none!important;
  height:auto!important;min-height:35px!important;
  padding:6px 4px!important;margin:0!important;
  font:700 12px/1.2 system-ui,sans-serif!important;
  white-space:normal!important;
}
#offline-select .mini-class[data-class="warrior"]::after{
  display:none!important;content:none!important;
}
#offline-select .char-create > #offline-skin-row{
  position:relative!important;inset:auto!important;order:2!important;
  transform:none!important;margin:0!important;
}
#offline-select .char-create > #offline-appearance{
  position:relative!important;inset:auto!important;transform:none!important;
  order:3!important;display:block!important;
  width:100%!important;max-width:100%!important;
  visibility:visible!important;opacity:1!important;
  margin:0!important;padding:8px!important;
  box-sizing:border-box!important;
  height:auto!important;max-height:190px!important;overflow:auto!important;
  background:#0c1126e8!important;
  border:1px solid #55517c!important;border-radius:9px!important;
}
#offline-select .char-create > #offline-appearance:empty{
  display:none!important;
}
#offline-select #offline-appearance .ac-tabs,
#offline-select #offline-appearance .ac-seg{
  position:relative!important;inset:auto!important;
  display:flex!important;flex-wrap:wrap!important;gap:4px!important;
}
#offline-select .char-create > .auth-actions{
  position:relative!important;inset:auto!important;transform:none!important;
  order:4!important;display:flex!important;
  width:100%!important;max-width:100%!important;
  justify-content:space-between!important;gap:8px!important;
  margin:5px 0 0!important;padding:0!important;
}
#offline-select .char-create > .auth-actions button{
  flex:1 1 0!important;min-width:0!important;max-width:none!important;
  position:relative!important;inset:auto!important;
  min-height:42px!important;white-space:normal!important;
}
#offline-select #offline-preview-container{
  position:relative!important;inset:auto!important;transform:none!important;
  order:0!important;display:block!important;
  box-sizing:border-box!important;
  width:100%!important;height:clamp(200px,40dvh,400px)!important;
  min-height:200px!important;max-width:100%!important;
  margin:0!important;overflow:hidden!important;
}
#offline-select #offline-class-details{
  position:relative!important;inset:auto!important;transform:none!important;
  display:block!important;visibility:visible!important;
  width:100%!important;max-height:160px!important;
  overflow:auto!important;margin:0!important;
}
#offline-select #highfly-p45-hunter-info,
#offline-select #highfly-p47-info,
#offline-select #highfly-p46-hunter-info{display:none!important}
@media(max-height:480px) and (orientation:landscape){
  #offline-select:not([hidden]){height:96dvh!important;max-height:96dvh!important;
    width:98vw!important;max-width:98vw!important;padding:8px!important}
  #offline-select .auth-title{font-size:17px!important;margin:0 0 5px!important}
  #offline-select .charselect-layout{gap:9px!important}
  #offline-select .charselect-col-left,
  #offline-select .charselect-col-right,
  #offline-select .char-create{gap:5px!important}
  #offline-select #offline-preview-container{height:46dvh!important;min-height:120px!important}
  #offline-select .char-create > #offline-appearance{max-height:26dvh!important}
  #offline-select .char-create .mini-class-row > .mini-class[data-class]{
    min-height:29px!important;font-size:10px!important;padding:3px!important}
  #offline-select #offline-class-details{max-height:18dvh!important}
}
"""
JS_TEXT=r"""/* P69 creator read-only view diagnostic; activates only with
   ?hf_p69_creator_diag=1. NEVER creates fake character models or modifies game. */
(function(){
 'use strict';
 if(!new URLSearchParams(location.search).has('hf_p69_creator_diag'))return;
 function mount(){
  const root=document.getElementById('offline-select');
  if(!root||document.getElementById('hf-p69-creator-state'))return;
  const banner=document.createElement('div');
  banner.id='hf-p69-creator-state';
  banner.style.cssText='position:fixed;bottom:8px;left:8px;z-index:2147483640;max-width:94vw;background:#08152ff2;border:1px solid #68bdf4;color:#fff;padding:7px 9px;border-radius:7px;font:11px/1.3 monospace;pointer-events:none';
  document.body.append(banner);
  function tick(){
   const preview=document.getElementById('offline-preview-container');
   const classes=[...root.querySelectorAll('.mini-class[data-class]')];
   const visible=root&&!root.hasAttribute('hidden')&&getComputedStyle(root).display!=='none';
   const numCanvas=preview?.querySelectorAll('canvas').length||0;
   const images=preview?.querySelectorAll('img').length||0;
   const kids=preview?.children.length||0;
   banner.textContent='P69 editor '+(visible?'visible':'oculto')+
    ' · clases DOM '+classes.length+
    ' · clases renderizadas '+classes.filter(x=>x.getBoundingClientRect().width>0).length+
    ' · preview hijos '+kids+' / canvas '+numCanvas+' / imágenes '+images;
  }
  tick();setInterval(tick,1500);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
 else mount();
})();
"""
def safe(path:Path)->bool:
 return not path.is_symlink() and path.resolve().is_relative_to(LAB.resolve())
def plan():
 if LAB.is_symlink() or not LAB.is_dir() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('P69_CREATOR_LAB_MISSING')
 if BACKUP.exists() or BACKUP.is_symlink() or CSS.exists() or CSS.is_symlink() or DIAG.exists() or DIAG.is_symlink() or REPORT.exists():
  raise RuntimeError('P69_CREATOR_ALREADY_INSTALLED_STOP')
 if not safe(HTML) or not safe(MAIN) or not safe(CSS) or not safe(DIAG):
  raise RuntimeError('P69_CREATOR_UNSAFE_FILES')
 if not HTML.is_file() or not MAIN.is_file():
  raise RuntimeError('P69_CREATOR_SOURCE_MISSING')
 src=HTML.read_text('utf8')
 main=MAIN.read_text('utf8')
 for needle in ('id="offline-select"','id="char-name"','id="offline-preview-container"',
                'id="offline-appearance"','id="offline-class-details"',
                'id="btn-start-offline"','id="server-opt-offline"',
                'HIGHFLY_P69_NATIVE_LOADER_CLEAN'):
  if src.count(needle)!=1:
   raise RuntimeError('P69_CREATOR_HTML_ANCHOR_DRIFT_'+needle+'_'+str(src.count(needle)))
 for key in CLASSES:
  if not re.search(r'<button\b[^>]*\bdata-class="'+key+r'"',src):
   raise RuntimeError('P69_CREATOR_CLASS_NOT_IN_MARKUP_'+key)
 for marker in ('HIGHFLY_P69_FURY_CORE','HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES'):
  if marker not in main:raise RuntimeError('P69_CREATOR_MAIN_MARK_MISSING_'+marker)
 for obsolete in ('<script defer src="/highfly_p42_hunter.js"></script>',
                  '<script defer src="/highfly_p45_branding.js"></script>',
                  '<script defer src="/highfly/p47.js"></script>',
                  '<link rel="stylesheet" href="/highfly/p47.css" />'):
  if obsolete in src:raise RuntimeError('P69_CREATOR_LEGACY_FILTER_STILL_ENABLED_'+obsolete)
 if src.count('</head>')!=1:raise RuntimeError('P69_CREATOR_HEAD_DRIFT')
 addition=(
 '<!-- '+MARK+': native editor only, no changes to game logic -->\n'
 '<link rel="stylesheet" href="/highfly/p69_native_creator_clean.css" />\n'
 '<script defer src="/highfly/p69_native_creator_diagnostic.js"></script>\n')
 return src,src.replace('</head>',addition+'</head>',1)

def run(apply=False):
 old,new=plan()
 info={'phase':'P69_ISOLATED_NATIVE_CREATOR_LAYOUT','mode':'APPLY' if apply else 'DRY_RUN',
       'lab':str(LAB),'privatePort':4176,'classes':list(CLASSES),
       'previewModelAssetsReplaced':False,'preview3DVerified':False,
       'nativeEditorFunctionsChanged':False,'mainModified':False,
       'FURYWorldNpcChanged':False,'savedGamesChanged':False,
       'activeP64Modified':False,'P43Modified':False,'browserVerified':False,
       'backup':str(BACKUP),'diagnosticSuffix':'?hf_p69_creator_diag=1',
       'willEdit':['index.html'],
       'willCreate':['public/highfly/p69_native_creator_clean.css',
                     'public/highfly/p69_native_creator_diagnostic.js']}
 if not apply:
  print('[P69 CREATOR REPAIR] '+json.dumps(info,ensure_ascii=False,indent=2));return
 BACKUP.write_text(old,'utf8')
 if BACKUP.read_text('utf8')!=old:raise RuntimeError('P69_CREATOR_BACKUP_MISMATCH')
 made=[]
 try:
  if HTML.read_text('utf8')!=old:raise RuntimeError('P69_CREATOR_CONCURRENT_EDIT')
  for f,body in ((CSS,CSS_TEXT),(DIAG,JS_TEXT)):
   with f.open('x',encoding='utf8') as stream:stream.write(body)
   made.append(f)
  HTML.write_text(new,'utf8')
  info['htmlSha256']=hashlib.sha256(new.encode()).hexdigest()
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps({**info,'utc':datetime.now(timezone.utc).isoformat()},
     ensure_ascii=False,indent=2)+'\n','utf8')
 except BaseException:
  HTML.write_text(old,'utf8')
  for f in made:
   if f.is_file() and not f.is_symlink():f.unlink()
  raise
 print('[P69 CREATOR REPAIR] '+json.dumps(info,ensure_ascii=False,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--apply',action='store_true')
 run(parser.parse_args().apply)
