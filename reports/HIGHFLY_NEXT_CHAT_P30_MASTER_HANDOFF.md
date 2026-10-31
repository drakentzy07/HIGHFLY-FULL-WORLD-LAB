# HIGHFLY ORIGIN — TRANSFERENCIA AL CHAT NUEVO / AUDITORÍA MAESTRA P30

**Fecha:** 31/10/2026. **Repositorio:** `drakentzy07/HIGHFLY-FULL-WORLD-LAB`, rama `highfly-origin-commercial-p0`.
**Codespaces:** `/workspaces/HIGHFLY-FULL-WORLD-LAB`.
**Original analizado:** `levy-street/world-of-claudecraft` v0.44.7, commit fijado `493c35a108cef6c8aa290e8793107b1cd117886e`, copia en `.workspace/claudecraft-v0.44.7`.
**Stage:** `.workspace/highfly-origin-stage-p0`.
**Colección propia (NO publicar su ZIP):** `.workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip`.

## Decisiones irrevocables de producto
- SOLO el personaje del jugador es **Hunter Universal**. Sin clases ni especializaciones jugables. Aprende habilidades físicas/mágicas mediante compras, misiones, drops y fusiones. Equipar no crea otra clase.
- NPC de ClaudeCraft conservan **sus propios ID, nombre, diálogo, misión, profesión, comercio, posición, facción, IA y movimiento**. El cuerpo/ropa/accesorios visuales se recuperan de nuestro KayKit Complete SOURCE V7 (o recursos externos legalmente válidos) **sin homogeneizarlos**.
- Ejemplo verificado en el manifiesto original: `brother_halven`/Reliquary Keeper usa `npc_reliquary_keeper` -> `models/chars/players/paladin.glb`; `npc_smith` -> `models/chars/players/barbarian.glb`; los NPC modulares usan `models/chars/modular/warrior_modular.glb` más el mapa individual `npc_looks.ts`.
- Conservar por separado todos los monstruos, especies/IA, tablas de loot, armas, armaduras, ítems, zonas, barcos, misiones, dungeons, interfaces, habilidades, equipamientos, animaciones.
- Mantener recursos CC0 genuinos ya válidos, incluidos Quaternius, Kenney, ambientCG, Poly Haven, loafbrr y otras fuentes verificadas. **KayKit SOLO de nuestro Complete SOURCE V7**, no volver a usar importaciones FREE viejas como fuente.
- Código MIT de ClaudeCraft ≠ licencia MIT de todo su arte. Los medios `With the project only`, `No, permission required` y sin registro necesitan revisión; no copiarlos automáticamente a HIGHFLY independiente.

## Estado comprobado antes de P30
- Mundo ya **ENTRA Y SE PUEDE MOVER** en Codespaces preview 4174 (capturas del usuario 31/10).
- Sistema de misiones/diálogos/HUD/minimapa aparece; NPC y jugador no están visiblemente restaurados en las pruebas.
- P21 recuperó 48 assets CC0. P22 generó 249 GLB temporales más otros recursos para salvar el arranque.
- P26 restauró 3 GLB originales CC0 y P23 convirtió 6 desde KayKit SOURCE V7: **240 GLB temporales seguían pendientes**.
- P28 generó 11 imágenes originales de materiales/carga; la pantalla de arranque dejó de bloquear la entrada.
- Al recorrer el mundo surgieron **48 rutas dinámicas fallidas**: 33 KTX2 de variantes, 9 GLB VFX, 4 KTX2 VFX, 1 modelo dummy y 1 loading art. No significan que NPC o skills no tengan lógica.
- P29 pasa 8 tests; la primera medición `actorModelsPresent: 0` era **incorrecta en varias rutas**, ya que buscaba `models/chars/knight.glb` en lugar de `models/chars/players/knight.glb`. Corregido en Github; hay que repetir auditoría, no interpretar el viejo 0/7.
- No asumir que una compilación `exitCode 0` demuestra juego completo/seguro/legal.

## Auditoría maestra nueva P30
`scripts/highfly_p30_master_original_world_inventory.py`
`tests/test_highfly_p30_master_original_world_inventory.py`

Inspecciona el árbol completo `public/` del original, los archivos `src/`, manifiestos `scripts/assets/specs/*.json` (src->out), CREDITS.md, tabla NPC_KEYS, NPC_LOOKS, modelos y animaciones, registros de NPC/mobs/ítems/loot/equipamiento/quests de `src/sim/content`, los packs KayKit SOURCE, archivos actuales del stage y rutas observadas en logs.

**17 categorías:** NPC, loot, armas, armaduras, monstruos, personajes, edificios, estructuras, vegetación/fauna, ítems, agua/lava/tierra/clima, barcos, interacciones/movimiento, menús/HUD, habilidades/VFX, audio, otros.

Salida en `.workspace/reports/highfly-p30-master/`:
- `P30_MASTER_SUMMARY.json`
- `P30_ALL_MEDIA_AND_USAGE.csv` — cada asset, fuente/especificación, cita de licencia, uso en código, estado del stage y candidato KayKit por nombre.
- `P30_EVERY_NPC_AND_VISUAL.csv` — identidad NPC -> visual, cuerpo, animaciones y apariencia.
- `P30_SIM_NPC_MOBS_ITEMS_LOOT_QUESTS.csv` — NPC, mobs, quests, ítems, coords literales y nombres. Mapear casos calculados manualmente.
- `P30_EVERY_SOURCE_SYSTEM.csv` — módulos reales de simulación, render, interacciones, menús y pipelines.

**P30 es una auditoría ESTÁTICA y READ ONLY**. No demuestra todos los spawns de runtime, los equipos con nombres dinámicos, compatibilidad de rigs o licencia de un archivo no registrado. Da pista exacta cuando existe y señala lo no resuelto; jamás inventar un match visual ni dar el mundo como 100% auditado sin pruebas.

## Primer comando en el chat nuevo

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p30_master_original_world_inventory.py' && \
python3 scripts/highfly_p30_master_original_world_inventory.py && \
python3 scripts/highfly_p29_actor_skill_vfx_audit.py
```

Pedir el resultado `[HIGHFLY] P30 MASTER AUDIT` y `[HIGHFLY] P29 AUDIT`. Si P30 falla, corregir el script, volver a correr tests; no volver a generar placeholders.

**Próxima fase:** convertir P30 en matriz de cambios visuales 1:1 (NPC primero), con verificación de rigs/animaciones/texturas, luego dummies y VFX; después loot/armas/armaduras/monstruos, edificios y mundo. Preservar tabla y lógica sin tocarlas. Construcción privada y prueba de navegador tras cada lote.

