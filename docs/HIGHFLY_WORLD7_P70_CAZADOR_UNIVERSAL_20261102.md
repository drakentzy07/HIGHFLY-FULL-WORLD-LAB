# HIGHFLY — WORLD 7 / P70 — Cazador Universal (núcleo aislado)

**Origen:** `highfly-origin-commercial-p0` @ `0b6183fa052f36f18188e89296bfd85bad4994ec` (P69, 2026-11-01).
**Rama de trabajo:** `highfly-world7-p70-hunter-universal-20261102`.
**Estado:** código base y pruebas preparados; **NO integrado** en el stage privado; **sin RUN**, **sin despliegue** y sin modificaciones del gameplay de la rama base.

## Hallazgo verificable

- P13 contiene `characterPreview.setClass('warrior')` como puente visual explícitamente temporal; su propia documentación reconoce que la simulación sigue en Guerrero.
- P69 instala gesto de posición sólo para `targetMode === 'position'`, por lo que `fireball` con objetivo individual no genera línea por ese camino.
- P48 verifica `p.onGround` para activar dash; la secuencia salto → dash aéreo → segundo salto no queda habilitada de punta a punta.
- El catálogo original 0.44.7 define `PlayerClass`, `ALL_CLASSES`, `ResourceType` (rage/mana/energy/focus), crecimiento de stats por clase y `AbilityDef.class`. Sustituir una cadena 'warrior' por 'hunter' no alcanza y puede romper guardado, UI, PvP o skills.
- El commit P69 sólo confirma publicación de instalador; la propia ficha de P69 dice **NO aplicado al stage privado** en ese momento.

## Entregado en esta rama

1. `pilot/highfly_hunter_universal_core_p70.mjs`: núcleo de **identidad universal, apariencia separada, cinco stats base STR/AGI/VIT/PER/INT, recursos HP/MP/Energía, 4 slots activas + 1 pasiva, skills aprendidas por adquisición, comprobación de nivel/arma/coste, cinco geometrías de apuntado y resolución de clips reales del rig**. No contiene clase ni ejecuta daño.
2. `tests/highfly_hunter_universal_p70.test.mjs`: contratos para inicio idéntico entre skins KayKit, no dar habilidades gratis al cambiar apariencia, independencia de baseStats frente a ítems, filtros de skills, aim y clips faltantes.
3. Este documento: trazabilidad y secuencia de integración.

## Reglas de diseño acordadas

**Un cazador, múltiples skins**. Knight, Mage, Rogue, etc. representan visuales/rigs, nunca ramas de progresión obligatorias. El mismo Hunter arranca con parámetros globales de stats, nivel y recursos sin depender del rig elegido. Todo avatar persistente necesita un ID estable y guardado propio.

**REUSE FIRST, legal**. Reutilizar código MIT verificable y animaciones/models CC0/propios compatibles. Revisar licencia y atribución de cada clip original antes de redistribuir comercialmente, sin copiar recursos privados no autorizados. Sin placeholders geométricos.

**FURY físico**. ATK no es una skill ni un recast; el daño sólo se crea por evento autorizado en `Sim`. Movimiento 360° y cámara son independientes. El input de salto/dash debe ser por eventos de pulsación consumibles, no por estados mantenidos que accidentalmente se pierden o duplican.

## Próximas integraciones, por dependencia (NO realizadas)

| Bloque | Integración | Criterio |
| --- | --- | --- |
| P70-A | Lectura privada de stage (manifiesto, clips GLB actuales, versión aplicada de P68/P69, guardado) | Reconciliar estado real, no asumir que publicar equivale a aplicar |
| P70-B | Adaptador `legacyClass` **interno**, con perfil Hunter y stats universales como fuente de verdad; UI un solo personaje y skins | Ningún cambio de skin altera baseStats, nivel, skills o progresión |
| P70-C | Reglas de habilidades y equipos sin `AbilityDef.class` en el dominio HIGHFLY; traductor de habilidades originales autorizadas | Fireball aprendible en cualquier skin; costes MP, energía física, HP; migración de guardado reproducible |
| P70-D | Adaptador de animación KayKit por rig y arma, con inventario real de clips cargados | Sin errores por animaciones inexistentes y sin suponer que el clip genera la mecánica |
| P70-E | FURY input/physics: joystick 360, dash suelo/aire controlado, salto→dash→salto, mortal direccional, ATK1–4, cancel windows | Eventos de una sola pulsación, colisiones reales, sin teleport ni doble daño |
| P70-F | Aim de line/cone/circle/target/self con preview y cancelación, servidor autoritativo donde aplique | Fireball y skills cuerpo a cuerpo comparten gesto, geometría según skill |
| P70-G | Validación PC/S23 y regresión RPG total | NPC, misiones, portal, loot, bolsa, inventario, guardado, editor no se rompen |

## Probar el núcleo aislado

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git fetch origin highfly-world7-p70-hunter-universal-20261102
git switch highfly-world7-p70-hunter-universal-20261102
node --test tests/highfly_hunter_universal_p70.test.mjs
```

Este test **no prueba una build Vite ni Android**. Una vez que P70-B/P70-F tengan adaptadores privados y TypeScript compile, validar in situ y hacer PR controlado hacia la rama jugable. **No ejecutar instaladores P69/P70 hasta confirmar el stage**.

## Riesgos expresos

- Reutilizar `warrior` como *adaptador de transporte temporal* no hace que la identidad HIGHFLY dependa de Guerrero; quitarlo sin atender tipos, skills y guardado sería irresponsable. El adaptador debe eliminarse gradualmente, con gates reales comprobados.
- El sistema original usa estadísticas distintas (str/agi/sta/int/spi) y recursos particulares por clase; STR/AGI/VIT/PER/INT y HP/MP/Energía necesitan **mapeo y recalibración declarados**, no equivalencias asumidas.
- Un clip sin retarget, raíz compatible, huesos esperados o derechos claros no se incorpora.
- No migrar partidas antiguas ni sobrescribir progreso sin backup/verificación de checksum y rollback.
