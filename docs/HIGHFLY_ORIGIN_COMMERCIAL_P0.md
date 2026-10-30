# HIGHFLY ORIGIN — plan de independencia comercial (P0)

**Motor seleccionado exclusivamente:** World of ClaudeCraft **v0.44.7**, commit `493c35a108cef6c8aa290e8793107b1cd117886e`. **No se integran modelos ni escenas de v0.45.4.** La 0.44.7 original se conserva sin cambios como referencia jugable en la rama `highfly-kaykit-v0447-lab`.

## Estado real al 30/10/2026

- El juego de referencia funciona en PC y su personaje KayKit aparece en el creador, aunque tiene un retardo inicial observado de ~20 s.
- Inventario de 6.443 archivos `public/` del original; **6.341 sin verificar**, 43 con indicios de restricciones explícitas, 19 project-only y 40 candidatos KayKit a cotejar. Estos números son resultados de un detector parcial, no un dictamen legal de todos los medios.
- Los 11 edificios Eastbrook registrados se apoyan en siete modelos KayKit Hexagon. Sus GLB tienen cabecera válida; las licencias siguen sujetas a comprobación exacta.
- **La rama comercial no ha pasado aún revisión individual de archivos, dependencias, marca, sonido, fuentes ni UI, ni tiene una build jugable propia.** La publicación está bloqueada.

## Tres capas independientes

1. **REFERENCIA FUNCIONAL (PRIVADA)**: `highfly-kaykit-v0447-lab`, se mantiene el juego original sin sustituir modelos; puerto 4173 PRIVATE. No subir `dist/`.
2. **CÓDIGO HIGHFLY EN DESARROLLO (PRIVADO)**: `highfly-origin-commercial-p0`. Comando `bash scripts/highfly_prepare_commercial_p0.sh` prepara una copia de código fuente v0.44.7 sin copiar recursos `public/`, dentro de `.workspace/highfly-origin-stage-p0/`. No es todavía un juego jugable ni auditado por completo.
3. **HIGHFLY RELEASABLE**: se permite solo cuando el manifiesto de cada recurso exacto, la revisión de dependencias/marca/UI y la validación de juego completo hayan pasado y una persona haya documentado la aprobación. Los workflows actualmente rechazan la publicación.

## Licencias

- Código MIT: conservar archivo `LICENSE` y el aviso de copyright original donde corresponda. La licencia del repositorio no cubre automáticamente todo `public/`, los assets incrustados en código, ni todas las dependencias.
- **KayKit Complete CC0**: catalogar los archivos obtenidos de la fuente de KayKit, su versión y licencia; revisar si tienen derivados o contenido mezclado antes de marcarlos como aprobados.
- **Excluir de la distribución independiente**: modelos, texturas, iconos, música y sonidos `With the project only`, `No, permission required`, `CC BY-NC`, recursos de procedencia desconocida; también eliminar branding y marcas del juego de origen.
- El chequeo técnico de derechos **no sustituye** una revisión profesional de licencias y marcas antes de comercializar.

## Catálogo KayKit Complete v7

Hay un listado de archivos de v7 aportado por el usuario (solo nombres). Contiene 23 carpetas de paquetes; **no equivale a disponer de los modelos 3D originales en este repositorio o Codespace**. Se han localizado, entre otros:

| Pack (v7) | Prioridad HIGHFLY | Por qué |
|---|---|---|
| KayKit Adventurers 2.0 | Alta | Protagonista, NPC y skins; comprobar `Rig_Medium` / `Rig_Large` |
| KayKit Character Animations 1.1 | Alta | Movimiento, combate y compatibilidad de rig |
| KayKit Skeletons 1.1 | Alta | Monstruos esqueléticos / rig |
| KayKit Medieval Hexagon Pack 1.0.1 | Alta | Edificios existentes y ampliación de ciudad |
| KayKit Dungeon Pack 1.1 | Alta | Dungeon, salas e interiores |
| KayKit Fantasy Weapons Bits 1.0 | Alta | Armas / equipamiento visible |
| KayKit Forest Nature Pack 1.0 | Alta | Flora, roca y biomas |
| KayKit Furniture Bits 1.0 | Media | Interiores |
| KayKit RPG Tools Bits 1.0 | Media | Objetos interactivos |

**No copiar el pack completo al repositorio público**: además de ahorrar almacenamiento, importa primero solo los subpacks necesarios a la carpeta privada ignorada por Git.

### Cómo analizar modelos originales cuando estén disponibles

Subir desde el equipo local a la carpeta privada del Codespace `.workspace/private-imports/The Complete KayKit Collection v7/` los paquetes que vayamos a utilizar. Se pueden cargar con el explorador de VS Code de Codespaces; no hace falta subir todo el ZIP de una vez. Verificar que se conserven archivos `.gltf + .bin + texturas` o `.glb`, según pack. Después ejecutar:

```bash
node scripts/highfly_catalog_kaykit_v7.mjs
```

El comando solo genera metadatos locales: `.workspace/reports/kaykit-v7/KAYKIT_V7_LOCAL_CATALOG.json`. No los modifica, publica ni importa al juego. Un paquete parcialmente transferido se contará como parcial.

### Preparación de código HIGHFLY

Solo en un Codespace o clon de la rama **`highfly-origin-commercial-p0`**, ejecutando desde raíz:

```bash
bash scripts/bootstrap_original.sh
bash scripts/highfly_prepare_commercial_p0.sh
```

Si existe una etapa creada anteriormente, el comando **se niega a sobrescribirla**, para evitar pérdida de trabajo. La fase P0 no compila: las referencias gráficas todavía requieren sustituciones.

## Roadmap ejecutable

- P0: separar código y multimedia, prueba CI de prohibición de release y catálogo KayKit; **en curso**.
- P1: importar **un** modelo/pack autorizado de KayKit, mapear a un identificador de juego en un entorno de prueba aislado, validar render/colisiones/animación y demostrar rollback.
- P2: reemplazar paulatinamente todos los recursos no autorizados o desconocidos manteniendo sistemas RPG; verificar ausencia de referencias rotas.
- P3: identidad HIGHFLY, personaje único Hunter, menús Android español y HUD MOBA, guardar/progresión 1–20.
- P4: builds web y Android listas para distribución solo después de revisión legal exhaustiva, compatibilidad y QA.

## Principios acordados

- REUSE FIRST. No reconstruir sistemas que funcionan sin necesidad.
- No se repite la investigación de otro motor RPG: ClaudeCraft 0.44.7 es el baseline.
- Escalas/puertas, murallas épicas, ciudad grande e interiores se revisarán después de la identidad y licencias, no ahora.
- No se crean clases definitivas: HIGHFLY empleará Hunter universal sin especialización fija; los modelos adicionales podrán representar NPC, adversarios o skins desbloqueables tras validación visual y de animaciones.
- Nunca confundir **CI verde de pruebas de scripts** con **juego funcionando** o **licencia comercial aprobada**.
