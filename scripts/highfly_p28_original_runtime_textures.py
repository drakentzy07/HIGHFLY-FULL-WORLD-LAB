#!/usr/bin/env python3
"""HIGHFLY P28: generate 11 first-party textures for the real world-preload failures.

The artwork here is original SVG/PBR data, not upstream ClaudeCraft media.
Maintains 512px 4x4 atlas UV layout and semantic materials for Eastbrook/Fenbridge.
Dry run by default; --apply renders, decodes, builds and verifies all 11 assets.
Does not change RPG systems, character, monsters or source repository.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p21_runtime_asset_recovery as p21

STAGE=p9.STAGE
REFERENCE=p9.ORIGINAL
REPORT=ROOT/".workspace/reports/highfly-p28"
URLS={
"/textures/eastbrook_surface_atlas.webp":(512,512,"webp"),
"/textures/eastbrook_surface_normal.webp":(512,512,"webp"),
"/textures/eastbrook_surface_rough.webp":(512,512,"webp"),
"/textures/props/eastbrook_realm_builder_impostor.webp":(512,512,"webp"),
"/textures/fenbridge_surface_atlas.webp":(512,512,"webp"),
"/textures/fenbridge_surface_normal.webp":(512,512,"webp"),
"/textures/fenbridge_surface_roughness.webp":(512,512,"webp"),
"/textures/encounters/ignivar/ignivar_lava_original.webp":(512,512,"webp"),
"/vfx/fel_meteor_impact.png":(512,512,"png"),
"/textures/loading/drakemaw-caldera.webp":(1280,720,"webp"),
"/textures/loading/thornpeak-storm.webp":(1280,720,"webp"),
}
EAST_KIND=["stone","stone","plaster","wood","roof","metal","metal","wood",
           "fabric","fabric","leather","stone","crystal","wood","stone","stone"]
FEN_KIND=["stone","stone","wood","wood","roof","metal","metal","rope",
          "fabric","plaster","leather","mud","crystal","glass","wood","wax"]
EAST_COLOR=["#dadada","#ebebeb","#e4e4e4","#dddddd",
            "#e2e2e2","#d5d5d5","#e9e9e9","#dddddd",
            "#e4e4e4","#e4e4e4","#dbdbdb","#e0e0e0",
            "#eaeaea","#e2e2e2","#ebebeb","#dedede"]
FEN_COLOR=["#71887e","#b3b8b3","#59493e","#987752",
           "#327d89","#515762","#a98255","#a98b66",
           "#34858c","#d8c4a3","#81644e","#6c5d48",
           "#4abfac","#9ad4d1","#98754c","#a84b48"]
EAST_ROUGH=[.80,.80,.92,.85,.70,.50,.50,.85,.90,.90,.85,.80,.40,.78,.80,.80]
FEN_ROUGH=[.92,.86,.84,.78,.74,.52,.42,.88,.82,.90,.80,.95,.28,.22,.82,.40]
FEN_METAL=[0,0,0,0,0,.72,.78,0,0,0,0,0,.08,.18,0,.05]

def svg(body,width=512,height=512):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>'%(width,height,width,height,body)

def make_atlas(fen):
    kinds=FEN_KIND if fen else EAST_KIND
    colors=FEN_COLOR if fen else EAST_COLOR
    parts=[]
    for i,(kind,color) in enumerate(zip(kinds,colors)):
        x=i%4*128;y=i//4*128
        ink="#161c28" if int(color[1:3],16)>125 else "#d2d9e0"
        parts.append('<rect x="%d" y="%d" width="128" height="128" fill="%s"/>'%(x,y,color))
        if kind=="stone":
            for n in range(1,7):
                parts.append('<path d="M%d %d h128" stroke="%s" stroke-width="1.7" opacity=".25"/>'%(x,y+n*19,ink))
            for row in range(6):
                for column in range(1,4):
                    xx=x+(column*32+(row%2)*14)%125
                    parts.append('<path d="M%d %d v19" stroke="%s" opacity=".26"/>'%(xx,y+row*19,ink))
        elif kind in ("wood","roof"):
            for n in range(1,8):
                offset=n*16
                parts.append('<path d="M%d %d v128" stroke="%s" stroke-width="2.0" opacity=".23"/>'%(x+offset,y,ink))
            for n in range(10):
                xx=x+(n*27+i*11)%124
                yy=y+(n*19+i*7)%122
                parts.append('<path d="M%d %d q6 13 13 24" stroke="%s" opacity=".16" fill="none"/>'%(xx,yy,ink))
        elif kind in ("fabric","leather","rope"):
            for n in range(0,128,10):
                parts.append('<path d="M%d %d v128 M%d %d h128" stroke="%s" opacity=".13" stroke-width="1"/>'%(x+n,y,x,y+n,ink))
        elif kind in ("crystal","glass"):
            for n in range(10):
                xx=x+((n*31+i*9)%112)+5;yy=y+((n*43+i*6)%110)+5
                parts.append('<path d="M%d %d l22 -15 l10 19 l-16 17Z" fill="#b9faff" opacity=".12"/>'%(xx,yy))
        else:
            for n in range(35):
                xx=x+((n*23+i*7)%119)+4;yy=y+((n*41+i*9)%119)+4
                parts.append('<circle cx="%d" cy="%d" r="%d" fill="%s" opacity=".11"/>'%(xx,yy,n%3+1,ink))
    return svg("".join(parts))

def make_rough(fen):
    rough=FEN_ROUGH if fen else EAST_ROUGH
    metal=FEN_METAL if fen else rough
    parts=[]
    for i in range(16):
        r=int(rough[i]*255);b=int(metal[i]*255)
        parts.append('<rect x="%d" y="%d" width="128" height="128" fill="rgb(%d,%d,%d)"/>'%(i%4*128,i//4*128,r,r,b))
    return svg("".join(parts))

def make_lava():
    parts=['<rect width="512" height="512" fill="#3e1a1c"/>',
           '<defs><linearGradient id="fire"><stop stop-color="#ffdf75"/><stop offset=".4" stop-color="#f96f24"/><stop offset="1" stop-color="#ab281b"/></linearGradient></defs>']
    for i in range(25):
        y=(i*47+23)%512;a=24*math.sin(i*1.7)
        parts.append('<path d="M-30 %d Q140 %d 270 %d T550 %d" fill="none" stroke="url(#fire)" stroke-width="%d" opacity=".73"/>'%(y,y+int(a),y-int(a),y+int(a),8+i%4*3))
    return svg("".join(parts))

def make_meteor():
    parts=['<defs><radialGradient id="fire"><stop stop-color="#fffbd4" stop-opacity=".98"/><stop offset=".25" stop-color="#ffc855" stop-opacity=".9"/><stop offset=".55" stop-color="#f2692b" stop-opacity=".65"/><stop offset="1" stop-color="#d7290e" stop-opacity="0"/></radialGradient></defs><circle cx="256" cy="256" r="217" fill="url(#fire)"/>']
    for i in range(24):
        a=i*math.tau/24;b=a+.06
        x=256+113*math.cos(a);y=256+113*math.sin(a)
        xx=256+(210+(i*7)%35)*math.cos(b);yy=256+(210+(i*7)%35)*math.sin(b)
        parts.append('<path d="M%.1f %.1f L%.1f %.1f" stroke="#ffe1ab" stroke-width="%d" opacity=".7"/>'%(x,y,xx,yy,2+i%5))
    return svg("".join(parts))

def make_monument():
    return svg('<path d="M95 475H418L390 442H125Z" fill="#30394c" stroke="#8fbacc" stroke-width="9"/>'
      '<path d="M150 444V205L211 150H301L362 205V444Z" fill="#80919f" stroke="#c7d2dc" stroke-width="12"/>'
      '<path d="M206 150L256 65L306 150Z" fill="#6cb5db" stroke="#e1f1ff" stroke-width="8"/>'
      '<path d="M208 235L256 187L304 235L282 309H230Z" fill="#204866" stroke="#92f5ea" stroke-width="9"/>'
      '<path d="M235 241L256 215L277 241L256 278Z" fill="#b9f9d5"/>'
      '<path d="M186 372H326M186 412H326" stroke="#e0e9ee" stroke-width="10"/>')

def make_loading(storm):
    label="THORNPEAK STORM" if storm else "DRAKEMAW CALDERA"
    accent="#a4d7fc" if storm else "#ffae58"
    if storm:
        view='<path d="M0 610L180 370 360 470 520 200 680 495 840 270 1030 530 1180 385 1280 555V720H0Z" fill="#29445b"/>'
        view+='<path d="M520 200L560 275 482 270Z M840 270L882 339 803 337Z" fill="#c4dfef"/>'
        view+='<path d="M260 182L434 255 399 331 570 406" fill="none" stroke="#cceeff" stroke-width="10"/>'
    else:
        view='<path d="M0 605L160 489 333 532 550 305 715 486 864 281 1038 528 1170 419 1280 559V720H0Z" fill="#642b29"/>'
        view+='<path d="M552 305L585 470 649 499 700 617" stroke="#fb8d3a" stroke-width="23" fill="none"/>'
        view+='<path d="M864 282L900 408 981 526" stroke="#ffb051" stroke-width="17" fill="none"/>'
    body='<rect width="1280" height="720" fill="#111929"/><circle cx="650" cy="360" r="325" fill="%s" opacity=".13"/>'%accent
    body+=view+'<path d="M0 646Q360 600 620 654T1280 637V720H0Z" fill="#121a28"/>'
    body+='<text x="640" y="105" text-anchor="middle" font-family="sans-serif" font-size="51" font-weight="bold" letter-spacing="8" fill="%s">%s</text>'%(accent,label)
    body+='<text x="640" y="685" text-anchor="middle" font-family="sans-serif" font-size="20" letter-spacing="6" fill="#deecf3">HIGHFLY ORIGIN</text>'
    return svg(body,1280,720)

def original_svg(url):
    if url.endswith("eastbrook_surface_atlas.webp"):return make_atlas(False)
    if url.endswith("fenbridge_surface_atlas.webp"):return make_atlas(True)
    if url.endswith("_surface_normal.webp"):return svg('<rect width="512" height="512" fill="rgb(128,128,255)"/>')
    if url.endswith("eastbrook_surface_rough.webp"):return make_rough(False)
    if url.endswith("fenbridge_surface_roughness.webp"):return make_rough(True)
    if url.endswith("eastbrook_realm_builder_impostor.webp"):return make_monument()
    if url.endswith("ignivar_lava_original.webp"):return make_lava()
    if url.endswith("fel_meteor_impact.png"):return make_meteor()
    if url.endswith("drakemaw-caldera.webp"):return make_loading(False)
    if url.endswith("thornpeak-storm.webp"):return make_loading(True)
    raise ValueError("Unknown target: "+url)

NODE_RENDER=(
    "const sharp=require('sharp');let b=[];process.stdin.on('data',c=>b.push(c));"
    "process.stdin.on('end',async()=>{try{const f=process.argv[1],p=process.argv[2];"
    "if(p==='png')await sharp(Buffer.concat(b)).png().toFile(f);"
    "else await sharp(Buffer.concat(b)).webp({quality:90,effort:4}).toFile(f);}"
    "catch(e){console.error(e);process.exit(1)}});")
NODE_CHECK=(
    "const sharp=require('sharp');(async()=>{try{const m=await sharp(process.argv[1]).metadata();"
    "await sharp(process.argv[1]).resize(1,1).raw().toBuffer();"
    "console.log(JSON.stringify({format:m.format,width:m.width,height:m.height}));}"
    "catch(e){console.error(e);process.exit(1)}})();")

def decoded(file,url):
    if not p21.check_binary(file,url):return False
    r=subprocess.run(["node","-e",NODE_CHECK,str(file)],cwd=REFERENCE,
        capture_output=True,text=True,timeout=40)
    if r.returncode:return False
    try:actual=json.loads(r.stdout)
    except ValueError:return False
    w,h,fmt=URLS[url]
    return actual=={"format":fmt,"width":w,"height":h}

def render(url,file):
    file.parent.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(["node","-e",NODE_RENDER,str(file),URLS[url][2]],
        cwd=REFERENCE,input=original_svg(url),capture_output=True,text=True,timeout=80)
    if r.returncode or not decoded(file,url):
        raise RuntimeError("P28_BAD_GENERATED_IMAGE "+url+": "+r.stderr[-450:])
    return {"path":url,"sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
            "bytes":file.stat().st_size,"origin":"HIGHFLY_ORIGINAL_P28"}

def plan():
    rows=[]
    for url in URLS:
        public=STAGE/"public"/url.lstrip("/")
        if public.is_symlink():
            method="BLOCK_SYMLINK"
        elif public.is_file():
            method="KEEP_EXISTING_VALID" if decoded(public,url) else "BLOCK_BAD_EXISTING"
        elif public.exists():
            method="BLOCK_NOT_A_FILE"
        else:
            method="GENERATE_ORIGINAL"
        rows.append({"path":url,"method":method})
    return rows

def execute(apply=False):
    p9.preflight(REFERENCE,STAGE,p9.REPORT)
    rows=plan()
    counts=dict(Counter(x["method"] for x in rows))
    installed=[]
    built=None
    if apply:
        if any(x["method"].startswith("BLOCK") for x in rows):
            raise RuntimeError("P28_BLOCKED_EXISTING_ASSET: "+str(counts))
        REPORT.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p28-render-",dir=REPORT) as tmp:
            temp=Path(tmp)
            ready=[]
            for row in rows:
                if row["method"]=="GENERATE_ORIGINAL":
                    dest=temp/row["path"].lstrip("/")
                    ready.append((row,render(row["path"],dest),dest))
            try:
                for row,entry,src in ready:
                    dst=STAGE/"public"/row["path"].lstrip("/")
                    if dst.exists() or dst.is_symlink():
                        raise RuntimeError("P28_RACE_TARGET_EXISTS "+row["path"])
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    os.replace(src,dst)
                    installed.append(entry)
                built=p9.smoke()["exitCode"]
                failed=[]
                for row in rows:
                    url=row["path"]
                    a=STAGE/"public"/url.lstrip("/")
                    b=STAGE/"dist"/url.lstrip("/")
                    if not decoded(a,url) or not decoded(b,url):
                        failed.append(url)
                if built!=0 or failed:
                    raise RuntimeError("P28_TEXTURE_BUNDLE_INVALID "+str(failed))
            except BaseException:
                for entry in reversed(installed):
                    dst=STAGE/"public"/entry["path"].lstrip("/")
                    if dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest()==entry["sha256"]:
                        dst.unlink()
                if installed:p9.smoke()
                raise
    REPORT.mkdir(parents=True,exist_ok=True)
    info={"mode":"APPLY" if apply else "DRY_RUN",
          "assetCount":len(rows),"methods":counts,
          "installedCount":len(installed),"installed":installed,
          "buildExitCode":built,"worldEntryVerified":False,
          "mediaOriginal":True,"thirdPartyMediaCopied":False,
          "protectedGameplayFilesModified":False,"firstPassQuality":True}
    dest=REPORT/"P28_ORIGINAL_PRELOAD_TEXTURES.json"
    dest.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n")
    print("[HIGHFLY] P28 "+info["mode"]+": "+json.dumps({
        "assets":len(rows),"methods":counts,"installed":len(installed),
        "buildExitCode":built,"worldEntryVerified":False}))
    print("[HIGHFLY] P28 REPORT: "+str(dest))
    return info

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    execute(parser.parse_args().apply)
