#!/usr/bin/env python3
"""HIGHFLY P22 procedural model generation + 266-path complete coverage tests."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import highfly_p22_owned_asset_rebuilder as p22


def read_glb(path: Path):
    data=path.read_bytes()
    magic,version,total=struct.unpack_from("<4sII",data,0)
    if magic != b"glTF" or version != 2 or total != len(data):
        raise AssertionError("Not a complete glTF 2.0 GLB")
    length,kind=struct.unpack_from("<I4s",data,12)
    if kind != b"JSON":raise AssertionError("Missing JSON chunk")
    root=json.loads(data[20:20+length])
    pos=20+length
    length2,kind2=struct.unpack_from("<I4s",data,pos)
    if kind2 != b"BIN\x00":raise AssertionError("Missing binary chunk")
    if pos+8+length2 != total:raise AssertionError("GLB incomplete or extra bytes")
    if root["buffers"][0]["byteLength"] != length2:
        raise AssertionError("Binary length mismatch")
    for view in root["bufferViews"]:
        if view["byteOffset"] + view["byteLength"] > length2:
            raise AssertionError("Accessor escapes binary chunk")
    return root


class P22OwnedRebuildTests(unittest.TestCase):
    def test_full_captured_inventory_is_266_unique_paths(self):
        paths=p22.capture_paths()
        self.assertEqual(len(paths),266)
        self.assertEqual(len(set(paths)),266)
        self.assertEqual(sum(s.endswith(".webp") for s in paths),2)
        self.assertEqual(sum(s.endswith(".glb") for s in paths),264)

    def test_procedural_glbs_have_real_geometry_and_valid_gltf2_buffers(self):
        paths=p22.capture_paths()
        with tempfile.TemporaryDirectory() as temp:
            for idx,url in enumerate(paths):
                if not url.endswith(".glb"):continue
                dst=Path(temp)/f"{idx}.glb"
                metadata=p22.build_model(url,dst)
                self.assertGreater(metadata["triangles"],15,url)
                self.assertGreater(metadata["bytes"],500,url)
                doc=read_glb(dst)
                self.assertEqual(doc["asset"]["version"],"2.0")
                self.assertEqual(doc["nodes"][0]["extras"]["highflyOrigin"],
                                 "original_procedural_p22")
                self.assertTrue(doc["meshes"][0]["primitives"],url)

    def test_reuse_does_not_allow_any_upstream_project_only_assets(self):
        self.assertEqual(len(p22.REUSE),15)
        for target,source in p22.REUSE.items():
            self.assertTrue(target.startswith("/models/"))
            self.assertTrue(source.startswith("/models/"))
            self.assertFalse(source.startswith("/models/drakelands_kit/"))
            self.assertFalse(source.startswith("/models/dungeon/ignivar"))
        self.assertTrue(all("with_project" not in s for s in p22.REUSE.values()))

    def test_semantic_assets_distinguish_gameplay_roles(self):
        pairs = {
            "/models/dungeon/ignivar_prop_reactor.glb":"ignivar_mechanical",
            "/models/biome/hex_castle.glb":"structure",
            "/models/props/wickharbor_wharf.glb":"harbor_or_dock",
            "/models/props/rift_portal.glb":"portal_or_gate",
            "/models/mounts/valorsteed.glb":"creature",
            "/models/props/streetlamp_wraithwood_ghost.glb":"lighting",
            "/models/world_quests/shipwreck/hull_fragment.glb":"shipwreck",
            "/models/props/dragon_eggs.glb":"custom_prop",
        }
        for url, expected in pairs.items():
            self.assertEqual(p22.role_for(url),expected,url)

    def test_loading_images_are_original_highfly_vectors(self):
        for path in ("/textures/loading/crystal-delve.webp",
                     "/textures/loading/eastbrook-mine-duel.webp"):
            image=p22.screen_svg(path)
            self.assertIn("<svg ",image)
            self.assertIn("HIGHFLY ORIGIN",image)
            self.assertNotIn("ClaudeCraft",image)
            self.assertIn("</svg>",image)


if __name__=="__main__":
    unittest.main()
