import importlib.util
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/highfly_install_animation_lab_p3_0447.py"
SPEC = importlib.util.spec_from_file_location("p3_installer", SCRIPT)
# The source script imports the sibling P2 GLB inspector.
import sys
sys.path.insert(0, str(SCRIPT.parent))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def report(path, root, animations, target_names=None):
    return {
        "path": str(path.relative_to(root)),
        "nodeNames": target_names or ["a", "b", "c"],
        "jointCount": 23,
        "animationCount": animations,
        "animations": [{"name": "Idle"}, {"name": "Walk"}][:animations],
        "animationTargetNames": ["a", "b", "c"] if animations else [],
    }


class P3Tests(unittest.TestCase):
    def test_plan_is_readonly_and_uses_medium_donors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lib = root / "lib"
            upstream = root / "original"
            ca = lib / "KayKit Character Animations 1.1/Animations/gltf/Rig_Medium"
            ad = lib / "KayKit Adventurers 2.0/Animations/gltf/Rig_Medium"
            ca.mkdir(parents=True)
            ad.mkdir(parents=True)
            first = ca / "Rig_Medium_MovementBasic.glb"
            second = ca / "Rig_Medium_CombatMelee.glb"
            duplicate = ad / "Rig_Medium_CombatMelee.glb"
            incompatible = ca / "Rig_Medium_Extra.glb"
            for file in (first, second, duplicate, incompatible):
                file.write_bytes(b"fixture-data")
            def fake_info(file, original):
                d = report(file, original, 1)
                if file == incompatible:
                    d["animationTargetNames"] = ["unmatched"]
                return d
            fake_targets = {
                "hero": {"nodeNames": ["a", "b", "c"], "jointCount": 23},
                "skeleton": {"nodeNames": ["a", "b", "c"], "jointCount": 23},
            }
            with patch.object(module, "verify_sources"), patch.object(module, "model_nodes", return_value=fake_targets), patch.object(module, "model_info", side_effect=fake_info):
                plan, copies = module.plan(upstream, lib)
            self.assertEqual(len(plan["donors"]), 2)
            self.assertEqual(plan["donors"][0]["title"], "Rig_Medium_MovementBasic")
            self.assertEqual(len(copies), 2)
            self.assertEqual(len(list(root.rglob("manifest.json"))), 0)

    def test_install_preserves_preexisting_p1_assets_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            upstream = root / ".workspace/claudecraft-v0.44.7"
            (upstream / "public/highfly-private-pilot").mkdir(parents=True)
            p1 = upstream / "public/highfly-private-pilot/manifest.json"
            p1.write_text("original p1 unchanged", encoding="utf-8")
            (upstream / "src").mkdir()
            (upstream / "vite.config.ts").write_text(
                "        editor: fileURLToPath(new URL('editor.html', import.meta.url)),\n",
                encoding="utf-8",
            )
            pilot = root / "pilot"
            pilot.mkdir()
            (pilot / "highfly-animation-lab-p3.html").write_text("<html>fixture</html>", encoding="utf-8")
            (pilot / "highfly_animation_lab_p3.ts").write_text("// fixture", encoding="utf-8")
            donor = root / "owned.glb"
            donor.write_bytes(b"private-owned-mock")
            manifest = {"sourceCommit": module.PIN, "models": [], "donors": [{"title": "fixture"}]}
            copies = [(donor, upstream / "public/highfly-private-p3/donor_00.glb")]
            with patch.object(module, "ROOT", root):
                module.install(upstream, manifest, copies)
                module.install(upstream, manifest, copies)
                self.assertEqual(p1.read_text(encoding="utf-8"), "original p1 unchanged")
                self.assertEqual((upstream / "public/highfly-private-p3/donor_00.glb").read_bytes(), donor.read_bytes())
                donor.write_bytes(b"now different")
                with self.assertRaisesRegex(RuntimeError, "DIFFERENT_EXISTING_P3_FILE"):
                    module.install(upstream, manifest, copies)

if __name__ == "__main__":
    unittest.main()
