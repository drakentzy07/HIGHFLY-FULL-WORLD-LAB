// Build a non-mutating list of Eastbrook's existing building IDs and asset
// references so HIGHFLY replacements preserve placement, quest anchors and IDs.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildKaykitCandidates, exactRightsHints, classifyAsset } from './inventory_kaykit_0447.mjs';
import { readCreditsFamilies } from './audit_credits.mjs';

export function scanEastbrookBuildings(source) {
  // The literal makeBuilding rows are just one component of the world layout.
  // This deliberately does NOT pretend to cover procedural props/interiors.
  const pattern = /makeBuilding\(\s*'([^']+)'\s*,\s*'(\/models\/[^']+\.glb)'/g;
  const found = [];
  for (const match of source.matchAll(pattern)) {
    found.push({ id: match[1], assetId: match[2], publicPath: 'public' + match[2] });
  }
  return found;
}

export async function plan(upstream, target) {
  const layout = await readFile(path.join(upstream, 'src/sim/eastbrook_layout.ts'), 'utf8');
  const credits = readCreditsFamilies(await readFile(path.join(upstream, 'CREDITS.md'), 'utf8'));
  const names = [
    'scripts/assets/specs/gale_harbor.json',
    'scripts/assets/specs/biome_packs.json',
  ];
  const specs = await Promise.all(names.map(async (name) =>
    ({ name, data: JSON.parse(await readFile(path.join(upstream, name), 'utf8')) })));
  const candidates = buildKaykitCandidates(specs, credits);
  const hints = exactRightsHints(credits);
  const buildings = scanEastbrookBuildings(layout).map((b) => ({
    ...b,
    ...classifyAsset(b.publicPath, candidates, hints),
    instruction: 'KEEP ID AND FOOTPRINT. TEST collision, NPC anchors, interior, entry, door scale.',
  }));
  if (buildings.length < 8) throw Error('EASTBROOK_LAYOUT_CHANGED: insufficient makeBuilding records');
  const report = {
    source: 'v0.44.7 src/sim/eastbrook_layout.ts',
    note: 'Building reference blueprint ONLY. No licensed assets or runtime modifications.',
    count: buildings.length,
    buildings,
  };
  await mkdir(target, { recursive: true });
  await writeFile(path.join(target, 'EASTBROOK_BUILDINGS.json'), JSON.stringify(report, null, 2) + '\n');
  const byStatus = {};
  for (const b of buildings) byStatus[b.status] = (byStatus[b.status] ?? 0) + 1;
  return { count: buildings.length, byStatus, target };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const upstream = path.resolve(process.argv[2] ?? '.workspace/claudecraft-v0.44.7');
  const target = path.resolve(process.argv[3] ?? '.workspace/reports/v0.44.7/media');
  console.log('[HIGHFLY] Eastbrook integration blueprint:', JSON.stringify(await plan(upstream, target)));
}
