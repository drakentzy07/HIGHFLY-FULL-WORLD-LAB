// HIGHFLY ORIGIN v0.44.7: isolated KayKit GLB viewer in PRIVATE local clone.
// It does not load or mutate gameplay, progression, world state, NPCs, quests or saves.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

type Source = { key: 'hero' | 'skeleton'; title: string; file: string; donor?: string | null };
type PilotManifest = { project: string; sourceCommit: string; models: Source[] };
const root = document.getElementById('stage')!;
const status = document.getElementById('status')!;
const clips = document.getElementById('clips') as HTMLSelectElement;
const buttons = {
  hero: document.getElementById('hero') as HTMLButtonElement,
  skeleton: document.getElementById('skeleton') as HTMLButtonElement,
};
const canvas = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
canvas.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
canvas.outputColorSpace = THREE.SRGBColorSpace;
canvas.setClearColor(0x060b17);
root.appendChild(canvas.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#070d1d');
scene.fog = new THREE.Fog(0x070d1d, 8, 22);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
camera.position.set(2.8, 2.0, 4.0);
const orbit = new OrbitControls(camera, canvas.domElement);
orbit.enableDamping = true;
orbit.target.set(0, 0.9, 0);
orbit.minDistance = 1.3;
orbit.maxDistance = 9;
orbit.update();
const hemi = new THREE.HemisphereLight(0xaedaff, 0x243257, 2.5);
scene.add(hemi);
const key = new THREE.DirectionalLight(0xd3edff, 3.3);
key.position.set(-3, 6, 5); scene.add(key);
const rim = new THREE.DirectionalLight(0x876eff, 2.0);
rim.position.set(3, 4, -3); scene.add(rim);
const grid = new THREE.GridHelper(12, 24, 0x3067ae, 0x182b4d);
grid.position.y = -0.015; scene.add(grid);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200),
  new THREE.MeshStandardMaterial({ color: 0x081126, roughness: 0.9 }));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.02;
scene.add(floor);
const modelRoot = new THREE.Group();
scene.add(modelRoot);
const loader = new GLTFLoader();
const clock = new THREE.Clock();
let mixer: THREE.AnimationMixer | null = null;
let active: THREE.Object3D | null = null;
let manifest: PilotManifest;
let serial = 0;
let actions: THREE.AnimationClip[] = [];
let disposed = false;

async function loadModel(url: string) {
  return await loader.loadAsync(url);
}
function setStatus(msg: string) { status.textContent = msg; }
function clearPrevious() {
  if (mixer) mixer.stopAllAction();
  mixer = null;
  if (active) modelRoot.remove(active);
  active = null;
  clips.replaceChildren(new Option('Sin animación', ''));
}
function resetCamera() {
  camera.position.set(2.8, 2.0, 4);
  orbit.target.set(0, 0.9, 0);
  orbit.update();
}
function playClip(index: number) {
  if (!mixer) return;
  mixer.stopAllAction();
  const clip = actions[index];
  if (clip) {
    mixer.clipAction(clip).reset().play();
    setStatus('Animación: ' + clip.name + ' · rig y deformación a comprobar visualmente');
  }
}
async function selectModel(which: 'hero' | 'skeleton') {
  const ticket = ++serial;
  const source = manifest.models.find(m => m.key === which);
  if (!source) { setStatus('Modelo no disponible en el pack importado.'); return; }
  for (const [name, button] of Object.entries(buttons))
    button.setAttribute('aria-pressed', String(name === which));
  setStatus('Cargando ' + source.title + '...');
  try {
    const gltf = await loadModel(source.file);
    if (ticket !== serial) return;
    clearPrevious();
    const body = gltf.scene;
    const box = new THREE.Box3().setFromObject(body);
    const size = box.getSize(new THREE.Vector3());
    if (!Number.isFinite(size.y) || size.y < 0.001)
      throw new Error('GLB sin altura visible válida');
    const center = box.getCenter(new THREE.Vector3());
    body.position.set(-center.x, -box.min.y, -center.z);
    const wrapper = new THREE.Group();
    wrapper.scale.setScalar(1.7 / size.y);  // display reference only, never changes game scale
    wrapper.add(body);
    active = wrapper;
    modelRoot.add(wrapper);
    mixer = new THREE.AnimationMixer(body);
    actions = gltf.animations.slice();
    if (source.donor) {
      try {
        const donor = await loadModel(source.donor);
        if (ticket !== serial) return;
        const names = new Set(actions.map(c => c.name));
        for (const clip of donor.animations) if (!names.has(clip.name)) actions.push(clip);
      } catch (error) {
        console.warn('Optional KayKit animation donor unavailable:', error);
      }
    }
    for (let index = 0; index < actions.length; index++)
      clips.add(new Option(actions[index].name, String(index)));
    if (actions.length) {
      const idle = actions.findIndex(c => /idle/i.test(c.name));
      const pick = idle >= 0 ? idle : 0;
      clips.value = String(pick);
      playClip(pick);
    }
    setStatus(source.title + ' · GLB OK · ' + actions.length +
      ' clips detectados · referencia visual normalizada a 1,70 m; no representa la escala real del juego');
  } catch(error) {
    console.error(error);
    if(ticket === serial) setStatus('Error al cargar el modelo: ' + String(error));
  }
}
for (const [name, button] of Object.entries(buttons))
  button.addEventListener('click', () => void selectModel(name as 'hero'|'skeleton'));
clips.addEventListener('change', () => { const n = Number(clips.value); if(Number.isInteger(n)) playClip(n); });
document.getElementById('reset')?.addEventListener('click', resetCamera);
function sizeToParent() {
  const w = Math.max(root.clientWidth, 1), h = Math.max(root.clientHeight, 1);
  canvas.setSize(w, h, false);
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', sizeToParent);sizeToParent();
function frame() {
  if(disposed) return;
  requestAnimationFrame(frame);
  mixer?.update(Math.min(clock.getDelta(), 0.05));
  orbit.update();
  canvas.render(scene, camera);
}
frame();
window.addEventListener('pagehide',()=>{disposed=true;orbit.dispose();canvas.dispose();});
try {
  const response = await fetch('/highfly-private-pilot/manifest.json', {cache:'no-store'});
  if(!response.ok) throw Error('Falta manifiesto privado del piloto: HTTP ' + response.status);
  manifest = await response.json() as PilotManifest;
  if(manifest.sourceCommit !== '493c35a108cef6c8aa290e8793107b1cd117886e')
    throw Error('Versión distinta a ClaudeCraft v0.44.7');
  await selectModel('hero');
} catch(error) { console.error(error);setStatus('Piloto no preparado: '+String(error)); }
