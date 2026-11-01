# HIGHFLY WORLD RPG FITNESS — P66+P67 integrado

## Observación del video (01/11/2026)
- Logo y splash excelentes; progreso, consejos y barra cruzan el arte; la carga no se percibe como una interfaz integrada.
- Menú cuadrado con botones funcionales, aunque acabado visual genérico.
- HUD de combate con controles demasiado heterogéneos y círculos secundarios de habilidad vacíos.
- El movimiento del cazador gira la cámara. Al presionar ATK no aproxima ni orienta lo suficientemente bien.
- El joystick izquierdo debe dirigir únicamente al personaje; gesto derecho sigue siendo cámara independiente.

## Implementado en GitHub, pendiente de instalar y probar en Codespaces
`scripts/highfly_p66_p67_premium_combat.py` + regresión `tests/test_highfly_p66_p67_premium_combat.py` (11 pruebas definidas). Este paso actúa sobre la versión privada `P65` que el usuario verificó como `BUILD_GREEN_BROWSER_PENDING` y hace un único build/rollback.

### P66: HUD e intro
- CSS propio en `public/highfly/p66_p67_premium.css` sin duplicar botones ni alterar callbacks.
- Progreso real de carga y consejo en una banda inferior translucida violeta, la imagen HIGHFLY se conserva y no se reemplaza por un logo ficticio.
- PASIVA, SALTAR, EVADIR y S1 sobre la misma línea, igual diámetro y separación. ATK principal permanece destacado, el icono/cooldown de S1 es real.
- Menú cuadrado existente: mejor borde, sombras, tipografía, iconos y rejilla. Los botones siguen invocando sus APIs originales.
- Pantalla completa del navegador sujeta a permiso por gesto (P48). CSS por sí solo no puede ocultar el chrome del browser.

### P67: movimiento, cámara y combate
- `updateCamera()` deja de forzar al modo táctil a seguir el cuerpo del personaje en juego activo; mantiene arrastre táctil derecho, pinza de zoom y el recentrado existente.
- La orientación al tocar ATK y tener objetivo vivo hostil frente a uno aplica `facing` mientras no hay movimiento manual.
- `onWorldTap` y `attackNearest` invocan `highflyApproachEnemy`: aproximación opcional de hasta 15 unidades, con el pathfinding ya existente, distancia final 2,6, sin teletransporte ni desactivar obstáculos. Fuera de rango solo selecciona y arma autoataque.
- El motor de click-to-move ya cancela la aproximación si recibe movimiento manual del joystick, si se habilita mouselook o si el jugador está muerto. La habilitación temporal es específica del ID de entidad iniciado por ATK.
- P65 mantiene movimiento 360 relativo a la cámara. P63 mantiene el combo de daño real y P64 el jabalí animado.
- **No se implementó aún el nuevo combate de ataques individuales instantáneos por tap, blending de animaciones, cancel windows ni combo aéreo**; se mantiene como siguiente trabajo, no se afirma que ya exista.

### Editor HIGHFLY (respuesta al usuario)
P55–P58: selección, arrastrar/mover, girar/escalar, ocultar, restaurar, «Quitar (borrador)», guardar borradores en localStorage y exportar JSON. No realiza eliminaciones persistentes de colisiones/quest/props en el juego y no incorpora por ahora catálogo de colocación de nuevos elementos. Para los conos y tulipanes, seleccionar, ocultar y exportar propuesta con ID; luego revisar la fuente antes de aplicar al mundo.

## Comando de Codespaces
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p66_p67_premium_combat.py' -v && \
python3 scripts/highfly_p66_p67_premium_combat.py && \
python3 scripts/highfly_p66_p67_premium_combat.py --apply
```
El installer declara `BUILD_GREEN_BROWSER_PENDING` solo si la compilación Vite P9 devuelve exitCode=0; tests unitarios sintéticos no garantizan runtime real Android. Si algo falla antes de editar o durante la compilación, se bloquea o revierte a P65 sin borrar modelos originales.

## QA requerida
Ver en Galaxy S23 Ultra en horizontal: 1) intro sin texto encima del logo; 2) 4 controles con tema uniforme, S1 ejecuta la skill real; 3) menú `...` abre acciones; 4) joystick permite girar/retroceder sin girar la cámara; 5) derecho gira cámara sin movimiento; 6) toque monstruo y ATK orientan, aproximan hasta 15 unidades, se detienen a distancia y ceden inmediatamente a joystick; 7) loot/quests/saves intactos. Documentar latencia y posibles glitches de auto-cam.
