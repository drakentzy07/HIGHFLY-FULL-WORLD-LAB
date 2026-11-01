# HIGHFLY P60 — teclado Delete + mercado real de Eastbrook

## Confirmación
- P59 JSON del usuario: `highflyMicro:eastbrook_market_stall_provisions:solid`, parent `highflyMicro:eastbrook_market_stall_provisions`, modelo runtime visible a (-18.922,0.421,-107.84), 3.234×2.7×3.036, ID original `eastbrook_market_stall_provisions`.
- Segundo puesto oficial: `eastbrook_market_stall_world_market` en (-20.5,-94). Ambos están definidos en `src/sim/eastbrook_layout.ts` y usan la URL `/models/props/eastbrook_market_stall.glb`.
- Fuente original MIT revisada en commit `493c35a108cef6c8aa290e8793107b1cd117886e`: `scripts/assets/eastbrook_town/furniture.js` implementa `buildMarketStall` con postes, toldo tricolor, mercancía, mostrador, barril y sacos. Contrato en `scripts/assets/eastbrook_town/model.js`.
- El hecho de que HIGHFLY muestre una casita en lugar de un puesto sugiere una discrepancia visual; **la causa precisa aún no está demostrada** (sustituto GLB, shader/materiales, u otro factor). Comparar hashes y efectivos assets privados antes de elegir reemplazo.

## P60
- `scripts/highfly_p60_delete_market_audit.py`: solo sobre P59 stage, modifica `src/editor/highfly_eastbrook_studio.ts`. Backups, rollback Vite.
- Captura Delete y Backspace con listener de teclado en fase capture **solo cuando hay un objeto con ID estable seleccionado y el usuario no escribe en campos**.
- Ejecuta `removeVisual()` como propuesta JSON, nunca cambia mundo, servicios, collider, IA, items ni NPC. Limpia selección para siguiente clic, pero mantiene registro en catálogo para Restaurar.
- El inspector P59 ya no convierte un `highflyMicroId` estable en un ID transitorio `mesh:uuid`: selecciona el grupo fuente completo.
- Genera `.workspace/reports/highfly-p60/MARKET_ASSET_AUDIT.json` con listas de GLB original/privado, tamaño y SHA-256, sin redistribuir archivos, y estado de igualdad. Si no encuentra archivos no deduce identidad.
- Los assets de mercado de terceros que se propongan desde KayKit Complete deben verificarse contra las licencias y archivos efectivamente disponibles; NO presuponer que se incluye un stall determinado.

## Ejecutar
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p60_delete_market_audit.py' -v
python3 scripts/highfly_p60_delete_market_audit.py --apply
cat .workspace/reports/highfly-p60/MARKET_ASSET_AUDIT.json
```
Cuando build verde, reiniciar preview privado 4174, abrir `/editor.html?hf_eastbrook_studio=1`, seleccionar puesto en escena/catalogo, presionar Supr/Backspace, seleccionar otro objeto, restaurar desde catálogo o exportar JSON.

## No afirmar completado
- Script publicado y pruebas de contrato añadidas, aún no compilado en Codespace ni validado browser. El objetivo es **eliminar visualmente de la sesión y exportar propuesta**, no eliminar definitivamente un servicio.
- Cuando se conozcan hashes/asset URL y screenshot, decidir si regenerar mercado con fuente procedimental MIT verificable o usar KayKit autorizado; NO reemplazar modelos de todo Eastbrook por aproximaciones geométricas.
