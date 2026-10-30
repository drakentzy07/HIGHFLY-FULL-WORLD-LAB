import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { scanEastbrookBuildings } from '../scripts/plan_eastbrook_kaykit_0447.mjs';

test('Eastbrook scan preserves stable building ID and complete asset path', () => {
  const text = [
    "const BUILDINGS = [",
    "  makeBuilding('eastbrook_bank', '/models/biome/hexb_townhall.glb', 'house', {x:12,z:-94}, 8.6,12.7,6.9, 0),",
    "  makeBuilding(",
    "    'eastbrook_chapel',",
    "    '/models/biome/hex_church.glb',",
    "    'chapel',",
    "  ),",
    "];",
  ].join('\n');
  assert.deepEqual(scanEastbrookBuildings(text), [
    {id:'eastbrook_bank',assetId:'/models/biome/hexb_townhall.glb',publicPath:'public/models/biome/hexb_townhall.glb'},
    {id:'eastbrook_chapel',assetId:'/models/biome/hex_church.glb',publicPath:'public/models/biome/hex_church.glb'},
  ]);
});

test('private rights-audit runner pins version, never builds/publishes or mutates world', () => {
  const script = readFileSync(new URL('../scripts/audit_kaykit_0447.sh', import.meta.url), 'utf8');
  assert.match(script, /493c35a108cef6c8aa290e8793107b1cd117886e/);
  assert.match(script, /inventory_kaykit_0447/);
  assert.match(script, /plan_eastbrook_kaykit_0447/);
  assert.ok(!/git add|git push|vite build|deploy-pages|rm -rf/.test(script));
});
