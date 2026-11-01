# HIGHFLY WORLD RPG FITNESS — P69 FURY CORE / Plan de Integración Real

Fecha: 2026-11-01. Estado **escrito y publicado en GitHub, NO aplicado al stage privado de Codespaces**.

## Decisiones aprobadas
- Hunter Universal: un único personaje persistente, sin obligarlo a una clase. El core RPG heredado puede mostrar «Guerrero» temporalmente mientras se migra el modelado de clases, NO se presenta como concluido.
- **ATK básico físico por pulsación**, sin habilidad/casteo/recast, sin magia, ni barra de carga. Cada tap = intención de un impacto físico real, con ventana de 0.25 s y buffer de entrada; el sim valida la legalidad y aplica el daño únicamente a través de `tryPlayerSwing` -> `meleeSwing`. El contador de cuatro golpes y 1.28x cuarto impacto sigue siendo la implementación P63 para golpes conectados.
- Multitáctil: pulgar izquierdo mueve; pulgar derecho mueve cámara; los dedos que pulsan/arrastran skills no roban cámara/joystick.
- Dash según dirección que esté aplicando el joystick; caída/obstáculos siguen pasando por barrido de colisiones P48. No inventar teletransporte ni dash sin colisiones.
- Soft-target 360: priorizar objetivo vivo hostil seleccionado si cumple reglas y radio; de lo contrario el más cercano dentro de 15u sin orientación manual obligatoria. No copiar IDs falsos.
- Habilidades no cargadas: mantener → arrastrar → retícula REAL → soltar para confirmar. Soltar dentro del botón cancelar X = sin coste/cooldown. Las habilidades `targetMode=position` no self-centered reutilizan `Hud.castSlot` → `GroundAimController` → `castAbilityAt`. Las habilidades normales/empowered retienen su ruta nativa original, sin forzar un patrón que no corresponda.
- Habilidades especiales cargadas (empowerStages) conservan carga explícita cuando esa habilidad lo requiere. No hay casteo en ATK básico.

## Código que P69 prepara
- `scripts/highfly_p69_fury_core.py`: instalador protegido `--apply`, copia de seguridad, restauración en fallo P9.
- `src/game/highfly_fury_skill_touch.ts`: control único de apuntado de skills de posición, captura de un dedo, cancelación por X, blur/pointercancel, mundo relativo a yaw de cámara.
- `src/sim/combat/highfly_manual_taps.ts`: cola de un tap pendiente y cadence de 5 ticks (0.25s).
- `src/main.ts`: restaura el signo 360 verificado en `stepPlayerMotion`; conecta HUD, selección hostil y aproximación P67; conecta el apuntado real.
- `src/ui/hud.ts` y `src/ui/hud/action_bar/mobile_action_ring_controller.ts`: ATK llama al handler manual offline; las habilidades conocen la asignación real actual de ranuras y cooldowns.
- `src/sim/sim.ts` + `src/sim/combat/auto_attack.ts`: offline solamente; un input válido crea una sola llamada de golpe a la simulación. PvP, host/network, originales y ataques no táctiles no deben alterarse.
- `public/highfly/p69_fury_core.css`: cancelador X; conserva el HUD anterior por ahora.
- `tests/test_highfly_p69_fury_core.py`: 13 tests de contratos de integración. Unitarios sintéticos **no sustituyen** compilación Typescript ni prueba en Android.

## LIMITACIONES REALES: NO afirmar completo
1. El golpe manual por tap queda **sólo en modo OFFLINE**, pues el servidor actual no tiene un mensaje de comando manual firmado y validado: online sigue el ataque nativo. Debe implementarse en protocolo y servidor antes de lanzar multijugador/comercial.
2. La animación de ataques se dispara por el impacto nativo cuando éste ocurre; todavía faltan blending avanzado, ataques aéreos, hitstop, cancel windows visuales y variaciones de doble arma.
3. FURY aim C1 se conecta sólo a skills existentes de suelo con un icono asignado, alcance conocido y `touchPreciseGroundAim=true`. No genera mágicamente Fireball curvo ni pone skills en slots vacíos. Aim C2 debe incluir línea/cono/target/lock, previsualizadores propios, cancelación y futura curva física real aprobada por el motor.
4. La dirección digital de movimiento utiliza `mi.forward` más ángulo analógico continuo, conservando velocidad máxima. Aún falta movimiento con velocidad analógica proporcional y validación real de aceleración, virajes y animación.
5. Se conserva la barra/gráficos/inventario; se dedicará una fase a una sola interfaz HIGHFLY anime isekai VIP, sin copiar UI protegida.
6. El prototipo aún reutiliza estructuras de clases y recursos internos de la versión MIT original. El cazador universal y los 253 iconos de biblioteca requieren integración propia posterior.
7. Las skills con castTime real y `empowerStages` siguen el comportamiento dictado por el juego; los básicos no tienen castTime ni recast.

## Operación
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p69_fury_core.py' -v && \
python3 scripts/highfly_p69_fury_core.py && \
python3 scripts/highfly_p69_fury_core.py --apply
```
**Sólo después de ejecutar** la cadena y observar `BUILD_GREEN_BROWSER_PENDING` se podrá probar en el navegador Codespaces y S23 Ultra. Si falla TypeScript, la instalación hace rollback a P68.

## Protocolo de verificación tangible
- 360°: arriba, abajo, izquierda, derecha, diagonales y los ángulos 20°, 40°, 60° manteniendo cámara fija; verificar que no haya inversión y que el dash corra en el mismo vector actual.
- ATK con lobo/jabalí dentro 3–5u y sin target: una pulsación = uno y sólo un intento; cuatro taps próximos = hasta cuatro golpes (registrar misses por azar y daño real).
- ATK con enemigo a 8–12u: seleccionar/acercar si joystick quieto; si joystick se mueve, cancelar la aproximación.
- Apuntado: equipar en S1 una skill REAL de posición ya conocida, activar `touchPreciseGroundAim`, mantener/arrastrar/soltar. Confirmar que retícula del terreno coincide con dónde cae habilidad y gasta cooldown una sola vez.
- Cancelar: mantener S1 y arrastrar a X superior derecha; ningún daño/cooldown al cancelar, ninguna rotación de cámara involuntaria.
- Regresión: abrir menú, bolsas, loot, NPC, misión y guardado. Volver a jugar tras perder foco; no quedar aim atascado.
- NO considerar completo por un BUILD GREEN: se necesitan clips de S23 para confirmar.

## Próximas etapas dentro de una sola arquitectura
- **FURY C2**: shot/manual hit server-authoritative y estados de combate/dash/jump compartidos por online/offline.
- **FURY C3**: apuntado completo line/cone/circle/target/self; efectos y trayectoria propia incluyendo Fireball curvo; botones S1–S4 con skills reales y cooldown.
- **FURY C4**: secuencia física aérea, doble salto/mortal direccional, bonificación real por maniobra, cancel windows y transiciones de rig KayKit.
- **UI HIGHFLY VIP**: estética anime isekai propia para inventario/bolsa/personaje, corregir iconos ART253 y selector KayKit. Se hará luego de validar FURY.
