// HIGHFLY private offline lab: audit ORIGINAL v0.44.7 CREDITS per family.
// This is NOT a media allowlist: files are blocked pending separate provenance checks.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

export const PINNED_UPSTREAM_SHA='493c35a108cef6c8aa290e8793107b1cd117886e';

export function classifyMedia(license,redistribution){
  const l=license.replaceAll('**','').trim(),r=redistribution.replaceAll('**','').trim();
  if(l==='CC0 1.0'&&r==='Yes') return 'CANDIDATE_CC0_REQUIRES_FILE_CHECK';
  if(l==='MIT'&&r==='Yes, attribution required') return 'CANDIDATE_MIT_REQUIRES_NOTICE_AND_FILE_CHECK';
  if(r==='With the project only')return 'EXCLUDE_PROJECT_ONLY';
  if(r==='No, permission required')return 'EXCLUDE_RIGHTS_RESERVED';
  if(r==='Non-commercial only, with attribution')return 'EXCLUDE_NONCOMMERCIAL';
  return 'BLOCK_REVIEW_OTHER_LICENSE';
}

export function readCreditsFamilies(markdown){
  const rows=[];
  for(const [index,line] of markdown.split(/\r?\n/).entries()){
    const match=line.match(/^\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$/);
    if(!match)continue;
    const [assets,author,source,license,redistribution]=match.slice(1).map(x=>x.trim());
    if(assets==='Assets'||assets==='---')continue;
    rows.push({
      id:`V0447-MEDIA-${String(rows.length+1).padStart(3,'0')}`,
      line:index+1,assets,author,source,license,redistribution,
      decision:classifyMedia(license,redistribution),
      fileStatus:'UNVERIFIED',
      replacement:'UNASSIGNED'
    });
  }
  if(rows.length<100)throw new Error('INCOMPLETE_CREDITS_TABLE: counted '+rows.length+' rows');
  return rows;
}

export function summarize(rows){
  const counts={};
  for(const x of rows) counts[x.decision]=(counts[x.decision]??0)+1;
  return counts;
}

if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)){
  const original=path.resolve(process.argv[2]??'.workspace/claudecraft-v0.44.7/CREDITS.md');
  const target=path.resolve(process.argv[3]??'.workspace/reports/v0.44.7');
  const md=await readFile(original,'utf8');
  if(!md.includes('This file is the operative licence record'))
    throw new Error('NOT_UPSTREAM_CREDITS');
  const records=readCreditsFamilies(md);
  const report={
    schemaVersion:1,source:'levy-street/world-of-claudecraft',
    tag:'v0.44.7',commit:PINNED_UPSTREAM_SHA,
    note:'Per-family registry only. NO asset included or approved for HIGHFLY shipping.',
    reportStatus:'PER_FAMILY_ONLY_ALL_FILES_UNVERIFIED',
    totals:summarize(records),records
  };
  await mkdir(target,{recursive:true});
  await writeFile(path.join(target,'CREDITS_0447_AUDIT.json'),JSON.stringify(report,null,2)+'\n');
  const out=['# HIGHFLY — revisión inicial de medios ClaudeCraft 0.44.7',
   '', 'Referencia original: '+PINNED_UPSTREAM_SHA,
   '', 'Estado: NO APTO PARA DISTRIBUCIÓN / auditado por FAMILIAS, no por archivo',
   '',...Object.entries(report.totals).map(([k,v])=>'- '+k+': '+v),
   '', 'Archivo JSON: CREDITS_0447_AUDIT.json',
   '', 'No incluir medios project-only/rights-reserved/NC/unknown en una build HIGHFLY.'];
  await writeFile(path.join(target,'RESUMEN.md'),out.join('\n')+'\n');
  console.log('HIGHFLY 0.44.7 license report generated at '+target+'; '+records.length+' unverified families.');
  for(const [decision,num] of Object.entries(report.totals))console.log('  '+decision+': '+num);
}
