// HIGHFLY 0.44.7: read-only, fail-closed inventory for a PRIVATE Codespace.
// No license is granted by this script. No game files are modified or published.
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { readCreditsFamilies } from './audit_credits.mjs';

export const UPSTREAM_0447 = '493c35a108cef6c8aa290e8793107b1cd117886e';
export const SPEC_FILES = [
  'scripts/assets/specs/biome_packs.json',
  'scripts/assets/specs/gale_harbor.json',
];
export const PROVISIONAL = 'KAYKIT_CC0_CANDIDATE_REQUIRES_FILE_VERIFICATION';
export const BLOCKED = 'BLOCKED_UNVERIFIED';

export function normalizeRelativeMediaPath(value) {
  if (typeof value !== 'string') return null;
  const candidate = value.replaceAll('\\', '/').replace(/^public\//, '');
  if (!candidate || candidate.startsWith('/') || candidate.includes('?') || candidate.includes('#')) return null;
  const parts = candidate.split('/');
  if (parts.some((p) => !p || p === '.' || p === '..')) return null;
  if (!/^[A-Za-z0-9_./()+ -]+$/.test(candidate)) return null;
  return candidate;
}
export function buildKaykitCandidates(specs, creditsRows) {
  const credit = creditsRows.find((r) =>
    /Kay Lousberg \(KayKit\)/i.test(r.author) &&
    /Medieval Hexagon Pack/.test(r.assets) &&
    r.license.replaceAll('**', '').trim() === 'CC0 1.0' &&
    r.redistribution === 'Yes');
  const candidates = new Map();
  if (!credit) return candidates;
  for (const { name, data } of specs) {
    for (const item of data.items ?? []) {
      if (!/KayKit[-_ /].*(Hexagon|Medieval)/i.test(item.src ?? '')) continue;
      const logical = normalizeRelativeMediaPath(item.out);
      if (!logical || !logical.startsWith('models/')) continue;
      candidates.set('public/' + logical, {
        pack: 'KayKit Medieval Hexagon Pack',
        sourceSpec: name,
        sourceBasename: path.posix.basename(String(item.src).replaceAll('\\', '/')),
        licenseFamily: 'CREDITS.md / Medieval Hexagon Pack / CC0 1.0 / Yes',
      });
    }
  }
  return candidates;
}
export function exactRightsHints(creditsRows) {
  const hints = new Map();
  const tick = String.fromCharCode(96);
  for (const row of creditsRows) {
    const rights = String(row.redistribution).replaceAll('**', '');
    let status;
    if (rights === 'No, permission required') status = 'BLOCKED_RIGHTS_RESERVED';
    else if (rights === 'With the project only') status = 'BLOCKED_PROJECT_ONLY_FOR_INDEPENDENT_HIGHFLY';
    else if (rights === 'Non-commercial only, with attribution') status = 'BLOCKED_NONCOMMERCIAL';
    else continue;
    const spans = row.assets.split(tick);
    for (let i = 1; i < spans.length; i += 2) {
      const raw = spans[i];
      if (!raw.startsWith('public/') || /[{}*<>]/.test(raw) || raw.includes(',')) continue;
      const logical = normalizeRelativeMediaPath(raw);
      if (!logical) continue;
      const key = 'public/' + logical;
      if (!hints.has(key)) hints.set(key, { status, creditsLine: row.line });
    }
  }
  return hints;
}
export function classifyAsset(file, candidates, rightsHints) {
  const explicitBlock = rightsHints.get(file);
  if (explicitBlock) return { status: explicitBlock.status, creditsLine: explicitBlock.creditsLine };
  const candidate = candidates.get(file);
  if (candidate) return { status: PROVISIONAL, ...candidate };
  return { status: BLOCKED };
}
async function walkFiles(directory, prefix = '') {
  const output = [];
  for (const ent of await readdir(directory, { withFileTypes: true })) {
    const relative = prefix ? prefix + '/' + ent.name : ent.name;
    if (ent.isDirectory()) output.push(...await walkFiles(path.join(directory, ent.name), relative));
    else if (ent.isFile()) output.push(relative);
  }
  return output;
}
async function sha256(filepath) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(filepath)) hash.update(chunk);
  return hash.digest('hex');
}
export async function inventory(upstream, target) {
  const markdown = await readFile(path.join(upstream, 'CREDITS.md'), 'utf8');
  const credits = readCreditsFamilies(markdown);
  const specs = [];
  for (const name of SPEC_FILES) {
    specs.push({ name, data: JSON.parse(await readFile(path.join(upstream, name), 'utf8')) });
  }
  const candidates = buildKaykitCandidates(specs, credits);
  const hints = exactRightsHints(credits);
  const files = (await walkFiles(path.join(upstream, 'public'))).sort();
  const records = [];
  for (const relative of files) {
    const filename = 'public/' + relative;
    const filepath = path.join(upstream, filename);
    const { size } = await stat(filepath);
    records.push({
      file: filename,
      bytes: size,
      sha256: await sha256(filepath),
      ...classifyAsset(filename, candidates, hints),
    });
  }
  const count = {};
  for (const entry of records) count[entry.status] = (count[entry.status] ?? 0) + 1;
  const report = {
    schemaVersion: 1,
    upstream: 'levy-street/world-of-claudecraft',
    tag: 'v0.44.7',
    sourceCommit: UPSTREAM_0447,
    purpose: 'PRIVATE AUDIT ONLY. NO ASSET IS LICENSED FOR HIGHFLY RELEASE BY THIS REPORT.',
    fileCount: records.length,
    countByStatus: count,
    records,
  };
  await mkdir(target, { recursive: true });
  await writeFile(path.join(target, 'MEDIA_ALL_FILES.json'), JSON.stringify(report, null, 2) + '\n');
  const provisional = records.filter((r) => r.status === PROVISIONAL);
  await writeFile(path.join(target, 'KAYKIT_CANDIDATES.json'), JSON.stringify(provisional, null, 2) + '\n');
  await writeFile(path.join(target, 'RESUMEN_INVENTARIO.md'), [
    '# HIGHFLY KayKit-first — v0.44.7 media',
    '',
    'ESTADO: todos los archivos sin aprobación legal individual de publicación.',
    '',
    'Versión original: ' + UPSTREAM_0447,
    'Archivos inventariados: ' + records.length,
    ...Object.entries(count).sort().map(([key, n]) => '- ' + key + ': ' + n),
    '',
    'Los candidatos KayKit provienen de specs de importación + CREDITS CC0.',
    'Un candidato no equivale a un archivo aprobado: revisar licencia,',
    'proveniencia, derivaciones y recursos internos antes de publicar.',
    'La carpeta .workspace/ queda excluida de Git y todo permanece privado.',
    '',
  ].join('\n'));
  return { fileCount: records.length, countByStatus: count, kaykitCandidates: provisional.length, target };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const upstream = path.resolve(process.argv[2] ?? '.workspace/claudecraft-v0.44.7');
  const target = path.resolve(process.argv[3] ?? '.workspace/reports/v0.44.7/media');
  const result = await inventory(upstream, target);
  console.log('[HIGHFLY] v0.44.7 media inventory:', JSON.stringify(result));
  console.log('[HIGHFLY] Every entry remains BLOCKED or a CC0 CANDIDATE. No shipping authorization.');
}
