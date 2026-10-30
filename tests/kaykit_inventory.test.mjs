import test from 'node:test';
import assert from 'node:assert/strict';
import {
  PROVISIONAL, BLOCKED, normalizeRelativeMediaPath,
  buildKaykitCandidates, exactRightsHints, classifyAsset,
} from '../scripts/inventory_kaykit_0447.mjs';

const credits = [{
  author: 'Kay Lousberg (KayKit)',
  assets: 'Medieval Hexagon Pack (hex buildings, hex tiles, walls, bridge)',
  license: 'CC0 1.0',
  redistribution: 'Yes',
  line: 17,
}];
const specs = [{
  name: 'scripts/assets/specs/gale_harbor.json',
  data: { items: [
    { src: 'Complete KayKit Collection v5/KayKit Medieval Hexagon Pack/building_home_A_blue.gltf',
      out: 'models/biome/hexb_home_a.glb' },
    { src: 'a private project model', out: 'models/city/restricted.glb' },
  ] },
}];

test('KayKit candidates require correct source spec AND CC0 registry entry', () => {
  const yes = buildKaykitCandidates(specs, credits);
  assert.equal(yes.size, 1);
  assert.equal(yes.get('public/models/biome/hexb_home_a.glb').pack, 'KayKit Medieval Hexagon Pack');
  assert.equal(classifyAsset('public/models/biome/hexb_home_a.glb', yes, new Map()).status, PROVISIONAL);
  assert.equal(classifyAsset('public/models/city/restricted.glb', yes, new Map()).status, BLOCKED);
  assert.equal(buildKaykitCandidates(specs, []).size, 0);
});

test('a restrictive exact-file credit wins even if a KayKit candidate exists', () => {
  const rights = exactRightsHints([
    { line: 22, assets: 'Project body (public/models/biome/hexb_home_a.glb)', redistribution: 'No, permission required' },
    { line: 23, assets: 'User recording ' + String.fromCharCode(96) + 'public/models/biome/hexb_home_a.glb' + String.fromCharCode(96),
      redistribution: 'No, permission required' },
  ]);
  const candidates = buildKaykitCandidates(specs, credits);
  assert.equal(classifyAsset('public/models/biome/hexb_home_a.glb', candidates, rights).status, 'BLOCKED_RIGHTS_RESERVED');
});

test('project-only and noncommercial explicit paths are never approved', () => {
  const tick = String.fromCharCode(96);
  const rows = [
    {line: 2, assets: tick + 'public/audio/sfx/woc.mp3' + tick, redistribution: 'With the project only'},
    {line: 3, assets: tick + 'public/audio/music/restricted.mp3' + tick, redistribution: 'Non-commercial only, with attribution'},
  ];
  const hints = exactRightsHints(rows);
  assert.equal(classifyAsset('public/audio/sfx/woc.mp3', new Map(), hints).status, 'BLOCKED_PROJECT_ONLY_FOR_INDEPENDENT_HIGHFLY');
  assert.equal(classifyAsset('public/audio/music/restricted.mp3', new Map(), hints).status, 'BLOCKED_NONCOMMERCIAL');
  assert.equal(classifyAsset('public/audio/unknown.wav', new Map(), hints).status, BLOCKED);
});

test('inventory path sanitization rejects traversal, wildcards and absolute paths', () => {
  for (const p of ['../x', 'models/../x.glb', '/etc/passwd', 'models/**/wild.glb', 'models/a?b', 'models//x.glb']) {
    assert.equal(normalizeRelativeMediaPath(p), null, p);
  }
  assert.equal(normalizeRelativeMediaPath('public/models/biome/hexb_home_a.glb'), 'models/biome/hexb_home_a.glb');
  assert.equal(normalizeRelativeMediaPath('models\\biome\\hexb_home_a.glb'), 'models/biome/hexb_home_a.glb');
});
