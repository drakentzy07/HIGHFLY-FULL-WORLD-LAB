// Read-only local KayKit Complete v7 catalog. Does not publish, copy or edit files.
// User must place their owned original pack inside the ignored .workspace/ directory.
import { readdir, lstat, mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import path from 'node:path';

export const MEDIA_EXTENSIONS=new Set(['.gltf','.glb','.fbx','.obj','.blend',
  '.png','.jpg','.jpeg','.webp','.bin','.mtl','.wav','.ogg','.mp3']);
export const MODEL_EXTENSIONS=new Set(['.gltf','.glb','.fbx','.obj','.blend']);
export const ART_CATEGORIES={
  'KayKit Adventurers 2.0':'player_and_npc_rig_review',
  'KayKit Character Animations 1.1':'animation_rig_review',
  'KayKit Skeletons 1.1':'monsters_and_rig_review',
  'KayKit Medieval Hexagon Pack 1.0.1':'town_and_buildings',
  'KayKit Dungeon Pack 1.1':'dungeons_and_interiors',
  'KayKit Fantasy Weapons Bits 1.0':'equipment_and_weapons',
  'KayKit Forest Nature Pack 1.0':'biomes_and_nature',
  'KayKit Furniture Bits 1.0':'interiors',
  'KayKit RPG Tools Bits 1.0':'rpg_props_and_interactions',
};
export function identifyPack(relative) {
  const p=relative.replaceAll('\\','/').split('/');
  const part=p[0]?.startsWith('The Complete KayKit Collection v7')?p[1]:p[0];
  return part||'UNKNOWN';
}
export function classifyKaykitFile(relative) {
  const extension=path.extname(relative).toLowerCase();
  const pack=identifyPack(relative);
  return {
    pack,extension,category:ART_CATEGORIES[pack]||'other_pack',
    candidateForVisualCatalog:MEDIA_EXTENSIONS.has(extension),
    requiresRigCheck:/(Adventurers|Animations|Skeletons)/.test(pack),
    isModel:MODEL_EXTENSIONS.has(extension),
  };
}
async function walk(root,subdir='',out=[]) {
  const entries=await readdir(path.join(root,subdir),{withFileTypes:true});
  for(const e of entries){
    const rel=subdir?subdir+'/'+e.name:e.name,full=path.join(root,rel);
    const m=await lstat(full);
    if(m.isSymbolicLink())throw Error('SYMLINK_NOT_ALLOWED: '+rel);
    if(m.isDirectory())await walk(root,rel,out);
    else if(m.isFile())out.push({rel,size:m.size});
    if(out.length>100000)throw Error('TOO_MANY_FILES');
  }
  return out;
}
async function sha256(filename) {
  const h=createHash('sha256');
  for await(const chunk of createReadStream(filename))h.update(chunk);
  return h.digest('hex');
}
export async function catalog(root,output) {
  const base=path.basename(root),meta=await lstat(root);
  if(!meta.isDirectory()||!base.startsWith('The Complete KayKit Collection v7'))
    throw Error('EXPECTED_UNPACKED_KAYKIT_V7_ROOT');
  const records=[];
  const filenames=await walk(root);
  const countByPack={};const byExtension={};
  for(const f of filenames){
    const info=classifyKaykitFile(f.rel);
    const entry={relativePath:f.rel,bytes:f.size,...info};
    // Hash only canonical game-ready GLB/GLTF assets now. Full pack hash
    // enumeration comes later at the exact-file commercial allowlist stage.
    if(info.extension==='.glb'||info.extension==='.gltf')
      entry.sha256=await sha256(path.join(root,f.rel));
    records.push(entry);
    countByPack[info.pack]=(countByPack[info.pack]||0)+1;
    byExtension[info.extension]=(byExtension[info.extension]||0)+1;
  }
  await mkdir(output,{recursive:true});
  const result={
    schemaVersion:1,
    project:'HIGHFLY ORIGIN',
    input:'User-provided KayKit Complete v7, private Codespace; READ ONLY',
    licenseStatus:'CC0 FAMILY CLAIM — INDIVIDUAL SOURCE/INTEGRITY REVIEW REQUIRED',
    fileCount:records.length,countByPack,byExtension,records,
  };
  await writeFile(path.join(output,'KAYKIT_V7_LOCAL_CATALOG.json'),JSON.stringify(result,null,2)+'\n');
  await writeFile(path.join(output,'KAYKIT_V7_SUMMARY.md'),[
    '# HIGHFLY KayKit Complete v7 catalog (private)',
    '', 'Pack content metadata only: no binaries copied, no public GitHub upload.',
    'Model formats need renderer conversion and rig compatibility validation.',
    '', 'Total: '+records.length,
    ...Object.entries(countByPack).sort((a,b)=>b[1]-a[1]).map(([pack,n])=>'- '+pack+': '+n),
    '', 'Licenses and derivative source provenance must be validated before release.',
    ''
  ].join('\n'));
  return {count:records.length,packs:Object.keys(countByPack).length,modelFiles:records.filter(x=>x.isModel).length,output};
}
if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)){
  const root=path.resolve(process.argv[2]||'.workspace/private-imports/The Complete KayKit Collection v7');
  const output=path.resolve(process.argv[3]||'.workspace/reports/kaykit-v7');
  console.log('[HIGHFLY] Private KayKit source catalog:',JSON.stringify(await catalog(root,output)));
}
