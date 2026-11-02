#!/usr/bin/env python3
"""P43 isolated diagnostic upgrade: capture browser-side /src/main.ts fetch result.

Only updates the already-installed opt-in ?hf_p43_diag=1 diagnostic JS,
NEVER source, gameplay, asset links, save/localStorage, P64 or checkpoint.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
LAB=WORK/'highfly-p43-restore-lab'
JS=LAB/'public/highfly_p43_android_diag.js'
BACKUP=LAB/'.hf-p43-android-diag-before-fetch.js'
REPORT=WORK/'reports/highfly-world7/P43_DIAG_FETCH_MAIN_INSTALL.json'
MARK='HIGHFLY_P43_BROWSER_MAIN_FETCH_CHECK'
ANCHOR='  function report(){\n'
INJECTION=r"""  // HIGHFLY_P43_BROWSER_MAIN_FETCH_CHECK: same-origin, read-only, opt-in.
  // The PC local terminal getting HTTP 200 does not prove that Android or
  // Codespaces' authenticated browser can fetch the module. Capture redirects,
  // incorrect MIME (HTML sign-in page), CORS errors, and browser network errors.
  async function checkBrowserModule(){
    const url='/src/main.ts';
    try {
      const response=await fetch(url,{
        credentials:'same-origin',cache:'no-store',redirect:'follow'
      });
      const body=await response.text();
      const ct=response.headers.get('content-type')||'';
      const finalURL=new URL(response.url,location.href);
      const tag=response.status+' '+ct+' redirected='+response.redirected+
        ' url='+finalURL.origin+finalURL.pathname+
        ' bytes='+body.length+
        ' html='+(/^\s*<!doctype html|^\s*<html/i.test(body));
      add('BROWSER FETCH MAIN',tag);
      if(response.ok && /javascript/i.test(ct) && !(/^\s*<!doctype html|^\s*<html/i.test(body))){
        add('MAIN DATA','JavaScript is fetchable in browser; inspect module import graph or parser.');
      } else {
        add('MAIN DATA','Module not valid JavaScript or access redirected. Check Codespaces port/auth.');
      }
    } catch (e) {
      add('BROWSER FETCH MAIN FAILED',(e&&e.stack)||String(e));
    }
  }
  void checkBrowserModule();
"""
def run():
    if not LAB.is_dir() or LAB.is_symlink() or not LAB.resolve().is_relative_to(WORK.resolve()):
        raise RuntimeError('P43_LAB_NOT_FOUND_OR_UNSAFE')
    if not JS.is_file() or JS.is_symlink():
        raise RuntimeError('P43_ANDROID_DIAG_SCRIPT_MISSING_OR_UNSAFE')
    if BACKUP.exists() or BACKUP.is_symlink() or REPORT.exists():
        raise RuntimeError('P43_BROWSER_FETCH_DIAG_ALREADY_INSTALLED')
    original=JS.read_text('utf8')
    if original.count(ANCHOR)!=1 or 'hf_p43_diag' not in original or MARK in original:
        raise RuntimeError('P43_DIAG_ANCHOR_DRIFT')
    update=original.replace(ANCHOR,INJECTION+ANCHOR,1)
    BACKUP.write_text(original,'utf8')
    if BACKUP.read_text('utf8')!=original: raise RuntimeError('P43_DIAG_BACKUP_FAILED')
    JS.write_text(update,'utf8')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    info={'phase':'P43_BROWSER_FETCH_MODULE_PROBE',
          'mode':'APPLY','activeP64Modified':False,
          'gameSourceModified':False,'progressModified':False,
          'browserVerified':False,'originalSha256':hashlib.sha256(original.encode()).hexdigest(),
          'updatedSha256':hashlib.sha256(update.encode()).hexdigest(),
          'backup':str(BACKUP),
          'urlSuffix':'?hf_p43_diag=1&hf_p43_probe=2'}
    REPORT.write_text(json.dumps(info,indent=2)+'\n','utf8')
    print('[P43 MODULE FETCH DIAGNOSTIC] '+json.dumps(info,indent=2))
if __name__=='__main__':run()
