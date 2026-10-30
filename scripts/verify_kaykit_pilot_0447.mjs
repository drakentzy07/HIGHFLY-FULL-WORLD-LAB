// HIGHFLY P1 — Validate the real KayKit Eastbrook building baseline in-place.
// Read-only: no changes to GLBs, game sources, Vite preview or the git repository.
import { open, readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { readCreditsFamilies } from './audit_credits.mjs';
import { buildKaykitCandidates, exactRightsHints, classifyAsset, PROVISIONAL } from './inventory_kaykit_0447.mjs';

export const PIN = '493c35a108cef6c8aa290e8793107b1cd117886e';
export const PLAYER_REFERENCE_METERS = 1.70;

// Parse the shipped Eastbrook BUILDINGS layout, not a hand-maintained catalog.
// Keep source IDs and design dimensions; do not recompute or change footprints.
export function parseBuildingSpecs(src) {
  const section = src.match(/const BUILDINGS = \[([\s\S]*?)\] as const;/);
  if (!section) throw Error('EASTBROOK_BUILDING_TABLE_MISSING');
  const pattern = /makeBuilding\(\s*'([^']+)',\s*'(\/models\/[^']+\.glb)',\s*'(house|inn|chapel)',\s*\{\s*x:\s*(-?[\d.]+),\s*z:\s*(-?[\d.]+)\s*\},\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*(-?[\d.]+)/g;
  const result = [];
  for (const x of section[1].matchAll(pattern)) {
    result.push({
      id: x[1], assetId: x[2], kind: x[3],
      x: Number(x[4]), z: Number(x[5]),
      width: Number(x[6]), height: Number(x[7]), depth: Number(x[8]),
      rotationRadians: Number(x[9]),
    });
  }
  if (result.length !== 11 || new Set(result.map(x => x.id)).size !== result.length) {
    throw Error('EASTBROOK_STRUCTURE_MISMATCH: expected 11 unique unchanged buildings; got ' + result.length);
  }
  return result;
}

export function inspectGlbHeader(buffer, byteLength) {
  if (buffer.length < 12 || byteLength < 12) return { valid: false, reason: 'TOO_SMALL' };
  if (buffer.toString('ascii', 0, 4) !== 'glTF') return { valid: false, reason: 'WRONG_MAGIC' };
  const version = buffer.readUInt32LE(4);
  const expectedLength = buffer.readUInt32LE(8);
  if (version !== 2) return { valid: false, reason: 'GLTF_VERSION_' + version };
  if (expectedLength !== byteLength) {
    return { valid: false, reason: 'GLB_LENGTH_MISMATCH', declaredBytes: expectedLength, actualBytes: byteLength };
  }
  return { valid: true, version, bytes: byteLength };
}
async function verifyGlb(filename) {
  let file;
  try {
    file = await open(filename, 'r');
    const { size } = await file.stat();
    const buf = Buffer.alloc(12);
    const { bytesRead } = await file.read(buf, 0, 12, 0);
    return inspectGlbHeader(buf.subarray(0, bytesRead), size);
  } catch (error) {
    return { valid: false, reason: error.code || String(error) };
  } finally {
    await file?.close();
  }
}

export async function run(upstream, target) {
  const layout = await readFile(path.join(upstream, 'src/sim/eastbrook_layout.ts'), 'utf8');
  const specs = parseBuildingSpecs(layout);
  const credits = readCreditsFamilies(await readFile(path.join(upstream, 'CREDITS.md'), 'utf8'));
  const specPaths = ['scripts/assets/specs/gale_harbor.json', 'scripts/assets/specs/biome_packs.json'];
  const sourceSpecs = await Promise.all(specPaths.map(async name =>
    ({ name, data: JSON.parse(await readFile(path.join(upstream, name), 'utf8')) })));
  const candidates = buildKaykitCandidates(sourceSpecs, credits);
  const hints = exactRightsHints(credits);
  const records = await Promise.all(specs.map(async b => {
    const file = 'public' + b.assetId;
    const glb = await verifyGlb(path.join(upstream, file));
    const rights = classifyAsset(file, candidates, hints);
    return {
      ...b,
      file,
      glb,
      rights,
      heightVsPlayer: Number((b.height / PLAYER_REFERENCE_METERS).toFixed(2)),
      physicalNote: 'height is a layout setting, not measured door clearance',
      testChecklist: ['visible from street', 'no terrain sink', 'walkable approach', 'wall collision', 'NPC/quest anchors'],
    };
  }));
  const failure = records.filter(r => !r.glb.valid || r.rights.status !== PROVISIONAL);
  const result = {
    format: 1, upstreamSha: PIN, kind: 'PRIVATE_KAYKIT_BASELINE',
    disclaimer: 'Metadata inspection only; not a runtime test, door measurement or redistribution authorization.',
    playerReferenceMeters: PLAYER_REFERENCE_METERS,
    buildings: records,
    validGlbCount: records.filter(r => r.glb.valid).length,
    provisionalKaykitCount: records.filter(r => r.rights.status === PROVISIONAL).length,
    failedCount: failure.length,
  };
  await mkdir(target, { recursive: true });
  await writeFile(path.join(target, 'KAYKIT_EASTBROOK_P1.json'), JSON.stringify(result, null, 2) + '\n');
  await writeFile(path.join(target, 'KAYKIT_EASTBROOK_P1.md'), [
    '# HIGHFLY P1 — Test de edificios KayKit en Eastbrook',
    '', 'Version: v0.44.7 / ' + PIN,
    'NO PUBLICAR LA COMPILACION ORIGINAL. Todas las licencias son candidatas hasta revisión individual.',
    '', '| ID | Modelo | Ancho | Alto | Prof. | x altura del jugador | GLB |',
    '|---|---|---:|---:|---:|---:|---|',
    ...records.map(r => '| ' + r.id + ' | ' + path.posix.basename(r.assetId) + ' | ' + r.width +
      ' | ' + r.height + ' | ' + r.depth + ' | ' + r.heightVsPlayer +
      ' | ' + (r.glb.valid ? 'cabecera OK' : r.glb.reason) + ' |'),
    '', 'Prueba manual de campo: entrar a Eastbrook, acercarse a una casa, taberna,',
    'taller e iglesia; comprobar posicion, tamaño de las puertas, colisiones y NPC.',
    'Guardar capturas de las puertas junto al personaje 1.70 m de referencia.',
    'La altura de edificios NO verifica por sí sola la altura de las puertas.',
    '',
  ].join('\n'));
  if (failure.length) throw Error('KAYKIT_P1_FAIL_CLOSED: ' + failure.map(r => r.id).join(', '));
  return { buildings: records.length, glbValidated: result.validGlbCount, rightsCandidates: result.provisionalKaykitCount, target };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const root = path.resolve(process.argv[2] ?? '.workspace/claudecraft-v0.44.7');
  const output = path.resolve(process.argv[3] ?? '.workspace/reports/v0.44.7/pilot');
  const result = await run(root, output);
  console.log('[HIGHFLY] KayKit P1 baseline:', JSON.stringify(result));
}
