import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { strictRelativePath, validateManifest, validatePolicy, auditMediaTree } from '../scripts/highfly_release_gate.mjs';
import { allowCodeFile, SOURCE_COMMIT } from '../scripts/highfly_stage_code_0447.mjs';
import { classifyKaykitFile, identifyPack } from '../scripts/highfly_catalog_kaykit_v7.mjs';

function sampleAsset(b) {
  return {
    path:'public/models/biome/hexb_home_a.glb',
    sha256:createHash('sha256').update(b).digest('hex'),
    license:'CC0-1.0',
    sourceUrl:'https://kaylousberg.itch.io/kaykit-medieval-hexagon',
    evidenceUrl:'https://creativecommons.org/publicdomain/zero/1.0/',
    author:'Kay Lousberg',
    reviewedBy:'human reviewer',reviewedOn:'2026-10-30'
  };
}
test('source stage is hard-pinned to the KayKit 0.44.7 version',()=>{
  assert.equal(SOURCE_COMMIT,'493c35a108cef6c8aa290e8793107b1cd117886e');
  assert.equal(allowCodeFile('src/game/sim.ts'),true);
  assert.equal(allowCodeFile('src/render/images/ui-icon.png'),false);
  assert.equal(allowCodeFile('src/render/models/a.glb'),false);
  assert.equal(allowCodeFile('public/x.ts'),false);
  assert.equal(allowCodeFile('src/.env'),false);
  assert.equal(allowCodeFile('src/vendor/node_modules/example.js'),false);
});
test('independent HIGHFLY release is locked by default',()=>{
  const policy={
    schemaVersion:1,project:'HIGHFLY ORIGIN',releaseApproved:false,
    checks:{mediaProvenance:false,thirdPartyDependencies:false},
    reviewer:null,approvedOn:null
  };
  const failures=validatePolicy(policy);
  assert.ok(failures.includes('RELEASE_LOCKED'));
  assert.ok(failures.includes('PENDING_mediaProvenance'));
  assert.ok(failures.includes('FINAL_HUMAN_SIGNOFF_MISSING'));
});
test('per-file media whitelist is strict, not family-only',()=>{
  const entry=sampleAsset('fixture');
  assert.deepEqual(validateManifest({schemaVersion:1,assets:[entry]}),[]);
  assert.ok(validateManifest({schemaVersion:1,assets:[{...entry,license:'With the project only'}]}).length);
  assert.ok(validateManifest({schemaVersion:1,assets:[{...entry,path:'public/../out.glb'}]}).length);
  assert.ok(validateManifest({schemaVersion:1,assets:[{...entry,sourceUrl:'',evidenceUrl:''}]}).length);
  assert.ok(validateManifest({schemaVersion:1,assets:[entry,entry]}).length);
  assert.equal(strictRelativePath('public/models/test.glb'),true);
  assert.equal(strictRelativePath('public/models/../../secret.glb'),false);
});
test('missing, extra or changed media blocks release',async()=>{
  const dir=await mkdtemp(path.join(tmpdir(),'highfly-rights-'));
  try {
    await mkdir(path.join(dir,'models'),{recursive:true});
    const a=sampleAsset('good');
    await writeFile(path.join(dir,'models/hexb_home_a.glb'),'good');
    const manifest={schemaVersion:1,assets:[a]};
    assert.deepEqual(await auditMediaTree(dir,manifest),[]);
    await writeFile(path.join(dir,'models/hexb_home_a.glb'),'changed');
    assert.ok((await auditMediaTree(dir,manifest)).some(x=>x.includes('SHA256_CHANGED')));
    await writeFile(path.join(dir,'models/unknown.glb'),'bad');
    assert.ok((await auditMediaTree(dir,manifest)).some(x=>x.includes('UNAPPROVED_MEDIA')));
  } finally {await rm(dir,{recursive:true,force:true});}
});
test('KayKit v7 metadata supports pack categories without assuming animation compatibility',()=>{
  assert.equal(identifyPack('The Complete KayKit Collection v7/KayKit Adventurers 2.0/file.fbx'),'KayKit Adventurers 2.0');
  assert.equal(classifyKaykitFile('KayKit Adventurers 2.0/Assets/a.fbx').requiresRigCheck,true);
  assert.equal(classifyKaykitFile('KayKit Medieval Hexagon Pack 1.0.1/Assets/gltf/house.gltf').isModel,true);
});
