#!/usr/bin/env bash
# HIGHFLY ORIGIN P0: prepare a PRIVATE code-only development stage.
# Does NOT publish, remove original media, convert characters or create game build.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ORIG="$ROOT/.workspace/claudecraft-v0.44.7"
STAGE="$ROOT/.workspace/highfly-origin-stage-p0"
EXPECTED=493c35a108cef6c8aa290e8793107b1cd117886e
if [[ ! -f "$ORIG/LICENSE" ]]; then
  echo "[HIGHFLY] Original v0.44.7 is missing. First: bash scripts/bootstrap_original.sh" >&2
  exit 2
fi
if [[ "$(git -C "$ORIG" rev-parse HEAD)" != "$EXPECTED" ]]; then
  echo "[HIGHFLY] WRONG VERSION, refused. Expected ClaudeCraft 0.44.7 only." >&2
  exit 3
fi
node "$ROOT/scripts/highfly_release_gate.mjs" --preflight
node "$ROOT/scripts/highfly_stage_code_0447.mjs" "$ORIG" "$STAGE"
[[ -d "$STAGE/public" ]] || { echo "MISSING_EMPTY_PUBLIC"; exit 4; }
if [[ "$(find "$STAGE/public" -type f | wc -l)" != "0" ]]; then
  echo "BLOCK: Original public media unexpectedly copied." >&2
  exit 5
fi
echo "[HIGHFLY] Source-only stage prepared: $STAGE"
echo "[HIGHFLY] Original reference untouched, no user media imported."
echo "[HIGHFLY] Commercial release LOCKED until file-by-file approval and full tests."
