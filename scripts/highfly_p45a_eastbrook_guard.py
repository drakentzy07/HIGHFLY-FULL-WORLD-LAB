#!/usr/bin/env python3
"""HIGHFLY P45A: live Eastbrook visual object audit + guarded oversized filtering.

Safe scope: private stage src/render/eastbrook_town.ts. No edits to sim,
collision layouts, quests, NPCs, player, persistence, models, or KayKit.
Overlarge individual building visuals are hidden only when empirically
measured >2x layout plus absolute giant threshold; the rest are unchanged.
Add ?hf_debug_eastbrook=1 for on-screen exact building IDs/sizes.
Add ?hf_hide_eastbrook=eastbrook_bank to temporarily hide one named building
for identification (only in that preview URL). No data deletion.
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
STAGE=p9.STAGE
OUT=ROOT/".workspace/reports/highfly-p45-eastbrook-diagnostics"
REL="src/render/eastbrook_town.ts"
MARK="HIGHFLY_P45_EASTBROOK_VISUAL_GUARD"

CODE="""
  // HIGHFLY_P45_EASTBROOK_VISUAL_GUARD — observe actual placed GLB bounding
  // boxes, not just raw mesh accessor dimensions. Never change simulation.
  const highflyP45Params = new URLSearchParams(window.location.search);
  const highflyP45Debug = highflyP45Params.get('hf_debug_eastbrook') === '1';
  const highflyP45Hide = new Set(
    (highflyP45Params.get('hf_hide_eastbrook') ?? '').split(',').filter(Boolean),
  );
  const highflyP45Rows: string[] = [];
  const highflyP45CheckBuilding = (
    building: (typeof EASTBROOK_LAYOUT.buildings)[number],
    visual: THREE.Group,
  ): void => {
    visual.updateWorldMatrix(true, true);
    const measured = new THREE.Box3().setFromObject(visual).getSize(new THREE.Vector3());
    const expected = building.nativeDimensions;
    const gigantic = (
      (measured.x > Math.max(30, expected.width * 2.2)) ||
      (measured.y > Math.max(27, expected.height * 2.2)) ||
      (measured.z > Math.max(30, expected.depth * 2.2))
    );
    const named = highflyP45Hide.has(building.id);
    if (gigantic || named) {
      // Hide the DRAWABLE ONLY. Collision remains unmodified; this is a
      // safety quarantine until the exact offending GLB is fixed.
      visual.visible = false;
      console.warn('[HIGHFLY P45] ocultando estructura visual', {
        id: building.id, model: building.assetId, expected,
        measured: measured.toArray(), gigantic, manual: named,
      });
    }
    const summary =
      building.id + ' | ' + building.assetId.split('/').pop() + ' | ' +
      measured.toArray().map((v) => v.toFixed(1)).join(' x ') +
      (gigantic ? ' [GIGANTE]' : named ? ' [OCULTADO MANUALMENTE]' : '');
    highflyP45Rows.push(summary);
  };
  if (highflyP45Debug && typeof document !== 'undefined') {
    window.setTimeout(() => {
      const id = 'highfly-p45-eastbrook-audit';
      if (document.getElementById(id)) return;
      const panel = document.createElement('details');
      panel.id = id;
      panel.open = true;
      panel.style.cssText =
        'position:fixed;top:110px;left:5px;max-height:35vh;overflow:auto;' +
        'max-width:min(510px,90vw);z-index:2147483500;background:#061523ed;' +
        'border:1px solid #4bc9ee;color:#def7ff;border-radius:8px;' +
        'padding:8px;font:12px monospace;white-space:pre-wrap;';
      const summary = document.createElement('summary');
      summary.textContent = 'HIGHFLY P45 — ESTRUCTURAS EASTBROOK';
      panel.append(summary);
      const content = document.createElement('div');
      content.textContent = highflyP45Rows.join('\\n') +
        '\\n\\nIdentificar: ?hf_hide_eastbrook=ID (preview) y recargar.';
      panel.append(content);
      document.body.append(panel);
    }, 0);
  }
"""
def one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError("P45_ANCHOR_DRIFT "+label+" count="+str(n))
 return s.replace(a,b,1)
def patch(s):
 if MARK in s:raise RuntimeError("P45_ALREADY_APPLIED")
 s=one(s,
  "  const buildingGroups: THREE.Object3D[] = [];\n  for (const building of EASTBROOK_LAYOUT.buildings) {",
  "  const buildingGroups: THREE.Object3D[] = [];\n"+CODE+"\n  for (const building of EASTBROOK_LAYOUT.buildings) {",
  "building loop")
 s=one(s,
  "      const built = buildKitBuilding(building, kitTemplate.raw, groundAt);\n      group.add(built.group);",
  "      const built = buildKitBuilding(building, kitTemplate.raw, groundAt);\n"
  "      highflyP45CheckBuilding(building, built.group);\n"
  "      group.add(built.group);",
  "kit branch")
 s=one(s,
  "    const built = buildBuilding(building, template, groundAt, atlas);\n    group.add(built.group);",
  "    const built = buildBuilding(building, template, groundAt, atlas);\n"
  "    highflyP45CheckBuilding(building, built.group);\n"
  "    group.add(built.group);",
  "normal branch")
 return s
def run(apply=False):
 p9.preflight(p9.ORIGINAL,STAGE,p9.REPORT)
 file=STAGE/REL
 if not file.is_file() or file.is_symlink():raise RuntimeError("P45_MISSING_STAGE_RENDERER")
 before=file.read_text(encoding="utf8")
 after=patch(before)
 if apply:
  backup=OUT/"backups"/REL
  if backup.exists() or backup.is_symlink():raise RuntimeError("P45_BACKUP_EXISTS")
  backup.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(file,backup)
  if hashlib.sha256(file.read_bytes()).digest()!=hashlib.sha256(backup.read_bytes()).digest():
   raise RuntimeError("P45_BACKUP_BAD")
  if file.read_text(encoding="utf8")!=before:raise RuntimeError("P45_CHANGED_DURING_APPLY")
  file.write_text(after,encoding="utf8")
 OUT.mkdir(parents=True,exist_ok=True)
 result={
  "phase":"P45A_EASTBROOK_RUNTIME_GEOMETRY_GUARD",
  "mode":"APPLY" if apply else "DRY_RUN",
  "giantOutlierFilter":"measured Three.js Box3 >2.2x expected and >27-30 world units",
  "browserDebug":"?hf_debug_eastbrook=1",
  "manualVisualHide":"?hf_hide_eastbrook=eastbrook_bank",
  "simulationCollisionChanged":False,
  "townModelsOrDimensionsChanged":False,
  "npcChanged":False,"saveChanged":False,
  "browserVerified":False
 }
 (OUT/"P45A_REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
 print("[HIGHFLY] P45A EASTBROOK: "+json.dumps(result))
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
 run(p.parse_args().apply)
