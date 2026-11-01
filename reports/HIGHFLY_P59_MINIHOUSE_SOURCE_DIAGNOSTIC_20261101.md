# HIGHFLY P59 — Diagnóstico de las mini casitas de Eastbrook

## Hallazgo confirmado
El usuario probó P58: «quita el objeto pero no la mini casita». Por tanto, el objeto ocultado y la mini casa **son mallas diferentes**. No hay pruebas de que compartan el ID del objeto vecino ni de que sean un puesto del mercado.

## Fuente revisada
- Original ClaudeCraft v0.44.7, commit 493c35a108cef6c8aa290e8793107b1cd117886e.
- `src/render/eastbrook_town.ts`: `buildMicroBatches` fusiona bancos, puestos y vallas; P58 separa esas categorías sólo en el editor.
- `src/render/props.ts`: `activeContent.props.buildings` y `decorProps` se generan por otra ruta, que puede tener grupos/mallas sin identificadores estables. Existen más rutas de objetos en `src/render/renderer.ts`.
- No atribuir la mini casita a ninguna ruta sin un raycast registrado.

## P59: inspector de selección
- Instalador `scripts/highfly_p59_minihouse_trace.py` y pruebas `tests/test_highfly_p59_minihouse_trace.py`.
- Modifica únicamente TS/CSS del editor privado P58. No toca simulación, colisiones, personajes, items ni assets.
- Botón «🔎 Identificar casita: siguiente clic» habilita diagnóstico de raycast de 9 posiciones de pantalla.
- Captura geometría real, material, jerarquía, punto/centro, dimensiones, nombres de ancestros, `userData`, categoría, e IDs cercanos **sólo como proximidad**.
- El botón «Descargar diagnóstico de casita» genera `HIGHFLY_P59_CASITA_SOURCE_LOG.json`, para adjuntar al chat.
- Si una malla es pequeña, no fusionada y pertenece a props, permite seleccionarla para ensayo de ocultación visual. El `mesh:uuid` provisional **no es ID persistente**.
- Copias privadas y rollback automático ante fallo del build; no aplicar propuestas al mapa hasta revisión del diagnóstico.

## Procedimiento VS Code
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p59_minihouse_trace.py' -v
python3 scripts/highfly_p59_minihouse_trace.py --apply
```
Si verde, reiniciar servidor de preview en el stage privado, puerto 4174 con visibilidad Private. Abrir `/editor.html?hf_eastbrook_studio=1`, pulsar «Identificar casita», hacer clic exactamente sobre la casita, descargar JSON y adjuntarlo.

## Estado
Publicación de script/tests; el usuario todavía debe probar `--apply`/Vite y el navegador. No afirmar que la mini casa fue solucionada hasta recibir el diagnóstico.
