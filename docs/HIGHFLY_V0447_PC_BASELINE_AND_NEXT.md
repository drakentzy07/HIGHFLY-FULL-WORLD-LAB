# HIGHFLY v0.44.7 — BASELINE VALIDADA Y PRIMERA INTEGRACIÓN KAYKIT

Fecha: 2026-10-30. Rama: `highfly-kaykit-v0447-lab`. Fuente original: `493c35a108cef6c8aa290e8793107b1cd117886e`.

## Lo que funcionó en PC (observación del usuario)

- Compilación optimizada privada en el puerto 4173.
- Selector **Offline**, creación de personaje, clases y personalización.
- El modelo del personaje KayKit aparece en la pantalla de creación tras la corrección del visor; en la prueba observada demoró unos 20 segundos.
- Mundo navegable con personajes y edificios KayKit, NPC, monstruos, combate y habilidades.
- El usuario informa que inventario, equipo, loot y otras funciones RPG se comportan correctamente.

Estas son **observaciones de la prueba en PC**, no prueba automatizada de gameplay ni validación de licencia. Falta verificar editor/mapas, regiones avanzadas, guardado a largo plazo, Android horizontal, rendimiento y contenido de niveles 1–20.

## Decisión para HIGHFLY

- Congelar la base original 0.44.7 como referencia jugable.
- Preservar código MIT y IDs estables de mapa, personaje y NPC donde sea legal y técnicamente viable.
- Usar **KayKit Complete CC0** como biblioteca principal de personajes, edificios, naturaleza y enemigos; reutilizar los modelos KayKit ya presentes en la v0.44.7 tras verificación individual.
- Reemplazar material ClaudeCraft restringido, iconos de terceros sin licencia transferible, música no comercial y recursos sin procedencia. NO publicar todavía el juego original completo.
- No migrar en bloque a 0.45.4; evaluar separadamente sus mejores herramientas MIT más adelante.

## Entregables reales de fase 1

- `scripts/inventory_kaykit_0447.mjs`: recorre todo `public/` del Codespace privado, calcula SHA-256 y etiqueta de forma conservadora. Ningún archivo se marca listo para publicación.
- `scripts/plan_eastbrook_kaykit_0447.mjs`: lista IDs y modelos referenciados por `makeBuilding()` en Eastbrook, sin modificar ni borrar nada.
- `scripts/audit_kaykit_0447.sh`: confirma commit y genera ambos informes bajo `.workspace/reports/v0.44.7/media/` (privado, ignorado en Git).
- Pruebas CI para bloqueos legales, rutas seguras y preservación de IDs de edificios.

## Cómo correr la auditoría sin cerrar el juego

En VS Code, con el Codespace 0.44.7 abierto, **creá una SEGUNDA terminal** (ícono + al lado de Terminal), dejá el servidor 4173 funcionando y ejecutá:

```bash
git pull --ff-only
bash scripts/audit_kaykit_0447.sh
```

El inventario recorre y calcula hashes de miles de archivos; puede consumir CPU y disco durante su ejecución. Revisá `RESUMEN_INVENTARIO.md`, `KAYKIT_CANDIDATES.json` y `EASTBROOK_BUILDINGS.json` bajo `.workspace/reports/v0.44.7/media/`.

## Próxima integración de modelos

No necesitamos sustituir lo que ya es KayKit compatible. Primero cotejar `KAYKIT_CANDIDATES.json` contra archivos originales del **KayKit Complete** del usuario; ese paquete vive inicialmente en una carpeta privada e ignorada por Git, no se vuelca al repo público. Para cambiar un modelo en el motor mantener IDs de edificios, footprints, colisiones, puertas, NPC anchors y entrada a interiores. Para los personajes, verificar compatibilidad con `Rig_Medium` y cada clip antes de reconfigurar clases.

### Escalas HIGHFLY a verificar con humanoide de referencia 1,70 m

- Puertas de vivienda: >= 2,00 m de luz libre.
- Edificios: proporciones razonables respecto al personaje, sin paredes de escala miniatura.
- Murallas y fortificaciones: significativamente mayores que una persona; medidas definitivas según zona y paso transitable.

Las medidas son especificaciones de diseño, todavía no cambios validados en el motor. 

## Advertencia legal

El repositorio original es código MIT con multimedia de licencias separadas. `With the project only`, `No, permission required`, CC BY-NC o archivo desconocido NO es material autorizado para distribuir HIGHFLY independiente. Hasta completar comprobación por archivo, la distribución pública de la compilación original sigue bloqueada.
