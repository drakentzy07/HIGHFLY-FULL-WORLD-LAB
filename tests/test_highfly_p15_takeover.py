import importlib.util
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/highfly_p15_takeover.py"
SPEC = importlib.util.spec_from_file_location("highfly_p15_takeover", SOURCE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)

CREDITS = """# Asset Credits and Asset Licenses
| Basis Universal KTX2 transcoder | Binomial LLC | source | Apache-2.0 | Yes, attribution required |
| Terrain PBR textures (Grass001, Ground023, Rock026) | ambientCG | source | CC0 1.0 | Yes |
| Surface-detail PBR textures (Bark012) | ambientCG | source | CC0 1.0 | Yes |
| Worn-metal surface-detail PBR texture | Poly Haven | source | CC0 1.0 | Yes |
| Medieval wood surface-detail PBR texture | Poly Haven | source | CC0 1.0 | Yes |
| Canopy clump-detail textures | ambientCG | source | CC0 1.0 | Yes |
| Thornhollow battleground terrain textures | ambientCG | source | CC0 1.0 | Yes |
| HDRI environment maps | Poly Haven | source | CC0 1.0 | Yes |
"""
LICENSE = "MIT License\n\nCopyright (c) 2026 Levy Street\n"


class HighflyTakeoverTests(unittest.TestCase):
    def make_world(self, root):
        original = root / ".workspace/claudecraft-v0.44.7"
        stage = root / ".workspace/highfly-origin-stage-p0"
        out = root / ".workspace/reports/highfly-p15"
        archive = root / ".workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip"
        original.mkdir(parents=True)
        stage.mkdir(parents=True)
        (original / "CREDITS.md").write_text(CREDITS)
        (original / "LICENSE").write_text(LICENSE)
        for name in ("index.html", "play.html"):
            (stage / name).write_text(
                '<html><head><title>World of ClaudeCraft</title></head>'
                '<body><img class="main-logo" src="/worldofclaudecraft-logo.png" />'
                '<span>World of ClaudeCraft</span></body></html>'
            )
        for name, data in (
            ("basis/basis_transcoder.js", b"Apache binary"),
            ("basis/basis_transcoder.wasm", b"Apache binary 2"),
            ("textures/terrain/Rock026_Color.ktx2", b"ambientcg asset"),
            ("textures/terrain/Rock0260_Color.ktx2", b"unrecorded asset"),
            ("textures/structures/Bark012_Normal.jpg", b"ambientcg"),
            ("textures/foliage/Moss002_Normal.jpg", b"ambientcg"),
            ("textures/battleground/ground.jpg", b"ambientcg"),
            ("textures/battleground/decals/ground.jpg", b"project art not CC0"),
            ("ui/skills/warrior/icon.webp", b"restricted CraftPix"),
        ):
            file = original / "public" / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        (original / "src").mkdir(parents=True, exist_ok=True)
        (original / "src/game.ts").write_text("export const game=true;")
        return original, stage, archive, out

    def test_accepts_positive_license_only_and_rejects_unrecorded_media(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, stage, archive, out = self.make_world(root)
            with patch.object(p, "ROOT", root):
                matches = p.allowed_media(original, stage, CREDITS)
            names = {r["relative"] for r in matches}
            self.assertIn("basis/basis_transcoder.wasm", names)
            self.assertIn("textures/terrain/Rock026_Color.ktx2", names)
            self.assertIn("textures/structures/Bark012_Normal.jpg", names)
            self.assertIn("textures/foliage/Moss002_Normal.jpg", names)
            self.assertIn("textures/battleground/ground.jpg", names)
            self.assertNotIn("textures/terrain/Rock0260_Color.ktx2", names)
            self.assertNotIn("textures/battleground/decals/ground.jpg", names)
            self.assertNotIn("ui/skills/warrior/icon.webp", names)
            self.assertTrue(all("evidence" in r and r["license"] for r in matches))

    def test_requires_credits_row_to_match_license_and_redistribution(self):
        with self.assertRaisesRegex(RuntimeError, "CREDITS_LICENSE_ROW_NOT_VERIFIED"):
            p.row_with_credit(
                "| Basis Universal KTX2 transcoder | X | X | Apache-2.0 | No, permission required |",
                "Basis Universal KTX2 transcoder", "Apache-2.0")

    def test_brand_replacement_is_idempotent_and_preserves_dom_ids(self):
        html = (
            '<html><head><title>World of ClaudeCraft</title>'
            '<link rel="canonical" href="https://worldofclaudecraft.com/" />'
            '</head><body><img id="title-logo" src="/worldofclaudecraft-logo.png" />'
            '<button id="btn-offline">Offline</button></body></html>'
        )
        modified = p.stage_brand_html(html)
        self.assertIn("HIGHFLY ORIGIN", modified)
        self.assertIn('src="/highfly-private-p15/highfly-logo.svg"', modified)
        self.assertIn('id="btn-offline"', modified)
        self.assertNotIn('rel="canonical"', modified)
        self.assertEqual(modified, p.stage_brand_html(modified))

    def test_restores_missing_code_and_licensed_boot_media_not_restricted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, stage, archive, out = self.make_world(root)
            before = (original / "public/ui/skills/warrior/icon.webp").read_bytes()
            fake_audit = {
                "code": {"missingCodeFiles": ["src/game.ts"]},
                "coreRpgCodeIdentical": True,
                "media": {"literalReferencesUnresolved": 47},
                "ownedKayKitWorld": {"modelMatchingStatuses": {"NO_EXACT_KAYKIT_SOURCE": 10}},
            }
            with patch.object(p, "ROOT", root), patch.object(p.p9,"preflight", return_value={} ), patch.object(
                    p.p12, "validate", return_value=None), patch.object(
                    p.p14, "code_inventory", return_value={"missingCodeFiles": ["src/game.ts"]}), patch.object(
                    p.p14, "audit", return_value=fake_audit), patch.object(
                    p.p12, "source_manifest", return_value={"exactMatches": [], "statuses": {}}), patch.object(
                    p.p12, "index_models", return_value={}), patch.object(
                    p.p12, "zip_members", return_value={}):
                import zipfile
                archive.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(archive, "w"):
                    pass
                result = p.apply(original, stage, archive, out, include_models=False, run_build=False)
            self.assertTrue((stage / "src/game.ts").is_file())
            self.assertTrue((stage / "public/basis/basis_transcoder.wasm").is_file())
            self.assertTrue((stage / "public/highfly-private-p15/highfly-logo.svg").is_file())
            self.assertFalse((stage / "public/ui/skills/warrior/icon.webp").exists())
            self.assertEqual((original / "public/ui/skills/warrior/icon.webp").read_bytes(), before)
            self.assertIn("HIGHFLY ORIGIN", (stage / "index.html").read_text())
            self.assertTrue(result["simRpgCorePreserved"])
            self.assertEqual(result["unresolvedMediaReferences"], 47)
            self.assertIsNone(result.get("viteBuild"))


if __name__ == "__main__":
    unittest.main()
