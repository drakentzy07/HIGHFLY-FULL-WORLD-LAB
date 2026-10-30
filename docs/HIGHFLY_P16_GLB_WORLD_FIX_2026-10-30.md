# HIGHFLY P16 — Reparación del mundo a partir del KayKit propio

## Diagnóstico de las capturas del 30/10/2026
El navegador muestra la portada heredada, las nueve clases y un Knight invisible en el creador; el juego alcanza el loading y falla por múltiples modelos GLB: kcas_*, hexr_*, modelos de interiores de mazmorra, etc.

Se identificaron **dos causas distintas de carga**: (1) las equivalencias originales entre nombres GLB de ClaudeCraft y nombres del kit KayKit estaban en los JSON MIT de construcción del mundo, pero P12 no las utilizaba, y (2) `src/render/assets/media.ts` en producción resuelve recursos mediante un `manifest.generated.ts` con hashes originales inexistentes en HIGHFLY, incluso si ya hemos instalado modelos KayKit en public/.

Hay además un posible tercer bloqueo visual: el bridge del personaje P4 conservaba `attach` y `weaponSlots` de Warrior, referenciando arma y escudo del original, y el preview P13 seguía usando las armas iniciales de la clase. Este parche desliga dichos accesorios originales **solo visualmente y provisionalmente**, conservando intacta la simulación.

## Qué hace P16
- Lee de la referencia fijada los archivos `scripts/assets/specs/drakelands_castle.json`, `gale_harbor.json` y `dungeon.json` y sus pares exactos `src` KayKit/`out` HIGHFLY. No copia ningún GLB multimedia del original.
- Convierte los modelos correspondientes del ZIP KayKit Complete V7 privado mediante la herramienta P12 con sus comprobaciones de ZIP, GLB y no sobrescritura.
- Aísla el render provisional del Knight respecto de las referencias originales a espada y escudo. El inventario, estadísticas, movimiento, combate, loot y sistemas RPG siguen intactos.
- Hace que `assetUrl` en la build HIGHFLY privada busque `/models/...` de la carpeta `public/` **sin usar los hashes de la biblioteca original**.
- Audita algunas rutas de modelos usadas por el render y compila Vite privado. Reporta los faltantes y **no afirma que el mundo esté jugable**.

## Terminal 2 — después de detener el servidor 4174 con Ctrl+C

    cd /workspaces/HIGHFLY-FULL-WORLD-LAB
    git pull --ff-only && \
    python3 -m unittest discover -s tests -p 'test_highfly_p16_kaykit_spec_repair.py' && \
    python3 scripts/highfly_p16_kaykit_spec_repair.py --apply

Informe: `.workspace/reports/highfly-p16/P16_SPEC_KAYKIT_REPAIR.json`.

### Para volver a probar
    cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
    node ../claudecraft-v0.44.7/node_modules/vite/bin/vite.js preview --host 0.0.0.0 --port 4174 --strictPort

Puerto Codespaces 4174: PRIVATE; en la raíz `/` entrar a Offline para probar Knight y carga del mundo.

## Criterios de aceptación pendientes
Render visible del Knight; al menos un área de Eastbrook sin carga bloqueada; rutas GLB identificadas por disponibilidad efectiva; colisiones y escala coherentes; monstruos, NPC, combate, loot, inventario y guardado realmente probados. Las URL generadas dinámicamente no siempre están cubiertas por el escaneo estático. Mantener MIT y CC0/Apache con sus avisos y no publicar assets sin permisos.

## Notas
El logo HIGHFLY provisional aparece en la carga, pero textos de la portada y categorías del personaje todavía corresponden a la UI antigua. P16 prioriza que el motor encuentre correctamente el mundo y el personaje antes del rediseño completo de menús/HUD. Aun con Vite verde, los assets aún no encontrados en KayKit siguen siendo una tarea concreta de mapeo/creación.
