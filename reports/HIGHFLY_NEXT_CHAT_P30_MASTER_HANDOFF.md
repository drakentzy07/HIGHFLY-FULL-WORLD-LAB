# HIGHFLY ORIGIN — TRANSFERENCIA AL CHAT NUEVO / AUDITORÍA MAESTRA P30

**Fecha:** 31/10/2026. **Repositorio:** `drakentzy07/HIGHFLY-FULL-WORLD-LAB`, rama `highfly-origin-commercial-p0`.
**Codespaces:** `/workspaces/HIGHFLY-FULL-WORLD-LAB`.
**Original analizado:** `levy-street/world-of-claudecraft` v0.44.7, commit fijado `493c35a108cef6c8aa290e8793107b1cd117886e`, copia en `.workspace/claudecraft-v0.44.7`.
**Stage:** `.workspace/highfly-origin-stage-p0`.
**Colección propia (NO publicar su ZIP):** `.workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip`.

## Decisiones irrevocables de producto
- SOLO el personaje del jugador es **Hunter Universal**. Sin clases ni especializaciones jugables. Aprende habilidades físicas/mágicas mediante compras, misiones, drops y fusiones. Equipar no crea otra clase.
- NPC de ClaudeCraft conservan **sus propios ID, nombre, diálogo, misión, profesión, comercio, posición, facción, IA y movimiento**. El cuerpo/ropa/accesorios visuales se recuperan de nuestro KayKit Complete SOURCE V7 (o recursos externos legalmente válidos) **sin homogeneizarlos**.
- Ejemplo verificado en el manifiesto original: `brother_halven`/Reliquary Keeper usa `npc_reliquary_keeper` -> `models/chars/players/paladin.glb`; `npc_smith` -> `models/chars/players/barbarian.glb`; los NPC modulares usan `models/chars/modular/warrior_modular.glb` más el mapa individual `npc_looks.ts`.
- Conservar por separado todos los monstruos, especies/IA, tablas de loot, armas, armaduras, ítems, zonas, barcos, misiones, dungeons, interfaces, habilidades, equipamientos, animaciones.
- **REUSE FIRST — PRIORIDAD ABSOLUTA:** conservar *idénticos* los medios originales de ClaudeCraft cuya licencia específica y procedencia acrediten reutilización independiente (p. ej., CC0, MIT cumpliendo avisos), aun si figuran como faltantes en el stage. Restaurar desde la copia original fijada o reconstruir el archivo desde su fuente licenciada, sin reemplazarlo por KayKit porque sí. Cambiar el visual solo si faltan derechos, hay incompatibilidad técnica demostrada o se decide una mejora estética posterior. Nunca inferir licencia del arte desde la licencia MIT del código. Un archivo ausente en stage significa RESTAURAR/REVISAR, no REEMPLAZAR por defecto.
- **Caso de control comprobado en v0.44.7:** `scripts/assets/specs/characters.json` conecta `tmp/asset_src/quaternius_creatures/Wolf.glb` → `models/creatures/wolf.glb`; `CREDITS.md` (línea 101) identifica las criaturas animadas Quaternius, incluido el lobo, como CC0 1.0 redistribuibles. Este es recurso para *conservar*, verificando que los bytes concretos de la copia local correspondan a dicha fuente antes de restaurarlo.
- Mantener recursos CC0 genuinos ya válidos, incluidos Quaternius, Kenney, ambientCG, Poly Haven, loafbrr y otras fuentes verificadas. **KayKit SOLO de nuestro Complete SOURCE V7**, no volver a usar importaciones FREE viejas como fuente.
- Código MIT de ClaudeCraft ≠ licencia MIT de todo su arte. Los medios `With the project only`, `No, permission required` y sin registro necesitan revisión; no copiarlos automáticamente a HIGHFLY independiente.

## Estado comprobado antes de P30
- Mundo ya **ENTRA Y SE PUEDE MOVER** en Codespaces preview 4174 (capturas del usuario 31/10).
- Sistema de misiones/diálogos/HUD/minimapa aparece; NPC y jugador no están visiblemente restaurados en las pruebas.
- P21 recuperó 48 assets CC0. P22 generó 249 GLB temporales más otros recursos para salvar el arranque.
- P26 restauró 3 GLB originales CC0 y P23 convirtió 6 desde KayKit SOURCE V7: **240 GLB temporales seguían pendientes**.
- P28 generó 11 imágenes originales de materiales/carga; la pantalla de arranque dejó de bloquear la entrada.
- Al recorrer el mundo surgieron **48 rutas dinámicas fallidas**: 33 KTX2 de variantes, 9 GLB VFX, 4 KTX2 VFX, 1 modelo dummy y 1 loading art. No significan que NPC o skills no tengan lógica.
- P29 pasa 8 tests; la primera medición `actorModelsPresent: 0` era **incorrecta en varias rutas**, ya que buscaba `models/chars/knight.glb` en lugar de `models/chars/players/knight.glb`. Corregido en Github; hay que repetir auditoría, no interpretar el viejo 0/7.
- No asumir que una compilación `exitCode 0` demuestra juego completo/seguro/legal.

## Auditoría maestra nueva P30
`scripts/highfly_p30_master_original_world_inventory.py`
`tests/test_highfly_p30_master_original_world_inventory.py`

Inspecciona el árbol completo `public/` del original, los archivos `src/`, manifiestos `scripts/assets/specs/*.json` (src->out), CREDITS.md, tabla NPC_KEYS, NPC_LOOKS, modelos y animaciones, registros de NPC/mobs/ítems/loot/equipamiento/quests de `src/sim/content`, los packs KayKit SOURCE, archivos actuales del stage y rutas observadas en logs.

**17 categorías:** NPC, loot, armas, armaduras, monstruos, personajes, edificios, estructuras, vegetación/fauna, ítems, agua/lava/tierra/clima, barcos, interacciones/movimiento, menús/HUD, habilidades/VFX, audio, otros.

Salida en `.workspace/reports/highfly-p30-master/`:
- `P30_MASTER_SUMMARY.json`
- `P30_ALL_MEDIA_AND_USAGE.csv` — cada asset, fuente/especificación, cita de licencia, uso en código, estado del stage y candidato KayKit por nombre.
- `P30_EVERY_NPC_AND_VISUAL.csv` — identidad NPC -> visual, cuerpo, animaciones y apariencia.
- `P30_SIM_NPC_MOBS_ITEMS_LOOT_QUESTS.csv` — NPC, mobs, quests, ítems, coords literales y nombres. Mapear casos calculados manualmente.
- `P30_EVERY_SOURCE_SYSTEM.csv` — módulos reales de simulación, render, interacciones, menús y pipelines.

**Buscar cualquier entidad del inventario cuando finalice la auditoría:**

```bash
python3 scripts/highfly_p30_find.py brother_halven
python3 scripts/highfly_p30_find.py paladin.glb
python3 scripts/highfly_p30_find.py wolf
python3 scripts/highfly_p30_find.py training_dummy
```

**P30 es una auditoría ESTÁTICA y READ ONLY**. No demuestra todos los spawns de runtime, los equipos con nombres dinámicos, compatibilidad de rigs o licencia de un archivo no registrado. Da pista exacta cuando existe y señala lo no resuelto; jamás inventar un match visual ni dar el mundo como 100% auditado sin pruebas.

## Primer comando en el chat nuevo

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p30_master_original_world_inventory.py' && \
python3 scripts/highfly_p30_master_original_world_inventory.py && \
python3 scripts/highfly_p29_actor_skill_vfx_audit.py
```

Pedir el resultado `[HIGHFLY] P30 MASTER AUDIT` y `[HIGHFLY] P29 AUDIT`. Si P30 falla, corregir el script, volver a correr tests; no volver a generar placeholders.

**Próxima fase:** convertir P30 en matriz de cambios visuales 1:1 (NPC primero), con verificación de rigs/animaciones/texturas, luego dummies y VFX; después loot/armas/armaduras/monstruos, edificios y mundo. Preservar tabla y lógica sin tocarlas. Construcción privada y prueba de navegador tras cada lote.

## P31: primer caso real CC0, Quaternius Wolf
Tras P30: `wolf.glb` aparece como `SPEC_PROVIDER_CC0_REUSE_CANDIDATE` y `RESTORE_OR_REVIEW_MISSING_ASSET`. Confirmado en la fuente v0.44.7: `scripts/assets/specs/characters.json` contiene `tmp/asset_src/quaternius_creatures/Wolf.glb` → `models/creatures/wolf.glb`; `CREDITS.md` acredita criaturas animadas Quaternius CC0 1.0, redistribución Yes. No sustituir este lobo por KayKit.
Se agregó `scripts/highfly_p31_cc0_wolf_restore.py` y 3 pruebas aisladas. **Dry-run predeterminado**, `--apply` restaura exclusivamente el archivo original a la misma ruta del stage privado, comprobando commit original, fuente exacta, crédito CC0, cabecera GLB e identidad SHA256; sin sobreescribir archivos existentes, sin cambiar gameplay ni desplegar. Los 3 tests pasaron en aislamiento local, **pendiente confirmar en Codespace**:
```bash
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p31_cc0_wolf_restore.py'
python3 scripts/highfly_p31_cc0_wolf_restore.py
python3 scripts/highfly_p31_cc0_wolf_restore.py --apply
```
Los siguientes lotes deberán usar un registro explícito de procedencia/licencia por recurso: ***nunca*** tratar todos los `SPEC_PROVIDER_CC0_REUSE_CANDIDATE` como autorizados sin inspección. P31 sirve como piloto para la restauración sistemática, no demuestra que el lobo ya aparezca en runtime.

## P33 — Recuperación global CC0 y diagnóstico del Hunter (31 Oct 2026)
Tras revisar P32 (auditoría 15 zonas), se confirmó que el borrado de 9 clases de jugador podría afectar al selector/creador, pero por sí solo NO explica la falta de cuerpos NPC. El sistema NPC usa una biblioteca modular `warrior_modular.glb` y donantes de clips (con excepciones como Brother Aldric). `P30` no demuestra licencias ni render/instancias definitivas. P32 es alcance documental, no una auditoría efectuada.

NUEVO: `scripts/highfly_p33_world_cc0_restore.py` con test `tests/test_highfly_p33_world_cc0_restore.py`. **Dry-run por defecto**, escanea todo el `public` original (GLB y PNG/JPG/WebP con verificaciones), cruce exacto `src -> out` según specs y fuente acreditada CC0, restaura masivamente solo faltantes aprobados y sustituye únicamente P22 provisional por un original CC0 documentado conservando copia de seguridad. No altera el RPG ni el selector de personaje. Recursos project-only/no verificados quedan bloqueados, no instala el `warrior_modular.glb` sin derechos demostrados. El informe identifica rutas actor y diferencias de código original/stage para diagnosticar el Hunter. No ejecuta un build ni prueba el navegador por sí mismo.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p33_world_cc0_restore.py'
python3 scripts/highfly_p33_world_cc0_restore.py
python3 scripts/highfly_p33_world_cc0_restore.py --apply
python3 scripts/highfly_p29_actor_skill_vfx_audit.py
```

**PRÓXIMO BLOQUEADOR**: leer resultados `[HIGHFLY] P33 ACTORS` y `[HIGHFLY] P33 SELECTOR`, comprobar el `warrior_modular.glb`, y entonces reparar selector del Hunter y su fuente visual sin restaurar 9 clases. Los modelos CC0 no garantizan personajes visibles si falta composición modular. Validar build privado, navegador y rutas dinámicas antes de prometer mundo completo.

## P34 — fallback visual reparador por falta del GLB modular
P33 usuario ejecutado OK: **83 CC0 restaurados**, `actorModelsPresent:8/9`, falta `models/chars/modular/warrior_modular.glb`; `mage_classic.glb` y `training_dummy.glb` siguen en REVIEW. P33 distinguió `manifest.ts` y `assets.ts` como los dos archivos de render modificados respecto al original. La ausencia de clases seleccionables NO explica por sí sola la falta de los modelos NPC.

Nuevo `scripts/highfly_p34_fixed_actor_fallback.py` + pruebas `tests/test_highfly_p34_fixed_actor_fallback.py`. Ante ausencia de la biblioteca modular, modifica SOLO la copia privada del stage: desactiva temporalmente `setModularLookProvider` en `src/render/characters/index.ts` para usar rigs fijos ya restaurados (NPC según `visualKeyFor`, Hunter según manifest HIGHFLY), evita precarga de defs modulares ausentes en `manifest.ts`, y si falta `mage_classic.glb`, usa `npc_mage` CC0 para Brother Aldric, sin cambiar su ID, diálogos, posición ni quests. Hace copias de seguridad antes; no modifica 9 clases, simulación, rama de ClaudeCraft ni Pages. Los rostros/apariencias originales de NPC modulares NO quedan restaurados hasta hallar fuente modular autorizada o implementar composición 100% propia y compatible.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p34_fixed_actor_fallback.py'
python3 scripts/highfly_p34_fixed_actor_fallback.py
python3 scripts/highfly_p34_fixed_actor_fallback.py --apply
python3 scripts/highfly_p9_private_build_smoke.py
python3 scripts/highfly_p29_actor_skill_vfx_audit.py
```

`P34` usa fuentes con anclas exactas y aborta ante cambios que no reconoce; los tests aún requieren ejecución en Codespaces. **No demuestra visibilidad ni corrección del editor Hunter** sin prueba interactiva. Si quedan NPC invisibles, investigar donantes de animación GLB o attachments faltantes a través del informe de red del navegador. No publicar si hay medios project-only no aprobados.

## P35 — diagnóstico real de NPC invisibles, bolsa e inventario (31/10)
Tras P33 (83 CC0 restaurados) y P34 (fallback a rigs fijos), la prueba visual del usuario confirma: Hunter visible y móvil, Proving Shore explorable, **NPC siguen invisibles** pese al interactuable `F Talk`; campana/faroles aún se ven geométricos; pantalla de clases antiguas y thumbnails rotos; bolsa e inventario también requieren revisión. Se adjuntó JSON P20 de browser de 31/10 a las 15:28 UTC: 567 peticiones, 63 respuestas fallidas, 19 rutas únicas (9 GLB VFX, 5 skins de Knight, 4 KTX2 VFX, 1 dummy). **NO incluye rutas NPC**: el detector observa fetch/HTML fallback pero NO fallos internos de `createCharacterVisual`; no confundir con los 48 ítems estáticos P29.

Nuevo `scripts/highfly_p35_actor_ui_debug.py` y `tests/test_highfly_p35_actor_ui_debug.py`. Instrumentación temporal SOLO de stage privado: añade recolector en `index.html`, registros internos de `src/render/renderer.ts` (intentos NPC + si logra crear view y si hay visual/root visible) y `src/render/characters/index.ts` (excepciones visuales), más scanner de imágenes rotas en los menús, incluida bolsa/inventario. Añade botón superior `HIGHFLY P35 - NPC/BOLSA` que descarga `HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json`. Requiere build privado P9. Tiene copias de seguridad y es reversible; **NO repara NPC automáticamente** sino que identifica por qué se omiten. Ejecutar tests, dry-run, apply y P9; entrar al juego, abrir bolsa/inventario, recorrer y accionar botón. No publicar esta instrumentación.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p35_actor_ui_debug.py'
python3 scripts/highfly_p35_actor_ui_debug.py
python3 scripts/highfly_p35_actor_ui_debug.py --apply
python3 scripts/highfly_p9_private_build_smoke.py
```

## P36 — NPC invisibles, primera corrección de contingencia (31 Oct 2026)
Prueba visual P35 confirmó: NPC siguen invisibles en **The Proving Shore** aunque aparece `F Talk`; Hunter sí es visible; bolsa e inventario muestran imágenes ausentes; guardado offline reportado como no funcional. La sospecha de tutorial-único es plausible, pues varios NPC del tutorial (p.ej. `ferryman_odo`) caen en `npc_villager` mientras `marshal_redbrook` de Eastbrook usa `npc_knight`; **NO demostrada todavía**. P35 sólo diagnosticó y usuario todavía no compartió `HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json` del botón.

Nuevo `scripts/highfly_p36_npc_visible_fallback.py` y test: el catch de `createCharacterVisual`, cuando `e.kind === 'npc'`, prueba un rig fijo por rol (Paladin/Mage/Shaman/Rogue) y después `player_warrior` comprobado en pantalla. Mantiene NPC templateId, quest, banca, vendor, diálogos, jugador Hunter único, salva y combate. Solo fallback si falla la creación del visual original; no restaura las apariencias autorales ni afirma NPC visibles hasta prueba en Codespaces. Solo stage privado, backup de `index.ts`, no public deploy.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p36_npc_visible_fallback.py'
python3 scripts/highfly_p36_npc_visible_fallback.py
python3 scripts/highfly_p36_npc_visible_fallback.py --apply
python3 scripts/highfly_p9_private_build_smoke.py
```
Recargar navegador, verificar Proving Shore y Eastbrook; si NPC sigue oculto, usar botón P35 para descargar JSON, distinguir `npc_view_attempt`, `actor_visual_error` y `npc_fixed_fallback_success`. El salvado offline es bloqueo separado prioritario DESPUÉS de que NPC sean visibles e interactivos.

## MILESTONE 31 Oct 2026 — P36 VISUALMENTE CONFIRMADO EN THE PROVING SHORE 🎯
Capturas del usuario a las 15:52 UTC prueban NPC 3D **visibles** y rotulados: `Ferryman Odo`, `Warden Tam`, `Overseer Pell`, `Drillmaster Rook`, `Tidewarden Nel` (y otros); Hunter `DRAKENLAB` visible, pueblo tutorial explotable. Antes los NPC eran invisibles y sólo se veía `F Talk`. P36 **sí desbloqueó el renderizado de cuerpos NPC**. Los modelos aparecen como guerreros/knights similares (fallback), NO recrean los rasgos y equipos de `npc_looks.ts`. Verificar interacción efectiva de comercio/quest con diálogo; etiquetas y cuerpos visibles no garantizan que se haya probado la interacción. Es importante conservar P36 mientras se reconstruye apariencia original o equivalente independiente.

Nuevo P20 JSON adjuntado a las 15:51:56 UTC: `fetchAssetAttempts:564`, `badFetchResponses:60`, `distinctFailures:19`. Entre los faltantes sigue `/models/creatures/training_dummy.glb`, varias 9 VFX GLB, cuatro KTX2 de efecto y cinco skins de Knight (datos del JSON). Este número **no mide NPC invisibles ni todo el alcance de P29**. El modelo dummy original tiene crédito específico `Generated creature model + animations (training_dummy)` **Project asset — With the project only**, NO CC0; no instalar como CC0. Rehacer dummy propio con KayKit CC0/recursos propios o analizar uso bajo autorización concreta del fork. Mantener sistema combat dummy original sin modelo hasta su reemplazo.

Hallazgo legal de editor: `src/ui/appearance_customizer.ts`, `src/render/characters/modular.ts`, `src/render/characters/npc_looks.ts`, `src/ui/charselect_redesign.ts` están bajo MIT del **código**, no necesitan volver a tener nueve clases jugables, se pueden adaptar al Hunter único. Los meshes, peinados, ojos, cuerpos, atlas, equipamientos empaquetados en `warrior_modular.glb` **NO** están automáticamente autorizados por MIT; CREDITS establece que medios requieren licencia propia. Desarrollar/portar una biblioteca modular HIGHFLY propia de CC0/medios adquiridos; conservar `npc_looks.ts` como datos/configuración al remapear caras y peinados. El fallback P36 es provisional y no se debe retirar hasta validar el sustituto.

Prioridades explícitas actualizadas:
1. Confirmar NPC visibles **e interactivos**, preservar misiones/comercio y mirar `HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json` si existen problemas residuales en los modelos; ya se ve el botón P35 en las capturas.
2. Restaurar variedad visual con assets propios/CC0 por roles/rasgos sin tocar clase única de jugador ni romper NPC. Diseñar piezas modular HIGHFLY compatibles, no todos knights.
3. Rehacer maniquí de entrenamiento 3D original y legal (P20 falta `training_dummy.glb`).
4. Diagnosticar y reparar guardado offline.
5. Iconos de bolsa, inventario, faroles/campana, traducción y menús premium.

NO convertir P20 "19 fallos" en una promesa de mundo completo. NO eliminar P36 sin sustituto visible. NO publicar las imágenes/personajes del autor sin licencia individual.

## P37 — variedad visual NPC con seis rigs CC0 y sin assets externos (31 Oct 2026)
Tras **P36 confirmado en imágenes** (NPCs visibles pero todos parecidos a Warrior), la causa probable de fallback persistente es que los rigs alternativos `player_paladin` / `player_rogue` / `player_mage` exigen donantes de clips/armas ausentes aunque sus cuerpos GLB originales CC0 estén presentes. P37 no sustituye la funcionalidad RPG ni el Hunter Universal: crea seis visuales NPC de cuerpo fijo `highfly_npc_{knight,mage,rogue,barbarian,paladin,druid}`, basados en modelos `models/chars/players/*.glb` aprobados en P33, **sin `animUrls` externos ni `attach` faltantes**, con tint discreto según `Entity.color`, y los registra en el manifest para preload. Mapea explícitamente los nueve NPC del tutorial a roles aproximados (Odo→Druid, Maren/Rook→Knight, Wick→Mage, Finch/Bryn/Tam→Rogue, Pell→Barbarian, Nel→Druid) y también el resto de NPC del mundo según `NPC_KEYS`. El visual original individual y la configuración `npc_looks.ts` se conservan en código, pero estos nuevos cuerpos **no recrean peinados/ojos/rostros** del GLB modular no verificado. Respetar datos originales y reconstruir módulos propios después. **P36 queda intacto** como red de seguridad ante cualquier nuevo error.

Nuevos `scripts/highfly_p37_npc_cc0_roles.py` y `tests/test_highfly_p37_npc_cc0_roles.py`. Se instalan solo en `.workspace/highfly-origin-stage-p0/src/render/characters/manifest.ts`, con dry-run y backup. Chequean ruta/cabecera de seis GLB, existencia de fallback P36/P34, anclas y escritura. No afectan scripts del repositorio original, simulación, misiones, clases, guardado ni publicación.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p37_npc_cc0_roles.py'
python3 scripts/highfly_p37_npc_cc0_roles.py
python3 scripts/highfly_p37_npc_cc0_roles.py --apply
python3 scripts/highfly_p9_private_build_smoke.py
```

**Aún por validar desde navegador**: que distintos NPC usen rigs diferenciados, que sigan interactivos (F Talk, quests, vendor) y que los nueve tutoriales estén representados. Mantener botón P35 y descargar `HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json` para examinar fallback y error interno si persisten clones. El muñeco del tutorial `training_dummy.glb` continúa faltando y su autorización es `With the project only`, no CC0; requiere sustituto licenciado. Guardado offline, inventario, iconos, decoración y editor Hunter siguen pendientes de corrección separada.

Licencias: `appearance_customizer.ts`, `npc_looks.ts`, `modular.ts` son código MIT reutilizable conservando licencia; la biblioteca 3D `warrior_modular.glb` con cabellos/piezas particulares no adquiere CC0/MIT por estar en el repositorio. P37 utiliza los seis modelos KayKit CC0 acreditados y recuperados, **no** reutiliza esa biblioteca de geometría no verificada.

## P38 — causa REAL de NPC todos Warrior y maniquí invisible (31 Oct 2026)
El usuario adjuntó `HIGHFLY_P35_NPC_BOLSA_INVENTARIO.json` y nuevo P20. P35 reveló **111 `actor_visual_error`**, 14 `npc_fixed_fallback_success`, ocho NPC-view candidates. Todos los NPC anotados `highfly_npc_druid` (Ferryman Odo), `highfly_npc_rogue` (Warden Tam y otros), `highfly_npc_knight` (Maren/Rook), `highfly_npc_barbarian` (Pell) fallan por `character asset not preloaded: models/chars/players/<rol>.glb`; P36 finaliza con `fallbackKey: player_warrior`. **El fallo no es ausencia del modelo GLB en disco**, ni desactivación de nueve clases: falta completar la precarga interna/URL de producción y `gltfByUrl` antes del renderizador. El registro P35 también muestra 43 imágenes DOM rotas (iconos de inventario) que **no** son la prioridad actual. P20 conserva 19 rutas GLB/KTX2 que no incluyen GLB NPC, pero sí `models/creatures/training_dummy.glb`. Este modelo original es Tripo project-only y no debe presentarse como CC0.

Nuevo `scripts/highfly_p38_npc_preload_and_dummy.py` + `tests/test_highfly_p38_npc_preload_and_dummy.py`: cuatro parches **SOLO en stage privado** y copia de asset CC0 documentado:
1. `src/render/assets/media.ts` enruta directamente seis modelos NPC KayKit CC0 de `public/models/chars/players/*.glb` y un blanco CC0 (el stage no contiene necesariamente el `/media/<hash>.glb` de ClaudeCraft original).
2. `src/render/characters/assets.ts` exporta `preloadHighflyNpcRoleBodies()` que llama a `prepareCharacterUrl` y llena el verdadero registro `gltfByUrl`. Un fallo individual no impide entrar al juego, P36 sigue de respaldo.
3. `src/main.ts` invoca la precarga de seis antes de construir/renderizar el mundo.
4. `src/render/characters/manifest.ts` usa como apariencia 3D de `mob_training_dummy` el recurso `models/biome/hex_target.glb`, un blanco de práctica de **KayKit Medieval Hexagon Pack CC0** procedente de `scripts/assets/specs/gale_camp.json`. Se copia el GLB original por SHA256 si faltase; no inventa geometría ni toca NPC/loot/combate/métricas de dummy. Sus clips humanoides se mantuvieron como configuración por compatibilidad temporal; el modelo objetivo es **estático**, su animación ha de validarse en navegador. No reintroduce el modelo original Tripo.

Script requiere P37/P36 existentes, valida fuente y crédito CC0, seis modelos GLB, anclas exactas, guarda backup de los cuatro TS antes de modificar. Cambios futuros de fuente → aborta. **NO probado aún en Codespaces**:
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p38_npc_preload_and_dummy.py'
python3 scripts/highfly_p38_npc_preload_and_dummy.py
python3 scripts/highfly_p38_npc_preload_and_dummy.py --apply
python3 scripts/highfly_p9_private_build_smoke.py
```
Verificar navegador: Odo ≠ Maren ≠ Pell, los nueve NPC tutorial visibles y `F Talk`; blanco de tiro en los camps de dummy, sus colisiones y contador de golpes; monitor P35 debe bajar errores `character asset not preloaded` de seis GLB. Puede persistir fallback si archivos GLB no son decodificables o precarga falla. No asegurar funcionalidad completa hasta resultado de usuario. Guardado offline e iconos siguen pendientes.

## P38 HOTFIX — Codespaces 31 Oct 2026 17:52
El usuario ejecutó la secuencia P38 original (rev `0daceb2`). Los tres unit tests pasaron, pero el **primer DRY_RUN falló antes de escribir el stage**, con `P38_SOURCE_ANCHOR_DRIFT media-direct-route count=0`. `media.ts` en el stage HIGHFLY no conserva dos líneas adyacentes idénticas al upstream. **No se aplicó P38, no corrió P9**; P37 sigue siendo la última compilación verde.

Hotfix: `scripts/highfly_p38_npc_preload_and_dummy.py` inyecta la excepción para rutas directas KayKit CC0 al comienzo de `assetUrl()`, usando una única ancla `export function assetUrl(url: string): string {`, conservando intacto cualquier resolver HIGHFLY personalizado (no presupone `import.meta.env.DEV`). Test nuevo comprueba resolver personalizado y que se inyecta la ruta antes de sus decisiones. Commit(s): `690285b`, `54202e8`.

**Siguiente comando** (P38 hotfix; sin P37):
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only && \
python3 -m unittest discover -s tests -p 'test_highfly_p38_npc_preload_and_dummy.py' && \
python3 scripts/highfly_p38_npc_preload_and_dummy.py && \
python3 scripts/highfly_p38_npc_preload_and_dummy.py --apply && \
python3 scripts/highfly_p9_private_build_smoke.py
```
Si falla otra ancla/source o falta el GLB original, el script aborta y debe investigarse, no se debe copiar recursos alternativos a ciegas. `--apply` solo corre después de dry-run correcto. No asegurar que NPC o dummy ya cambiaron visualmente sin navegador.
