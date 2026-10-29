# HIGHFLY — Criterios de referencia 0.45.4

## Lo que estamos haciendo
- Pegar un enlace a Codespaces **no es** declarar el juego clonado o jugable.
- La copia de trabajo se crea mediante `scripts/bootstrap_original.sh` cuando se inicia un Codespace.
- Se conserva una réplica local de los directorios de motor, interfaz, editor, servidor, datos y multimedia del runtime original. Se excluye documentación pesada y capturas históricas.
- Descarga de código y multimedia directamente del repositorio público original, fijada al commit `ebd3aa444352952321e0108b335722fe26d35716` / `v0.45.4`.
- `src/game/offline_mode_gate.ts` permite Play Offline únicamente en desarrollo.
- `/editor.html` es la entrada del editor original, no una herramienta HIGHFLY adaptada.
- Páginas, archivos ZIP, artifacts, releases y puertos públicos quedan excluidos de esta fase.

## Licencia y procedencia
1. MIT se aplica al **código fuente**, con avisos. No cubre el material multimedia.
2. Los archivos marcados `With the project only` NO entrarán en el producto HIGHFLY independiente; tampoco los reservados, CC BY-NC ni material sin licencia conocida.
3. La descarga temporal privada para inspeccionar **no es una autorización para distribuir** el proyecto original completo.
4. Las familias CC0 de `CREDITS.md` son solo candidatas: cada modelo/sonido/textura requiere trazabilidad por archivo y dependencias antes de su inclusión en una build.
5. Si un edificio de Eastbrook usa un modelo prohibido, conservar layout/código MIT pero reemplazar visual, colisión y materiales con alternativas independientes.
6. No añadir los originales a `git add`. La carpeta `.workspace/` se ignora; guardarla sin subirla ni crear paquetes redistribuibles.

## Prueba funcional pendiente
El primer Codespace debe verificar (y dejar por escrito resultados): inicio offline, creación de personaje, Eastbrook, NPC, misiones, combates/loot, inventario/bolsas, economía, guardado; acceso a editor, edición y playtest. Éxito de arranque no garantiza funcionalidad de servidor multijugador ni una build HIGHFLY.

## Nota de infraestructura
Codespaces puede tener costo y requiere capacidad de disco/RAM (el media runtime original es pesado). Puertos privados protegidos por autenticación GitHub; la dirección deja de funcionar cuando se detiene el Codespace. La variante independiente para móviles y web público se preparará después de la auditoría.
