#!/usr/bin/env python3
"""P69 lab-only: restore the ORIGINAL nine class selector and Offline dev default.

The P69 recovery contains P42/P45 Hunter-only filters and P47 presentation,
which can obscure the native character editor and route to the Online login.
This guarded fix modifies only P69's index.html and src/main.ts. It neither
changes the P69 game, NPCs, GLB, Sim, FURY, save implementation, nor art.
P64 and P43 labs are NEVER modified. Dry run by default.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p69-restore-lab'
HTML=LAB/'index.html'
MAIN=LAB/'src/main.ts'
BACKUP=LAB/'.hf-p69-offline-nine-classes-backup'
REPORT=WORK/'reports/highfly-world7/P69_NATIVE_OFFLINE_NINE_CLASSES.json'
MARK='HIGHFLY_P69_NATIVE_OFFLINE_NINE_CLASSES'
CLASSES=('warrior','paladin','hunter','rogue','priest','shaman','mage','warlock','druid')
PREVIEW_MARK='HIGHFLY_P69_NATIVE_LOADER_CLEAN'
BLOCKS=(
 ('P42_HUNTER_STYLE',r'<style id="highfly-p42-hunter-styles">\s*.*?</style>\s*'),
 ('P45_HUNTER_STYLE',r'<style id="highfly-p45-brand-css">\s*.*?</style>\s*'),
)
LINKS=(
 ('P42_HUNTER_SCRIPT','<script defer src="/highfly_p42_hunter.js"></script>'),
 ('P45_HUNTER_SCRIPT','<script defer src="/highfly_p45_branding.js"></script>'),
 ('P47_OVERRIDE_CSS','<link rel="stylesheet" href="/highfly/p47.css" />'),
 ('P47_OVERRIDE_SCRIPT','<script defer src="/highfly/p47.js"></script>'),
)
def hash_(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def checked(path:Path)->str:
 if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(LAB.resolve()):
  raise RuntimeError('P69_NINE_CLASSES_UNSAFE_OR_MISSING_FILE '+str(path))
 return path.read_text('utf8')

def edit_html(src:str):
 if MARK in src:raise RuntimeError('P69_NINE_CLASSES_ALREADY_APPLIED_TO_HTML')
 for anchor in ('id="offline-select"','id="server-opt-offline"','id="charcreate-panel"',
   'HIGHFLY_P69_FURY_CORE',PREVIEW_MARK):
  if src.count(anchor)!=1:
   raise RuntimeError('P69_NINE_CLASSES_EXPECTED_HTML_MARKER_'+anchor+'_'+str(src.count(anchor)))
 for classname in CLASSES:
  if not re.search(r'<button\b[^>]*\bdata-class="'+classname+r'"',src):
   raise RuntimeError('P69_NINE_CLASSES_NATIVE_CONTROL_MISSING_'+classname)
 updated=src
 removed=[]
 for label,pattern in BLOCKS:
  hits=re.findall(pattern,updated,flags=re.S)
  if len(hits)>1:raise RuntimeError('P69_NINE_CLASSES_DUPLICATE_'+label)
  if hits:
   updated=re.sub(pattern,'',updated,count=1,flags=re.S)
   removed.append(label)
 for label,html in LINKS:
  count=updated.count(html)
  if count>1:raise RuntimeError('P69_NINE_CLASSES_DUPLICATE_'+label)
  if count:
   updated=updated.replace(html,'',1)
   removed.append(label)
 if 'P42_HUNTER_SCRIPT' not in removed or 'P42_HUNTER_STYLE' not in removed:
  raise RuntimeError('P69_NINE_CLASSES_P42_FILTER_NOT_FOUND_REVIEW_SOURCE')
 if updated.count('</head>')!=1:raise RuntimeError('P69_NINE_CLASSES_HEAD_ANCHOR_DRIFT')
 updated=updated.replace('</head>',
   '<!-- '+MARK+': P42/P45 class hiders removed; native 9-class editor remains -->\n</head>',1)
 return updated,removed

def edit_main(src:str):
 if MARK in src:raise RuntimeError('P69_NINE_CLASSES_ALREADY_APPLIED_TO_MAIN')
 for anchor in ('HIGHFLY_P69_FURY_CORE','HIGHFLY_P41_OFFLINE_SAVE',
                'readHighflySave','handleOfflineSelect','server-opt-offline'):
  if anchor not in src:raise RuntimeError('P69_NINE_CLASSES_NATIVE_MAIN_ANCHOR_MISSING_'+anchor)
 pattern=re.compile(r'(?m)^([ \t]*)const[ \t]+offlineAvailable(?:[ \t]*:[ \t]*boolean)?'
                    r'[ \t]*=[ \t]*([\s\S]{0,350}?);[ \t]*(?=\r?$)')
 matches=list(pattern.finditer(src))
 if len(matches)!=1:raise RuntimeError('P69_NINE_CLASSES_OFFLINE_GATE_DRIFT_'+str(len(matches)))
 anchor="    applyServerMode('online');"
 if src.count(anchor)!=1:raise RuntimeError('P69_NINE_CLASSES_DEFAULT_ONLINE_ANCHOR_'+str(src.count(anchor)))
 gate=matches[0]
 updated=src[:gate.start()]+gate.group(1)+'const offlineAvailable = import.meta.env.DEV;'+\
  ' // '+MARK+': original Offline mode in private Vite development only'+src[gate.end():]
 updated=updated.replace(anchor,
  "    // P69: prefer original Offline realm only in Vite dev; normal online choice stays.\n"
  "    applyServerMode(offlineAvailable ? 'offline' : 'online');",1)
 return updated

def plan():
 if LAB.is_symlink() or not LAB.is_dir() or not LAB.resolve().is_relative_to(WORK.resolve()):
  raise RuntimeError('P69_NINE_CLASSES_LAB_NOT_FOUND')
 if BACKUP.exists() or BACKUP.is_symlink() or REPORT.exists() or REPORT.is_symlink():
  raise RuntimeError('P69_NINE_CLASSES_ALREADY_APPLIED_OR_BACKUP_EXISTS')
 if (LAB/'src').is_symlink():raise RuntimeError('P69_NINE_CLASSES_SRC_SYMLINK')
 original_html=checked(HTML)
 original_main=checked(MAIN)
 updated_html,removed=edit_html(original_html)
 updated_main=edit_main(original_main)
 return {'old':{'index.html':original_html,'src/main.ts':original_main},
         'new':{'index.html':updated_html,'src/main.ts':updated_main},
         'removed':removed,
         'classOptions':list(CLASSES),
         'mode':'DRY_RUN',
         'browserVerified':False,'activeP64Modified':False,
         'P43Modified':False,'nativeGameCodeModified':False,
         'p69FuryPreserved':True,'saveFormatUnchanged':True}

def run(apply=False):
 data=plan()
 summary={k:v for k,v in data.items() if k not in ('old','new')}
 summary['mode']='APPLY' if apply else 'DRY_RUN'
 summary['lab']=str(LAB)
 summary['backups']=str(BACKUP)
 summary['modifiedFiles']=['index.html','src/main.ts']
 if not apply:
  print('[P69 NATIVE OFFLINE 9 CLASSES] '+json.dumps(summary,ensure_ascii=False,indent=2))
  return
 BACKUP.mkdir(mode=0o700)
 try:
  for rel,old in data['old'].items():
   target=BACKUP/rel
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_text(old,'utf8')
   if target.read_text('utf8')!=old:
    raise RuntimeError('P69_NINE_CLASSES_BACKUP_FAILED_'+rel)
  for rel,new in data['new'].items():
   target=LAB/rel
   if checked(target)!=data['old'][rel]:raise RuntimeError('P69_NINE_CLASSES_CONCURRENT_SOURCE_'+rel)
   target.write_text(new,'utf8')
   if checked(target)!=new:raise RuntimeError('P69_NINE_CLASSES_WRITE_FAILED_'+rel)
  summary['sha256']={rel:hash_((LAB/rel).read_bytes()) for rel in data['new']}
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf8')
 except BaseException:
  for rel,old in data['old'].items():
   (LAB/rel).write_text(old,'utf8')
  raise
 print('[P69 NATIVE OFFLINE 9 CLASSES] '+json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true')
 args=p.parse_args()
 run(args.apply)
