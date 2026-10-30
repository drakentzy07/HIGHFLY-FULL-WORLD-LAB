// HIGHFLY ORIGIN, pinned v0.44.7: stage TEXT SOURCE ONLY in a private workspace.
// NOT a commercial release, not a legal clearance and not a runnable build yet.
import { mkdir, readdir, copyFile, readFile, writeFile, lstat, stat } from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

export const SOURCE_COMMIT='493c35a108cef6c8aa290e8793107b1cd117886e';
export const SOURCE_DIRS=['src','server','data','scripts','build','headless','third_party','patches'];
export const ROOT_FILES=['LICENSE','package.json','pnpm-lock.yaml','tsconfig.json',
  'vite.config.ts','index.html','play.html','editor.html','CREDITS.md'];
export const CODE_EXTENSIONS=new Set(['.ts','.tsx','.js','.jsx','.mjs','.cjs','.css',
  '.json','.html','.sql','.sh','.md','.py','.yml','.yaml','.txt','.toml','.xml']);
const NO_COPY_NAMES=new Set(['.env','.npmrc','.git','.DS_Store']);
export function allowCodeFile(rel) {
  const parts=rel.split('/');
  if(parts.some(p=>NO_COPY_NAMES.has(p)||p==='node_modules'||p==='public'||
    p.includes('secret')||p.includes('private_key')))return false;
  return CODE_EXTENSIONS.has(path.extname(parts.at(-1)).toLowerCase());
}
async function copyTree(source,dest,relative,stats) {
  let entries;
  try{entries=await readdir(path.join(source,relative),{withFileTypes:true});}
  catch(e){if(e.code==='ENOENT')return;throw e;}
  await mkdir(path.join(dest,relative),{recursive:true});
  for(const entry of entries) {
    const child=relative+'/'+entry.name;
    const meta=await lstat(path.join(source,child));
    if(meta.isSymbolicLink()) {stats.skippedSymlinks++;continue;}
    if(meta.isDirectory()) {await copyTree(source,dest,child,stats);continue;}
    if(!meta.isFile()||!allowCodeFile(child)){stats.skippedOther++;continue;}
    if(meta.size>8000000){stats.skippedOversize++;continue;}
    await mkdir(path.dirname(path.join(dest,child)),{recursive:true});
    await copyFile(path.join(source,child),path.join(dest,child));
    stats.codeFiles++;
  }
}
export async function stageCode(source,dest) {
  const sha=execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
  if(sha!==SOURCE_COMMIT)throw Error('SOURCE_SHA_MISMATCH');
  const license=await readFile(path.join(source,'LICENSE'),'utf8');
  if(!license.startsWith('MIT License')||!license.includes('Copyright (c) 2026 Levy Street'))
    throw Error('UPSTREAM_LICENSE_UNEXPECTED');
  try {await stat(dest);throw Error('DESTINATION_ALREADY_EXISTS: no overwrite');}
  catch(e){if(e.code!=='ENOENT')throw e;}
  const stats={codeFiles:0,skippedSymlinks:0,skippedOther:0,skippedOversize:0};
  await mkdir(dest,{recursive:true});
  for(const d of SOURCE_DIRS)await copyTree(source,dest,d,stats);
  for(const name of ROOT_FILES) {
    try {
      const from=path.join(source,name),info=await lstat(from);
      if(!info.isFile())throw Error('ROOT_NOT_REGULAR: '+name);
      await copyFile(from,path.join(dest,name));
      stats.codeFiles++;
    }catch(e){if(e.code!=='ENOENT')throw e;}
  }
  await mkdir(path.join(dest,'public'),{recursive:true});
  const report={
    project:'HIGHFLY ORIGIN',source:'World of ClaudeCraft v0.44.7',
    sourceCommit:SOURCE_COMMIT,
    status:'PRIVATE CODE STAGE; NOT REVIEWED FOR COMMERCIAL REDISTRIBUTION',
    originalPublicMediaCopied:false,
    notice:'Source trees, JS dependencies, trademarks, inline art, generated output and data still require audits. No release.',
    stats,
  };
  await writeFile(path.join(dest,'HIGHFLY_STAGE_STATUS.json'),
    JSON.stringify(report,null,2)+'\n');
  return {destination:dest,...stats};
}
if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)) {
  const source=path.resolve(process.argv[2]||'.workspace/claudecraft-v0.44.7');
  const dest=path.resolve(process.argv[3]||'.workspace/highfly-origin-stage-p0');
  console.log('[HIGHFLY] PRIVATE SOURCE STAGE:',JSON.stringify(await stageCode(source,dest)));
}
