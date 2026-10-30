# HIGHFLY ORIGIN P6 — proteger sistemas RPG e importar KayKit Medieval Hexagon

Base: World of ClaudeCraft v0.44.7, commit 493c35a108cef6c8aa290e8793107b1cd117886e. Rama de trabajo: highfly-origin-commercial-p0.

## Garantías de la etapa actual

El P0 conserva 5.314 archivos de código en la etapa independiente privada. P4 añadió modelos visuales Knight y Skeleton sin alterar el motor sim ni partidas. No se han borrado las reglas de inventario, equipamiento, loot, enemigos o misiones. Los recursos originales faltantes en HIGHFLY sí impiden afirmar que ya exista una versión independiente jugable.

P6 compara byte a byte los archivos críticos de ambas copias:
- Motor y datos; inventario; loot y cadáveres.
- Equipamiento y armaduras.
- Ciclo de vida de monstruos.
- Misiones y recompensas.
- Definición del mapa Eastbrook.

Además indexa los packs que contiene el ZIP original de KayKit Complete V7: edificios, biomas, dungeons, muebles, armas, RPG Tools, personajes, esqueletos y animaciones. Genera informe privado; no copia recursos.

## Terminal 2 del mismo Codespace

Ejecutar:

~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p6_rpg_and_world_packs.py'
python3 scripts/highfly_p6_rpg_and_world_packs.py
~~~

Confirmar salida P6 CORE PRESERVATION OK antes de extraer modelos. Si hay errores, parar y revisar.

## Extracción del primer pack de edificios (solo después del P6 verde)

Si la carpeta de Medieval Hexagon aún NO existe en la colección extraída, usar:

~~~bash
python3 scripts/highfly_kaykit_zip_intake.py \
  .workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip \
  --pack "KayKit Medieval Hexagon Pack 1.0.1" \
  --extract \
  --destination .workspace/private-imports/kaykit-v7-selected
~~~

Esta acción solo extrae material de KayKit al Codespace privado. No lo importa a HIGHFLY ni lo publica. Si ya existe el pack, no intentar extraer encima porque el script protege contra sobreescritura.

## Hitos siguientes

Primero mapear edificios de Eastbrook a modelos Medieval Hexagon verificados, conservando IDs, escala de puertas, colisiones, interiores y anclajes de NPC. Después integrar vegetación y mundo exterior, enemigos variados, NPC, loot, armas, armaduras y recursos multimedia necesarios, sin perder el RPG completo. Construir la versión HIGHFLY privada y probar el circuito de jugador, combate, cadáver, inventario y guardado. Finalmente completar Hunter Universal, skins Adventurers, editor futuro hombre/mujer, movimiento y HUD Android horizontal.

La licencia MIT del código no autoriza automáticamente todos los archivos de la carpeta public del juego original. Solo introducir multimedia verificada, mantener el puerto privado y bloquear publicación hasta auditoría completa.
