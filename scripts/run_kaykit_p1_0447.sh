#!/usr/bin/env bash
# Read-only HIGHFLY P1: verify 11 existing CC0 KayKit building candidates in Eastbrook.
# Keep the optimized private preview running in its FIRST terminal.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM="$ROOT/.workspace/claudecraft-v0.44.7"
REPORTS="$ROOT/.workspace/reports/v0.44.7/pilot"
EXPECTED=493c35a108cef6c8aa290e8793107b1cd117886e
if [[ ! -f "$UPSTREAM/src/sim/eastbrook_layout.ts" ]]; then
  echo "Original v0.44.7 checkout missing. Run bash scripts/bootstrap_original.sh" >&2
  exit 2
fi
if [[ "$(git -C "$UPSTREAM" rev-parse HEAD)" != "$EXPECTED" ]]; then
  echo "Wrong upstream SHA. Pilot aborted with no changes." >&2
  exit 3
fi
node "$ROOT/scripts/verify_kaykit_pilot_0447.mjs" "$UPSTREAM" "$REPORTS"
echo
echo "[HIGHFLY] Private P1 results:"
echo "  $REPORTS/KAYKIT_EASTBROOK_P1.md"
echo "  $REPORTS/KAYKIT_EASTBROOK_P1.json"
echo "No game changes, no asset publishing, no restart needed."
