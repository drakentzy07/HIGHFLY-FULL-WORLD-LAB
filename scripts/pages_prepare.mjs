// Prepare a PUBLIC trial build of the ClaudeCraft MIT engine without ANY unapproved media.
// It acts only on the ephemeral upstream checkout inside GitHub Actions, not on HIGHFLY source.
import {readFileSync,writeFileSync,mkdirSync,rmSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
const project=process.argv[2]&&path.resolve(process.argv[2]);
const registry=process.argv[3]&&path.resolve(process.argv[3]);
if(!project||!registry||!existsSync(path.join(project,'src/game/offline_mode_gate.ts')))
 throw Error('Expected upstream working tree and approved-media registry');
const doc=JSON.parse(readFileSync(registry,'utf8'));
if(doc.sourceCommit!=='ebd3aa444352952321e0108b335722fe26d35716')throw Error('SOURCE_PIN_MISMATCH');
if(doc.assets.length!==16)throw Error('UNEXPECTED_ASSET_COUNT');
const staged=[];
for(const asset of doc.assets){
 if(asset.license!=='CC0-1.0'||!asset.path.startsWith('public/')||!/^public\/[\w./-]+$/.test(asset.path)||
    !/^[0-9a-f]{40}$/.test(asset.gitBlobSha))throw Error('UNVERIFIED_MEDIA '+asset.path);
 const full=path.join(project,asset.path);
 const bytes=readFileSync(full);
 const gitSha=createHash('sha1').update('blob '+bytes.length+'\0').update(bytes).digest('hex');
 if(gitSha!==asset.gitBlobSha)throw Error('UPSTREAM_MEDIA_CHANGED '+asset.path);
 staged.push({path:asset.path,bytes});
}
rmSync(path.join(project,'public'),{recursive:true,force:true});
for(const item of staged){const p=path.join(project,item.path);mkdirSync(path.dirname(p),{recursive:true});writeFileSync(p,item.bytes);}
const offline=path.join(project,'src/game/offline_mode_gate.ts');
let offlineSource=readFileSync(offline,'utf8');
if(!offlineSource.includes('return isDev;'))throw Error('OFFLINE_SOURCE_GATE_CHANGED');
offlineSource=offlineSource.replace('return isDev;', "return isDev || import.meta.env.VITE_HIGHFLY_PAGES_OFFLINE === '1';");
writeFileSync(offline,offlineSource);
const media=path.join(project,'src/render/assets/media.ts');
let mediaSource=readFileSync(media,'utf8');
const old="return MEDIA_ASSETS[logical] ?? `/${logical}`;";
if(!mediaSource.includes(old))throw Error('MEDIA_URL_SOURCE_CHANGED');
mediaSource=mediaSource.replace(old,
 "return import.meta.env.BASE_URL + (MEDIA_ASSETS[logical] ?? `/${logical}`).replace(/^\\/+/, '');");
writeFileSync(media,mediaSource);
console.log('HIGHFLY STRICT STAGE: all source public media removed; only '+staged.length+' exact CC0 blobs restored.');
console.log('Offline Pages flag enabled; MIT engine and world logic remain from original source.');
