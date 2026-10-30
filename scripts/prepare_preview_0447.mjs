// Applies PRIVATE-CODESPACE-only build adaptations to a disposable v0.44.7 checkout.
// Do not commit the modified upstream tree or publish its resulting dist/.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';

const upstream = path.resolve(process.argv[2] ?? '.workspace/claudecraft-v0.44.7');
const gate = path.join(upstream, 'src/game/offline_mode_gate.ts');
const vite = path.join(upstream, 'vite.config.ts');
if (!existsSync(gate) || !existsSync(vite)) throw Error('Missing v0.44.7 source checkout. Run bootstrap first.');

function exactReplace(filename, from, to) {
  const contents = readFileSync(filename, 'utf8');
  if (contents.includes(to)) return 'already prepared';
  if (!contents.includes(from)) throw Error('UPSTREAM_SOURCE_CHANGED: ' + filename);
  writeFileSync(filename, contents.replace(from, to));
  return 'patched';
}

console.log('Offline gate:', exactReplace(
  gate,
  'return isDev;',
  "return isDev || import.meta.env.VITE_HIGHFLY_OFFLINE_LAB === '1';",
));
console.log('i18n preload:', exactReplace(
  vite,
  '    i18nModulepreloadPlugin(),',
  '    // HIGHFLY private optimized preview: disable optional locale manifest preload.',
));
console.log('PRIVATE LAB ONLY: the source copy in .workspace/ is modified; GitHub repo is not.');
