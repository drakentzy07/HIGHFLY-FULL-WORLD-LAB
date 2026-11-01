# HIGHFLY P55 — EDITOR ORIGINAL 2.0 + CARGA (2026-11-01)

## Dirección
No desarrollar un editor nuevo. El editor original existente está en `editor.html`, `src/editor/main.ts`, `src/editor/app.ts`, `src/editor/3d/viewport.ts`, `src/editor/asset_browser.ts`, `src/editor/inspector.ts`. Tiene selección y colocación de assets, cámara 3D, transformaciones, undo, guardar/exportar mapas. `customMapToWorldContent` y `rebuildActiveWorld` usan `clonePropsWithoutEastbrookLayout`, lo que impide que su modo habitual muestre Eastbrook exactamente como el juego. P55 **no sustituye ese editor**: suma un modo opt-in sobre los mismos componentes.

## P55
- Script `scripts/highfly_p55_private_editor_studio.py`.
- Test `tests/test_highfly_p55_private_editor_studio.py`.
- Instala en `.workspace/highfly-origin-stage-p0` y respalda en `.workspace/reports/highfly-p55/backups`.
- El modo `?hf_eastbrook_studio=1` usa el `BUILTIN_WORLD` completo en el Sim y Renderer del editor original, con herramientas normales bloqueadas en Seleccionar para impedir alteración accidental de misiones/sim.
- `src/render/props.ts` etiqueta y preserva individualmente en ese modo los decorProps cercanos a Eastbrook para permitir identificación por clic de `source key + x,z`. No cambia comportamiento del juego normal.
- Panel inspector de casas oficiales (11), bóveda, monumento, decoraciones de la zona y datos de sus modelos/posiciones. El selector de mallas fusionadas sin ID **no habilita borrado peligroso**.
- Botones: ocultar visualmente, restaurar, copiar diagnóstico, exportar borrador JSON. **No existe borrado real ni reemplazo persistente todavía**: el JSON es una propuesta revisable; requieren evaluar collider/quest antes de aplicar.
- `public/highfly/p55_loading.css`: imagen del logo al 89% de la altura de viewport y estado/barra/consejo alineados abajo en espacio reservado, usando el progreso real de `#ls-fill`.

## Ejecución precisa en Codespace VS Code
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git status --short
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p55_private_editor_studio.py' -v
python3 scripts/highfly_p55_private_editor_studio.py
python3 scripts/highfly_p55_private_editor_studio.py --apply
```
Si la compilación privada P9 sale verde, servidor:
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
```
Abrir **`/editor.html?hf_eastbrook_studio=1`** desde la URL de la pestaña **Ports** (4174) de Codespaces. En **Ports**, configurar **Port Visibility = Private**; este ajuste de permisos, no el parámetro URL, hace privado el editor. Mantener repositorio público sólo con scripts; `.workspace`, KayKit SOURCE y compilación quedan fuera de Git.

Pantalla de carga: probar la raíz `/` de la misma URL y revisar tamaños PC y Samsung S23 Ultra horizontal.

## Próxima comprobación visual concreta
1. Seleccionar el monumento en Studio y **Ocultar visualmente**: observar si desaparece el cono dorado. Restaurar. Si desaparece, identificador `eastbrook_realm_builder_monument` y revisión de visual GLB/FX, no borrado del servicio.
2. Seleccionar mini casita/pinchos; exportar diagnóstico (incluye ID, GLB y ubicación si tiene root individual). Las construcciones de `eastbrook_layout` NO deben borrarse sólo por ser pequeñas.
3. Identificar granja por origen de props y contrastar escala/collider. Reemplazo permanente sólo cuando cada ID y licencia estén verificados.
4. Adaptar el **AssetBrowser existente** para registrar biblioteca privada de KayKit SOURCE y los assets previamente auditados; no publicar ni copiar sin licencia.

## Estado
- Scripts y test publicados en GitHub.
- P55 no ejecutado en Codespace desde esta sesión.
- Compilación Vite real, imágenes PC/Android, Editor Studio, jabalíes y FURY 360° todavía no verificados en P55.
- No volver a ejecutar P46–P54 ni activar `hf_probe_eastbrook_kmed=hide` en prueba final.
