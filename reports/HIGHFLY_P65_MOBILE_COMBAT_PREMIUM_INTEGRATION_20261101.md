# HIGHFLY WORLD RPG FITNESS — P65 Mobile Combat C2 + HUD Premium

## Estándar de identidad
El producto es **HIGHFLY WORLD RPG FITNESS**. El proyecto integra únicamente código MIT/CC0/activos licenciados de distintas fuentes externas. Ningún nombre o marca externa identifica el juego HIGHFLY.

## P65 integrado en un solo instalador privado
`scripts/highfly_p65_mobile_combat_hud_c2.py`
`tests/test_highfly_p65_mobile_combat_hud_c2.py`

Instalador incremental sobre el P64 verde, con preflight de la base original PINNED, protección de fuentes RPG, validación de anclajes únicos, copias de seguridad y rollback si Vite falla. Parches SOLO en stage Codespaces ignorado; GLBs propietarios no se añaden al repositorio público.

**Cambio de UI:**
- Pantalla de carga Android usa `100dvh`, cover y safe areas. La barra de navegación física y el chrome del navegador **no pueden ocultarse automáticamente sin gesto**; P48 ya intentaba `requestFullscreen` en el ingreso.
- HUD HP/MP/energía renderizado por el `#player-frame` original, reubicado al vértice superior izquierdo, nunca reemplazado por números falsos.
- Tres puntos `#mobile-menu-anchor` debajo del HUD, ahora abre directamente el **panel cuadrado centrado** `#mobile-extra-controls` con sus callbacks reales: bolsas, personaje, mapa, skillbook, misiones y opciones. El viejo launcher lineal por gesto se desactiva solo en este shell.
- Nuevo botón **PASIVA** abre el spellbook de verdad; NO lanza una pasiva (las pasivas no se castean ni tienen uso activo). Slot de skill activo S1 es el botón de acción real `data-mobile-index=0` con cooldown del motor. SALTAR conserva `onJump`; EVADIR conserva `input.triggerTouchDash` P48 y colisiones. ATK conserva el motor P63.
- Afinación visual azul/cian/violeta. Se ocultan enlaces externos de la interfaz heredada para no confundir HIGHFLY.

**Cambio de jugabilidad:**
- `MobileControls` detecta tap corto en canvas que NO sea gesto de arrastre ni selección de retícula, llama a callback opcional `onWorldTap`. `main.ts` usa `renderer.pick(x,y)` con entidad realmente atacable y `world.targetEntity` + `world.startAutoAttack`; no daño falso, no campos invisible de ataque. Botón Target sigue disponible para cambiar blanco.
- `resolveMove` en dispositivo `body.mobile-touch` convierte adelante/atrás/laterales del joystick en vector relativo a `input.camYaw`, orienta `facing` con `atan2` y emite avance, sin backpedal. No toca la física ni modifica desktop, mobs, loot o quests. Necesita prueba real en móvil para verificar que cámara libre y giros sean cómodos.

**La C2 NO es Combat Supremo final.** Siguen pendientes: cancelar frames de combos, ataque instantáneo por tap, buffering, remates aéreos, lock-on opcional con rango/LoS, skills encadenadas, VFX finales, rig pasivo equipable y FPS estables en S23 Ultra.

## Objetos raros en el mapa
El editor privado P55-P59 puede seleccionar y ocultar piezas visibles, generar borrador JSON y devolverlas. Para retirar permanentemente `eastbrook_realm_builder_monument`, `eastbrook_monument_fx`, picos, cajas, vegetación o decoraciones desconocidas hay que auditar **ID, fuente legal, colisión y función** de cada pieza; la geometría de roca/campana puede ser cobertura de interacción, por lo que no se borra a ciegas. Mantener esto como backlog visual después de pruebas C2.

## Ejecutar una sola vez
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p65_mobile_combat_hud_c2.py' -v && \
python3 scripts/highfly_p65_mobile_combat_hud_c2.py && \
python3 scripts/highfly_p65_mobile_combat_hud_c2.py --apply
```

Resultado requerido antes de reclamar éxito: P65 `BUILD_GREEN_BROWSER_PENDING`, P9 exitCode=0, luego prueba en preview privado puerto 4174 en landscape Samsung S23 Ultra. Las pruebas sintéticas NO sustituyen prueba end-to-end de acciones y controles.
