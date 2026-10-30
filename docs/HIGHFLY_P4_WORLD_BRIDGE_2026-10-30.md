# HIGHFLY ORIGIN P4 — puente de personajes al mundo propio

Fecha: 30/10/2026. Base original congelada: World of ClaudeCraft v0.44.7, commit 493c35a108cef6c8aa290e8793107b1cd117886e. Rama de HIGHFLY: highfly-origin-commercial-p0.

## Punto de partida real

- P0 realizado en Codespaces: 5.314 archivos de código copiados en .workspace/highfly-origin-stage-p0/; public/ empieza vacío. El clon privado de ClaudeCraft permanece como referencia de sistemas.
- KayKit Complete V7 íntegro y privado, 23 packs en ZIP reconstruido; se han extraído hasta ahora Adventurers 2.0, Character Animations 1.1 y Skeletons 1.1.
- P2: 39 GLB válidos, 22 con animaciones, 0 errores; Knight y Skeleton Minion 23 huesos y 23/23 coincidencias de nombres en donantes Rig_Medium.
- P3: el usuario confirmó que ambos modelos se mueven espectacularmente en el visor 3D privado. VALIDACIÓN VISUAL BÁSICA, no prueba de movimiento dentro del RPG.
- El original v0.44.7 ya tiene un sistema sofisticado de VisualDef, ClipMap, animUrls, skinning, equipamiento visible, personajes modulares masculinos/femeninos y cuerpos de NPC con props. Reutilizarlo, no recrearlo desde cero.

## Decisión de diseño confirmada

HIGHFLY ORIGIN es un RPG independiente construido *sobre el código y los sistemas legalmente reutilizables* de ClaudeCraft, preservando mundo, lugares, NPC, misiones, monstruos, IA, combate, progresión, loot, equipamiento, interiores y editor cuando sean válidos. La estética y nuevo contenido provienen de KayKit Complete V7 y recursos propios/autorizados, con auditoría de licencias por archivo.

No convertir HIGHFLY en un visor aislado ni en un mundo pequeño desde cero. No volver a AnyRPG ni saltar a ClaudeCraft 0.45.

- Personaje único **Hunter Universal**, sin obligación de clases. Apariencias iniciales: personajes Adventurers 2.0 compatibles.
- **Editor futuro:** elegir sexo masculino/femenino, apariencia/skin, nombre y componentes compatibles del cuerpo; respetar que algunos modelos GLB fijos no permiten cambiar de sexo sin variantes o adaptación. No inferir sexo a partir de la textura.
- Más skins compatibles por desbloqueo de misiones, jefes, exploración y recompensas; sin alterar stats base por skin.
- Modelos de NPC para comerciantes, guardias, aldeanos y demás; su **profundidad de interacción** se deriva del RPG original y se mejora con nuevas rutinas y acciones.
- Armas, armaduras, materiales y objetos KayKit como loot real: cadáver/contexto -> inventario -> equipamiento visible y guardado, no reemplazar lógica sana del original.
- Preservar y mejorar movimiento, cámara, esquiva, dash, doble salto, ATK 1-2-3-4, ataques aéreos, aim real y HUD MOBA horizontal Android S23 Ultra; es una evolución progresiva, no requisito previo para validar la conexión de modelos.
- Todos los packs tienen valor a futuro: Medieval Hexagon, Forest Nature, Dungeon, Furniture, Fantasy Weapons Bits, RPG Tools Bits y los demás. Importar al runtime únicamente los recursos usados y verificados, evitando peso innecesario.
- Comprobar escala de ciudades, puertas, murallas, colisiones e interiores al integrar construcciones.

## Primer puente P4 implementado en script (NO es build jugable todavía)

El script scripts/highfly_bridge_hunter_world_p4.py:
1. Comprueba existencia de la etapa HIGHFLY independiente y datos de origen.
2. Inspecciona Knight, Skeleton y los GLB propios Rig_Medium MovementBasic, General, CombatMelee, CombatRanged de KayKit, requiriendo clips base.
3. Copia **solo** esos seis GLB al public/ de la etapa privada HIGHFLY (no desde ClaudeCraft).
4. Añade un bloque reversible VITE_HIGHFLY_P4=1 a src/render/characters/manifest.ts de la etapa HIGHFLY; hace la conexión preliminar del avatar warrior de prueba y skel_minion sin tocar sim, inventario, datos del mundo ni partidas. Las clases originales no son todavía el diseño final.
5. Rechaza conflictos y NO escribe en GitHub modelos privados, NO publica ni construye juego.
6. Lo que aún queda es sustituir/autorizar muchos otros medios de la etapa vacía, adaptar selección de skin y Hunter único, probar armas/colisiones/animaciones con gameplay, construir un runtime privado HIGHFLY y pasar controles de release.

### En el mismo Codespace, terminal 2:

~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_bridge_hunter_world_p4.py'
python3 scripts/highfly_bridge_hunter_world_p4.py --install
~~~

Si sale FAILED o ERROR, **detenerse y copiar salida**. El control evita modificar recursos de ClaudeCraft y evita sobrescribir cambios en la etapa HIGHFLY. Un estado P4 verde significa puente de código/medios privados colocado, **NO juego 3D funcional** aún.

### Próximo hito P5

Preparar el runtime privado independiente de HIGHFLY con todos los recursos necesarios de licencia verificada, hacer que el avatar Adventurers seleccione skin y entrar al mundo de Eastbrook; probar guardar/cargar y combate. Conectar un enemigo Skeleton y luego un NPC, arma, cadáver contextual, inventario y equipamiento. Mantener ClaudeCraft original para diagnóstico, sin publicar los archivos completos.

La etapa de código HIGHFLY reside bajo .workspace/ e ignora Git. Los parches y herramientas de transformación quedan versionados en GitHub; el código transformado debe revisarse y persistirse como fuente propia de HIGHFLY antes de convertirlo en repo/release final. La ausencia de contenido en public/ mantiene la publicación bloqueada.

**Puerto privado en Codespaces. No subir packs KayKit ni publicar la compilación original mientras falten revisiones de licencia.**
