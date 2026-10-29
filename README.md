# HIGHFLY — FULL WORLD LAB

**Laboratorio PRIVADO para inspeccionar World of ClaudeCraft v0.45.4 en modo offline, sin republicar sus archivos originales.**

- Fuente original: [levy-street/world-of-claudecraft](https://github.com/levy-street/world-of-claudecraft)
- Versión inmovilizada: **v0.45.4**
- SHA de commit: `ebd3aa444352952321e0108b335722fe26d35716`
- Estado HIGHFLY FULL: **NO INTEGRADO / NO AUDITADO POR ARCHIVO / NO DESPLEGADO**.
- Arquitectura: el código y los recursos del upstream se descargan de forma temporal al Codespace; **no quedan copiados en este repositorio**.
- Política: solo recursos libres CC0 o autorizados por MIT pueden formar parte de la distribución HIGHFLY (eventuales dependencias runtime no MIT deberán tratarse explícitamente). *With the project only*, `No, permission required`, CC BY-NC, recursos sin licencia verificada, y marcas no van a la distribución.

## Primer arranque en el navegador

1. Abre [Crear Codespace privado para HIGHFLY](https://codespaces.new/drakentzy07/HIGHFLY-FULL-WORLD-LAB) con tu cuenta GitHub. Elige una máquina con **al menos 4 núcleos/8 GB RAM** si tu cuota lo permite (puede tener costo).
2. Se ejecutará `scripts/bootstrap_original.sh` al crear el Codespace: clona **la versión exacta 0.45.4** en `.workspace/claudecraft-v0.45.4/`, omite capturas/documentos enormes, instala dependencias y genera el informe de licencias.
3. Cuando finalice, en la terminal integrada ejecuta:
   ```bash
   bash scripts/start_offline.sh
   ```
4. Abre la pestaña **Ports** y selecciona el puerto **5173** con visibilidad **Private**. Copia su URL HTTPS y ábrela en Chrome del S23 Ultra con sesión GitHub.
5. En el menú del original, elige **Play Offline**. Para el editor de mapas entra a la ruta **/editor.html** de esa misma URL.

**No existe un enlace jugable todavía.** El puerto funciona solo con el Codespace encendido, hasta que se prepare una versión HIGHFLY independiente y auditada.

### Verificaciones que necesitamos realizar

- Mundo: Eastbrook y resto de regiones/campamentos/caminos.
- Combate: desplazamiento, ataques, hit/death, cadáver y loot.
- Sistemas RPG: misiones, inventario/bolsas/equipamiento, comerciantes/economía y guardado.
- Editor original 2D/3D: cargar, colocar, editar, guardar, probar.
- Reemplazo de cada archivo multimedia fuera de CC0/MIT, antes de la primera build distribuible.
- Modo offline **de desarrollo**: los servicios online, guilds y economía entre jugadores no son equivalentes a servicios offline.

## Seguridad legal y técnica

**Nunca ejecutes `git add -f .workspace` ni subas el contenido bruto del juego a este repo.** Las exclusiones están fijadas en `.gitignore`. No publiques el puerto Codespaces ni el `dist/` original: contiene potencialmente material que HIGHFLY decidió no redistribuir.

El registro multimedia original `CREDITS.md` y la licencia `LICENSE` siguen perteneciendo a la copia de origen. El parser `scripts/audit_credits.mjs` crea un registro informativo por familia; **NO autoriza ni certifica los archivos individuales**.

Esta etapa es un laboratorio para ejecutar y verificar la base, no la integración full, la distribución final ni la publicación en Pages.
