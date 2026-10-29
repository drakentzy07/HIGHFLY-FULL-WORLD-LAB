#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="$PWD/.workspace/claudecraft-v0.45.4"
if [[ ! -d "$BASE/.git" ]]; then
  git clone --depth 1 --filter=blob:none --sparse --branch v0.45.4 https://github.com/levy-street/world-of-claudecraft.git "$BASE"
  git -C "$BASE" sparse-checkout set src public scripts data server tests third_party patches build skies_in mediawiki electron bot android ios dev headless docs/i18n
fi
SHA="$(git -C "$BASE" rev-parse HEAD)"
[[ "$SHA" == "ebd3aa444352952321e0108b335722fe26d35716" ]] || { echo "Original version hash mismatch"; exit 2; }
[[ -f "$BASE/src/editor/main.ts" && -f "$BASE/src/sim/sim.ts" && -f "$BASE/CREDITS.md" ]] || { echo "Missing original components"; exit 3; }
 (cd "$BASE" && npx --yes pnpm@10.34.5 install --frozen-lockfile)
echo "Original source prepared offline. Run: bash scripts/start_offline.sh"
