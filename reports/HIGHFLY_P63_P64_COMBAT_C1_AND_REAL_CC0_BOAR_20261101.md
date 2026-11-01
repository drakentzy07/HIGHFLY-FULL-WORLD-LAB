# HIGHFLY Combat C1 (P63) + Jabalí REAL CC0 (P64)

## Alcance real
- P63 ajusta **solo altura visual** de ambos puestos de Eastbrook de 2.7 a un mínimo de 3.2; las huellas 2.8×2.2 y colisiones no cambian.
- P63 cambia el control ATK para que pulsaciones sucesivas no paren inadvertidamente un auto-ataque ya activo contra enemigo hostil. Reutiliza `handleMobileAttackTap` y la SIM de ClaudeCraft, sin fingir golpes.
- El núcleo `src/sim/combat/highfly_melee_combo.ts` lleva una cadena sobre mainhand meleeSwing **realmente conectado**, por blanco y tick, avanza 1,2,3,4, reinicia con objetivo distinto o intervalo >90 ticks. Cuarto golpe escala daño **1.28x** por `weaponMult` pasando por acierto/evasión/crit/armadura original. No agrega daño si el ataque falla y no repite ataques extra. Skills on-next-swing se excluyen.
- `CharacterVisual.playAttack()` reusa clips originales con cuatro acentos de velocidad 1.0,1.09,1.13,0.94 en golpes animados; esto NO sincroniza cada pulsación con un impacto instantáneo; el ritmo del motor continúa siendo el de auto-ataque.
- Respeta sistema de movimiento P48 (dash/salto), 4 slots de skills y NPCs, comerciantes, quests, loot y guardado.

## Jabalíes de Eastbrook
- Fuente de `src/sim/content/zone1.ts`: 5 `wild_boar` en (58,-72) y 4 en (97,-43), suman 9; IDs originales, IA/aggro, stats, quests, loot y posiciones se conservan.
- GLB original `/models/creatures/wild_boar.glb` es custom en manifest y no se encontró licencia CC0 libre suficiente. No redistribuir hasta verificar.
- P64 usa un **jabalí auténtico**, Gobkit Free Animal Pack Vol.2, modelo `https://gobkit.com/freebies/animalB/Boar.glb`. La ficha del proveedor y `https://gobkit.com/api/free` declaran `CC0 1.0` y animaciones nominales separadas `idle`, `walk`, `attack`, `dead`. P64 valida manifest y los cuatro clips DENTRO del GLB, la firma binaria y skinned rig ANTES de crear el archivo.
- P64 guarda el binario SOLO dentro del stage privado en `public/models/creatures/highfly_gobkit_boar_cc0.glb` y modifica source `manifest.ts`, `media.ts`, `assets.ts` para usar precarga diferida P39B. Nada de imágenes/GLBs en repo público.
- Rollback automático de los source changes y archivos creados si Vite falla.

## Código y pruebas
- `scripts/highfly_p63_combat_c1.py`, `tests/test_highfly_p63_combat_c1.py`, CI workflow P63.
- `scripts/highfly_p64_real_boar_cc0.py`, `tests/test_highfly_p64_real_boar_cc0.py`, CI workflow P64.

## ÚNICO COMANDO
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p63_combat_c1.py' -v && \
python3 -m unittest discover -s tests -p 'test_highfly_p64_real_boar_cc0.py' -v && \
python3 scripts/highfly_p63_combat_c1.py --apply && \
python3 scripts/highfly_p64_real_boar_cc0.py --apply
```

Si P63/P64 resultado `BUILD_GREEN_BROWSER_PENDING`, reiniciar servidor de preview en stage privado puerto 4174 y recargar el juego. Probar (1) puestos tamaño, (2) ATK repetido sosteniendo movimiento, (3) golpes reales/daño 4º en enemigo, (4) jabalíes animados en ambos campamentos. Si falla, se detiene la cadena; comunicar logs. En P64 puede fallar red/API; sin acceso no se instala un modelo no verificado.

## No confundir con COMBAT SUPREMO final
- Aún falta ATK **instantáneo por pulsaciones**, cancel windows y buffering, combos aéreos, aiming por skill, VFX/VFX por golpe, feedback de impacto, target assistance, recursos HP/MP/Energía, ataque en carrera calibrado y pruebas S23 horizontal.
- Estos son *cimientos realmente integrados con la SIM*, y no un prototipo paralelo ni demostración 100% completada.
- No se validaron P63/P64 con Vite ni navegadores hasta ejecución del usuario.

## Política REUSE FIRST
Primero reutilizar exactos materiales MIT/CC0 verificables de ClaudeCraft; si `With the project only` o `No, permission required`, reemplazar por KayKit propio / Quaternius / Kenney / otro CC0 documentado. No publicar SOURCE privado, no usar placeholders geométricos ni obras que carezcan de derechos verificados.
