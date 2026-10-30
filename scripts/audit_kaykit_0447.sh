#!/usr/bin/env bash
# Safe, read-only HIGHFLY v0.44.7 audit. Run in a SECOND Codespace terminal.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.workspace/claudecraft-v0.44.7"
OUT="$ROOT/.workspace/reports/v0.44.7/media"
EXPECTED=493c35a108cef6c8aa290e8793107b1cd117886e
if [[ ! -f "$SRC/CREDITS.md" ]]; then
  echo "Missing original source. First run bash scripts/bootstrap_original.sh" >&2
  exit 2
fi
if [[ "$(git -C "$SRC" rev-parse HEAD)" != "$EXPECTED" ]]; then
  echo "Unexpected upstream version; refusing to attribute files to v0.44.7" >&2
  exit 3
fi
node "$ROOT/scripts/inventory_kaykit_0447.mjs" "$SRC" "$OUT"
node "$ROOT/scripts/plan_eastbrook_kaykit_0447.mjs" "$SRC" "$OUT"
echo
echo "HIGHFLY: private audit reports created under:"
echo "$OUT"
echo "MEDIA_ALL_FILES.json - every public source asset and hash"
echo "KAYKIT_CANDIDATES.json - likely CC0 sources, NOT shipping approval"
echo "EASTBROOK_BUILDINGS.json - existing IDs to preserve while swapping visuals"
echo "RESUMEN_INVENTARIO.md - license inventory summary"
echo "No game assets changed, no public publishing, no player progress reset."
