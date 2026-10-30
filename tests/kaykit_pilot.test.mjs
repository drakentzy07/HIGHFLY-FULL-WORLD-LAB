import test from 'node:test';
import assert from 'node:assert/strict';
import { parseBuildingSpecs, inspectGlbHeader } from '../scripts/verify_kaykit_pilot_0447.mjs';

test('KayKit P1 pins exactly 11 unique building IDs, models, world coordinates and dimensions', () => {
  const buildings = Array.from({length:11}, (_, i) =>
    "  makeBuilding('eastbrook_model_" + i + "', '/models/biome/hexb_home_a.glb', 'house', { x: -28, z: -122 }, 6.9, 9.4, 5.6, 2.55),");
  const source = 'const BUILDINGS = [\n' + buildings.join('\n') + '\n] as const;';
  const records = parseBuildingSpecs(source);
  assert.equal(records.length, 11);
  assert.deepEqual(records[0], {
    id:'eastbrook_model_0',assetId:'/models/biome/hexb_home_a.glb',kind:'house',
    x:-28,z:-122,width:6.9,height:9.4,depth:5.6,rotationRadians:2.55
  });
  assert.throws(() => parseBuildingSpecs('const BUILDINGS = [] as const;'), /MISMATCH/);
});

test('KayKit GLB header check blocks truncated, unknown and mismatched assets', () => {
  const buf = Buffer.alloc(12);
  buf.write('glTF',0,'ascii');
  buf.writeUInt32LE(2,4);
  buf.writeUInt32LE(12,8);
  assert.deepEqual(inspectGlbHeader(buf, 12), {valid:true,version:2,bytes:12});
  assert.equal(inspectGlbHeader(buf, 22).valid, false);
  buf.write('BAD!',0,'ascii');
  assert.equal(inspectGlbHeader(buf, 12).reason, 'WRONG_MAGIC');
  assert.equal(inspectGlbHeader(Buffer.alloc(6), 6).reason, 'TOO_SMALL');
});
