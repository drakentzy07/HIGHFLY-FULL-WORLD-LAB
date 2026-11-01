# HIGHFLY WORLD RPG FITNESS — P68 FURY GOLDEN Recovery / True-360 + Art Audit
Fecha: 2026-11-01

## VIDEO S23 (2m33s, 1030×480)
- Splash HIGHFLY casi perfecta, progreso funcional, pero el texto del consejo se pega a la izquierda fuera del panel central; P66 no lo corrige.
- HUD más coherente que P65, pero PASIVA y EVADIR rompen la temática: material, iconos, colores y distancias distintos; más botones de skills vacíos.
- El cazador navega al bosque y se enfrenta a lobos reales, con cadavres y loot en la simulación; combate aún auto-hit del antiguo sistema, no FURY 4 pulsaciones.
- Joystick circular dibujado, pero conversión a cuatro flags `TouchMoveInput` que produce ángulos de ocho direcciones. P65 además invirtió la fórmula de strafe lateral: para un toque a derecha y cameraYaw=0, `worldX=-1` cuando debería ser `+1`. Ambos causan diagonales torpes.
- La cámara ya no sigue automáticamente al cuerpo en móvil gracias a P67.

## P68: parche funcional escrito en GitHub
Archivos:
- `scripts/highfly_p68_fury_golden_recovery.py`
- `tests/test_highfly_p68_fury_golden_recovery.py`

Sólo modifica el stage privado derivado de P67, con backup/rollback. No publica recursos comerciales ni altera NPCs, colisiones, skills, IA, quests, loot ni motor de daño.

Acciones:
1. Añade campos `analogX/analogY` opcionales a `TouchMoveInput` y getter normalizado con deadzone. `mobile_controls.ts` pasa los vectores reales del dedo a `Input`, preservando flags nativos por compatibilidad.
2. Reemplaza el cálculo P65 de orientación por vector continuo relativo a cámara: `worldX=forward*sin(yaw)+right*cos(yaw)`, `worldZ=forward*cos(yaw)-right*sin(yaw)`, sin tocar `camYaw`. Corrección crucial de signos para derecha/diagonales.
3. Si ATK no tiene auto-ataque válido, invoca `attackNearest` del motor de HIGHFLY; no requiere marcar enemigo a mano. Reduce el área de adquisición de 40 a 15 unidades, conservando filtros existentes `isAttackableEntity` y navegación P67.
4. Coloca estado, barra y consejos en una rejilla centrada y evita que el consejo vuelva a quedar al extremo izquierdo.
5. Unifica acabado del grupo PASIVA, SALTAR, EVADIR, S1 y de las opciones del menú sin duplicar callbacks.
6. El sistema de daño P63 (4.º impacto 1.28), Gobkit P64, Cámara libre P67 siguen intactos.

## Material FURY histórico verificado para el siguiente bloque
- Repositorio `drakentzy07/cobalt-hollow-lab`, rama `highfly-rebirth-fury360-engine-20261022`:
  `fury360/src/fury_core.ts`: `acceptGoldenMovement`, `FuryAimGesture`, `pickFuryTarget`, `FuryComboClock`.
  `fury360/src/physical_combat.ts`: `FuryPhysicalCombatTimeline`, `planFuryAttackFacing`, `furySecondJumpVisual`, `furyPhysicalDashCue`.
  `fury360/src/skill_gestures.ts`: `FurySkillTouchController` con gesto press/drag/release/cancel, cursor actual y camera yaw sin manipular la física.
- Repositorio `drakentzy07/cobalt-hollow-lab`, rama `highfly-origin-v020-art253-fury-p4b-unified-20261028`:
  `origins/v020/fury/fury_core.ts`, `origins/v020/fury/patch_fury.mjs`, `origins/v020/mobility/fury_mobility.ts`.
- Historial F2.6/F2.6.2: fireball curvo, doble arma, mortal direccional, ataque móvil/aéreo; fuente de entregas previas, **no declararlo conectado al mundo actual** sin validar compatibilidad.
- Plan: P69 recuperar FURY F1 (apuntado de skills drag/soltar, raycast terreno, cancelar X) **sobre los skills nativos**; P70 F3 golpes individuales y combo con golpes reales autorizados, bonificación por mortal/dash solamente cuando el estado físico sea verificado; P71 biblioteca de skills, catálogo personal, VFX, selector personajes y UI.

## Íconos recuperados
`drakentzy07/cobalt-hollow-lab` rama `highfly-origin-v020-art253-fury-p4b-unified-20261028` contiene `origins/v020/art/MANIFIESTO_253.json` (253: 152 skills y 101 items), `origins/v020/art/overlay/public`. Los recursos no están automáticamente ligados a la build P67, y el catálogo declara `GENERADO_PENDIENTE_QA_ARTISTICA`. Tras verificar hash, especie/slot y derechos de cada uno, integrar a la biblioteca comercial-safe sin copiar imágenes de licencia restringida.
- El editor P55/P56/P57/P58 aún sólo permite seleccionar, mover, rotar, escalar, ocultar, restaurar y exportar borradores; no añadir ni borrar persistente del runtime.

## Operación privada
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p68_fury_golden_recovery.py' -v && \
python3 scripts/highfly_p68_fury_golden_recovery.py && \
python3 scripts/highfly_p68_fury_golden_recovery.py --apply
```
Preflight/dry run antes de aplicar. Sólo si el stage realmente compila Vite se emite `BUILD_GREEN_BROWSER_PENDING`. La interfaz, 360 real y targeting deben probarse después en S23 Ultra; test sintético no demuestra playability.
