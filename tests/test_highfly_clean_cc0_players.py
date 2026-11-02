"""Guard native CC0 player restore: GLB structure, exact source destinations, no fake assets."""
from __future__ import annotations
import importlib.util
import json
import struct
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hfnativecc0",ROOT/"scripts/highfly_clean_restore_pinned_cc0_players.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NativePlayerTest(unittest.TestCase):
 def test_minimal_valid_glb_metadata(self):
  obj={'asset':{'version':'2.0'},'nodes':[{'mesh':0,'skin':0}],
       'meshes':[{'primitives':[]}],'skins':[{'joints':[]}],
       'animations':[{'name':'Idle'}]*9}
  data=json.dumps(obj).encode()
  data+=b' ' *((4-len(data)%4)%4)
  buf=b'glTF'+struct.pack('<II',2,12+8+len(data))
  buf+=struct.pack('<I',len(data))+b'JSON'+data
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'knight.glb';path.write_bytes(buf)
   info=m.glb(path)
   self.assertEqual(info['skins'],1)
   self.assertEqual(info['animations'],9)
   self.assertEqual(info['skinnedNodes'],1)

 def test_rejects_non_glb_and_avoids_placeholder(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'knight.glb';path.write_bytes(b'<!DOCTYPE html>')
   self.assertIsNone(m.glb(path))
  self.assertEqual(len(m.ALLOWED),8)
  source=(ROOT/'scripts/highfly_clean_restore_pinned_cc0_players.py').read_text()
  self.assertIn("if dst.exists() or dst.is_symlink():",source)
  self.assertIn("CREDITS.md",source)
  self.assertIn("characters_v2.json",source)
  self.assertNotIn("make_box_geometry",source)

if __name__=="__main__":unittest.main()
