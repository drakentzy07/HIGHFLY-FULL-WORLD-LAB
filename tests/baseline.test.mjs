import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyMedia,readCreditsFamilies,PINNED_UPSTREAM_SHA} from '../scripts/audit_credits.mjs';

test('original pin is immutable 0.44.7 SHA',()=>{
  assert.equal(PINNED_UPSTREAM_SHA,'493c35a108cef6c8aa290e8793107b1cd117886e');
  const script=readFileSync(new URL('../scripts/bootstrap_original.sh',import.meta.url),'utf8');
  assert.match(script,/--branch v0\.44\.7/);
  assert.match(script,/493c35a108cef6c8aa290e8793107b1cd117886e/);
  assert.match(script,/--sparse/);
});
test('strict independent media license policy blocks project-only and NC',()=>{
  assert.equal(classifyMedia('CC0 1.0','Yes'),'CANDIDATE_CC0_REQUIRES_FILE_CHECK');
  assert.equal(classifyMedia('MIT','Yes, attribution required'),'CANDIDATE_MIT_REQUIRES_NOTICE_AND_FILE_CHECK');
  assert.equal(classifyMedia('Project asset','With the project only'),'EXCLUDE_PROJECT_ONLY');
  assert.equal(classifyMedia('Project asset, rights reserved','**No, permission required**'),'EXCLUDE_RIGHTS_RESERVED');
  assert.equal(classifyMedia('CC BY-NC 4.0','Non-commercial only, with attribution'),'EXCLUDE_NONCOMMERCIAL');
  assert.equal(classifyMedia('unknown',''),'BLOCK_REVIEW_OTHER_LICENSE');
});
test('mock CREDITS families are parsed without granting asset approval',()=>{
  const rows=readCreditsFamilies('# Asset Credits\n'+[
   '| Assets | Author | Source | License | Redistribution |',
   '|---|---|---|---|---|',
   ...Array.from({length:105},(_,i)=>
     i===0?'| Wolf | Quaternius | example.org | CC0 1.0 | Yes |':
      '| Project-specific media '+i+' | Project | own | Project asset | With the project only |')
  ].join('\n'));
  assert.equal(rows.length,105);
  assert.equal(rows[0].fileStatus,'UNVERIFIED');
  assert.equal(rows[0].decision,'CANDIDATE_CC0_REQUIRES_FILE_CHECK');
  assert.equal(rows[104].decision,'EXCLUDE_PROJECT_ONLY');
});
test('Codespaces port remains private in documentation and devcontainer is set up',()=>{
  const dev=JSON.parse(readFileSync(new URL('../.devcontainer/devcontainer.json',import.meta.url),'utf8'));
  assert.equal(dev.portsAttributes['5173'].onAutoForward,'notify');
  assert.equal(dev.postCreateCommand,'bash scripts/bootstrap_original.sh');
  assert.ok(dev.forwardPorts.includes(5173));
  assert.ok(dev.forwardPorts.includes(4173));
  assert.ok(readFileSync(new URL('../.gitignore',import.meta.url),'utf8').includes('.workspace/'));
});


test('private preview is isolated and guarded, not a public deployment',()=>{
  const start=readFileSync(new URL('../scripts/start_preview_0447.sh',import.meta.url),'utf8');
  const patch=readFileSync(new URL('../scripts/prepare_preview_0447.mjs',import.meta.url),'utf8');
  assert.match(start,/493c35a108cef6c8aa290e8793107b1cd117886e/);
  assert.match(start,/--port 4173/);
  assert.match(start,/VITE_HIGHFLY_OFFLINE_LAB=1/);
  assert.match(patch,/offline_mode_gate\.ts/);
  assert.match(patch,/UPSTREAM_SOURCE_CHANGED/);
  assert.match(readFileSync(new URL('../README.md',import.meta.url),'utf8'),/Private|PRIVATE/);
});
