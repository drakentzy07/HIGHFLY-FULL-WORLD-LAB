# HIGHFLY P58 — Eastbrook micro-objetos seleccionables

## Motivo
Capturas del usuario tras P57 muestran monumento alto reducido, posibilidad de ocultarlo y seleccionar/mover `decor:kmedBlacksmith@2,-112`, pero las mini casitas y otro cono no se pueden elegir individualmente.

## Evidencia del original 0.44.7
`src/render/eastbrook_town.ts` `buildMicroBatches` fusiona bancos `EASTBROOK_LAYOUT.civic.benches`, puestos `EASTBROOK_LAYOUT.market.stalls` y vallas `EASTBROOK_LAYOUT.fences` en sólo dos mallas estáticas, opaca y emisiva. Estas mallas **no tienen ID por instancia**, por lo que el raycast de P57 no puede elegir un puesto/objeto individual. Esto explica una categoría concreta de elementos no seleccionables, pero las mini casitas exactas todavía deben confirmarse en el navegador: no suponer que todas son puestos.

## P58
- Script `scripts/highfly_p58_individual_micro_editor.py`, sobre stage privado P57 compilado.
- Sólo con `?hf_eastbrook_studio=1`, divide las geometrías antes fusionadas en grupos con nombre `highflyMicro:<id>`, conservando URL del modelo y coordenadas originales.
- El juego normal conserva fusión, colisiones, IA, misiones, servicios, guardado y optimización.
- Editor 2.0: agrega los bancos, puestos y vallas a la búsqueda; clic directo por ID.
- Nuevo botón **Quitar (borrador)**: retira visualmente de la escena del editor y registra `remove_visual_proposal`, `requiresColliderReview:true`. **NO altera colisiones ni borra definitivamente**.
- **Guardar borrador + JSON** registra estas propuestas para que el usuario comparta el archivo y se convierta en un parche validado del mundo.
- Backups privados de dos archivos. Rollback ante fallo Vite; intentos previos conservados en histórico.
- El cono pequeño puede ser una parte independiente del FX del monumento; buscar `eastbrook_monument_fx` y ocultarlo por separado antes de intentar quitarlo del proyecto.

## Ejecutar una sola vez
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p58_individual_micro_editor.py' -v
python3 scripts/highfly_p58_individual_micro_editor.py
python3 scripts/highfly_p58_individual_micro_editor.py --apply
```

Si P9 compila verde, reiniciar Vite preview puerto 4174 privado, abrir `/editor.html?hf_eastbrook_studio=1`; buscar `eastbrook_market_stall`, probar selección, mover, quitar, restaurar, guardar JSON y compartir. Evitar botón **Guardar** del editor clásico porque guarda mapa distinto, no BUILTIN_WORLD. No eliminar IDs funcionales sin revisión de fuente.

## Estado
Scripts/test/report publicados. No existe evidencia aún de compilación P58 ni pruebas manuales PC/Android; no afirmar que todas las mini casitas estén identificadas o resueltas.
