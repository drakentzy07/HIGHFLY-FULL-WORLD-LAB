# HIGHFLY P62 — Eastbrook cierre visual sin afectar RPG

## Correcciones instalables
**El archivo P61 del usuario confirmó** 11 edificios, 2 stalls, 16 NPC, seis KayKit NPC role GLBs existentes. Ambos stalls comparten `/models/props/eastbrook_market_stall.glb`: original sha `a2d8...`, HIGHFLY provisional sha `c476a5656874884fb08a943a084d2c4a68b1f6832ddb7fbef33e62d75c628a04`.

**Licencia original:** `CREDITS.md` registra `Generated Eastbrook town kit (...) eastbrook_market_stall (...)` como `With the project only`, NO CC0. Nunca copiar los bytes del stall original, ni regenerar una copia derivada de los concept arts restringidos. El source code MIT y la licencia del modelo generado son cosas distintas.

**Solución segura:** `scripts/assets/specs/props.json` vincula `models/props/market_stand_1.glb` con `tmp/asset_src/quaternius_village/Market_Stand_1.glb`; CREDITS registra Medieval Village Pack de Quaternius CC0 1.0 Redistribución Yes. P62 valida exactamente ambas pruebas y copia la versión CC0 desde la referencia local a la ruta usada por los dos stalls. No cambia layout ni mundo original. Hash SHA-256 previo restringido a P61, no sobrescribe personalizaciones.

**NPC:** `scripts/highfly_p36_npc_visible_fallback.py` define `roleRig` comparando con `npc_knight`, `npc_smith`, etc. pero P37/P44 producen `highfly_npc_knight`, `highfly_npc_barbarian` etc. Por eso, en fallo de construcción inicial, P36 puede reintentar `player_rogue` y luego `player_warrior` independientemente de la identidad real. P62 prioriza `player_<role>` para los seis roles reconocidos; mantiene fallback de último recurso y no modifica ningún NPC sim, look, misión ni servicio. La corrección de fallback NO prueba que la construcción inicial ya sea correcta; la verificación visual sigue pendiente.

## Script y prueba
- `scripts/highfly_p62_closeout_market_npc.py` con `--apply`, protege los ficheros, respalda ambos, compila con P9 y restaura si falla.
- `tests/test_highfly_p62_closeout_market_npc.py`, cinco verificaciones de código, CC0 y seguridad.
- `.github/workflows/highfly-p62-eastbrook-closeout.yml` para checks de fuente.
- Sólo modifica stage privado (ignorado por Git): `src/render/characters/index.ts` y `public/models/props/eastbrook_market_stall.glb`.
- Stage base es P59 (P60 no requerido); no toca las modificaciones P55–P59 ni los assets P8.

## Comando
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p62_closeout_market_npc.py' -v && \
python3 scripts/highfly_p62_closeout_market_npc.py --apply
```

## Salida esperada
`Ran 5 tests ... OK`; `BUNDLE_BUILT_NOT_PLAYABLE_VERIFIED` y `P62` `BUILD_GREEN_BROWSER_PENDING`. La compilación real y la prueba visual NO se han ejecutado desde GitHub (stage privado sólo existe en Codespaces). Con verde, usar mismo preview Private puerto 4174 y recarga fuerte. Confirmar que los dos puestos parecen stands abiertos y que NPC de varios roles no son todos idénticos.

## Después: HIGHFLY COMBAT SUPREMO
Marcar Eastbrook como **baseline provisional no bloqueante**. Se mantiene lista de pendientes visuales (monumento, otros props y personajes) pero no seguir corrigiéndolos uno por uno hasta completar un hito del laboratorio de combate HIGHFLY. Prioridades: Hunter Universal, joystick 360/cámara, ataque básico 1-2-3-4, doble salto/dash/cancels, 4 skills con cooldown y aiming, combos aéreos, performance S23 horizontal. No introducir AnyRPG, no cargar assets no autorizados.

## Límites
- La solución NO declara Eastbrook 100% completo. Quedan otros modelos cuyo aspecto necesita revisión posterior.
- No puede demostrar visualmente el resultado sin ejecutar Codespace y comprobar en navegador.
- No ejecutar P60 antes de este parche; modificar el editor no soluciona el modelo usado por el juego.
