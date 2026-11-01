# HIGHFLY P56 — EASTBROOK EDITABLE STUDIO + MONUMENT NORMALIZATION

## Hallazgos confirmados por el usuario
- P55: cinco pruebas PASS, P9 Vite bundle verde (no equivale a prueba de navegador/Android).
- El usuario abrió el Editor 2.0 en Codespace y consiguió seleccionar/ocultar exactamente `eastbrook_realm_builder_monument`.
- El JSON capturó `-14.75, -102`, visual real `13.84 × 23.98 × 14.56`, altura declarada `7.6`; por lo tanto el cono gigante es el GLB del monumento, y no la antigua malla KMED.
- `src/sim/content/realm_builders.ts`: `REALM_BUILDER_PLACEHOLDER_NAME='Your Name Here'`; `src/render/realm_builder_monument_fx.ts` genera la proyección en el monumento. En español se ve «Tu nombre aquí». En offline no hay ganador real.
- El Editor P55 no podía seleccionar props globales no etiquetados ni transformar estructuras, porque el picker se limitaba al árbol `eastbrookTownRebuild`, y las herramientas originales de edición estaban bloqueadas para no alterar el mundo oficial.

## P56: alcance exacto
- `scripts/highfly_p56_editor_transform.py`: **sobre P55 ya aplicado**, ningún paso P46–P55 se repite.
- `tests/test_highfly_p56_editor_transform.py`: seis pruebas de patch de texto sobre la constante del editor P55 y fixtures controlados.
- `src/editor/highfly_eastbrook_studio.ts`: selección en el renderer completo, con filtro de props para mallas no identificadas; reconoce casas adicionales, edificios, decor, FX, cuerpo del monumento por separado. Para malla sin ID estable: sólo cambio visual temporal, no persistir como cambio de mapa.
- Transformación de vista usando `X / Z / Giro° / Escala`; botones `Aplicar posición/escala`, `Revertir transformación`, `Ocultar visualmente`, `Restaurar visual`, y exportación JSON con estado de propuesta. Se ajusta la matriz de Three.js sin tocar sim, colisión, NPC, quest ni el guardado.
- `src/render/props.ts`: añade identificación de casas built-in no pertenecientes a la tabla oficial sólo en el Editor Studio, sin afectar al juego ni el rendering normal.
- `src/render/eastbrook_town.ts`: si el GLB del monumento excede más del 50% la altura declarada, ajusta **sólo su primer objeto visual GLB** con escala uniforme hasta encajar en los límites declarados y lo apoya nuevamente en el suelo. No afecta click proxy, colisión ni FX; evita que el cono gigante siga tapando todo el escenario.
- `src/render/realm_builder_monument_fx.ts`: cuando sólo existe el placeholder original, oculta paneles y beams proyectados, **sin ocultar el monumento ni su servicio de premios**. En cuanto se recibe un nombre real, los paneles aparecen.
- Respaldo/rollback en `.workspace/reports/highfly-p56/backups`, privado; ejecuta P9 build. No crea assets nuevos ni publica biblioteca KayKit SOURCE.

## Código VS Code
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git status --short
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p56_editor_transform.py' -v
python3 scripts/highfly_p56_editor_transform.py
python3 scripts/highfly_p56_editor_transform.py --apply
```
Si P9 sale verde y el proceso Vite `preview` está ejecutándose en :4174, reiniciar el proceso (Ctrl+C y comando siguiente):
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
```
- Asegurar **Codespaces PORT 4174 Visibility: Private**.
- Abrir editor: `/editor.html?hf_eastbrook_studio=1`.
- Abrir juego: `/`. No activar el flag temporal `hf_probe_eastbrook_kmed=hide`.

## Pruebas manuales
1. En Editor, buscar `monument` y seleccionar BODY y `eastbrook_monument_fx` por separado, ocultar/restaurar. Verificar que el FX placeholder ya no aparece en offline.
2. Seleccionar una mini casa, corregir X/Z/Giro/Escala en el panel, aplicar, revertir, exportar el JSON. Para objetos fusionados la herramienta no puede garantizar una mutación aislada; no borrarlos sin ID.
3. En juego, el monumento debe medir aproximadamente la altura original de 7.6 unidades o menos; mantener funcionalidad click e interacción.
4. Revisar colisión real de mini casas y altura de la granja antes de generar cambios persistentes. Los cambios P56 son previews, **NO quedan guardados en mundo**.
5. Comprobar barra/carga P55 en Chrome PC y Android horizontal.

## Estado en esta conversación
- Scripts P56 y pruebas públicas escritas en la rama `highfly-origin-commercial-p0`.
- El usuario todavía no ejecutó `--apply` P56 en su Codespace, por lo que **no afirmar compilación verde, UX verificada ni corrección visual final**.
- No reemplazar la placa con un premio ficticio. La propiedad intelectual y licencia del GLB original del monumento aún requieren auditoría antes de explotación comercial.
