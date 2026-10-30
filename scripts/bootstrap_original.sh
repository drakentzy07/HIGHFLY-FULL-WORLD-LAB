#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="$PWD/.workspace/claudecraft-v0.44.7"
if [[ ! -d "$BASE/.git" ]]; then
  git clone --depth 1 --filter=blob:none --sparse --branch v0.44.7 https://github.com/levy-street/world-of-claudecraft.git "$BASE"
  git -C "$BASE" sparse-checkout set src public scripts data server tests third_party patches build skies_in mediawiki electron bot android ios dev headless docs/i18n
fi
SHA="$(git -C "$BASE" rev-parse HEAD)"
[[ "$SHA" == "493c35a108cef6c8aa290e8793107b1cd117886e" ]] || { echo "Original version hash mismatch"; exit 2; }
[[ -f "$BASE/src/editor/main.ts" && -f "$BASE/src/sim/sim.ts" && -f "$BASE/CREDITS.md" ]] || { echo "Missing original components"; exit 3; }
 (cd "$BASE" && npx --yes pnpm@10.34.5 install --frozen-lockfile)
node "scripts/audit_credits.mjs" "$BASE/CREDITS.md" ".workspace/reports/v0.44.7"
echo "0.44.7 private checkout ready with family-level rights report. Recommended: bash scripts/start_preview_0447.sh"
