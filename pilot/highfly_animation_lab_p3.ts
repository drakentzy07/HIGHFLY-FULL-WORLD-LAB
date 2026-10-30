// HIGHFLY ORIGIN P3 — PRIVATE, isolated KayKit rig/animation visualization.
// No engine, map, combat, NPC, inventory, loot or game save changes.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

type ModelEntry = { key: 'hero' | 'skeleton'; title: string; file: string };
type Donor = { title: string; file: string; clips: string[]; clipCount: number };
type Manifest = {
  project: string;
  phase: string;
  sourceCommit: string;
  models: ModelEntry[];
  donors: Donor[];
};
const root = document.getElementById('stage')!;
const status = document.getElementById('status')!;
const donorSelect = document.getElementById('donor') as HTMLSelectElement;
const clipSelect = document.getElementById('clips') as HTMLSelectElement;
const modelSelect = document.getElementById('model') as HTMLSelectElement;
const pauseButton = document.getElementById('pause') as HTMLButtonElement;
const speedInput = document.getElementById('speed') as HTMLInputElement;
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0x070d1d);
root.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#070d1d');
scene.fog = new THREE.Fog(0x070d1d, 9, 22);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
camera.position.set(2.9, 2.1, 4.1);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.target.set(0, 0.9, 0);
orbit.minDistance = 1.3;
orbit.maxDistance = 10;
orbit.update();
scene.add(new THREE.HemisphereLight(0xbcdcff, 0x384269, 2.3));
const keyLight = new THREE.DirectionalLight(0xf5f5ff, 3.2);
keyLight.position.set(-4, 6, 3);
scene.add(keyLight);
const rim = new THREE.DirectionalLight(0x6c80ff, 1.9);
rim.position.set(4, 4, -3);
scene.add(rim);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({
  color: 0x0d172b, roughness: 0.9,
}));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.025;
scene.add(floor);
const grid = new THREE.GridHelper(10, 20, 0x315b89, 0x152444);
grid.position.y = -0.012;
scene.add(grid);
const modelRoot = new THREE.Group();
scene.add(modelRoot);
const loader = new GLTFLoader();
const clock = new THREE.Clock();

let manifest: Manifest;
let actor: THREE.Object3D | null = null;
let visual: THREE.Group | null = null;
let mixer: THREE.AnimationMixer | null = null;
let activeAction: THREE.AnimationAction | null = null;
let availableClips: THREE.AnimationClip[] = [];
let serial = 0;
let requestSerial = 0;
let disposed = false;

function tell(message: string) { status.textContent = message; }
function resize() {
  const w = Math.max(root.clientWidth, 1), h = Math.max(root.clientHeight, 1);
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
resize();
function animate() {
  if (disposed) return;
  requestAnimationFrame(animate);
  mixer?.update(Math.min(clock.getDelta(), 0.05));
  orbit.update();
  renderer.render(scene, camera);
}
animate();
window.addEventListener('pagehide', () => {
  disposed = true;
  mixer?.stopAllAction();
  orbit.dispose();
  renderer.dispose();
});

function play(index: number) {
  if (!mixer) return;
  activeAction?.stop();
  activeAction = null;
  const clip = availableClips[index];
  if (!clip) {
    tell('Sin animación. El modelo permanece en su postura base.');
    pauseButton.disabled = true;
    return;
  }
  activeAction = mixer.clipAction(clip).reset();
  activeAction.timeScale = Number(speedInput.value);
  activeAction.play();
  pauseButton.disabled = false;
  pauseButton.textContent = 'Pausar';
  tell('Reproduciendo ' + clip.name + ' · comprobar postura, articulaciones y pies en el suelo.');
}
function clearActor() {
  activeAction?.stop();
  activeAction = null;
  mixer?.stopAllAction();
  mixer = null;
  actor = null;
  if (visual) modelRoot.remove(visual);
  visual = null;
  availableClips = [];
  clipSelect.replaceChildren(new Option('Sin animación', '-1'));
  pauseButton.disabled = true;
}
function suitableClips(donor: THREE.AnimationClip[], body: THREE.Object3D) {
  const objectNames = new Set<string>();
  body.traverse((obj) => { if (obj.name) objectNames.add(obj.name); });
  return donor.map((clip) => {
    // The P2 report compares GLB node names; here we discard clearly unbound
    // target tracks. This is still NOT a visual retarget/quality guarantee.
    const tracks = clip.tracks.filter((track) => {
      try {
        const target = THREE.PropertyBinding.parseTrackName(track.name).nodeName;
        return !target || objectNames.has(target);
      } catch {
        return false;
      }
    });
    if (!tracks.length) return null;
    return new THREE.AnimationClip(clip.name, clip.duration, tracks);
  }).filter((clip): clip is THREE.AnimationClip => Boolean(clip));
}
async function chooseDonor() {
  const ticket = ++requestSerial;
  const donor = manifest.donors[Number(donorSelect.value)];
  if (!donor || !actor) return;
  tell('Cargando animaciones ' + donor.title + '...');
  try {
    const data = await loader.loadAsync(donor.file);
    if (ticket !== requestSerial || !actor || !mixer) return;
    activeAction?.stop();
    activeAction = null;
    mixer.stopAllAction();
    availableClips = suitableClips(data.animations, actor);
    clipSelect.replaceChildren(new Option('Sin animación (pose base)', '-1'));
    for (let i = 0; i < availableClips.length; i++)
      clipSelect.add(new Option(availableClips[i].name, String(i)));
    const initial = availableClips.findIndex(c => /(^|_)idle/i.test(c.name) && !/fishing|bow|2h|t-pose/i.test(c.name));
    const move = availableClips.findIndex(c => /walk|run/i.test(c.name));
    const selected = initial >= 0 ? initial : (move >= 0 ? move : (availableClips.length ? 0 : -1));
    clipSelect.value = String(selected);
    if (selected >= 0) play(selected);
    else tell('No hay pistas enlazables en ' + donor.title + '. Probá otra biblioteca.');
  } catch (error) {
    if (ticket === requestSerial) tell('Error de animación: ' + String(error));
    console.error('[HIGHFLY P3] donor failed', error);
  }
}
async function chooseModel() {
  const ticket = ++serial;
  ++requestSerial;
  const entry = manifest.models.find(m => m.key === modelSelect.value);
  if (!entry) return;
  tell('Cargando ' + entry.title + '...');
  try {
    const gltf = await loader.loadAsync(entry.file);
    if (ticket !== serial) return;
    clearActor();
    const body = gltf.scene;
    const bounds = new THREE.Box3().setFromObject(body);
    const size = bounds.getSize(new THREE.Vector3());
    if (!Number.isFinite(size.y) || size.y < 0.001)
      throw Error('Modelo sin tamaño visible válido.');
    const center = bounds.getCenter(new THREE.Vector3());
    body.position.set(-center.x, -bounds.min.y, -center.z);
    const wrapper = new THREE.Group();
    wrapper.scale.setScalar(1.7 / size.y); // Viewer reference ONLY, not game scale.
    wrapper.add(body);
    modelRoot.add(wrapper);
    visual = wrapper;
    actor = body;
    mixer = new THREE.AnimationMixer(body);
    tell(entry.title + ' cargado. Buscando donantes de animación...');
    await chooseDonor();
  } catch (error) {
    if (ticket === serial) tell('Error de personaje: ' + String(error));
    console.error('[HIGHFLY P3] model failed', error);
  }
}
modelSelect.addEventListener('change', () => void chooseModel());
donorSelect.addEventListener('change', () => void chooseDonor());
clipSelect.addEventListener('change', () => {
  const index = Number(clipSelect.value);
  if (Number.isInteger(index)) play(index);
});
speedInput.addEventListener('input', () => {
  if (activeAction) activeAction.timeScale = Number(speedInput.value);
});
pauseButton.addEventListener('click', () => {
  if (!activeAction) return;
  activeAction.paused = !activeAction.paused;
  pauseButton.textContent = activeAction.paused ? 'Reanudar' : 'Pausar';
});
document.getElementById('reset')?.addEventListener('click', () => {
  camera.position.set(2.9, 2.1, 4.1);
  orbit.target.set(0, 0.9, 0);
  orbit.update();
});
try {
  const result = await fetch('/highfly-private-p3/manifest.json', { cache: 'no-store' });
  if (!result.ok) throw Error('Falta manifest P3: HTTP ' + result.status);
  manifest = await result.json() as Manifest;
  if (manifest.sourceCommit !== '493c35a108cef6c8aa290e8793107b1cd117886e')
    throw Error('Versión original distinta a v0.44.7.');
  modelSelect.replaceChildren();
  for (const model of manifest.models) modelSelect.add(new Option(model.title, model.key));
  donorSelect.replaceChildren();
  for (let i = 0; i < manifest.donors.length; i++) {
    const donor = manifest.donors[i];
    donorSelect.add(new Option(donor.title + ' (' + donor.clipCount + ' clips)', String(i)));
  }
  await chooseModel();
} catch (error) {
  console.error('[HIGHFLY P3] initialization failed', error);
  tell('P3 no preparado: ' + String(error));
}
