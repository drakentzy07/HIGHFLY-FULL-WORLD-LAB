# HIGHFLY — P53 POSTMORTEM / EASTBROOK OFICIAL VS. STAGE (2026-11-01)

## Resumen operativo

**El cubo gigantesco ya tiene un origen visual aislado**, pero NO está eliminado permanentemente: la URL de prueba \`?hf_audit_giants=1&hf_probe_eastbrook_kmed=hide\` oculta **14 meshes** \`kmed:*\` del área, incluidas representaciones near / far-bake, y el usuario confirmó por capturas que desapareció la pared. Sin dicho parámetro la pared puede volver. P53 NO cambió el generador original ni la simulación ni sus colisiones. Nunca volver a diagnosticar el cubo a ciegas.

**Nuevo problema visible después de ocultar el cubo:** en el centro de Eastbrook hay un enorme cono dorado con formas moradas (aspecto carpa) y una casita diminuta. Es necesario relacionar esos visuales con las entidades exactas del layout antes de cambiar escala/modelo. P35 DEBUG y HIGHFLY LOG reaparecieron; la carga sigue con barra/tip mal posicionados.

**FUENTES**: World of ClaudeCraft **v0.44.7 commit \`493c35a108cef6c8aa290e8793107b1cd117886e\`**, directamente:
- \`src/sim/eastbrook_layout.ts\` (estable layout; BUILDINGS ~ líneas 610-740; MONUMENT ~ 770-827; servicios ~ 1279-1348)
- \`src/render/eastbrook_town.ts\` (construcción \`eastbrookTownRebuild\` y \`buildKitBuilding\`)
- \`src/render/realm_builder_monument_fx.ts\` (\`buildRealmBuilderMonumentBody\` clona GLB, reescala, añade FX)
- \`src/render/props.ts\` (\`buildProps\` monta \`activeContent.props.buildings\`; pool \`kmed*\` reservado en origen a construcciones \`hollow*\` de Veiled Hollow)
- \`docs/design/eastbrook-revamp/site-plan.md\` (histórico/propuesta; no confundir con layout final congelado)

Enlaces:
- https://github.com/levy-street/world-of-claudecraft/blob/493c35a108cef6c8aa290e8793107b1cd117886e/src/sim/eastbrook_layout.ts
- https://github.com/levy-street/world-of-claudecraft/blob/493c35a108cef6c8aa290e8793107b1cd117886e/src/render/props.ts
- https://github.com/levy-street/world-of-claudecraft/blob/493c35a108cef6c8aa290e8793107b1cd117886e/src/render/realm_builder_monument_fx.ts

## 1. Los edificios que el layout oficial realmente prevé

El original congelado usa **11 edificios** en BUILDINGS, además del \`eastbrook_weekly_vault\` añadido aparte. La siguiente tabla es **del código original**, no inferida de capturas. Los modelos son referencias del original que HIGHFLY puede cambiar por equivalentes con licencia aprobada manteniendo IDs y funciones.

| ID oficial | Centro x,z | Modelo original declarado |
|---|---|---|
| eastbrook_bank | 12,-94 | \`/models/biome/hexb_townhall.glb\` |
| eastbrook_smithy | -2,-122 | \`/models/biome/hexb_workshop.glb\` |
| eastbrook_inn | -38,-88 | \`/models/biome/hexb_tavern.glb\` |
| eastbrook_chapel | 2,-78 | \`/models/biome/hex_church.glb\` |
| eastbrook_weaving_workshop | -28,-122 | \`/models/biome/hexb_home_a.glb\` |
| eastbrook_toolworks | -16,-128 | \`/models/biome/hexb_home_b.glb\` |
| eastbrook_home_market | -33,-111 | \`/models/biome/hexb_home_a.glb\` |
| eastbrook_home_east | 22,-106 | \`/models/biome/hexb_home_b.glb\` |
| eastbrook_quayside_home | -82,-102 | \`/models/biome/hexb_home_b.glb\` |
| eastbrook_harbour_market | -68,-108 | \`/models/biome/hexb_market.glb\` |
| eastbrook_dock_home | -50,-112 | \`/models/biome/hexb_home_a.glb\` |
| eastbrook_weekly_vault (civic weekly vault aparte) | 21,-119 | resuelto separadamente por \`src/render/eastbrook_town.ts\` |

El P50 reportado por el usuario tiene exactamente esos doce IDs e indica tamaños individuales ~7-14 unidades. **No eliminarlos por parecer mini casitas sin identificar**: hay tres casas de barrio y tres del puerto expresamente planificadas. Pequeñas y extrañas pueden ser modelos provisionales, decoraciones sueltas o edificios normales de mala escala; se necesita ID y transform.

### Otros elementos oficiales de Eastbrook que deben conservar sus funciones
- Monumento \`eastbrook_realm_builder_monument\` en **(-14.75,-102)**, **altura prevista 7.6**; \`entityId: 2_000_000_100\`, \`templateId: realm_builder_monument\`.
- Tablón \`eastbrook_noticeboard\`, en **(5,-89)**, dimensiones **2.4 × 2.6 × 0.6**, \`entityId: 2_000_000_001\`. NO confundir con las mallas gigantes; si parece pinchos, auditar asset visual y colisión aparte.
- Cofre banquero, buzón \`mailbox_eastbrook\` (-10,-98), tumbas, fuente/pozo, bancos, dos puestos comerciales, vallas, cuatro estaciones de crafteo, NPC con roles específicos y zonas de puerto. Sus interacciones/misiones no pueden desaparecer por hacer limpieza visual.
- **Grand Armoury** histórico (17.5,-5.5) NO explica el bloque en (-3.9,-112); en la fuente hay cambios de emplazamiento en rondas posteriores. No tocarlo como culpable sin prueba.

## 2. Lo que P52B midió realmente en HIGHFLY (archivo del usuario, JSON de 99 filas)

En \`?hf_audit_giants=1\`, antes de P53, el bloque ofensivo era geometría cerca de **x=-3.9, z=-112**:
- \`kmed:roof_dark\` 37.2 × 12.4 × 58.6, centro y=36.9
- \`kmed:stone\` 39 × 15.6 × 56.5, centro y=7
- \`kmed:plaster\` 37.9 × 29.9 × 55.6, centro y=14.2
- \`kmed:wood\` 39 × 32.2 × 55.4, centro y=15.3
- \`kmed:wood_light\` 37.9 × 1.6 × 1.4, centro y=42.9
- \`kmed:roof_blue\` 0.8 × 6.8 × 32, centro x=15.3,y=12.2,z=-112
- \`kmed:stone_light\` ~12.4 × 1.4 × 11.7, centro x=21.2,z=-112
- Muchos aparecen de a pares: un \`Scene > Group > Group > Group > Mesh\` cercano y \`Scene > Group > far-bake:0:-1\` lejano.

El usuario comprobó P53 **14 mallas KMED ocultas** en prueba, el cubo/pared desaparece. Otros edificios y NPC seguían presentes. Esto demuestra responsabilidad del grupo de materiales KMED, **NO todavía el ID exacto ni que 14 meshes sean 14 edificios**. Es probable que sean componentes de una o unas pocas instancias de GLB más un bake LOD. Evitar eliminación por índice \`#59\` etc (índices frágiles).

## 3. Hallazgo importante al comparar fuente original y HIGHFLY

El código original \`src/render/props.ts\` define \`kmedHomeA/B\`, \`kmedTavern\`, \`kmedChurch\`, \`kmedBlacksmith\`, \`kmedMarket\`, asociados a tipos \`hollowHouse / hollowInn / hollowChapel / hollowSmith / hollowMarket\` de **Veiled Hollow**. En cambio, el núcleo de Eastbrook declara \`hexb_*\` / \`hex_church\` y su renderer específico usa grupo \`eastbrookTownRebuild\`.

Por tanto es una anomalía técnica concreta que haya una **construcción gigante KMED** superpuesta al casco histórico de Eastbrook cerca de (-3.9,-112). La causa a verificar es el registro de colocación en \`activeContent.props.buildings\` (posible superposición de contenido de otra zona, cambio de kind, transformación o render residual), NO ajustar escala arbitrariamente en los 14 meshes ni eliminar todos los \`kmed*\` del mundo (que son decorados legítimos en Veiled Hollow).

**PRÓXIMA IMPLEMENTACIÓN CORRECTA**: instrumentar \`src/render/props.ts\` en el \`for (const b of activeContent.props.buildings)\`: registrar \`x,z,w,d,rot,kind,landmark,asset=buildingAssetPick(b)\`, junto con \`group\` y su \`THREE.Box3\` para el área x[-30,25], z[-160,-65]. Establecer \`userData.highflySourceBuildingId\` / group.name si existe ID estable; también auditar las instancias del far-bake collector en \`collectFarFieldPropInstances()\` para excluir sólo la misma instancia del bake. Comparar con IDs de \`EASTBROOK_LAYOUT\` y acta de removed placements. Corregir en **fuente de colocaciones** y su sim/colliders coordinados, con backup y build/check posterior. No confiar en \`?hf_probe_eastbrook_kmed=hide\` como solución definitiva: no está activo en URL normal.

## 4. ¿Qué es el cono/carpa dorada enorme que apareció después?

**Principal sospechoso fundamentado**: \`eastbrook_realm_builder_monument\`, exactamente en **(-14.75,-102)**, donde el screenshot muestra un cono grande color oro con pieza morada. P50 midió \`eastbrookRealmBuilderMonumentFxBody\` ~**13.8 × 24 × 14.6** (en lugar de la altura **7.6** del layout). El render original se crea en \`buildRealmBuilderMonumentBody()\` con GLB clonado, luego \`scale\` y VFX. Posible sustituto GLB inapropiado o escala triple; aún **no está demostrado** que ese visual concreto sea el cono hasta aislarlo en el mismo ángulo.

**PRUEBA SIN OTRA COMPILACIÓN**: usar juntos
\`?hf_audit_giants=1&hf_probe_eastbrook_kmed=hide&hf_probe_monument=hide\`.
El primer flag mantiene oculto el cubo, y el segundo oculta sólo cuerpo y FX del monumento. Si el cono desaparece, queda identificado. Si no, no atribuirlo al monumento. Respetar su ID, rango de interacción, misiones/bancos/estaciones y colisiones, y reemplazar sólo con recurso CC0/SOURCE autorizado y una altura apropiada y comprobada.

## 5. Mini casitas: decisión pendiente de auditoría

Las capturas muestran algunas construcciones desproporcionadamente pequeñas entre casas mayores. **NO pueden llamarse sobrantes sin conocer posición/modelo/ID**. Entre las explicaciones:
1. Las casas originales \`eastbrook_home_market\` / \`eastbrook_home_east\` / \`eastbrook_dock_home\` tienen IDs/uso legítimos pero GLBs sustitutos de escala inadecuada;
2. puestos de mercado, buzón, pozo, decoración o \`far-bake\` son props, NO casas;
3. edificaciones antiguas de \`activeContent.props.buildings\` no filtradas al levantar la nueva reconstrucción;
4. un fallback de modelo no aprobado o transform erróneo.
Auditar todos los meshes **incluso pequeños** de la plaza, agrupar por parent y coordenada (cercanía al player) y asignar cada uno a \`EASTBROOK_LAYOUT\`, \`REMOVED_EASTBROOK_PLACEMENTS\`, \`activeContent.props.buildings\` o decorProps. Sin etiquetas no borrar ni agrandar a ojo.

## 6. UI, mobile y legales — pendientes prioritarios

- P52 volvió a mostrar \`HIGHFLY P35 - NPC/BOLSA\` y \`HIGHFLY LOG · fallos · DESCARGAR\`, probablemente al sustituir CSS P50 por la nueva hoja visual. Corregir en código con un flag \`?hf_debug_ui=1\` y no borrar diagnósticos internos.
- Pantalla de carga: el logo espectacular está en fondo, pero \`Cargando mundo...\`, barra real \`#ls-fill\` y \`#ls-tip\` aparecen abajo, el consejo descuadrado/izquierda y reflujo según longitud. Hacer un solo overlay absoluto anclado al tercio inferior; contador y barra en posiciones estables, tips centrados en altura fija con límite de 2 líneas; nunca duplicar barras ni fingir progreso; traducir consejos residuales sobre «9 clases».
- Entrada y creador PC/Android aún requieren responsive premium, skins sexo/apariencia reales; conservar Hunter único e ID técnico warrior y P41/P46 autosave.
- Jabalíes ausentes: falta \`public/models/creatures/wild_boar.glb\`; no usar asset original no licenciado. Comparar KaKit privado nombres y autoría antes de copiar nada.
- Tablón de tutorial con apariencia de pinchos, barcos/natación deficientes. Reasignar sólo tras comprobar IDs/modelos y colisión.
- FURY Android 360, 4 skills reales, ATK, salto/evadir y giro todavía incompleto; P48 sólo fue fundación.
- Legal: stage y KayKit SOURCE privado; no subir ZIP/cuerpos GLB propietarios al GitHub público. No volver a usar AnyRPG.

## 7. Estado de ejecución

- P43 save/NPC/crabs/quests/loot funcionales en pruebas del usuario.
- P48 Android movilidad parcialmente reparada; no full FURY.
- P50 scene audit / P51 monument toggle aplicados y probados.
- P52 ZIP imagen/capa visual aplicado y compilado.
- P52B scene-audit global ejecutado (99 registros de grandes mallas en última URL).
- P53 KMED probe aplicado y **VERIFICADO VISUALMENTE**: 14 meshes escondidas, bloque gigante desaparece sólo en esa URL.
- NO corrección definitiva aún del placement KMED, mini casa, cono, debug overlays y loading UI.
- Verificado el JSON aportado por usuario para 99 objetos: no confundir water plane (3000 × 5000) o instancing foliage masivo con edificios gigantes.

## 8. Próximo chat — orden propuesto P54 (NO reejecutar P46–P53)

1. Corregir colocación/material \`kmed\` invasivo por ID, conservando mundo/LOD/colliders, y respaldar stage. Revisar legal y asset lineage.
2. Confirmar cono con el switch conjunto y restaurar monumento legítimo al tamaño/arte correcto (sólo visual si puede; preservar entity).
3. Hacer inventario completo de mini casas por id/coords/model contra tabla oficial, reemplazo validado CC0 cuando realmente corresponda.
4. Arreglar P35/LOG y refinamiento visual de Loading (no new artwork needed).
5. Auditar jabalíes/tablón/íconos y volver a FURY Android 360 con iteración real en S23.
6. Entregar una tanda de fixes coordinada con tests y build privado, NO prometer éxito Android hasta prueba.

Comando habitual para servidor DESPUÉS de build:
\`\`\`bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
\`\`\`
