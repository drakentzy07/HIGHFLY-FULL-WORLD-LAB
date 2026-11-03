#!/usr/bin/env node
// HIGHFLY Original Skin Studio: browser wrapper around ClaudeCraft's MIT pipeline.
// Runs locally in a private Codespace. Never passes --apply or publishes assets.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {existsSync,readFileSync,readdirSync,statSync,createReadStream} from 'node:fs';
import {resolve,join,extname} from 'node:path';
import {fileURLToPath} from 'node:url';

const LAB=resolve(fileURLToPath(new URL('..',import.meta.url)));
const ORIGINAL=join(LAB,'.workspace/claudecraft-v0.45.4');
const PIPELINE=join(ORIGINAL,'scripts/asset_pipeline/pipeline.mjs');
const JOBS=join(ORIGINAL,'tmp/asset_pipeline');
const HTML=join(LAB,'scripts/highfly_skin_studio.html');
const PORT=Number(process.env.HIGHFLY_SKIN_PORT||5185);
const CLASSES=Object.freeze({warrior:'knight',paladin:'paladin',hunter:'ranger',rogue:'rogue',priest:'mage',shaman:'barbarian',mage:'mage',warlock:'mage',druid:'druid'});
const history=new Map();let active=null;
function send(res,code,body,type='application/json; charset=utf-8'){
  res.writeHead(code,{'Content-Type':type,'X-Content-Type-Options':'nosniff','Cache-Control':'private,no-store','X-Frame-Options':'DENY'});
  res.end(type.startsWith('application/json')?JSON.stringify(body):body);
}
function err(res,code,message){send(res,code,{error:message});}
function serveFile(res,path,type,downloadName){
  if(!path||!existsSync(path))return err(res,404,'Archivo no disponible');
  const head={'Content-Type':type,'Content-Length':statSync(path).size,'Cache-Control':'private,no-store','X-Content-Type-Options':'nosniff'};
  if(downloadName)head['Content-Disposition']='attachment; filename="'+downloadName+'"';
  res.writeHead(200,head);createReadStream(path).pipe(res);
}
function payload(req){return new Promise((ok,no)=>{
  let s='';req.on('data',c=>{s+=c;if(s.length>12000){no(Error('Petición demasiado grande'));req.destroy();}});
  req.on('end',()=>{try{ok(JSON.parse(s));}catch{no(Error('JSON inválido'));}});
  req.on('error',no);
});}
function matchingDir(t){
  if(!existsSync(JOBS))return null;
  const prefix=t.mode==='skinmodel'?'skinmodel_'+t.name+'_':'skin_'+t.cls+'_'+t.suffix+'_';
  const found=readdirSync(JOBS,{withFileTypes:true}).filter(e=>e.isDirectory()&&e.name.startsWith(prefix)).map(e=>join(JOBS,e.name));
  found.sort((a,b)=>statSync(b).mtimeMs-statSync(a).mtimeMs);
  return found[0]||null;
}
function result(t){
  const dir=matchingDir(t);
  if(!dir)return {};
  if(t.mode==='skinmodel'){const output=join(dir,t.name+'.glb');return {output:existsSync(output)?output:null};}
  const output=join(dir,'alt_'+t.suffix+'.png');
  const preview=join(dir,'alt_'+t.suffix+'.render.png');
  return {output:existsSync(output)?output:null,preview:existsSync(preview)?preview:null};
}
function status(t){
  const f=result(t);
  return {id:t.id,mode:t.mode,cls:t.cls,status:t.state,logs:t.logs.slice(-95),error:t.error,hasOutput:!!f.output,hasPreview:!!f.preview,format:t.mode==='skinmodel'?'glb':'png'};
}
async function start(req,res){
  if(active)return err(res,409,'Ya existe una generación en curso');
  if(!existsSync(PIPELINE))return err(res,409,'Falta ClaudeCraft original; corré bash scripts/bootstrap_original.sh');
  const data=await payload(req);
  const cls=String(data.cls||''),mode=String(data.mode||'');
  if(!CLASSES[cls]||!['recolor','tripo','openai','skinmodel'].includes(mode))return err(res,400,'Clase o motor no válido');
  const label=String(data.label||'').trim().toLowerCase();
  if(!/^[a-z][a-z0-9_]{2,20}$/.test(label))return err(res,400,'El nombre debe comenzar con letra y usar 3-21 caracteres [a-z0-9_]');
  const prompt=String(data.prompt||'').trim();
  if(mode!=='recolor'&&(prompt.length<8||prompt.length>480))return err(res,400,'Ingresá una descripción de entre 8 y 480 caracteres');
  const stamp=Date.now().toString(36),suffix=(label+'_'+stamp).slice(0,34),name='hf_'+label+'_'+stamp;
  let args=['scripts/asset_pipeline/pipeline.mjs'];
  if(mode==='skinmodel')args.push('skinmodel','--class',cls,'--name',name,'--theme',prompt);
  else {
    args.push('skin','--class',cls,'--suffix',suffix);
    if(mode==='recolor'){
      const h=Number(data.hue),s=Number(data.saturation),l=Number(data.brightness);
      if(![h,s,l].every(Number.isFinite)||h< -180||h>180||s<.2||s>3||l<.2||l>3)return err(res,400,'Valores de recolorización inválidos');
      args.push('--recolor','hue='+h+',sat='+s+',light='+l);
    }else{
      if(mode==='tripo')args.push('--tripo');
      args.push('--prompt',prompt);
    }
  }
  const id='job_'+stamp;
  const t={id,mode,cls,suffix,name,state:'running',error:null,logs:['Iniciando ClaudeCraft original (pipeline.mjs)…']};
  history.set(id,t);while(history.size>20)history.delete(history.keys().next().value);
  active=id;
  const child=spawn(process.execPath,args,{cwd:ORIGINAL,shell:false,env:{...process.env},stdio:['ignore','pipe','pipe']});
  const append=chunk=>{for(const row of String(chunk).split(/\r?\n/))if(row.trim())t.logs.push(row.slice(0,550));if(t.logs.length>400)t.logs.splice(0,t.logs.length-400);};
  child.stdout.on('data',append);child.stderr.on('data',append);
  child.on('error',e=>{t.state='error';t.error=e.message;if(active===id)active=null;});
  child.on('close',code=>{
    if(t.state==='running'){
      t.state=code===0&&result(t).output?'ready':'error';
      if(t.state==='error')t.error='El motor terminó con código '+code+'. Revisá los logs.';
    }
    if(active===id)active=null;
  });
  send(res,200,{id,engine:'ClaudeCraft original',note:'No se ejecuta --apply'});
}
function request(req,res){
  let u;try{u=new URL(req.url,'http://local');}catch{return err(res,400,'URL inválida');}
  const p=u.pathname,cls=u.searchParams.get('class');
  if(p==='/'&&req.method==='GET')return serveFile(res,HTML,'text/html; charset=utf-8');
  if(p==='/api/base-model'&&req.method==='GET'){
    if(!CLASSES[cls])return err(res,400,'Clase no válida');
    return serveFile(res,join(ORIGINAL,'public/models/chars/players',CLASSES[cls]+'.glb'),'model/gltf-binary');
  }
  if(p==='/api/base-atlas'&&req.method==='GET'){
    if(!CLASSES[cls])return err(res,400,'Clase no válida');
    return serveFile(res,join(ORIGINAL,'public/textures/skins',CLASSES[cls],'base.png'),'image/png');
  }
  if(p==='/api/status'&&req.method==='GET'){
    const t=history.get(u.searchParams.get('id'));
    return t?send(res,200,status(t)):err(res,404,'No existe este trabajo');
  }
  if((p==='/api/output'||p==='/api/preview')&&req.method==='GET'){
    const t=history.get(u.searchParams.get('id'));
    if(!t)return err(res,404,'Trabajo no encontrado');
    const path=result(t)[p==='/api/output'?'output':'preview'];
    const ext=extname(path||'');
    return serveFile(res,path,ext==='.glb'?'model/gltf-binary':'image/png',u.searchParams.has('download')?'HIGHFLY_'+t.cls+'_'+t.suffix+ext:null);
  }
  if(p==='/api/generate'&&req.method==='POST'){
    try{if(req.headers.origin&&new URL(req.headers.origin).host!==req.headers.host)return err(res,403,'Origen no permitido');}catch{return err(res,403,'Origen no permitido');}
    start(req,res).catch(e=>err(res,500,e.message));return;
  }
  err(res,404,'Ruta inexistente');
}
if(!existsSync(PIPELINE)||!existsSync(HTML)){
  console.error('No está preparado el origen o el archivo HTML. Ejecutá bootstrap_original.sh y verificá los archivos del laboratorio.');
  process.exitCode=2;
}else createServer(request).listen(PORT,'0.0.0.0',()=>{
  console.log('HIGHFLY ORIGINAL SKIN STUDIO - ClaudeCraft v0.45.4');
  console.log('Abrí Ports > '+PORT+' > Open in Browser y mantené el puerto PRIVATE.');
  console.log('El código original de generación se ejecuta sin --apply.');
});
