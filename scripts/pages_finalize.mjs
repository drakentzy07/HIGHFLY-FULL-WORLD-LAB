// Post-build fail-closed audit: only MIT application code and 16 exact CC0
// model/texture files (and their SHA-256 hashed media copies) may go to Pages.
import {createHash} from 'node:crypto';
import {readFileSync,readdirSync,statSync,rmSync,writeFileSync,existsSync,copyFileSync} from 'node:fs';
import path from 'node:path';
const source=path.resolve(process.argv[2]??'upstream');
const manifest=JSON.parse(readFileSync(process.argv[3]??'config/pages_v0454_media_allowlist.json','utf8'));
const dist=path.join(source,'dist');
if(!existsSync(path.join(dist,'index.html'))||!existsSync(path.join(dist,'editor.html')))
 throw Error('HTML BUILD_INCOMPLETE');
const approved=new Map();
for(const a of manifest.assets){
 const bytes=readFileSync(path.join(source,a.path));
 const rel=a.path.replace(/^public\//,'');
 const parsed=path.posix.parse(rel),hash=createHash('sha256').update(bytes).digest('hex').slice(0,12);
 const media=path.posix.join('media',parsed.dir,parsed.name+'.'+hash+parsed.ext);
 approved.set(rel,createHash('sha256').update(bytes).digest('hex'));
 approved.set(media,createHash('sha256').update(bytes).digest('hex'));
}
let files=0,deleted=0,retainedMedia=0,bytes=0;
const BLOCK_EXT=new Set(['.glb','.gltf','.bin','.fbx','.hdr','.ktx2','.png','.jpg','.jpeg','.webp','.gif','.svg','.mp3','.ogg','.wav','.m4a','.woff','.woff2','.ttf','.otf','.wasm','.ico','.pdf']);
function audit(dir){
 for(const ent of readdirSync(dir,{withFileTypes:true})){
   const abs=path.join(dir,ent.name);
   if(ent.isDirectory()){audit(abs);continue;}
   const rel=path.relative(dist,abs).split(path.sep).join('/');
   const ext=path.extname(rel).toLowerCase();
   if(BLOCK_EXT.has(ext)){
     const data=readFileSync(abs),hash=createHash('sha256').update(data).digest('hex');
     if(!approved.has(rel)||approved.get(rel)!==hash){rmSync(abs);deleted++;continue;}
     retainedMedia++;
   }else if(!['.js','.css','.html','.json','.map','.txt','.webmanifest','.xml','.md','.'].includes(ext)){
      // Files without known clean class must never be released.
      rmSync(abs);deleted++;continue;
   }
   bytes+=statSync(abs).size; files++;
 }
}
audit(dist);
if(files<4)throw Error('SITE_FILES_INCOMPLETE '+files);
if(bytes>900*1024*1024)throw Error('PAGES_SITE_TOO_LARGE: '+bytes);
for(const a of manifest.assets){
 const rel=a.path.replace(/^public\//,'');
 if(!existsSync(path.join(dist,rel)))throw Error('APPROVED_MEDIA_MISSING: '+rel);
}
copyFileSync(path.join(source,'LICENSE'),path.join(dist,'UPSTREAM_MIT_LICENSE.txt'));
writeFileSync(path.join(dist,'HIGHFLY_TRIAL_NOTICE.txt'),[
  'HIGHFLY experimental ClaudeCraft 0.45.4 MIT-engine recovery. The original is by Levy Street.',
  'Independent test, not official ClaudeCraft. Only 16 pinned CC0 multimedia files shipped.',
  'All other media withheld pending rights review. Missing visuals/sounds are expected.',
  'No claim yet that quests, combat, map, character and editor work end to end.',
  'Repository: https://github.com/drakentzy07/HIGHFLY-FULL-WORLD-LAB',
  ''
].join('\n'));
writeFileSync(path.join(dist,'.nojekyll'),'');
console.log('PAGES RELEASE GATE: checked='+files+' allowedMedia='+retainedMedia+' excluded='+deleted+' bytes='+bytes);
console.log('Original code is MIT; original multimedia NOT redistributed except the 16 individually pinned CC0 items.');
