# HIGHFLY WORLD 7 / P71 — 9 CLASES + DRAKENLAB

2026-11-02. GitHub CI tests: GREEN. Private Codespace installation and browser QA: PENDING.

## Direction
Keep the 9 MIT RPG classes, their specializations, talents, skills, progression, 4 original resource types, equipment permissions, professions and saves. Build FURY GOLDEN movement and attack mechanics across all 9 classes. Independent KayKit skins are a separate visual upgrade after auditing all rigs.

P71 is a safe offline class TEST LAB. It does not finish universal FURY or skins yet.

## P71 files
- pilot/highfly_drakenlab_p71.ts: Spanish touch menu, 9 classes, button in-game. Switch class by full page reload to a newly constructed offline Sim with correct native class stats, starting skills, and inventory. Does NOT mutate a live class or online server data. Boot query is consumed once to avoid loops.
- pilot/highfly_drakenlab_p71.css: responsive landscape overlay for S23 Ultra, original text-only monograms (no proprietary art).
- scripts/highfly_world7_p71_drakenlab.py: guarded private-stage installer; dry-run default; backup, P9 Vite build and source rollback.
- scripts/highfly_world7_p71_visual_matrix.py: read-only inventory of all 9 character model paths, existence and declared GLB animations; no media redistribution approval inferred.
- tests/test_highfly_world7_p71_drakenlab.py: synthetic installer safety tests.

## Codespaces execution
From the current repo workspace:

    cd /workspaces/HIGHFLY-FULL-WORLD-LAB
    git fetch origin
    git switch highfly-world7-p71-nine-classes-drakenlab-20261102
    git pull --ff-only

    python3 -m unittest discover -s tests -p 'test_highfly_world7_p71_drakenlab.py' -v
    python3 scripts/highfly_world7_p71_drakenlab.py
    python3 scripts/highfly_world7_p71_visual_matrix.py

    # Only after successful precheck:
    python3 scripts/highfly_world7_p71_drakenlab.py --apply

    cat .workspace/reports/highfly-world7/p71/P71_STATUS.json
    cat .workspace/reports/highfly-world7/p71/P71_VISUAL_MATRIX.md

A successful P71 private build reports BUILD_GREEN_BROWSER_PENDING; it is not a gameplay test.

## Local preview in Codespaces

    cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
    node node_modules/vite/bin/vite.js preview --host 0.0.0.0 --port 4174

Open the PRIVATE Codespaces port 4174 URL and append:

    ?hf_drakenlab=1&hf_lab_cls=warrior&hf_lab_name=Draken

On game entry, the DRAKENLAB button appears. Select Paladin/Mage/Rogue/etc and press REINICIAR COMO. This reloads and enters a fresh offline world using original per-class Sim rules.

DO NOT make the Codespaces port public or publish this stage to Pages while privately acquired KayKit SOURCE or other proprietary media is inside.

## Limitations and next steps
- P71 does NOT currently decouple skins from class. P4 Knight bridge is already known to cover Warrior, not verified for every class.
- P71 does NOT add aerial dash, directional flip, combo chain or full skill aim to P69; those require per-class gameplay/rig implementation.
- Cannot claim 9 classes render correctly until inspecting P71_VISUAL_MATRIX and testing the actual game.
- Cannot claim commercial licensing clean until replacing prohibited icons, audio, models, emblems and profession art.

P72 will bind user-owned KayKit skins independently of class while preserving stats, then extend FURY Golden to class-specific melee/ranged/magic. Later iterate each class skill/cast/recast/cooldown and test PC/S23.
