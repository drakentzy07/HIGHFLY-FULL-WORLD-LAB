#!/usr/bin/env python3
"""P43 optional in-browser module-link error probe.

Adds a user-click diagnostic button to the already-installed P43 panel.
Only the isolated P43 public diagnostic script is changed; the real game source,
saved games and P64 remain untouched. Dynamic import MAY initialize the game
if it succeeds, hence requiring an explicit user click.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p43-restore-lab'
JS=LAB/'public/highfly_p43_android_diag.js'
BACKUP=LAB/'.hf-p43-android-diag-before-module-link.js'
REPORT=WORK/'reports/highfly-world7/P43_MODULE_LINK_PROBE_INSTALL.json'
MARK='HF_P43_LINK_PROBE_V1'
ANCHOR="    copy.textContent='COPIAR'; hide.textContent='OCULTAR';"
REPLACEMENT=r"""    copy.textContent='COPIAR'; hide.textContent='OCULTAR';
    // HF_P43_LINK_PROBE_V1: only a user click retries the failed entry import.
    // If the import succeeds it may initialize the game; never run automatically.
    const tryModule=document.createElement('button');
    tryModule.type='button';
    tryModule.textContent='PROBAR MOTOR';
    tryModule.style.cssText='background:#164b33;color:#fff;border:1px solid #68efa7;border-radius:5px;min-height:30px;padding:5px 8px';
    tryModule.onclick=async()=>{
      tryModule.disabled=true;
      add('MOTOR','Iniciando importación ESM por solicitud del usuario');
      tick();
      try{
        await import('/src/main.ts');
        add('MOTOR IMPORT','COMPLETÓ. El juego puede haber iniciado.');
      }catch(e){
        add('MOTOR IMPORT FALLÓ',(e&&e.stack)||(e&&e.message)||String(e));
      }
      tick();
      tryModule.disabled=false;
    };
    buttons.append(tryModule);"""
TAIL="    buttons.append(copy,hide);bar.append(title,buttons);host.append(bar,pre);document.body.append(host);"

def run():
    if not LAB.is_dir() or LAB.is_symlink() or not LAB.resolve().is_relative_to(WORK.resolve()):
        raise RuntimeError('P43_LAB_UNSAFE')
    if not JS.is_file() or JS.is_symlink() or BACKUP.exists() or BACKUP.is_symlink() or REPORT.exists():
        raise RuntimeError('P43_LINK_PROBE_NOT_READY_OR_ALREADY_INSTALLED')
    old=JS.read_text('utf8')
    if old.count(ANCHOR)!=1 or old.count(TAIL)!=1 or 'hf_p43_diag' not in old or MARK in old:
        raise RuntimeError('P43_LINK_PROBE_DIAG_ANCHOR_DRIFT')
    new=old.replace(ANCHOR,REPLACEMENT,1)
    if TAIL not in new or new.count(MARK)!=1:
        raise RuntimeError('P43_LINK_PROBE_VALIDATION_FAILED')
    BACKUP.write_text(old,'utf8')
    if BACKUP.read_text('utf8')!=old:
        raise RuntimeError('P43_LINK_PROBE_BACKUP_FAILED')
    try:
        JS.write_text(new,'utf8')
        info={'phase':'P43_NATIVE_MODULE_LINK_DIAG','mode':'APPLY',
              'activeP64Modified':False,'gameSourceModified':False,
              'offlineSavesModifiedByInstaller':False,
              'browserVerified':False,'backup':str(BACKUP),
              'probe':'Open ?hf_p43_diag=1&hf_p43_link=1, click PROBAR MOTOR, copy MOTOR IMPORT FALLÓ.',
              'warning':'Dynamic import may initialize game if it succeeds; only explicit tap triggers it.'}
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8')
        print('[P43 MODULE LINK PROBE] '+json.dumps(info,ensure_ascii=False,indent=2))
    except BaseException:
        JS.write_text(old,'utf8')
        raise
if __name__=='__main__':run()
