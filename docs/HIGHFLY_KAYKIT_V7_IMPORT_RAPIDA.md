# HIGHFLY ORIGIN — Importación KayKit rápida, segura y sin publicar modelos

## Archivos confirmados en la biblioteca del usuario

- `HIGHFLY_KAYKIT_V7_K1_SELECTED_SOURCE.zip` — 1,3 MB. Primera opción para diagnosticar contenido real.
- `KIT_COMPLETO_PARTE_01.zip` — 367 MB. Reservar hasta saber si hace falta.
- `KIT_COMPLETO_PARTE_02.zip` — 278 MB. Reservar hasta saber si hace falta.
- `KAYKIT_V7_LISTADO.txt` — inventario de rutas, **no binarios**.

Los ZIP se encontraron en la biblioteca de ChatGPT y se materializaron para la sesión. Las herramientas del asistente no ofrecen una transferencia binaria directa de esa biblioteca al Codespace del usuario. No subir ZIPs al GitHub público; transferencia manual desde el equipo al Explorador de VS Code (Codespaces) en carpeta git-ignored. **El ZIP de 1,3 MB no está aún verificado por contenido**; se inspeccionará antes de confiar en que incluya modelos.

## Un solo ZIP pequeño para comenzar

En un Codespace existente, preservando el servidor privado 4173 de la referencia jugable:

1. En una segunda terminal, revisar `git status --short`. No perder cambios sin commit.
2. `git fetch origin highfly-origin-commercial-p0`
3. `git switch --track origin/highfly-origin-commercial-p0` (si ya está creado localmente, `git switch highfly-origin-commercial-p0`).
4. `mkdir -p .workspace/private-imports/inbox`
5. Descargar el ZIP de 1,3 MB desde la biblioteca de ChatGPT a la PC y subirlo a `.workspace/private-imports/inbox/` mediante menú contextual **Upload...** en el explorador VS Code. No subir a raíz de repositorio.
6. Ejecutar **solo inspección**:

```bash
python3 scripts/highfly_kaykit_zip_intake.py \
  .workspace/private-imports/inbox/HIGHFLY_KAYKIT_V7_K1_SELECTED_SOURCE.zip
```

El resultado indica `countByPack`, `selectedFileCount` y `sampleSelected`, y crea `.workspace/reports/kaykit-v7/ZIP_IMPORT_PLAN.json`. No extrae medios. Si no contiene modelos para Adventurers/Hexagon, probar después ZIPs de mayor tamaño sin subirlos hasta tener una necesidad concreta.

## Extracción aislada si el ZIP contiene packs requeridos

Únicamente cuando la inspección haya mostrado >0 archivos del pack esperado:

```bash
python3 scripts/highfly_kaykit_zip_intake.py \
  .workspace/private-imports/inbox/HIGHFLY_KAYKIT_V7_K1_SELECTED_SOURCE.zip \
  --extract
```

Se extrae solo `KayKit Adventurers 2.0` y `KayKit Medieval Hexagon Pack 1.0.1` bajo `.workspace/private-imports/kaykit-v7-selected/`. Ni el repositorio público ni el mundo original se modifican.

El primer modelo que integraremos después de comprobarlo se probará en una copia privada aislada del juego, con mapeo reversible de archivo/ID, guardado y regresión de combate/quest/NPC. **No hacemos cambios masivos.**

## Restricciones

- La compilación original 0.44.7 permanece privada y separada; no publicar o cambiar Ports a Public.
- GitHub Actions en verde significan que pasaron pruebas de seguridad de scripts, no que todos los medios estén autorizados ni que la versión independiente sea jugable todavía.
- Verificar las condiciones y versión CC0 de cada fuente oficial antes de añadir una entrada a `config/highfly_approved_media.json`. Mantener aviso MIT de Levy Street y revisar dependencias, UI, fuentes, sonidos, marcas y derechos de terceros.
