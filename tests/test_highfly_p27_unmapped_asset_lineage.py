#!/usr/bin/env python3
"""P27 source lineage must never mistake string resemblance for usage rights."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p27_unmapped_asset_lineage as p27


class P27LineageTests(unittest.TestCase):
    def test_source_code_exact_model_name_with_line_reference(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp)
            directory=source/"scripts/assets"
            directory.mkdir(parents=True)
            (directory/"build_ignivar_props.mjs").write_text(
                'const file = "ignivar_prop_beam.glb";\n'
                'const unrelated = "ignivar_prop_beamery.glb";\n'
            )
            evidence,count=p27.script_lineage(source,[
                "/models/dungeon/ignivar_prop_beam.glb"])
            self.assertEqual(count,1)
            record=evidence["/models/dungeon/ignivar_prop_beam.glb"]
            self.assertEqual(len(record),1)
            self.assertEqual(record[0]["line"],1)
            self.assertEqual(record[0]["kind"],"ASSET_BUILD_SCRIPT_EXACT_IDENTIFIER")

    def test_build_script_family_is_only_a_hint(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp)
            asset=source/"scripts/assets/build_ignivar_props.mjs"
            asset.parent.mkdir(parents=True)
            asset.write_text("console.log('generator')")
            hints=p27.family_candidates("/models/dungeon/ignivar_prop_gate.glb",source)
            self.assertEqual(hints,["scripts/assets/build_ignivar_props.mjs"])
            self.assertEqual(p27.family_candidates("/models/unknown/new_asset.glb",source),[])

    def test_license_mentions_only_exact_asset_names(self):
        credits=[
            (10,"| Ignivar prop beam | World of ClaudeCraft | original | Project asset | With the project only |",
             ["Ignivar prop beam","World of ClaudeCraft","original","Project asset","With the project only"]),
            (12,"| etc | Quaternius | Quaternius nature | CC0 1.0 | Yes |",
             ["etc","Quaternius","Quaternius nature","CC0 1.0","Yes"]),
        ]
        result=p27.license_evidence("/models/dungeon/ignivar_prop_beam.glb",credits)
        # Human prose 'Ignivar prop beam' is not exact identifier (underscore).
        self.assertEqual(result,[])
        self.assertEqual(p27.license_evidence("/models/dungeon/another_asset.glb",credits),[])

    def test_scanner_ignores_binaries_and_symlink_like_large_files(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)
            directory=path/"src"
            directory.mkdir()
            (directory/"render.ts").write_text("const x='model'")
            (directory/"mesh.glb").write_bytes(b"glTF")
            files=list(p27.safe_text_sources(path))
            self.assertEqual(len(files),1)
            self.assertEqual(files[0].name,"render.ts")


if __name__=="__main__":
    unittest.main()
