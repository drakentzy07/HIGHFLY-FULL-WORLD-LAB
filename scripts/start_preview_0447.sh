#!/usr/bin/env bash
# HIGHFLY KayKit v0.44.7 — private optimized offline preview (no public deployment).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.workspace/claudecraft-v0.44.7"
if [[ ! -f "$SRC/package.json" ]]; then
  echo "v0.44.7 missing; first run: bash scripts/bootstrap_original.sh" >&2
  exit 2
fi
if [[ "$(git -C "$SRC" rev-parse HEAD)" != "493c35a108cef6c8aa290e8793107b1cd117886e" ]]; then
  echo "REF PIN MISMATCH: refusing preview" >&2
  exit 3
fi
node "$ROOT/scripts/prepare_preview_0447.mjs" "$SRC"
cd "$SRC"
if [[ ! -d node_modules ]]; then npx --yes pnpm@10.34.5 install --frozen-lockfile; fi
printf '\n[HIGHFLY] Generating translations and guide content...\n'
npx --yes pnpm@10.34.5 run i18n:gen
npx --yes pnpm@10.34.5 run wiki:content
node scripts/build_media_manifest.mjs generate
printf '\n[HIGHFLY] Building optimized PRIVATE client (will include upstream media).\n'
VITE_HIGHFLY_OFFLINE_LAB=1 NODE_OPTIONS=--max-old-space-size=5120 npx --yes pnpm@10.34.5 exec vite build --base=/
node scripts/build_media_manifest.mjs emit
printf '\n[HIGHFLY] PRIVATE preview ready on Codespaces port 4173.\n'
printf '[HIGHFLY] Ports > 4173 > visibility PRIVATE > open in browser; choose Offline.\n'
printf '[HIGHFLY] NEVER upload dist/ or set this port to Public.\n'
exec npx --yes pnpm@10.34.5 exec vite preview --host 0.0.0.0 --port 4173
