import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/highfly_probe_rig_compatibility_p2.py"
SPEC=importlib.util.spec_from_file_location("highfly_probe_rig_compatibility_p2", SCRIPT)
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

def make_glb(where,payload):
    where.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(payload).encode("utf-8")
    raw+=b" " * ((4-len(raw)%4)%4)
    size=12+8+len(raw)
    where.write_bytes(struct.pack("<4sII",b"glTF",2,size)+struct.pack("<I4s",len(raw),b"JSON")+raw)

def rig_payload(animations=False, names=None):
    names=names or ["Root","Hips","LeftArm","RightArm"]
    payload={"asset":{"version":"2.0"},"nodes":[{"name":n} for n in names],
             "skins":[{"joints":list(range(1,len(names)))}]}
    if animations:
        payload["animations"]=[
            {"name":"Walk","channels":[{"sampler":0,"target":{"node":1,"path":"rotation"}},
                                        {"sampler":0,"target":{"node":2,"path":"rotation"}}],
             "samplers":[{"input":0,"output":1}]},
            {"name":"Attack","channels":[{"sampler":0,"target":{"node":1,"path":"rotation"}}],
             "samplers":[{"input":0,"output":1}]}]
    return payload

class RigCompatibilityTests(unittest.TestCase):
    def test_json_reads_valid_glb_and_rejects_corrupt_header(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"model.glb"
            make_glb(file,rig_payload())
            info=module.read_glb_json(file)
            self.assertEqual(len(info["nodes"]),4)
            bad=file.read_bytes()[:8]+(1).to_bytes(4,"little")+file.read_bytes()[12:]
            file.write_bytes(bad)
            with self.assertRaises(ValueError):
                module.read_glb_json(file)

    def test_reports_potential_skeleton_animation_donor_without_modifying_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/".workspace/private-imports/kaykit-v7-selected/The Complete KayKit Collection v7"
            knight=root/module.HERO
            skeleton=root/module.SKELETON
            anim=root/"KayKit Skeletons 1.1/Animations/gltf/Rig_Medium/Skeletons_Movement.glb"
            make_glb(knight,rig_payload(animations=True))
            make_glb(skeleton,rig_payload())
            make_glb(anim,rig_payload(animations=True))
            (root/"KayKit Character Animations 1.1").mkdir(exist_ok=True)
            before={p:p.read_bytes() for p in (knight,skeleton,anim)}
            report=Path(d)/"reports/rig.json"
            result=module.scan(root,report)
            self.assertEqual(result["validGlb"],3)
            self.assertEqual(result["heroAndSkeleton"]["skeleton"]["embeddedClips"],0)
            donors=result["heroAndSkeleton"]["skeleton"]["topPotentialAnimationDonors"]
            self.assertTrue(donors)
            self.assertEqual(donors[0]["coveragePercent"],100)
            self.assertTrue(report.exists())
            self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_channel_compatibility_detects_missing_bones(self):
        donor={"path":"rig.glb","animationTargetNames":["Hips","LeftArm","Unknown"],
               "animations":[{"name":"Run"}],"animationCount":1,"jointNames":["Hips","LeftArm"]}
        target={"nodeNames":["Root","Hips","LeftArm"],"jointNames":["Hips","LeftArm"]}
        result=module.coverage(donor,target)
        self.assertEqual(result["matchingTargetNodes"],2)
        self.assertEqual(result["coveragePercent"],66.7)
        self.assertEqual(result["missingTargets"],["Unknown"])

if __name__=="__main__":unittest.main()
