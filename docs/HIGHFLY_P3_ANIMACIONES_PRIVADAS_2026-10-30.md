# HIGHFLY ORIGIN P3 — Knight y Skeleton con animaciones KayKit

Estado: laboratorio PRIVADO sobre la copia de referencia ClaudeCraft v0.44.7, commit 493c35a108cef6c8aa290e8793107b1cd117886e. La copia de código HIGHFLY de fase P0 ya existe en .workspace/highfly-origin-stage-p0. P3 valida el puente de animaciones ANTES de integrar los actores en ese mundo.

## Resultado del diagnóstico P2 aportado por el usuario

- 39 GLB válidos, 22 con animaciones, 0 errores.
- Knight.glb: 23 huesos, 0 clips embebidos.
- Skeleton_Minion.glb: 23 huesos, 0 clips embebidos.
- Donantes Rig_Medium Tools, CombatMelee, CombatRanged: 23/23 nombres de nodos animados presentes en ambos. Nombre igual NO equivale a animación probada.
- No usar Rig_Large por defecto aunque su índice de nombres coincida: las proporciones o poses de reposo pueden ser diferentes.

## Instalación privada

En el MISMO Codespace scary-troll (rama highfly-origin-commercial-p0), terminal 2:

~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_animation_lab_p3_0447.py'
python3 scripts/highfly_install_animation_lab_p3_0447.py --install
~~~

Este instalador (a) valida referencia v0.44.7 y P1 existente, (b) busca GLB de animación Rig_Medium reales entre Character Animations 1.1 y Adventurers 2.0 previamente extraídos, (c) copia archivos *solo* a la carpeta ignorada .workspace/claudecraft-v0.44.7/public/highfly-private-p3/, (d) agrega una segunda entrada de Vite a la copia privada y (e) instala su página y código de visor. No sobreescribe archivos diferentes ni modifica sim, mapas, combate, inventario, guardados ni P1.

En la terminal 1, si Vite preview está ejecutándose, detener con Ctrl+C. Luego:

~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
bash scripts/start_preview_0447.sh
~~~

Puerto Codespaces **4173 PRIVATE**. Abrir en el navegador la misma URL privada del puerto agregando /highfly-animation-lab-p3.html.

El selector de Modelo alterna Knight/Skeleton; Biblioteca elige archivo de animación, Clip permite probar idle, caminar, correr, atacar, etc. Controles de velocidad, rotación y cámara ayudan a identificar problemas visuales. Si al elegir un donante dice “No hay pistas enlazables”, anotar biblioteca/modelo y revisar el rig antes de adaptar la integración.

## Criterios para aprobar P3

- Knight: idle + caminar/correr + al menos un ataque se reproducen correctamente, sin deformaciones graves.
- Skeleton: idle + caminar + ataque correctos; no permanece rígido en pose T cuando está animado.
- No basta con que el visor liste clips; hace falta comprobarlo visualmente.
- Documentar cualquier clip roto, pies deslizantes, desplazamiento de raíz y escala/posición de arma.

## Próxima fase: HIGHFLY dentro del mundo

P4: integrar **un** actor con modelo/animaciones aprobadas en el render del código HIGHFLY; mantener IDs de entidad, sim, NPC, combate, inventario y loot. Priorizar personaje seleccionable de Adventurers (Hunter Universal; apariencia no clase), luego Skeleton como enemigo animado con IA/loot existente.

Más adelante: catálogo completo KayKit (construcciones, naturaleza, interiores, NPC, monstruos, armas, armaduras) y editor de mundo; reutilizar mundo/sistemas ClaudeCraft v0.44.7 y evolucionar cámara, movimiento, HUD y combos HIGHFLY. Los recursos se incorporan progresivamente, con licencia verificada por archivo; no subir ZIP ni dist al repositorio público.

**NUNCA poner 4173 Public ni desplegar este dist privado.**
