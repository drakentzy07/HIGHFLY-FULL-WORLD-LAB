# HIGHFLY — P1: visor 3D de KayKit Complete v7

Base exclusiva: World of ClaudeCraft 0.44.7, commit 493c35a108cef6c8aa290e8793107b1cd117886e.

El usuario ya confirmó CRC completo OK y extrajo Adventurers 2.0, Character Animations 1.1 y Skeletons 1.1 dentro de la carpeta privada .workspace.

## Instalar el visor sin tocar gameplay

En la SEGUNDA terminal de Codespaces, en la rama highfly-origin-commercial-p0:

```bash
git pull --ff-only
python3 scripts/highfly_install_model_pilot_0447.py --install
```

El instalador detecta un modelo válido de Adventurers y Skeletons, opcionalmente Rig_Medium_General, y copia solo esos GLB al clon ignorado de ClaudeCraft en .workspace. Añade una entrada Vite para compilar la nueva página HIGHFLY. No modifica el motor sim, el mundo, inventario, combate, NPC ni partidas.

En la PRIMERA terminal, detener Vite preview con Ctrl+C y ejecutar:

```bash
bash scripts/start_preview_0447.sh
```

Abrir el Codespaces privado del puerto 4173 en /highfly-kaykit-pilot.html. El visor permite rotación de cámara, zoom, selección de héroe/esqueleto y clips de animación disponibles.

## Estado y límites

- La escala 1,70 m de la vista es solo referencia visual. No representa altura medida del jugador en el RPG.
- Todavía no hay un actor nuevo en el mundo; la integración con NPC/monstruos es el siguiente paso luego de verificar rig y animaciones.
- No hay archivos originales de KayKit en el repositorio público. Solo se generan datos de prueba en la copia privada.
- La build actual de ClaudeCraft sigue siendo de referencia privada; nunca cambiar el puerto a Public ni publicar su dist.
- La preparación en CI no equivale a una prueba de render en Chrome ni autoriza comercializar contenido.

## Reversión

El original jugable queda accesible en la ruta / del puerto 4173. No borrar la carpeta privada del juego ni hacer git reset --hard. Los nuevos archivos de visor son highfly-kaykit-pilot.html, src/highfly_kaykit_pilot.ts y public/highfly-private-pilot dentro del clon ignorado; la integración Vite es una única entrada adicional.
