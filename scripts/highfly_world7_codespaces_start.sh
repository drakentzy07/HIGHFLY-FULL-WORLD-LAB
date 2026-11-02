#!/usr/bin/env bash
# HIGHFLY WORLD7 — safe Codespaces entry point (never applies stage patches).
set -Eeuo pipefail
cd "$(dirname "$0")/.."
echo "===================================================="
echo "HIGHFLY WORLD 7 / CAZADOR UNIVERSAL — P70 PRECHECK"
echo "===================================================="
branch="$(git branch --show-current)"
if [[ "$branch" != "highfly-world7-p70-hunter-universal-20261102" ]]; then
  echo "ERROR: Estás en la rama '$branch'."
  echo "Primero: git fetch origin highfly-world7-p70-hunter-universal-20261102"
  echo "Luego: git switch highfly-world7-p70-hunter-universal-20261102"
  exit 2
fi
command -v node >/dev/null || { echo "ERROR: Node.js no está disponible"; exit 2; }
command -v python3 >/dev/null || { echo "ERROR: Python3 no está disponible"; exit 2; }
echo
echo "[1/3] Contratos del Cazador Universal"
node --test tests/highfly_hunter_universal_p70.test.mjs
echo
echo "[2/3] Pruebas de seguridad del diagnóstico"
python3 -m unittest discover -s tests -p 'test_highfly_world7_codespace_audit.py' -v
echo
echo "[3/3] Auditoría de la instalación privada REAL"
python3 scripts/highfly_world7_codespace_audit.py
echo
echo "Informe: .workspace/reports/highfly-world7/P70_CODESPACE_AUDIT.md"
echo "JSON:    .workspace/reports/highfly-world7/P70_CODESPACE_AUDIT.json"
echo "No se modificaron la física, las clases, los archivos GLB ni el gameplay."
echo "No ejecutar P68/P69/P70 --apply sólo por tener este precheck en verde."
