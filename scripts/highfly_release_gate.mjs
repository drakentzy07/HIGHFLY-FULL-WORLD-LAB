// HIGHFLY ORIGIN release gate: deny by default. NEVER approves a family of assets.
// Run --preflight to validate manifests; --release to audit every file under
// the staged public/ directory and require all human release checks.
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { readFile, readdir, lstat } from 'node:fs/promises';
import path from 'node:path';

const HASH = /^[a-f0-9]{64}$/;
const ALLOWED_LICENSES = new Set(['CC0-1.0','MIT','CC-BY-4.0']);
const REQUIRED_CHECKS = ['mediaProvenance','thirdPartyDependencies',
  'trademarksAndBranding','fontsAndEmbeddedArt','attributionsAndNotices',
  'fullGameplayAndAndroid'];
const FORBIDDEN = /(?:^|\/)(?:woc|claudecraft|craftpix)(?:[/. _-]|$)/i;

export function strictRelativePath(v) {
  if (typeof v !== 'string' || !v || v.includes('\\') || v.includes('..') ||
      v.includes('//') || v.startsWith('/') || v.endsWith('/') ||
      !/^[a-zA-Z0-9._\/() -]+$/.test(v)) return false;
  return v.split('/').every(x => x !== '.' && x !== '..' && x !== '');
}
export function validateManifest(manifest) {
  const errors = [];
  if (manifest?.schemaVersion !== 1 || !Array.isArray(manifest.assets)) {
    return ['BAD_MANIFEST_SCHEMA'];
  }
  const ids = new Set();
  for (const [i, item] of manifest.assets.entries()) {
    const prefix = 'assets['+i+']';
    if (!strictRelativePath(item?.path) || !item.path.startsWith('public/')) {
      errors.push(prefix+': BAD_PATH'); continue;
    }
    if (ids.has(item.path)) errors.push(prefix+': DUPLICATE_PATH');
    ids.add(item.path);
    if (FORBIDDEN.test(item.path)) errors.push(prefix+': PROHIBITED_ASSET_NAME');
    if (!HASH.test(item.sha256||'')) errors.push(prefix+': BAD_HASH');
    if (!ALLOWED_LICENSES.has(item.license)) errors.push(prefix+': LICENSE_NOT_APPROVED');
    if (typeof item.sourceUrl !== 'string' || !/^https:\/\//.test(item.sourceUrl))
      errors.push(prefix+': SOURCE_PROVENANCE_MISSING');
    if (typeof item.evidenceUrl !== 'string' || !/^https:\/\//.test(item.evidenceUrl))
      errors.push(prefix+': LICENSE_EVIDENCE_MISSING');
    if (typeof item.author !== 'string' || !item.author.trim())
      errors.push(prefix+': AUTHOR_MISSING');
    if (item.license === 'CC-BY-4.0' &&
        (typeof item.attribution !== 'string' || !item.attribution.trim()))
      errors.push(prefix+': ATTRIBUTION_MISSING');
    if (typeof item.reviewedBy !== 'string' || !item.reviewedBy.trim() ||
        typeof item.reviewedOn !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(item.reviewedOn))
      errors.push(prefix+': HUMAN_FILE_REVIEW_MISSING');
  }
  return errors;
}
export function validatePolicy(policy) {
  if (!policy || policy.schemaVersion!==1 || policy.project!=='HIGHFLY ORIGIN')
    return ['BAD_RELEASE_POLICY'];
  const failed=REQUIRED_CHECKS.filter(k=>policy.checks?.[k]!==true)
    .map(k=>'PENDING_'+k);
  if (policy.releaseApproved!==true) failed.unshift('RELEASE_LOCKED');
  if (typeof policy.reviewer!=='string'||!policy.reviewer.trim()||
      typeof policy.approvedOn!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(policy.approvedOn))
    failed.push('FINAL_HUMAN_SIGNOFF_MISSING');
  return failed;
}
async function walk(root,relative='') {
  const acc=[];
  for(const dirent of await readdir(path.join(root,relative),{withFileTypes:true})) {
    const child=relative?relative+'/'+dirent.name:dirent.name;
    const full=path.join(root,child), meta=await lstat(full);
    if(meta.isSymbolicLink()) {acc.push({path:child,symlink:true});continue;}
    if(meta.isDirectory()) acc.push(...await walk(root,child));
    else if(meta.isFile()) acc.push({path:child,symlink:false});
    else acc.push({path:child,special:true});
  }
  return acc;
}
async function sha256(file) {
  const h=createHash('sha256');
  for await(const block of createReadStream(file)) h.update(block);
  return h.digest('hex');
}
export async function auditMediaTree(root,manifest) {
  const errors=validateManifest(manifest);
  if(errors.length) return errors;
  const allowed=new Map(manifest.assets.map(e=>[e.path.slice('public/'.length),e]));
  let files;
  try {files=await walk(root);}catch(e){return ['MEDIA_ROOT_MISSING_OR_UNREADABLE: '+e.code];}
  const found=new Set();
  for(const f of files) {
    if(f.symlink||f.special) {errors.push('NONREGULAR_FILE: '+f.path);continue;}
    if(!strictRelativePath(f.path)) {errors.push('UNSAFE_FILE_NAME: '+f.path);continue;}
    found.add(f.path);
    const approval=allowed.get(f.path);
    if(!approval) {errors.push('UNAPPROVED_MEDIA: '+f.path);continue;}
    if((await sha256(path.join(root,f.path)))!==approval.sha256)
      errors.push('SHA256_CHANGED: '+f.path);
  }
  for(const name of allowed.keys()) if(!found.has(name))
    errors.push('APPROVED_BUT_MISSING: '+name);
  return errors;
}

async function main() {
  const args=process.argv.slice(2), isRelease=args.includes('--release');
  const project=path.resolve(args.find(x=>!x.startsWith('--'))||'.');
  const policy=JSON.parse(await readFile(path.join(project,'config/highfly_release_policy.json'),'utf8'));
  const manifest=JSON.parse(await readFile(path.join(project,'config/highfly_approved_media.json'),'utf8'));
  const validation=validateManifest(manifest);
  if(!isRelease) {
    if(validation.length) throw Error('MANIFEST_INVALID:\n'+validation.join('\n'));
    console.log('HIGHFLY policy manifest valid. COMMERCIAL RELEASE STILL LOCKED.');
    return;
  }
  const errors=[...validation,...validatePolicy(policy)];
  const stage=process.env.HIGHFLY_RELEASE_STAGE;
  if(!stage) errors.push('HIGHFLY_RELEASE_STAGE_MISSING');
  else errors.push(...await auditMediaTree(path.join(path.resolve(stage),'public'),manifest));
  if(errors.length) throw Error('COMMERCIAL RELEASE BLOCKED:\n'+errors.join('\n'));
  console.log('HIGHFLY FILE GATE PASSED (still requires external legal/product review).');
}
if (process.argv[1] && path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)) {
  main().catch(e=>{console.error(String(e));process.exitCode=1;});
}
