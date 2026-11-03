#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ORIG=".workspace/claudecraft-v0.45.4"
if [[ ! -f "$ORIG/scripts/asset_pipeline/pipeline.mjs" ]]; then
  echo "Falta el motor ORIGINAL de ClaudeCraft."
  echo "Ejecuta primero: bash scripts/bootstrap_original.sh"
  exit 2
fi
if [[ ! -d "$ORIG/node_modules" ]]; then
  echo "Instalando dependencias desde el lockfile..."
  (cd "$ORIG" && npx --yes pnpm@10.34.5 install --frozen-lockfile)
fi
echo "HIGHFLY Original Skin Studio — puerto 5185"
echo "Abrí la pestaña Ports de Codespaces y dejá 5185 PRIVATE."
exec node scripts/highfly_original_skin_studio.mjs
