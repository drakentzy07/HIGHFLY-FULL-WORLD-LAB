# HIGHFLY WORLD — KayKit-first RPG lab (ClaudeCraft v0.44.7)

**Base elegida:** v0.44.7 — commit `493c35a108cef6c8aa290e8793107b1cd117886e`. This branch is an independent HIGHFLY development lab. The v0.45.4 reference remains untouched on `main`.

**Why:** v0.44.7 uses the KayKit Rig_Medium character/animation pipeline and KayKit Medieval Hexagon houses, harbor and chapel. We will integrate the user's KayKit Complete library, preserving the MIT RPG world, quests, AI, loot and editor; blocked media will be replaced **before** public distribution. This branch does NOT contain the full original game or the paid KayKit Complete files.

## Launch private Codespaces

1. Open this branch on GitHub and choose **Code → Codespaces → Create codespace on highfly-kaykit-v0447-lab**. Use a 4-core / 8-GB machine if available. GitHub may charge for usage.
2. The devcontainer will run `bash scripts/bootstrap_original.sh` on creation. It downloads the pinned upstream into the gitignored `.workspace/claudecraft-v0.44.7/`, installs packages and writes the license-family audit under `.workspace/reports/v0.44.7/`.
3. In VS Code terminal:
   ```bash
   bash scripts/start_preview_0447.sh
   ```
   This **private optimized build** is preferred over Vite development mode, which can overload the Codespaces HTTP/2 tunnel with thousands of source modules.
4. In **Ports**, keep port **4173** marked **Private**. Open its HTTPS URL and choose **Offline**, create a character, then enter world. The editor is at the same origin `/editor.html`.
5. Optional rapid dev mode (unbundled Vite modules, port 5173):
   ```bash
   bash scripts/start_offline.sh
   ```

**Keep the Codespace port private. Never upload/dist or deploy the original client, including generated `dist/`.** The original game includes nonredistributable assets. This branch is NOT approved for Pages distribution. The old v0.45.4 Pages trial and its scripts are historical and are not the 0.44.7 game or an approval to publish.

## Next gates

- Functional PC baseline: character, Eastbrook, AI/combat, quests, NPC, skills, loot, inventory, equipment, editor/playtest.
- Rights: exact-path manifests, hashes, sources, license, per-file replacement targets. Preserve MIT notices; independent HIGHFLY excludes project-only, rights-reserved, noncommercial and unknown media.
- KayKit Complete: bring from user's licensed source separately, check rig/animations, scale, interiors, collisions and LOD.
- Android landscape: test controls, camera, HUD and memory/performance on Samsung S23 Ultra.
- Later selective port of MIT editor code from 0.45.4; no bulk merges.

Read [the migration and safety plan](docs/HIGHFLY_KAYKIT_V0447_MIGRATION.md).
