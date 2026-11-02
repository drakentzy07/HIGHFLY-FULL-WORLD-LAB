#!/usr/bin/env python3
"""HIGHFLY ORIGIN CLEAN v0.44.7 — PRIVATE offline Vite bundle.

Motivation: browser fetches ~3374 Vite dev ESM modules; local Vite shows all
responding, but Chrome fails top-level ESM import intermittently and offline
menu does not boot. Build an optimized static Vite bundle into ONLY the ignored
private Codespace lab. Keep native nine class / startOffline logic unchanged.
Development-only offline gate remains functional inside PRIVATE preview build.
No HTTPS publishing, no Git repo media, no license assumptions.

--check read-only.
--apply generates a private build config with a virtual OFFLINE gate ONLY for the
 native src/main.ts import during private preview build, without editing any
 game source files. On build failure, generated config/output are rolled back.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/".workspace"
ORIGINAL=WORK/"claudecraft-v0.44.7"
STAGE=WORK/"highfly-origin-clean-0447"
CONFIG=STAGE/".highfly-private-offline-vite.config.mjs"
OUT=STAGE/".highfly-private-offline-dist"
GATE=STAGE/"src/game/offline_mode_gate.ts"
REPORTDIR=WORK/"reports/highfly-clean-0447"
LOG=REPORTDIR/"PRIVATE_BUNDLE_BUILD_LOG.txt"
REPORT=REPORTDIR/"PRIVATE_BUNDLE_BUILD_RESULT.json"
PIN="493c35a108cef6c8aa290e8793107b1cd117886e"
CONFIG_BODY="""// PRIVATE clean Codespaces preview only — NEVER deploy/bundle licensed SOURCE V7.
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
const root=path.dirname(fileURLToPath(import.meta.url));
export default defineConfig({
  root,
  base: '/',
  publicDir: path.join(root,'public'),
  plugins: [
    {
      name:'highfly-private-offline-only',enforce:'pre',
      resolveId(source,importer){
        const from=String(importer||'').split('?')[0];
        if(source==='./game/offline_mode_gate' && from.endsWith('/src/main.ts'))
          return '\\0highfly-clean-private-offline-gate';
      },
      load(id){
        if(id==='\\0highfly-clean-private-offline-gate')
          return 'export function isOfflineModeAvailable(isDev){return true;}';
      }
    },
    svelte()
  ],
  resolve: { alias: {'#bot-detector': path.join(root,'server/bot_detector/stub.ts')} },
  define: {
    __APP_VERSION__: JSON.stringify('HIGHFLY_CLEAN_0447_PRIVATE'),
    __APP_BUILD_ID__: JSON.stringify('clean0447'),
    __APP_BUILD_DATE__: JSON.stringify('2026-11-02'),
  },
  css: {transformer:'lightningcss'},
  build: {
    outDir: path.join(root,'.highfly-private-offline-dist'),
    emptyOutDir:true, copyPublicDir:true, target:'es2022',
    cssMinify:'lightningcss', chunkSizeWarningLimit:1700,
    rollupOptions: {
      input:path.join(root,'index.html'),
      output:{manualChunks(id){if(id.includes('node_modules/three/'))return 'vendor-three';}}
    }
  },
  preview:{host:'0.0.0.0',port:4181,strictPort:true}
});
"""

def within(file,base):
 return not file.is_symlink() and file.resolve().is_relative_to(base.resolve())
def digest(file):
 return hashlib.sha256(file.read_bytes()).hexdigest()
def check():
 if not WORK.is_dir() or WORK.is_symlink():
  raise RuntimeError("PRIVATE_BUNDLE_MISSING_WORKSPACE")
 for folder in (ORIGINAL,STAGE):
  if not folder.is_dir() or not within(folder,WORK):
   raise RuntimeError("PRIVATE_BUNDLE_BAD_WORKTREE "+str(folder))
 if not (STAGE/"public/models/chars/players/knight.glb").is_file():
  raise RuntimeError("PRIVATE_BUNDLE_KNIGHT_MODEL_MISSING")
 for file in (GATE,STAGE/"src/main.ts",STAGE/"index.html",ORIGINAL/"LICENSE",ORIGINAL/"CREDITS.md"):
  if not file.is_file() or not within(file,WORK):
   raise RuntimeError("PRIVATE_BUNDLE_MISSING_REQUIRED "+str(file))
 git=subprocess.check_output(["git","-C",str(ORIGINAL),"rev-parse","HEAD"],text=True).strip()
 if git!=PIN:raise RuntimeError("PRIVATE_BUNDLE_ORIGINAL_COMMIT_MISMATCH")
 native=(STAGE/"src/main.ts").read_text("utf8")
 if "const offlineAvailable = isOfflineModeAvailable(import.meta.env.DEV);" not in native:
  raise RuntimeError("PRIVATE_BUNDLE_NATIVE_OFFLINE_GATE_NOT_FOUND")
 if "applyServerMode(offlineAvailable ? 'offline' : 'online')" not in native:
  raise RuntimeError("PRIVATE_BUNDLE_CLEAN_OFFLINE_DEFAULT_NOT_INSTALLED")
 html=(STAGE/"index.html").read_text("utf8")
 if html.count('src="/src/main.ts"')!=1 or html.count('data-class="warrior"')<2:
  raise RuntimeError("PRIVATE_BUNDLE_NOT_ORIGINAL_NINE_CLASS_ENTRY")
 if not (STAGE/"node_modules/vite/bin/vite.js").is_file():
  raise RuntimeError("PRIVATE_BUNDLE_VITE_DEPENDENCY_MISSING")
 gate=GATE.read_text("utf8")
 # The PRIVATE preview uses an isolated Vite virtual module for the import from
 # main.ts; it does not rewrite or depend on the shape of this existing file.
 # Preserve prior HIGHFLY changes unchanged even if the gate was customized.
 if CONFIG.exists() or CONFIG.is_symlink():raise RuntimeError("PRIVATE_BUNDLE_CONFIG_ALREADY_PRESENT")
 if OUT.exists() or OUT.is_symlink():raise RuntimeError("PRIVATE_BUNDLE_OUTPUT_ALREADY_PRESENT")
 if REPORT.exists() or LOG.exists():raise RuntimeError("PRIVATE_BUNDLE_RESULT_ALREADY_PRESENT")
 # If original source contains proprietary art it is NOT automatically moved
 # into the stage. The bundle consumes ONLY STAGE/public approved inventory.
 return {
  "codeBase":"original pinned World of ClaudeCraft 0.44.7",
  "offlineSourceIsNative":True,
  "stagePrivate":True,
  "basePlayerRestored":True,
  "cssIndependent":True,
  "stageGateBefore":digest(GATE),
  "stageGateBytes":len(gate),
  "privateOfflineMethod":"VITE_VIRTUAL_MODULE_FOR_NATIVE_MAIN_ONLY",
  "outputDir":str(OUT),
  "startCommand":"node node_modules/vite/bin/vite.js preview --config .highfly-private-offline-vite.config.mjs --mode highfly-clean-private-offline --host 0.0.0.0 --port 4181 --strictPort"
 }
def apply():
 note=check()
 old_gate_hash=digest(GATE)
 REPORTDIR.mkdir(parents=True,exist_ok=True)
 try:
  if GATE.is_symlink() or digest(GATE)!=old_gate_hash:
   raise RuntimeError("PRIVATE_BUNDLE_GATE_CHANGED_DURING_PREFLIGHT")
  CONFIG.write_text(CONFIG_BODY,"utf8")
  env=os.environ.copy()
  env["NODE_OPTIONS"]="--max-old-space-size=3072"
  command=["node",str(STAGE/"node_modules/vite/bin/vite.js"),"build",
           "--config",str(CONFIG),"--mode","highfly-clean-private-offline"]
  p=subprocess.run(command,cwd=STAGE,env=env,encoding="utf8",
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=270,check=False)
  LOG.write_text(p.stdout[-200000:],"utf8")
  if p.returncode:
   raise RuntimeError("PRIVATE_BUNDLE_VITE_FAILED_EXIT_"+str(p.returncode))
  index=OUT/"index.html"
  if not index.is_file():
   raise RuntimeError("PRIVATE_BUNDLE_INDEX_NOT_EMITTED")
  html=index.read_text("utf8")
  if not any(x in html for x in ("/assets/","./assets/")):
   raise RuntimeError("PRIVATE_BUNDLE_JS_ASSETS_NOT_EMITTED")
  scripts=list((OUT/"assets").glob("*.js"))
  if not scripts:raise RuntimeError("PRIVATE_BUNDLE_NO_JS_CHUNKS")
  report={**note,
   "createdUtc":datetime.now(timezone.utc).isoformat(),
   "status":"STATIC_PRIVATE_BUNDLE_BUILT_BROWSER_ENTRY_NOT_YET_VERIFIED",
   "nativeGatePrivateMode":True,
   "nativeSourceEdited":False,
   "compiledJavaScriptChunks":len(scripts),
   "originalCodeModified":False,"otherLabsModified":False,
   "privateStageGateSha256After":digest(GATE),
   "buildLog":str(LOG),"servePort":4181,
   "publishApproved":False,"gameplayVerified":False}
  REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n","utf8")
  print("[HIGHFLY CLEAN PRIVATE BUNDLE] "+json.dumps({
   "status":report["status"],"javascriptChunks":len(scripts),
   "port":4181,"origin":str(OUT),"buildLog":str(LOG),
   "originalUntouched":True,"gameplayVerified":False,
   "nextCommand":note["startCommand"]
  },indent=2,ensure_ascii=False))
 except BaseException:
  # On errors delete only generated private output and config. No original
  # game source was edited, so there is nothing to restore in src/.
  if CONFIG.is_file() and not CONFIG.is_symlink():
   CONFIG.unlink()
  if OUT.is_dir() and not OUT.is_symlink():
   shutil.rmtree(OUT)
  print("[PRIVATE BUNDLE] FAILED; private config/output removed; game source unchanged; build failure log:",
    LOG if LOG.exists() else "unavailable",file=sys.stderr)
  raise
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--apply",action="store_true")
 args=parser.parse_args()
 if args.apply:apply()
 else:print("[PRIVATE BUNDLE PREFLIGHT] "+json.dumps(check(),indent=2,ensure_ascii=False))
