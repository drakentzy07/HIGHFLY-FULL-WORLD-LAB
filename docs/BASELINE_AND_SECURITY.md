# HIGHFLY KayKit / v0.44.7 — Safety and acceptance

Version is pinned at `493c35a108cef6c8aa290e8793107b1cd117886e` and only downloaded into gitignored `.workspace/` in the private Codespace. `main` retains v0.45.4 reference. Never include upstream binaries, multimedia, generated `dist/` or the user's purchased KayKit source in this public repository without reviewing exact redistribution rights and asset provenance. Ports 4173/5173 must remain PRIVATE.

0.44.7 includes KayKit CC0 and other free assets but ALSO restricted icons, project-only props/creatures, some music/SFX and other licensed media. Treat CREDITS family entries as *candidate* rights evidence; missing entries are not free. An upstream commit passing tests is not a legal clearance. This is not a deployable HIGHFLY release.

## Preflight / functional acceptance

- v0.44.7 pinned SHA, original `src/editor/main.ts`, `src/sim/sim.ts`, `CREDITS.md` found.
- Node 22, pnpm 10.34.5 install succeeds; game boots in optimized PRIVATE preview port 4173.
- Offline: character creation, Eastbrook, quests, NPC, combat, mobs, loot, inventory, equipment, save checked with screenshots.
- Editor: open `/editor.html`, save local map, playtest. Test only what this version implements.
- No public build until a fail-closed asset allowlist (file hash/provenance/license), full asset ref resolution, and browser/device regression pass.
