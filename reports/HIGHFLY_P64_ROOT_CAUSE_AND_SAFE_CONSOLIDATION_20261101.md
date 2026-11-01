# HIGHFLY — Diagnóstico de parches P39→P64, 1 de noviembre de 2026

## Estado establecido por terminal del usuario

1. P63: 6/6 pruebas OK; P9 `BUNDLE_BUILT_NOT_PLAYABLE_VERIFIED` con exitCode=0; `P63_COMBAT_C1` en estado `BUILD_GREEN_BROWSER_PENDING`. **Instalado en el stage privado, pero aún no verificado en navegador**. No reejecutar P63.
2. P64: **NO instalado**. El último comando detuvo la cadena en la prueba `test_media_and_lazy_load_once` (`RuntimeError not raised`), antes de ejecutar `--apply`.
3. Los errores anteriores fueron, en orden: validador GLB JSON-only erróneamente estricto; inserción `DIRECT_MEDIA_ALLOWLIST_2` porque `crab_ability_anims.glb` aparece dos veces por P39A+P39B; prueba de doble aplicación que descubrió que `edit_media()` admitía el mismo modelo una segunda vez.
4. **No se detectó un conflicto de versiones de ClaudeCraft** en estas trazas; son defectos de integración/adición de overlays sobre un stage acumulativo.

## Correcciones realizadas en GitHub

- `scripts/highfly_p64_real_boar_cc0.py` rechaza reinsertar el mismo marcador o ruta en media, assets y manifest, antes de tocar archivos.
- `tests/test_highfly_p64_real_boar_cc0.py` incluye regresión para dos rutas legacy del cangrejo, reinserción en media/assets/manifest y presencia de una ruta sin marcador.
- `python3 scripts/highfly_p64_real_boar_cc0.py --check-stage` **no descarga ni modifica nada**. Recorre los tres archivos fuente del stage P63, informa overlays P39B, repeticiones legacy (contadas por URL), estado de P63, ruta del nuevo GLB, validez de los tres anclajes y posibles conflictos; estas comprobaciones se realizan sobre strings en memoria.
- No se han eliminado los duplicados preexistentes: P39A/P39B pueden contener URLs iguales en listas; una limpieza automática a ciegas sería peligrosa si el contenido se usa en más de un sistema.

## Ruta corta segura para P64

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p64_real_boar_cc0.py' -v && \
python3 scripts/highfly_p64_real_boar_cc0.py --check-stage
```

**No ejecutar --apply hasta revisar el informe del doctor**, porque estamos revisando la fiabilidad del stage. Si el informe dice `patchReady: true` y no hay fuentes previas alteradas, podremos ejecutar solo `python3 scripts/highfly_p64_real_boar_cc0.py --apply` y comprobar `BUILD_GREEN_BROWSER_PENDING`. El live browser y las animaciones siguen pendientes.

## Arquitectura para dejar atrás la sucesión de PXX

- **Congelar baseline** de la versión jugable privada P63. Guardar manifest de hashes y copia protegida de todas las fuentes afectadas, sin publicar ni eliminar KayKit SOURCE.
- **Consolidar una única carpeta de overlays** con transformaciones declarativas por sistema (assets/licencias, NPC, mundo, combate), en lugar de reemplazar anclajes textuales entre P36, P39, P48, P58, P62 y P64.
- Un solo build/reproceso desde origen MIT pinned y conjunto aprobado de assets CC0/privados. Parches antiguos: archivados y deshabilitados del flujo diario; **no borrar respaldos ni repositorios**.
- Tests integrados sobre los archivos efectivamente ensamblados en el stage privado, además de unit tests sintéticos: comprobar IDs, anclajes únicos, licencias, duplicados, imports TypeScript, Vite, ejecución real en navegador y guardado.
- Generar `HIGHFLY_BUILD_MANIFEST.json` de hash para cada asset y fuente, identificando owner/licencia/origen; fallar si un recurso no autorizado llega al paquete.
- Reutilizar primero los recursos MIT/CC0 exactos de ClaudeCraft; sustituir únicamente los `With the project only`, restringidos o no verificados por recursos legales KayKit/CC0.
- **Separar la limpieza estructural de la próxima prueba de combate**. Primero estabilizar P63/P64, luego migrar a baseline sin destruir trabajo existente.

## Límites

El análisis se hizo sobre los logs suministrados por el usuario, los scripts actuales de GitHub y la documentación oficial de Gobkit (el Boar tiene CC0, clips idle/walk/attack/dead y está listado en /api/free). El stage de Codespaces es privado y no se ha ejecutado desde este entorno. Un doctor verde valida integración textual, NO garantiza jugabilidad ni corrección de balance/animaciones.
