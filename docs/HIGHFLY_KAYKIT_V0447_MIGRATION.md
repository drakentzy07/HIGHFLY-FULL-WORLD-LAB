# HIGHFLY WORLD — KayKit-first foundation (v0.44.7)

## Pinned reference
- Source: [levy-street/world-of-claudecraft](https://github.com/levy-street/world-of-claudecraft)
- Tag: `v0.44.7`
- Exact commit: `493c35a108cef6c8aa290e8793107b1cd117886e`
- Branch: `highfly-kaykit-v0447-lab`
- Original 0.45.4 lab stays untouched on `main`.

## Why v0.44.7
The original uses the KayKit Rig_Medium modular character system and KayKit Medieval Hexagon town models (e.g. `public/models/biome/hexb_townhall.glb` and `hex_church.glb`). It avoids the WOC character family and Tidehold painted asset family introduced later. The code is MIT; the media is NOT automatically MIT.

## Strict release policy
This is an audit/trial branch and is NOT a shipping build. The original media and preview dist live under ignored `.workspace/`; do not upload or share them. No public GitHub Pages release until an exact-path, hash-verified media allowlist and bundled-dependency audit are complete. Remove/replace all `No, permission required`, `With the project only` (HIGHFLY independent goal), `CC BY-NC`, unknown media, names, logos and marks. Retain required attribution/licenses for third-party code, CC BY and font licenses as applicable. `CREDITS.md` describes media families, not automatic item-by-item approval.

## First successful test requirements
1. Offline character creator: a KayKit-class rig visible, then enter world.
2. Eastbrook: KayKit Medieval Hexagon houses, roads, chapel, shop and harbor, working terrain and correct collision.
3. NPC quests, combat, skills, mob AI, corpse loot, inventory, equipment, level-up and save (offline characteristics may differ from server).
4. Map editor at `/editor.html`, local save, playtest, interior transition (if present). Record absent features rather than claiming completeness.
5. Record a baseline screenshot and bugs on PC, and then test on Samsung S23 Ultra in landscape without assuming PC controls are mobile ready.

## Integration path
- P0: Rebuild a functioning original on the new branch in a private Codespace. No gameplay changes.
- P1: Generate exact asset manifest and an explicit replacement map by identifier. Verify CC0 originals and the purchased KayKit Complete files (with filenames, source, hashes, pack, license).
- P2: Import KayKit Complete independently, with character skin/rig compatibility tests, stairs/doors/collision and building scale against character height.
- P3: Replace blocked media/IDs **before** deleting dependencies; test each map and NPC feature after each staged change.
- P4: Implement HIGHFLY universal Hunter, combat/movement and Android/MOBA HUD as modular changes; later selectively port MIT 0.45.4 editor features with tests.
- P5: Only publish after fail-closed rights gate passes, assets resolve, and real browser gameplay tests pass.

## Commands (Codespace on this branch)
```bash
bash scripts/bootstrap_original.sh
bash scripts/start_preview_0447.sh
```
The preview uses PRIVATE port 4173 and includes original media under `.workspace/` for local assessment only. It does NOT authorize redistributing those files. GitHub Codespaces can incur usage charges. Stop the Codespace after testing.
