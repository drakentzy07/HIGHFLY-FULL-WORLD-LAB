#!/usr/bin/env python3
"""HIGHFLY P22 — 266-path PRIVATE visual asset recovery.

Restores stage asset URLs reported by the post-P21 browser probe. For exact
compatible sources, reuses CC0 KayKit (P8) or Quaternius (P19) stage models.
For everything else creates ORIGINAL, deterministic, procedural low-poly GLBs
with semantic object families (not project-only ClaudeCraft art). Two original
loading-screen WebPs are rendered with installed sharp.

Important: This is a FIRST-PASS functional visual restoration; not a claim of
production art quality, rig/animation equivalence, collision correctness, or
playable gameplay. It never imports or copies ClaudeCraft project-only media.
It doesn't rewrite game logic, world placements, quests, mobs, or animation code.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import highfly_p9_private_build_smoke as p9
import highfly_p12_world_kaykit_batch as p12
import highfly_p21_runtime_asset_recovery as p21

REFERENCE = ROOT / ".workspace/claudecraft-v0.44.7"
STAGE = ROOT / ".workspace/highfly-origin-stage-p0"
OUTPUT = ROOT / ".workspace/reports/highfly-p22"
CAPTURE = ROOT / "reports/highfly_p21_fresh_missing_266.json"
EXPECTED_COUNT = 266
# Exact, known sources already present in private stage, never the original game's assets.
# _field names are field-quality variants of the same Quaternius CC0 tree mesh.
REUSE = {
    **{f"/models/foliage/{tree}_field.glb": f"/models/foliage/{tree}.glb"
       for tree in ("pine_1", "pine_2", "pine_4", "oak_1", "oak_2",
                    "oak_4", "oak_5", "twisted_1", "twisted_2", "twisted_3")},
    "/models/biome/hex_tavern.glb": "/models/biome/hexb_tavern.glb",
    "/models/biome/hex_blacksmith.glb": "/models/biome/hexb_workshop.glb",
    "/models/biome/hex_home_a.glb": "/models/biome/hexb_home_a.glb",
    "/models/biome/hex_home_b.glb": "/models/biome/hexb_home_b.glb",
    "/models/biome/hex_market.glb": "/models/biome/hexb_market.glb",
}
PALETTE = {
    "stone": (0.42, 0.45, 0.48), "stone_light": (0.64, 0.67, 0.69),
    "stone_dark": (0.27, 0.30, 0.34), "plaster": (0.80, 0.74, 0.63),
    "wood": (0.39, 0.24, 0.13), "wood_light": (0.64, 0.42, 0.23),
    "roof": (0.44, 0.18, 0.16), "roof_blue": (0.14, 0.29, 0.53),
    "roof_dark": (0.17, 0.19, 0.25), "iron": (0.25, 0.30, 0.34),
    "steel": (0.51, 0.55, 0.58), "bronze": (0.62, 0.39, 0.13),
    "gold": (0.90, 0.68, 0.25), "green": (0.19, 0.47, 0.24),
    "green_light": (0.29, 0.64, 0.31), "green_dark": (0.10, 0.28, 0.17),
    "leaf_yellow": (0.52, 0.55, 0.20), "reed": (0.55, 0.52, 0.29),
    "orange": (0.92, 0.35, 0.09), "ember": (0.98, 0.54, 0.07),
    "lava": (0.94, 0.18, 0.04), "ice": (0.46, 0.78, 0.93),
    "crystal": (0.42, 0.32, 0.84), "purple": (0.47, 0.17, 0.61),
    "white": (0.91, 0.88, 0.78), "cloth": (0.70, 0.66, 0.56),
    "sand": (0.72, 0.62, 0.40), "dark": (0.15, 0.16, 0.18),
    "water": (0.15, 0.48, 0.66), "flower": (0.87, 0.29, 0.56),
}


def vsub(a, b): return tuple(a[i] - b[i] for i in range(3))
def vadd(a, b): return tuple(a[i] + b[i] for i in range(3))
def vmul(a, t): return tuple(a[i] * t for i in range(3))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1],
                         a[2] * b[0] - a[0] * b[2],
                         a[0] * b[1] - a[1] * b[0])
def unit(a):
    d = math.sqrt(sum(x*x for x in a))
    return tuple(x/d for x in a) if d > 1e-8 else (0., 1., 0.)


class Geo:
    """Very small self-contained glTF 2.0 authoring library: no Blender needed."""
    def __init__(self):
        self.positions = {name: [] for name in PALETTE}
        self.normals = {name: [] for name in PALETTE}

    def tri(self, a, b, c, mat):
        n = unit(cross(vsub(b, a), vsub(c, a)))
        self.positions[mat].extend((*a, *b, *c))
        self.normals[mat].extend((*n, *n, *n))

    def quad(self, a, b, c, d, mat):
        self.tri(a, b, c, mat); self.tri(a, c, d, mat)

    def box(self, x, y, z, w, h, d, mat):
        x0, x1 = x - w/2, x + w/2
        y0, y1 = y - h/2, y + h/2
        z0, z1 = z - d/2, z + d/2
        p = ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
             (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))
        for a,b,c,d in ((0,3,2,1),(4,5,6,7),(0,4,7,3),
                        (1,2,6,5),(3,7,6,2),(0,1,5,4)):
            self.quad(p[a],p[b],p[c],p[d],mat)

    def beam(self, a, b, radius, mat, sides=6):
        v = unit(vsub(b, a))
        other = (0,0,1) if abs(v[2]) < .85 else (1,0,0)
        u = unit(cross(v, other))
        w = unit(cross(v, u))
        p0=[];p1=[]
        for i in range(sides):
            theta=i*math.tau/sides
            off=vadd(vmul(u, math.cos(theta)*radius),vmul(w, math.sin(theta)*radius))
            p0.append(vadd(a,off));p1.append(vadd(b,off))
        for i in range(sides):
            j=(i+1)%sides
            self.quad(p0[i],p0[j],p1[j],p1[i],mat)
            self.tri(a,p0[j],p0[i],mat)
            self.tri(b,p1[i],p1[j],mat)

    def cylinder(self, x, base, z, r, h, mat, sides=10, top_r=None):
        t=r if top_r is None else top_r
        if h <= 0: return
        a=(x,base,z);b=(x,base+h,z)
        for i in range(sides):
            t0=i*math.tau/sides;t1=(i+1)*math.tau/sides
            p0=(x+r*math.cos(t0),base,z+r*math.sin(t0))
            p1=(x+r*math.cos(t1),base,z+r*math.sin(t1))
            p2=(x+t*math.cos(t1),base+h,z+t*math.sin(t1))
            p3=(x+t*math.cos(t0),base+h,z+t*math.sin(t0))
            self.quad(p0,p1,p2,p3,mat)
            self.tri(a,p1,p0,mat)
            if t: self.tri(b,p3,p2,mat)

    def sphere(self,x,y,z,r,mat,rings=5,sides=9):
        for i in range(rings):
            a0=i*math.pi/rings;a1=(i+1)*math.pi/rings
            for j in range(sides):
                b0=j*math.tau/sides;b1=(j+1)*math.tau/sides
                def pt(a,b):
                    return (x+r*math.sin(a)*math.cos(b), y+r*math.cos(a),
                            z+r*math.sin(a)*math.sin(b))
                self.quad(pt(a0,b0),pt(a1,b0),pt(a1,b1),pt(a0,b1),mat)

    def gable(self,x,base,z,w,length,height,mat):
        # Two thick sloping roofs and gable ends, unlike a blocky flat top.
        a=(x-w*.55,base,z-length*.52);b=(x,base+height,z-length*.52)
        c=(x+w*.55,base,z-length*.52)
        d=(x-w*.55,base,z+length*.52);e=(x,base+height,z+length*.52)
        f=(x+w*.55,base,z+length*.52)
        self.quad(a,d,e,b,mat);self.quad(b,e,f,c,mat)
        self.tri(a,b,c,mat);self.tri(f,e,d,mat)

    def arch(self,x,z,width,height,depth,mat):
        for dx in (-width/2,width/2):
            self.box(x+dx,height*.5,z,.45,height,depth,mat)
        self.box(x,height+.15,z,width+.8,.5,depth,mat)
        self.box(x,height+.55,z,width+.2,.3,depth,"stone_light")

    def torus(self,x,y,z,r,tube,mat,segments=14):
        for i in range(segments):
            a=i*math.tau/segments;b=(i+1)*math.tau/segments
            p=(x+r*math.cos(a),y+r*math.sin(a),z)
            q=(x+r*math.cos(b),y+r*math.sin(b),z)
            self.beam(p,q,tube,mat,4)

    def gear(self,x,y,z,r):
        self.torus(x,y,z,r,.17,"iron",12)
        for i in range(8):
            a=i*math.tau/8
            self.beam((x,y,z),(x+math.cos(a)*r,y+math.sin(a)*r,z),.13,"steel",4)
            self.box(x+math.cos(a)*r*1.08,y+math.sin(a)*r*1.08,z,.23,.23,.38,"iron")
        self.cylinder(x,y-.1,z,.24,.25,"bronze",9)

    def to_glb(self, target: Path, name: str, role: str, review: bool) -> dict:
        raw=bytearray()
        views=[];accessors=[];primitives=[]
        matnames=list(PALETTE)
        for key in matnames:
            points=self.positions[key]
            if not points:continue
            n=self.normals[key]
            for coords,kind in ((points,"POSITION"),(n,"NORMAL")):
                while len(raw)%4:raw.append(0)
                offset=len(raw)
                raw.extend(struct.pack("<"+str(len(coords))+"f",*coords))
                views.append({"buffer":0,"byteOffset":offset,"byteLength":len(raw)-offset,"target":34962})
                accessor={"bufferView":len(views)-1,"componentType":5126,
                          "count":len(coords)//3,"type":"VEC3"}
                if kind=="POSITION":
                    accessor["min"]=[min(coords[i::3]) for i in range(3)]
                    accessor["max"]=[max(coords[i::3]) for i in range(3)]
                accessors.append(accessor)
            primitives.append({"attributes":{"POSITION":len(accessors)-2,"NORMAL":len(accessors)-1},
                               "material":matnames.index(key),"mode":4})
        if not primitives:raise RuntimeError("EMPTY_PROCEDURAL_MESH: "+name)
        mats=[{"name":k,"pbrMetallicRoughness":{
                    "baseColorFactor":[*v,1.0],"metallicFactor":.08,"roughnessFactor":.84},
               "doubleSided":True} for k,v in PALETTE.items()]
        obj={"asset":{"version":"2.0","generator":"HIGHFLY P22 original procedural geometry"},
             "scene":0,"scenes":[{"nodes":[0]}],
             "nodes":[{"name":name,"mesh":0,"extras":{
                 "highflyOrigin":"original_procedural_p22","role":role,
                 "qualityReviewRequired":review}}],
             "meshes":[{"primitives":primitives}],"materials":mats,
             "bufferViews":views,"accessors":accessors,"buffers":[{"byteLength":len(raw)}]}
        js=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        while len(js)%4:js+=b" "
        while len(raw)%4:raw.append(0)
        total=12+8+len(js)+8+len(raw)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("wb") as f:
            f.write(struct.pack("<4sII",b"glTF",2,total))
            f.write(struct.pack("<I4s",len(js),b"JSON"));f.write(js)
            f.write(struct.pack("<I4s",len(raw),b"BIN\x00"));f.write(raw)
        return {"triangles":sum(len(x)//9 for x in self.positions.values()),
                "bytes":target.stat().st_size}


def house(g,variant=0,drake=False,hollow=False):
    w=5.8+(variant%3)*1.2; d=5.5+(variant%2)*1.5; h=3.8+(variant%3)*.4
    roof="roof" if drake else "roof_blue" if variant%3==0 else "roof_dark"
    g.box(0,.20,0,w+.5,.4,d+.5,"stone")
    # Hollow shells have a genuine passage opening: a ~2.2m door.
    wall=".ignore"
    g.box(-w/2,h/2,0,.35,h,d,"plaster")
    g.box(w/2,h/2,0,.35,h,d,"plaster")
    g.box(0,h/2,-d/2,w,h,.33,"plaster")
    door=2.2
    g.box(-w/2+1, h/2,d/2,.33,h,.32,"wood")
    g.box((w+door)/4,h/2,d/2,(w-door)/2,h,.33,"plaster")
    g.box(-(w+door)/4,h/2,d/2,(w-door)/2,h,.33,"plaster")
    g.box(0,(h+door)/2,d/2,door,h-door,.33,"plaster")
    for x in (-w/2,w/2):
        for z in (-d/2+.18,d/2-.18):
            g.beam((x,.25,z),(x,h+.35,z),.16,"wood")
    for x in (-w/4,w/4):
        g.box(x,2.0,-d/2-.2,.83,1.05,.13,"roof_blue")
        g.box(x,2.0,-d/2-.28,.15,1.05,.12,"wood")
    g.gable(0,h+.25,0,w,d,1.9,roof)
    # roof tiles and ridge trim
    g.beam((0,h+2.13,-d*.53),(0,h+2.13,d*.53),.12,"wood_light")
    g.box(0,.14,-d*.70,1.8,.22,1.9,"stone_light")
    if hollow:
        for z in (-d/4,d/4):
            g.box(0,.50,z,1.6,.8,1.0,"wood")
    if "blacksmith" in ():
        pass


def tower(g,castle=False):
    radius=2.6 if castle else 1.8
    height=9 if castle else 7
    g.cylinder(0,0,0,radius,height,"stone",12)
    g.cylinder(0,height-.5,0,radius+.32,.6,"stone_light",12)
    for i in range(12):
        a=i*math.tau/12
        g.box(math.cos(a)*radius,height+.18,math.sin(a)*radius,.75,.75,.75,"stone")
    g.arch(0,radius+.12,1.5,2.2,.5,"wood")
    g.cylinder(0,height+.15,0,radius+.40,1.8,"roof",12,0)


def boat(g,large=False,broken=False):
    length=12 if large else 6
    w=3.4 if large else 2.1
    g.box(0,.35,0,w,1.2,length,"wood")
    for side in (-1,1):
        g.beam((side*w*.46,.8,-length*.55),(side*w*.5,.7,length*.55),.14,"wood_light")
    for i in range(4):
        z=-length*.42+i*length*.28
        g.box(0,1.0,z,w*.83,.12,.18,"wood_light")
    if not broken:
        g.beam((0,1,0),(0,7 if large else 4,0),.17,"wood")
        g.quad((0,2,-.1),(0,6 if large else 3.8,-.1),
               (2.1 if large else 1.4,5.2 if large else 3.1,-.1),
               (2.1 if large else 1.4,2,-.1),"cloth")
        g.box(0,1.2,-length*.6,w*.7,.2,.6,"bronze")
    else:
        for i in range(5):
            z=-length*.33+i*length*.18
            g.beam((-.7,.9,z),(.8,1.0,z+.4),.09,"wood_light")


def dock(g,long=False):
    width=5.5;length=21 if long else 10
    g.box(0,.8,0,width,.35,length,"wood")
    for x in (-width*.43,width*.43):
        for i in range(6 if long else 4):
            z=-length*.45+i*length/(5 if long else 3)
            g.cylinder(x,-2,z,.21,3.8,"wood",8)
            if i%2==0:
                g.beam((x,1,z),(x,2,z),.13,"wood_light")
    for i in range(12 if long else 6):
        z=-length*.46+i*length/(11 if long else 5)
        g.box(0,1.04,z,width,.09,.15,"wood_light")


def tree(g,seed,palm=False,dead=False,twisted=False):
    h=6.5+(seed%4)*.85
    tilt=1.4 if palm else .3 if twisted else 0
    g.beam((0,0,0),(tilt,h,0),.24 if palm else .40,"wood",8)
    if dead:
        for dx,dz in ((2,0),(-2,1),(1,-1)):
            g.beam((tilt*.7,h*.65,0),(tilt+dx,h*.86,dz),.12,"wood")
    elif palm:
        for i in range(8):
            a=i*math.tau/8
            end=(tilt+math.cos(a)*3.7,h-.8,math.sin(a)*3.7)
            g.beam((tilt,h,0),end,.15,"green_dark")
            for v in (0.52,0.8):
                x=tilt+math.cos(a)*3.7*v;z=math.sin(a)*3.7*v
                g.sphere(x,h-.5*v,z,.55,"green",3,6)
    else:
        for i in range(4):
            y=h*.52+i*h*.12
            g.sphere(tilt*.7+(i%2-.5)*.4,y,0,2.15-(i*.23),
                     "green" if seed%4 else "green_dark",4,9)


def crystal(g,seed,ice=False):
    color="ice" if ice else "crystal"
    for i in range(5):
        a=(i+.23*seed)*math.tau/5
        x=math.cos(a)*(.55+.1*i);z=math.sin(a)*(.55+.1*i)
        h=1.6+(i%3)*.65
        g.cylinder(x,0,z,.40,h,color,6,0)
        g.cylinder(x,0,z,.4,.27,"stone",6)


def lamp(g,name):
    g.cylinder(0,0,0,.24,3.15,"iron",8)
    g.box(0,3.30,0,.65,.7,.65,"bronze")
    color="ice" if any(s in name for s in ("frost","icicle")) else (
        "purple" if any(s in name for s in ("witch","wraith","ghost","night")) else
        "crystal" if "crystal" in name else
        "green_light" if any(s in name for s in ("ever","willow","reed","flower")) else "ember")
    g.sphere(0,3.40,0,.32,color,4,8)
    g.cylinder(0,3.7,0,.5,.3,"roof_dark",8,0)


def ring_portal(g):
    for i in range(18):
        a=i*math.tau/18;b=(i+1)*math.tau/18
        g.beam((2.7*math.cos(a),2.9+3.0*math.sin(a),0),
               (2.7*math.cos(b),2.9+3.0*math.sin(b),0),.25,"stone_dark")
    for i in range(7):
        a=i*math.tau/7
        g.sphere(2.7*math.cos(a),2.9+3*math.sin(a),0,.24,"crystal",3,6)
    g.box(0,.21,0,5.9,.4,2.2,"stone")


def role_for(path):
    name=PurePosixPath(path).stem.lower()
    if name.startswith("ignivar_"):return "ignivar_mechanical"
    if path.startswith("/models/world_quests/shipwreck/"):return "shipwreck"
    if "harbor" in name or "wharf" in name or "dock" in name or "boardwalk" in name:return "harbor_or_dock"
    if "ferry" in name or "boat" in name or "ship" in name or "glider" in name:return "watercraft"
    if "house" in name or "home" in name or any(w in name for w in (
        "inn","tavern","chapel","church","armoury","blacksmith","tannery",
        "apothecary","lodge","gatehouse","barracks","stables","building_","market",
        "castle","windmill","workbench","tower")):return "structure"
    if "portal" in name or "gate" in name or "arch" in name:return "portal_or_gate"
    if "valorsteed" in name or "fish" in name:return "creature"
    if "streetlamp" in name or "brazier" in name or "torch" in name:return "lighting"
    if "tree" in name or "palm" in name or "willow" in name:return "tree"
    if "rune" in name or "sigil" in name or "ritual" in name:return "rune"
    if "flower" in name or "lily" in name or "mushroom" in name or "reed" in name or "grass" in name:return "flora"
    if "crystal" in name or "ice" in name or "spire" in name:return "crystal"
    if "wall" in name or "palisade" in name or "hedge" in name:return "wall"
    if "wood" in name or "log" in name or "beam" in name:return "woodwork"
    if "chest" in name or "crate" in name or "goods" in name:return "container"
    if "scroll" in name or "ledger" in name or "order" in name or "grimoire" in name:return "book_or_scroll"
    if "farm" in name or "grain" in name or "gourd" in name or "sprout" in name:return "farm"
    return "custom_prop"


def build_model(path,target):
    name=PurePosixPath(path).stem.lower()
    category=role_for(path)
    seed=int(hashlib.sha256(path.encode()).hexdigest()[:8],16)
    g=Geo()
    if category=="ignivar_mechanical":
        if "beam" in name or "pillar" in name or "wall" in name:
            g.box(0,2,0,1.4,4,1.4,"stone_dark")
            for y in (.4,2,3.6):g.box(0,y,0,1.7,.22,1.7,"bronze")
            if "wall" in name:g.gear(0,2.5,.85,1)
        elif "chain" in name or "hook" in name:
            for i in range(8):
                y=5-i*.55
                g.torus(0,y,0,.30,.10,"iron",8)
            if "hook" in name:g.beam((0,.6,0),(.6,.25,0),.14,"steel")
        elif "gear" in name:
            g.gear(0,2.3,0,1.25);g.gear(-1.8,1.3,.5,.55)
            g.box(0,.45,0,3.5,.9,1.9,"stone_dark")
        elif "bridge" in name:
            dock(g,long=True)
            for z in (-7,7):
                for x in (-2.5,2.5):g.cylinder(x,-2,z,.45,5,"stone",8)
        elif "lava" in name or "forge" in name or "reactor" in name or "furnace" in name:
            g.cylinder(0,0,0,1.6,2.5,"stone_dark",10)
            g.cylinder(0,2.5,0,1.4,.4,"bronze",10)
            g.cylinder(0,2.95,0,1.0,.65,"lava",9,0.25)
            for i in range(6):
                a=i*math.tau/6
                g.beam((2*math.cos(a),0,2*math.sin(a)),(1.2*math.cos(a),3.0,1.2*math.sin(a)),.18,"iron")
        elif "anvil" in name:
            g.box(0,.65,0,1.8,1.3,.95,"steel")
            g.box(0,1.45,0,2.6,.38,1.35,"iron")
        elif "steam" in name or "pipe" in name or "pump" in name:
            g.cylinder(0,0,0,1.4,2.5,"iron",10)
            for i in range(4):
                a=i*math.tau/4
                g.beam((.5*math.cos(a),1.8,.5*math.sin(a)),
                       (2.1*math.cos(a),3,2.1*math.sin(a)),.2,"bronze")
            g.gear(0,1.5,1.2,.7)
        elif "lift" in name:
            for x in (-1.5,1.5):g.beam((x,0,0),(x,7.0,0),.22,"iron")
            for y in (0,3,6.5):g.box(0,y,0,3.6,.35,2.3,"wood")
            g.gear(0,6.5,1.25,.9)
        elif "gate" in name or "vault" in name:
            g.arch(0,0,4.0,5.3,1.2,"stone_dark")
            g.box(0,2.5,.0,3.7,4.5,.35,"iron")
            g.gear(0,2.4,.45,.85)
        elif "stair" in name:
            for i in range(8):g.box(0,.3+i*.48,-2.8+i*.8,3,.6,1,"stone")
        elif "cannon" in name:
            g.box(0,.45,0,2.3,.9,2.6,"wood")
            g.beam((0,1.35,-.9),(0,1.9,3.5),.5,"iron",12)
        else:
            g.cylinder(0,0,0,1.4,3.8,"stone_dark",10)
            g.torus(0,2.9,0,.9,.18,"bronze")
            crystal(g,seed)
    elif category=="structure":
        if any(w in name for w in ("castle","tower","watch","fortress")):
            if "castle" in name:
                g.box(0,2.4,0,10,4.8,10,"stone")
                for x in (-5.3,5.3):
                    for z in (-5.3,5.3):
                        g.cylinder(x,0,z,1.6,7,"stone",9)
                        g.cylinder(x,7,z,1.9,1.7,"roof",9,0)
                g.arch(0,5,2.5,4.1,1,"iron")
            else:tower(g)
        elif "windmill" in name:
            house(g,seed%3)
            g.beam((0,4.3,3.65),(0,10,3.65),.2,"wood")
            for i in range(4):
                a=i*math.tau/4
                end=(math.cos(a)*3.1,7+math.sin(a)*3.1,3.7)
                g.beam((0,7,3.7),end,.18,"wood")
                g.box(end[0],end[1],3.7,.55,.9,.13,"cloth")
        else:
            house(g,seed%5,"drakelands" in path or "barracks" in name,
                  "hollow" in name)
            if "blacksmith" in name or "forge" in name:
                g.cylinder(3.4,0,0,.8,2.4,"stone",10)
                g.cylinder(3.4,2.4,0,.7,.4,"ember",10,0)
    elif category=="harbor_or_dock":
        dock(g,long=True)
        if "harbor" in name:
            for i in (-1,1):
                g.box(i*4,2,-5,3.5,4,3.4,"plaster")
                g.gable(i*4,4,-5,3.5,3.4,1.25,"roof_dark")
            g.beam((-1,1,7),(-1,7,7),.2,"wood")
            g.beam((-1,7,7),(3,7,7),.15,"wood")
    elif category=="watercraft":
        boat(g,large="ferry" in name or "ship" in name,broken="broken" in name)
    elif category=="shipwreck":
        if "shipwreck"==name or "rowboat" in name:boat(g,large=True,broken=True)
        elif "anchor" in name:
            g.beam((0,0,0),(0,3,0),.16,"iron");g.torus(0,3,0,.43,.1,"iron")
            g.beam((-1,0,0),(1,0,0),.2,"iron")
        else:
            for i in range(5):
                z=i*.65-1.3
                g.beam((-1.7, .2+(i%3)*.1,z),(1.5,.4,z+.3),.11,"wood")
            g.box(0,.5,0,1.1,1,.9,"wood")
    elif category=="portal_or_gate":
        ring_portal(g)
    elif category=="creature":
        # Visual first-pass only. Static models cannot replace skeletal animation.
        if "horse" in name or "steed" in name:
            g.box(0,1.85,0,1.2,1.25,2.4,"wood")
            for x in (-.38,.38):
                for z in (-.85,.85):
                    g.beam((x,1.55,z),(x,0,z+.15),.16,"wood")
            g.beam((0,2.2,.75),(0,3.15,1.3),.36,"wood")
            g.sphere(0,3.1,1.5,.43,"wood_light")
            for x in (-.2,.2):g.sphere(x,3.3,1.7,.1,"dark")
        else:
            g.sphere(0,.6,0,.8,"water")
            g.beam((0,.7,-.4),(0,1.2,-1.5),.28,"water")
            g.box(0,.7,-1.45,1,.1,.8,"ice")
    elif category=="lighting":
        lamp(g,name)
    elif category=="tree":
        tree(g,seed,palm="palm" in name,dead="dead" in name,twisted="ghost" in name)
    elif category=="rune":
        g.cylinder(0,0,0,1.7,.2,"stone_dark",12)
        g.torus(0,.8,0,.8,.13,"crystal",16)
        for i in range(8):
            a=i*math.tau/8
            g.cylinder(math.cos(a)*1.2,.2,math.sin(a)*1.2,.12,.32,"gold",6)
    elif category=="flora":
        if "mushroom" in name:
            for i in range(5):
                x=math.cos(i*2)*.8;z=math.sin(i*2)*.8
                g.cylinder(x,0,z,.16,1+(i%3)*.24,"cloth",8)
                g.cylinder(x,1+(i%3)*.24,z,.58,.45,"purple" if "glow" in name else "roof",9,0)
        else:
            for i in range(8):
                a=i*math.tau/8
                x=math.cos(a)*.8;z=math.sin(a)*.8
                g.beam((x,0,z),(x*.9,1.5+(i%3)*.18,z*.9),.06,"green")
                g.sphere(x*.9,1.45+(i%3)*.18,z*.9,.26,"flower" if "flower" in name else "reed",3,6)
    elif category=="crystal":
        crystal(g,seed,"ice" in name or "frost" in name)
    elif category=="wall":
        g.box(0,2.0,0,6.0,4.0,.75,"stone" if "hedge" not in name else "green")
        for x in (-2.8,0,2.8):
            g.box(x,4.2,0,.8,.8,1.0,"stone_light" if "hedge" not in name else "green_dark")
    elif category=="woodwork":
        for x in (-.65,0,.65):
            g.beam((x,0,0),(x,3,0),.24,"wood")
        g.beam((-.9,2.6,0),(.9,2.6,0),.15,"wood_light")
    elif category=="container":
        g.box(0,.58,0,1.5,1.15,1.2,"wood")
        for x in (-.64,.64):g.box(x,.62,0,.12,1.3,1.25,"iron")
        g.box(0,1.20,0,1.65,.18,1.35,"wood_light")
        if "chest" in name:g.box(0,.8,.68,.2,.38,.1,"gold")
    elif category=="book_or_scroll":
        g.box(0,.10,0,.85,.16,1.3,"wood")
        g.box(0,.2,0,.72,.07,1.15,"cloth")
        g.box(0,.28,.05,.1,.06,.95,"bronze")
    elif category=="farm":
        g.box(0,.25,0,2.7,.5,3.3,"wood")
        g.box(0,.56,0,2.25,.19,2.9,"sand")
        for i in range(7):
            x=(i%3-1)*.63;z=(i//3-1)*.75
            g.beam((x,.6,z),(x,.9+(seed%4)*.16,z),.07,"green")
            if "stage4" in name or "feast" in name:
                g.sphere(x,1.05,z,.26,"leaf_yellow",3,6)
    else:
        # Distinct, categorized silhouettes: not an invisible/error-suppression dummy.
        if any(w in name for w in ("cannon","pump","engineering","gear","machine")):
            g.box(0,.6,0,2.2,1.2,1.8,"iron")
            g.gear(0,1.7,1,1)
        elif "totem" in name or "statue" in name or "shrine" in name:
            g.cylinder(0,0,0,1.1,1,"stone",8)
            g.cylinder(0,1,0,.65,3.4,"stone_light",8)
            g.sphere(0,4.3,0,.9,"gold" if "gold" in name else "crystal")
        elif "bridge" in name:
            dock(g)
        elif "bell" in name:
            g.arch(0,0,2.6,3.6,1.1,"wood")
            g.cylinder(0,2.3,0,.7,.65,"bronze",10,.3)
        elif "crate" in name or "barrel" in name:
            g.cylinder(0,0,0,.63,1.5,"wood",10)
            for y in (.2,1.3):g.cylinder(0,y,0,.7,.12,"iron",10)
        else:
            g.cylinder(0,0,0,.95,.6,"stone_dark",10)
            g.cylinder(0,.6,0,.55,1.7,"bronze",8,.2)
            g.sphere(0,2.6,0,.53,"crystal")
    statistics=g.to_glb(target,name,category,True)
    return {"generation":"ORIGINAL_PROCEDURAL_FIRST_PASS","role":category,
            "qualityReviewRequired":True,
            "animationReviewRequired":category=="creature" or "glider" in name,
            "collisionScaleReviewRequired":category in (
                "harbor_or_dock","structure","portal_or_gate","ignivar_mechanical"),
            **statistics}


def screen_svg(path: str) -> str:
    is_crystal="crystal" in path
    name="CRYSTAL DELVE" if is_crystal else "EASTBROOK MINES"
    accent="#6ee7fd" if is_crystal else "#f8ac54"
    # Entirely first-party vector artwork, no borrowed game characters or images.
    seed=int(hashlib.sha256(path.encode()).hexdigest()[:8],16)
    stones=[]
    for i in range(22):
        x=(i*139+seed%211)%1280
        y=360+(i*91)%420
        w=30+(i*17)%125
        stones.append(f'<path d="M{x} {y} l{-w//2} {w//2} l{w} 6 z" fill="#1a2437" opacity=".8"/>')
    towers='<path d="M180 530 L180 280 250 280 250 530 M1000 530 L1000 215 1080 215 1080 530" fill="#1a293d" stroke="#49779a" stroke-width="12"/>'
    crystal='<path d="M640 210 L735 390 650 650 545 450 Z" fill="#285673" stroke="#83e5fd" stroke-width="9" opacity=".9"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">'
      f'<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#091024"/><stop offset="1" stop-color="#24435c"/></linearGradient>'
      f'<radialGradient id="glow"><stop stop-color="{accent}" stop-opacity=".53"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>'
      '<rect width="1280" height="720" fill="url(#sky)"/>'
      '<circle cx="650" cy="355" r="340" fill="url(#glow)"/>'
      '<path d="M0 590 L160 330 330 540 490 310 750 535 950 240 1280 570 1280 720 0 720 Z" fill="#152638"/>'
      +(crystal if is_crystal else towers)+''.join(stones)
      +'<path d="M0 620 Q400 580 650 680 T1280 610 L1280 720 L0 720 Z" fill="#0a1426"/>'
      f'<text x="640" y="104" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="51" letter-spacing="9" fill="{accent}">{name}</text>'
      '<text x="640" y="670" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#becfdf" letter-spacing="5">HIGHFLY ORIGIN</text>'
      '</svg>')


def make_webp(path: str, destination: Path):
    svg=screen_svg(path)
    destination.parent.mkdir(parents=True,exist_ok=True)
    script=("const sharp=require('sharp');"
            "let b=[];process.stdin.on('data',c=>b.push(c));"
            "process.stdin.on('end',async()=>{try{await sharp(Buffer.concat(b)).webp({quality:86,effort:4}).toFile(process.argv[1]);}"
            "catch(e){console.error(e);process.exit(1)}});")
    process=subprocess.run(["node","-e",script,str(destination)],
                           cwd=REFERENCE,input=svg,encoding="utf8",
                           text=True,capture_output=True,timeout=70)
    if process.returncode or not destination.is_file():
        raise RuntimeError("P22_WEBP_SHARP_NOT_READY: "+process.stderr[-500:])
    return {"generation":"ORIGINAL_HIGHFLY_VECTOR_TO_WEBP",
            "role":"original_loading_art","qualityReviewRequired":True,
            "bytes":destination.stat().st_size}


def capture_paths():
    obj=json.loads(CAPTURE.read_text(encoding="utf8"))
    items=obj.get("paths")
    if obj.get("pathCount")!=EXPECTED_COUNT or not isinstance(items,list) or len(items)!=EXPECTED_COUNT or len(set(items))!=EXPECTED_COUNT:
        raise RuntimeError("P22_EXPECTED_POST_P21_CAPTURE_266_REQUIRED")
    if not all(p21.safe_asset_path(path) for path in items):
        raise RuntimeError("P22_UNSAFE_CAPTURE_PATH")
    return items


def plan():
    paths=capture_paths()
    result=[]
    for url in paths:
        p=STAGE/"public"/url.lstrip("/")
        d=STAGE/"dist"/url.lstrip("/")
        src=REUSE.get(url)
        entry={"path":url,"category":"/".join(PurePosixPath(url).parts[1:3])}
        if p.is_symlink() or d.is_symlink():
            entry["method"]="REVIEW_SYMLINK"
        elif p.is_file():
            entry["method"]="STAGE_ALREADY_PRESENT"
            entry["stageValid"]=p21.check_binary(p,url)
        elif src and (STAGE/"public"/src.lstrip("/")).is_file() and p21.check_binary(STAGE/"public"/src.lstrip("/"),src):
            entry["method"]="COPY_KNOWN_CC0_STAGE"
            entry["source"]=src
        elif url.endswith(".webp"):
            entry["method"]="GENERATE_OWN_LOADING_ART"
        elif url.endswith(".glb"):
            entry["method"]="GENERATE_OWN_GEOMETRY"
            entry["role"]=role_for(url)
        else:entry["method"]="BLOCK_UNEXPECTED_FORMAT"
        result.append(entry)
    return result


def apply(plan_items):
    blocked=[x for x in plan_items if x["method"] in (
        "REVIEW_SYMLINK","BLOCK_UNEXPECTED_FORMAT") or
        x["method"]=="STAGE_ALREADY_PRESENT" and not x.get("stageValid",False)]
    if blocked:
        raise RuntimeError("P22_UNSAFE_STAGE_STATE: "+str(blocked[:8]))
    output=[]
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p22-staging-",dir=str(OUTPUT)) as tmp:
        temp=Path(tmp)
        produced=[]
        for row in plan_items:
            url=row["path"]
            method=row["method"]
            if method=="STAGE_ALREADY_PRESENT":continue
            dest=temp/url.lstrip("/")
            dest.parent.mkdir(parents=True,exist_ok=True)
            if method=="COPY_KNOWN_CC0_STAGE":
                src=STAGE/"public"/row["source"].lstrip("/")
                if not p21.check_binary(src,row["source"]):
                    raise RuntimeError("P22_CC0_SOURCE_BAD: "+row["source"])
                shutil.copyfile(src,dest)
                metadata={"generation":"REUSED_VERIFIED_STAGE_CC0",
                          "provenance":"P8 owned KayKit or P19 Quaternius CC0",
                          "source":row["source"],
                          "qualityReviewRequired":row["path"].startswith("/models/biome/")}
            elif method=="GENERATE_OWN_LOADING_ART":
                metadata=make_webp(url,dest)
            else:metadata=build_model(url,dest)
            if not p21.check_binary(dest,url):
                raise RuntimeError("P22_GENERATED_MEDIA_INVALID: "+url)
            produced.append((dest,STAGE/"public"/url.lstrip("/"),metadata,url))
        # Only publish after ALL candidates generated and verified.
        for src,dst,metadata,url in produced:
            if dst.exists() or dst.is_symlink():
                raise RuntimeError("P22_DESTINATION_RACE: "+url)
            dst.parent.mkdir(parents=True,exist_ok=True)
            os.replace(src,dst)
            output.append({"path":url,"sha256":p12.digest(dst),**metadata})
    return output


def status_after(paths):
    result=[]
    for url in paths:
        rel=url.lstrip("/")
        pub=STAGE/"public"/rel;dist=STAGE/"dist"/rel
        status=("OK" if p21.check_binary(pub,url) and p21.check_binary(dist,url) and
                p12.digest(pub)==p12.digest(dist) else
                "PUBLIC_ABSENT" if not pub.is_file() else
                "DIST_ABSENT" if not dist.is_file() else "BAD_BINARY_OR_MISMATCH")
        result.append({"path":url,"status":status})
    return result


def run(should_apply: bool, rebuild: bool=True):
    p9.preflight(REFERENCE,STAGE,p9.REPORT)
    paths=capture_paths()
    before=plan()
    counts=dict(Counter(x["method"] for x in before))
    installed=[]
    build_code=None
    if should_apply:
        installed=apply(before)
        if rebuild:
            build_code=p9.smoke()["exitCode"]
    checked=status_after(paths) if should_apply and rebuild else []
    results=dict(Counter(x["status"] for x in checked))
    item_map={x["path"]:x for x in installed}
    report={"phase":"HIGHFLY_P22_266_FIRST_PASS_OWNED_ASSET_RECOVERY",
            "mode":"APPLY" if should_apply else "DRY_RUN",
            "dateUtc":datetime.now(timezone.utc).isoformat(),
            "originalReferenceModified":False,"gameSimulationModified":False,
            "projectOnlyClaudeArtCopied":False,"publicDeployment":False,
            "all266AvailableInBuiltBundle":should_apply and rebuild and results=={"OK":266},
            "gameplayVerified":False,"productionQualityVerified":False,
            "captured":len(paths),"methodCounts":counts,
            "installedCount":len(installed),"installed":installed,
            "items":[{**x,**({"result":item_map[x["path"]]} if x["path"] in item_map else {})} for x in before],
            "buildExitCode":build_code,"postBuildCounts":results,"postBuild":checked,
            "notes":["Technical first-pass art intentionally requires scene-by-scene visual review.",
                     "Static procedural horse/fish is not an animated rig. Mount animation and clip contracts still need QA.",
                     "No original ClaudeCraft project-only, restricted, or unrecorded media is copied.",
                     "Only 266 paths from fresh browser capture evaluated; other lazy-loaded assets may still be absent.",
                     "This is NOT a confirmation of playable world or commercial readiness."]}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    out=OUTPUT/"P22_RECOVERY_266.json"
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("[HIGHFLY] P22 "+report["mode"]+": "+json.dumps({
        "paths":len(paths),"methods":counts,"installed":len(installed),
        "buildExitCode":build_code,"postBuild":results,
        "gameplayVerified":False},ensure_ascii=False))
    print("[HIGHFLY] P22 REPORT: "+str(out))
    if should_apply and build_code != 0:raise SystemExit("P22_BUILD_FAILED_CHECK_P9")
    if should_apply and rebuild and results!={"OK":266}:
        raise SystemExit("P22_RUNTIME_ASSETS_NOT_ALL_BUNDLED")
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--no-build",action="store_true")
    args=parser.parse_args()
    run(args.apply,not args.no_build)


if __name__=="__main__":main()
