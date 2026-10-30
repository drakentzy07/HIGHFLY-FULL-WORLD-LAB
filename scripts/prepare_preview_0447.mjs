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


// FIX: v0.44.7 waits for the entire character preload manifest before showing
// the creation model. One unrelated GLB failure previously discarded the
// preview altogether even when its selected class model was already resident.
// Keep the error visible in the console, but attempt the independently guarded
// CharacterVisual instead. World and simulation code remain untouched.
const main = path.join(upstream, 'src/main.ts');
const originalMain = readFileSync(main, 'utf8');
const preloadBefore = '  charactersReady()\n    .then(() => {';
const preloadAfter =
  "  charactersReady()\n" +
  "    .catch((err: unknown) => {\n" +
  "      console.warn('[HIGHFLY 0.44.7] Incomplete character preload; trying selected class preview:', err);\n" +
  "    })\n" +
  "    .then(() => {";
const panelBefore = "const activePanelId = ['#charselect-panel', '#offline-select'].find((id) => {";
const panelAfter = "const activePanelId = ['#charselect-panel', '#charcreate-panel', '#offline-select'].find((id) => {";
const containerBefore =
  "activePanelId === '#offline-select'\n          ? '#offline-preview-container'\n          : '#online-preview-container';";
const containerAfter =
  "activePanelId === '#offline-select'\n          ? '#offline-preview-container'\n          : activePanelId === '#charcreate-panel'\n            ? '#charcreate-preview-container'\n            : '#online-preview-container';";
const afterInitBefore =
  "          previewClassBody(cls);\n        }\n      }\n    })";
const afterInitAfter =
  "          previewClassBody(cls);\n        }\n        // If the selected panel opened during asset loading, reparent and\n" +
  "        // resize the canvas now: its earlier panel-change event saw null.\n" +
  "        if (activePanelId) updatePreviewContainer(activePanelId);\n" +
  "      }\n    })";
function replaceOnce(source, before, after, tag) {
  if (source.includes(after)) return source;
  if (!source.includes(before)) throw Error('UPSTREAM_PREVIEW_SOURCE_CHANGED: ' + tag);
  if (source.indexOf(before) !== source.lastIndexOf(before))
    throw Error('UPSTREAM_PREVIEW_MULTIPLE_MATCHES: ' + tag);
  return source.replace(before, after);
}
let revised = replaceOnce(originalMain, preloadBefore, preloadAfter, 'preload fallback');
revised = replaceOnce(revised, panelBefore, panelAfter, 'active panel');
revised = replaceOnce(revised, containerBefore, containerAfter, 'panel container');
revised = replaceOnce(revised, afterInitBefore, afterInitAfter, 'layout sync');
if (revised !== originalMain) writeFileSync(main, revised);
console.log('Creation preview: independent fail-soft and panel reparent/resize applied.');
