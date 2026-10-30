# HIGHFLY ORIGIN — Plan de ataque P2 · 30 de octubre de 2026

**Línea base congelada**: World of ClaudeCraft v0.44.7, commit `493c35a108cef6c8aa290e8793107b1cd117886e`. No incorporar otras versiones ni AnyRPG.

## Situación confirmada (no confundir la previsualización con un actor dentro del RPG)

- Colección KayKit Complete v7 del usuario reconstruida desde dos partes, CRC total OK: 23 packs y 29.358 entradas ZIP. La cifra 18.255 corresponde a archivos de formatos de modelo; NO a 18.255 personajes distintos.
- Tres packs extraídos a `.workspace/private-imports/kaykit-v7-selected`: Adventurers 2.0 (503 archivos), Character Animations 1.1 (49), Skeletons 1.1 (159). Catálogo generado: 711 archivos, 424 modelos.
- Visor privado de KayKit en ClaudeCraft v0.44.7 comprobado por el usuario en Chrome: `Knight.glb` carga, con materiales/texturas y **15 clips detectados**; `Skeleton_Minion.glb` carga y renderiza en T-pose, **0 clips embebidos**. Todavía no se demostró compatibilidad ni reproducción real de donantes de animación para el esqueleto.
- Motor RPG v0.44.7 sigue jugable en su clon de referencia; no se tocaron combate, mapas, NPC, misiones, loot, saves.
- Repositorio público solo contiene scripts, pruebas y documentación. Todos los modelos de KayKit permanecen privados en `.workspace`, sin publicación.

## Meta de progreso: un avance jugable tangible en una sesión, no solo un catálogo

### P2-A · Animación del esqueleto / comprobación de rig

1. Ejecutar `python3 scripts/highfly_probe_rig_compatibility_p2.py` desde la rama `highfly-origin-commercial-p0`. El script inspecciona el JSON de los GLB sin extraer ni reescribir modelos, lista esqueletos y posibles donantes de animación (coincidencia de nombres de nodos).
2. Identificar archivos nativos de animaciones para `Skeleton_Minion.glb`; preferir donantes del propio pack Skeletons. Validar `Idle`, caminar, correr, atacar, recibir golpe y morir de manera visual. La coincidencia de nodos no garantiza rig compatible ni animación válida.
3. Si Skeleton Minion no es retargeteable con los recursos disponibles, utilizar temporalmente otro enemigo KayKit **con animaciones probadas** sin quitar el Skeleton del catálogo; no inventar clips ni romper el GLB.

**Criterio verde**: aparece un esqueleto de pie, sin T-pose en idle, y al menos una animación locomotora y una acción de ataque verificadas en navegador. No subir modelos al repo público.

### P2-B · Catálogo jugable de personajes de KayKit

1. Tomar el pack Adventurers 2.0, enumerar los personajes reales de `Characters/gltf` y sus variantes por rig (`Rig_Medium`, `Rig_Large`).
2. Agregar un selector visual de modelos en visor privado sin duplicar scripts de motor ni comprometer las partidas.
3. Identificar un avatar temporal HIGHFLY **Hunter Universal** (sin clases), separado de las apariencias cosméticas y del árbol de habilidades; no fijar Knight como la única skin definitiva.

**Criterio verde**: distintos personajes visibles y un avatar de prueba identificado con animaciones de caminar/correr/atacar.

### P2-C · Primer modelo KayKit dentro del mundo REAL

1. Integrar **una sola variante** de personaje visible en la ruta de gráficos del clon privado, siguiendo `src/render/characters/manifest.ts`, `assets.ts` y `visual.ts`; esos componentes ya resuelven modelos y animaciones.
2. Preservar íntegramente IDs de entidades, backend, posiciones, colisiones, targeting, estadísticas, equipamiento, inventario, misiones y guardado; cambiar primero la representación visual, no la lógica sim.
3. Hacer el cambio reversible por configuración de prueba HIGHFLY; si falla la carga, se conserva el visual previo. No sustituir un modelo ajeno fuera de un sandbox privado.

**Criterio verde**: recorrer la zona existente con personaje KayKit y cámara funcional, guardar/cargar sin regresiones.

### P2-D · Enemigo KayKit, combate y loot

1. Conectar esqueleto animado a un único arquetipo enemigo de prueba, en zona segura o con combate calibrado; sin reemplazar toda la IA.
2. Verificar patrulla/aggro, recepción de daño, animaciones, muerte, persistencia de cadáver o loot contextual, incorporación de botín apilable al inventario.
3. Usar las habilidades y físicas del juego existentes como puente, sin inventar todavía el combate final MOBA.

**Criterio verde**: atacar, derrotar y lootear al enemigo; no aparecen objetos infinitos en el suelo; la partida no se rompe.

### P2-E · Mundo, escalas y HUD Mobile

1. Solo después de C y D: importar una tanda de edificios originales de Medieval Hexagon Pack y elementos Forest Nature en Eastbrook, sin destruir calles, NPC ni interiores.
2. Escalas de referencia: humanoide 1,70 m, puerta de vivienda al menos 2 m, edificios y muralla perceptiblemente mayores; mantener colisiones correctas.
3. HUD táctil horizontal S23 Ultra tipo MOBA: joystick 360° izquierda, cámara libre derecha, ATK y cuatro skills derecha, salto/dash centrales; español. Dejar como fase progresiva, no bloquear la integración inicial por estética.

## Orden de trabajo por riesgo

| Prioridad | Meta | Dependencia | Evidencia mínima |
|---|---|---|---|
| 1 | Donantes de animación Skeleton y Rig_Medium | ZIP v7 y piloto 3D | clips reproducidos correctamente |
| 2 | Selector de personajes del pack | modelos de Adventurers | navegación y cambio de skin sin crasheos |
| 3 | Un jugador KayKit dentro de Eastbrook | animación verificada | caminar, girar, atacar, guardar |
| 4 | Enemigo KayKit con drop | controlador existente y clips | matar y lootear, inventario apilado |
| 5 | Ampliar escenario/HUD S23 | 3 y 4 estables | portal y mundo sin regresiones |

## Qué NO vamos a hacer

- No reiniciar proyecto, ni clonar v0.45, ni volver a migrar a AnyRPG, ni desarmar ClaudeCraft hasta que el puente visual funcione.
- No importar los 23 packs completos al runtime de Android: la colección de fuente puede estar disponible completa, pero el build debe incorporar solo recursos usados y licenciados.
- No llamar 'personajes únicos HIGHFLY' a los modelos estándar KayKit: son recursos KayKit personalizables.
- No subir el ZIP completo, modelos privados ni build con recursos sin licencias verificadas a GitHub Pages/public.
- No prometer que la prueba de rig garantiza funcionamiento sin ver clips y combate real en S23 Ultra.

## Para retomar desde otra PC

1. Abrir el mismo Codespace `scary-troll` desde `https://github.com/codespaces`; no crear uno nuevo.
2. En terminal de repo en rama `highfly-origin-commercial-p0`: `git pull --ff-only`.
3. Ejecutar `python3 scripts/highfly_probe_rig_compatibility_p2.py` y compartir las líneas `[HIGHFLY] PRIVATE RIG P2:`. El informe detallado se guarda en `.workspace/reports/kaykit-v7/RIG_COMPATIBILITY_P2.json`.
4. Mantener puerto 4173 **PRIVATE**; para ver visor usar `/highfly-kaykit-pilot.html`.

## Estado comercial

Todos los experimentos dentro de `.workspace` son privados. Antes de una publicación HIGHFLY se debe validar la licencia/procedencia de cada modelo, textura, audio, icono y código. El origen MIT de ClaudeCraft aplica al código con sus avisos, no concede por sí solo derechos sobre todos los medios de su paquete original.
