#!/usr/bin/env python3
"""HIGHFLY P43: read-only provenance and NPC preservation inventory.

Never declares the stage commercially clean. Inspects exactly what the
isolated P43 lab currently serves and its dependency on active P64 media.
No copies, deletion, changes to source, saves, node_modules or any assets.
Only writes a report beneath .workspace/reports/.
"""
from __future__ import annotations
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.workspace'
P43=WORK/'highfly-p43-restore-lab'
STAGE=WORK/'highfly-origin-stage-p0'
MASTER=WORK/'reports/highfly-p30-master'
OUT=WORK/'reports/highfly-world7/P43_REAL_MEDIA_NPC_PROVENANCE.json'
ROLES=('knight','mage','rogue','barbarian','paladin','druid')
GAME_FILES={
  'npc_manifests':'src/render/characters/manifest.ts',
  'npc_renderer':'src/render/characters/index.ts',
  'player_classes':'src/sim/content/classes.ts',
  'char_appearance':'src/sim/content/npc_looks.ts',
  'entry':'src/main.ts',
}
MEDIA={'.glb','.gltf','.obj','.fbx','.png','.jpg','.jpeg','.webp','.svg',
       '.ktx2','.hdr','.exr','.ogg','.mp3','.wav','.flac','.woff','.woff2','.ttf'}

def load_csv(name):
    p=MASTER/name
    if not p.is_file() or p.is_symlink():return []
    with p.open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))

def main():
    if P43.is_symlink() or not P43.is_dir() or not P43.resolve().is_relative_to(WORK.resolve()):
        raise RuntimeError('ISOLATED_P43_LAB_NOT_FOUND')
    if (P43/'public').is_symlink() or not (P43/'public').is_dir():
        raise RuntimeError('P43_PUBLIC_UNSAFE')
    if not (P43/'index.html').is_file():raise RuntimeError('P43_INDEX_MISSING')
    html=(P43/'index.html').read_text('utf8')
    result={
      'phase':'HIGHFLY_P43_REAL_MEDIA_NPC_PROVENANCE',
      'timestampUtc':datetime.now(timezone.utc).isoformat(),
      'mode':'READ_ONLY_AUDIT', 'activeP64Modified':False, 'P43Modified':False,
      'saveModified':False,'commercialReleaseApproved':False,
      'originalCheckpointIsFullLicensedStandaloneBuild':False,
      'gameCodeAndMediaAreSeparateLicenseDecisions':True,
      'p439ClassSelectMarkup':all('data-class="'+x+'"' in html for x in
          ('warrior','paladin','hunter','rogue','priest','shaman','mage','warlock','druid')),
      'offlineNativeSelectorInMarkup':'id="server-opt-offline"' in html,
      'diagnosticsPresent':'highfly_p43_android_diag.js' in html,
      'risk':'DO NOT PUBLISH as commercially clean until EVERY served file has individual provenance.',
    }
    stage_status=STAGE/'HIGHFLY_STAGE_STATUS.json'
    if stage_status.is_file() and not stage_status.is_symlink():
        try:
            data=json.loads(stage_status.read_text('utf8'))
            result['stageManifest']={k:data.get(k) for k in
              ('sourceCommit','originalPublicMediaCopied') if k in data}
        except (json.JSONDecodeError,UnicodeDecodeError):
            result['stageManifest']='INVALID_JSON'
    result['codeEvidence']={}
    for k,rel in GAME_FILES.items():
        f=P43/rel
        if f.is_file():
            src=f.read_text('utf8')
            result['codeEvidence'][k]={
              'present':True,'size':f.stat().st_size,
              'P35_NPC_UI_DEBUG':'HIGHFLY_P35_ACTOR_UI' in src,
              'P36_NPC_CC0_FALLBACK':'HIGHFLY_P36_NPC_FIXED_RIG_FALLBACK' in src,
              'P37_NPC_ROLE_CC0_MAPPING':'HIGHFLY_P37_NPC_CC0_ROLE_RIGS' in src,
              'P39_CC0_MOB_LAZY':'HIGHFLY_P39B_ALL_MOBS_CC0_LAZY_LOAD' in src}
        else:
            result['codeEvidence'][k]={'present':False}
    manifest=P43/'src/render/characters/manifest.ts'
    m=manifest.read_text('utf8') if manifest.is_file() else ''
    result['P37Cc0NpcRoleCandidates']=[
      {'role':n,'model':'models/chars/players/'+n+'.glb',
       'referencedByP43Manifest':('models/chars/players/'+n+'.glb') in m,
       'existsInP43Public':(P43/'public/models/chars/players'/(n+'.glb')).is_file()}
      for n in ROLES
    ]
    master_npc=load_csv('P30_EVERY_NPC_AND_VISUAL.csv')
    result['historicalP30NpcAudit']={
      'available':bool(master_npc),'rows':len(master_npc),
      'isRuntimeVisibilityProof':False,
      'notes':'Entity identity/quests are independent from mesh render; original NPC model may be non-redistributable.',
      'examples':[{k:x.get(k) for k in
        ('npcId','npcOriginalVisualKey','modelUrl')} for x in master_npc[:12]]}
    p30=load_csv('P30_ALL_MEDIA_AND_USAGE.csv')
    p30by={x.get('asset','').lstrip('/'):x for x in p30}
    assets=[]
    links=[]
    root=P43/'public'
    for top in sorted(root.iterdir()):
        links.append({
          'entry':top.name,'isSymlink':top.is_symlink(),
          'pointsIntoActiveStage':top.is_symlink() and
             top.resolve().is_relative_to((STAGE/'public').resolve())})
    for f in root.rglob('*'):
        if not f.is_file() or f.suffix.lower() not in MEDIA:continue
        rel=f.relative_to(root).as_posix()
        row=p30by.get(rel,{})
        assets.append({
          'path':rel,'bytes':f.stat().st_size,
          'kind':f.suffix.lower(),
          'p30ProviderFromSpec':row.get('providerFromSpec') or None,
          'p30LicenseEvidence':row.get('licenseEvidenceStatus') or 'NOT_IN_P30_OR_NO_EVIDENCE',
          'servedFromActiveP64Stage':f.resolve().is_relative_to((STAGE/'public').resolve()),
          'licensedForRedistribution':'NOT_VERIFIED_BY_THIS_AUDIT'
        })
    result['publicAssetInventory']={
      'assetCount':len(assets),'typeCounts':dict(Counter(x['kind'] for x in assets)),
      'topLevelSymlinksIntoP64':sum(x['pointsIntoActiveStage'] for x in links),
      'topLevelSymlinksTotal':sum(x['isSymlink'] for x in links),
      'rootEntries':len(links),'fromActiveP64':sum(x['servedFromActiveP64Stage'] for x in assets),
      'p30RowsAvailable':len(p30),
      'p30EvidenceStates':dict(Counter(x['p30LicenseEvidence'] for x in assets)),
      'unverifiedForRelease':len(assets),
      'notYetProvenExamples':[x for x in assets
        if x['p30LicenseEvidence']=='NOT_IN_P30_OR_NO_EVIDENCE'][:12],
      'candidateEvidenceExamples':[x for x in assets
        if x['p30LicenseEvidence']!='NOT_IN_P30_OR_NO_EVIDENCE'][:12]
    }
    result['priorAuditReportsFound']={name:(MASTER/name).is_file() for name in
      ('P30_ALL_MEDIA_AND_USAGE.csv','P30_EVERY_NPC_AND_VISUAL.csv')}
    result['limitations']=[
      'A 700-step loader is not a count of NPCs or permission checks.',
      'HTTP 200 and visually present models do not prove licenses.',
      'P37 role mappings do not guarantee every NPC was rendered, animated or distinct.',
      'Provenance candidates from P30 do not independently approve each current binary.',
      'Any public/code release must pass an explicit per-file license and dependency gate.',
      'Current lab uses symlinked media from active stage and should remain private.',
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print('[P43 PROVENANCE NPC AUDIT] '+json.dumps({
      'gameCodePreserved':True,
      'nineClassSelector':result['p439ClassSelectMarkup'] if 'p439ClassSelectMarkup' in result else result['p43'+ '9ClassSelectMarkup'],
      'npcSourceEvidence':result['codeEvidence'].get('npc_renderer'),
      'npcRoleCandidates':result['P37Cc0NpcRoleCandidates'],
      'assetCounts':{k:result['publicAssetInventory'][k] for k in
        ('assetCount','fromActiveP64','topLevelSymlinksIntoP64','p30RowsAvailable',
         'p30EvidenceStates','unverifiedForRelease')},
      'commercialReleaseApproved':False,'report':str(OUT)
      },indent=2,ensure_ascii=False))
if __name__=='__main__':main()
