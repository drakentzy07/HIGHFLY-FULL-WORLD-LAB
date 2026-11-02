// HIGHFLY WORLD 7 P71 DRAKENLAB: strictly private OFFLINE-only class test launcher.
// Reload a fresh Sim, never mutate the class of a live entity. No asset reuse.
import type { PlayerClass } from '../sim/types';

export const DRAKENLAB_CLASSES = [
  'warrior', 'paladin', 'hunter', 'rogue', 'priest',
  'shaman', 'mage', 'warlock', 'druid',
] as const satisfies readonly PlayerClass[];

const LABELS: Record<PlayerClass, string> = {
  warrior: 'Guerrero', paladin: 'Paladín', hunter: 'Cazador',
  rogue: 'Pícaro', priest: 'Sacerdote', shaman: 'Chamán',
  mage: 'Mago', warlock: 'Brujo', druid: 'Druida',
};
const MARKS: Record<PlayerClass, string> = {
  warrior: 'GR', paladin: 'PA', hunter: 'CA', rogue: 'PI',
  priest: 'SA', shaman: 'CH', mage: 'MA', warlock: 'BR', druid: 'DR',
};
const ROOT_ID = 'highfly-drakenlab-p71';

export function isDrakenLabClass(value: string | null): value is PlayerClass {
  return DRAKENLAB_CLASSES.some((cls) => cls === value);
}

export function isDrakenLabEnabled(search: string): boolean {
  return new URLSearchParams(search).get('hf_drakenlab') === '1';
}

export function validDrakenLabName(name: string): boolean {
  return /^[A-Za-z][A-Za-z' -]{1,15}$/.test(name);
}

export function readDrakenLabBoot(search: string): { cls: PlayerClass; name: string } | null {
  const params = new URLSearchParams(search);
  const cls = params.get('hf_lab_cls');
  const name = params.get('hf_lab_name');
  if (params.get('hf_drakenlab') !== '1' || !isDrakenLabClass(cls) ||
      !name || !validDrakenLabName(name)) return null;
  return { cls, name };
}

// One-shot boot avoids an infinite restart loop if a model or runtime fails.
export function consumeDrakenLabBootRequest(): { cls: PlayerClass; name: string } | null {
  const request = readDrakenLabBoot(window.location.search);
  if (!request) return null;
  const url = new URL(window.location.href);
  url.searchParams.delete('hf_lab_cls');
  url.searchParams.delete('hf_lab_name');
  window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
  return request;
}

export function restartDrakenLab(cls: PlayerClass, name: string): void {
  if (!isDrakenLabClass(cls)) throw new Error('DRAKENLAB_INVALID_CLASS');
  const safeName = validDrakenLabName(name) ? name : 'Draken';
  const url = new URL(window.location.href);
  url.searchParams.set('hf_drakenlab', '1');
  url.searchParams.set('hf_lab_cls', cls);
  url.searchParams.set('hf_lab_name', safeName);
  url.searchParams.delete('diagnostics');
  url.searchParams.delete('diagnosticsAuto');
  window.location.assign(url.toString());
}

export function mountDrakenLab(options: {
  currentClass: PlayerClass;
  playerName: string;
  onChoose: (cls: PlayerClass) => void;
}): void {
  if (!isDrakenLabClass(options.currentClass)) return;
  if (document.getElementById(ROOT_ID)) return;
  const root = document.createElement('div');
  root.id = ROOT_ID;
  root.className = 'hf-lab';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'hf-lab-toggle';
  toggle.setAttribute('aria-label', 'Abrir DrakenLAB: cambiar clase');
  toggle.textContent = 'DRAKENLAB';
  root.appendChild(toggle);

  const panel = document.createElement('section');
  panel.className = 'hf-lab-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'DrakenLAB - nueve clases');
  panel.hidden = true;
  const header = document.createElement('div');
  header.className = 'hf-lab-header';
  const heading = document.createElement('div');
  const headingStrong = document.createElement('strong');
  headingStrong.textContent = 'DRAKENLAB';
  const headingSmall = document.createElement('small');
  headingSmall.textContent = '9 clases · laboratorio offline';
  heading.append(headingStrong, headingSmall);
  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'hf-lab-close';
  close.setAttribute('aria-label', 'Cerrar DrakenLAB');
  close.textContent = '×';
  header.append(heading, close);
  panel.appendChild(header);
  const current = document.createElement('p');
  current.className = 'hf-lab-current';
  current.textContent = 'Personaje: ' + options.playerName + ' · Actual: ' + LABELS[options.currentClass];
  panel.appendChild(current);
  const grid = document.createElement('div');
  grid.className = 'hf-lab-grid';
  let selected: PlayerClass = options.currentClass;
  const buttons = new Map<PlayerClass, HTMLButtonElement>();
  const action = document.createElement('button');
  action.type = 'button';
  action.className = 'hf-lab-action';
  const update = (): void => {
    for (const [cls, btn] of buttons) {
      const active = cls === selected;
      btn.classList.toggle('selected', active);
      btn.setAttribute('aria-pressed', String(active));
      btn.title = active ? 'Clase actual o seleccionada' : 'Probar ' + LABELS[cls];
    }
    const same = selected === options.currentClass;
    action.disabled = same;
    action.textContent = same
      ? LABELS[selected] + ' · Clase actual'
      : 'REINICIAR COMO ' + LABELS[selected].toUpperCase();
  };
  for (const cls of DRAKENLAB_CLASSES) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'hf-lab-class';
    const emblem = document.createElement('span');
    emblem.className = 'hf-lab-emblem';
    emblem.textContent = MARKS[cls];
    const label = document.createElement('span');
    label.textContent = LABELS[cls];
    button.append(emblem, label);
    button.addEventListener('click', () => { selected = cls; update(); });
    buttons.set(cls, button);
    grid.appendChild(button);
  }
  panel.appendChild(grid);
  const notice = document.createElement('p');
  notice.className = 'hf-lab-notice';
  notice.textContent =
    'PRUEBA LOCAL · Se reinicia el mundo. Inventario, progreso y habilidades ' +
    'no se transfieren entre clases. No modifica personajes online.';
  panel.appendChild(notice);
  action.addEventListener('click', () => {
    if (selected !== options.currentClass) {
      action.disabled = true;
      action.textContent = 'REINICIANDO LAB…';
      options.onChoose(selected);
    }
  });
  panel.appendChild(action);
  root.appendChild(panel);
  const open = (value: boolean): void => {
    panel.hidden = !value;
    toggle.setAttribute('aria-expanded', String(value));
    if (value) { update(); close.focus(); }
    else toggle.focus();
  };
  toggle.addEventListener('click', () => open(panel.hidden));
  close.addEventListener('click', () => open(false));
  root.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !panel.hidden) { e.preventDefault(); open(false); }
  });
  update();
  document.body.appendChild(root);
}
