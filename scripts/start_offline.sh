#!/usr/bin/env bash
# Start ONLY the upstream development client. No server accounts, no deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.workspace/claudecraft-v0.45.4"
if [[ ! -f "$SRC/package.json" ]]; then
  echo "Original checkout missing. First run: bash scripts/bootstrap_original.sh" >&2
  exit 2
fi
echo "Starting local offline-capable game and map editor at port 5173."
echo "Codespaces: keep the forwarded port PRIVATE. In the game choose Play Offline."
cd "$SRC"
exec npx --yes pnpm@10.34.5 exec vite --host 0.0.0.0 --port 5173
