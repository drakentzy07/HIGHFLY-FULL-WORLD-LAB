# HIGHFLY — P1 KayKit v0.44.7: Prueba visual y de integridad

## Estado

Base 0.44.7 funcional en PC, personaje KayKit recuperado en creador. El original permanece intacto. Esta prueba trabaja con los modelos KayKit que **ya estaban en ClaudeCraft**, no agrega todavía el pack Complete comprado por el usuario.

## Primer test de recursos y escala (privado)

Mantener el juego en el puerto 4173 **Private**. En otra terminal:

```bash
git pull --ff-only
bash scripts/run_kaykit_p1_0447.sh
```

El script verifica el commit original, las 11 estructuras de Eastbrook, los siete modelos KayKit referenciados, cabeceras y tamaño de archivos GLB, metadatos del pack y dimensiones de layout. Se niega a marcar todo como aprobado si falla un modelo o una evidencia. No modifica recursos ni compila el juego.

Abrir `.workspace/reports/v0.44.7/pilot/KAYKIT_EASTBROOK_P1.md` y el JSON complementario. **Este es un test de metadatos y cabeceras, no una prueba de render, colisiones, malla interior o derechos de redistribución individual.**

## Segundo test, manual, en el juego actual

1. Entrar Offline con un personaje KayKit y llegar a Eastbrook Vale.
2. Examinar **una casa**, **la taberna**, **el taller** y **la iglesia**. Situarse junto a las entradas para capturar la escala relativa a un personaje de referencia de 1,70 m. La altura total del edificio no garantiza altura real de puerta.
3. Caminar por las calles y alrededor de paredes, puertas y objetos; observar colisiones, clipping, terreno, NPC y marcadores de misión.
4. Repetir el combate normal, loot e inventario cerca de la zona para asegurar que no cambió la base funcional.

Medir aparte interior, planta superior, apertura de puertas y recorrido entre zonas: el inventario de 11 edificios no demuestra que todos tengan interiores jugables. Registrar ausencias como pendientes y no dar por hecho un interior.

## Después del test P1

- No sustituir las 11 casas KayKit existentes si son compatibles y su licencia individual queda verificada. Mantener su ID y referencias.
- Preparar importación **privada** del KayKit Complete del usuario desde un ZIP o carpeta en `.workspace/`, sin subirlo al repositorio público.
- Inventariar personajes, animaciones `Rig_Medium`, casas, interiores, decorados y monstruos y probar primero **un solo recurso nuevo** en una ubicación aislada, con rollback.
- Solo entonces comenzar los reemplazos de assets restringidos, uno por uno, antes de publicación.

### Ideas futuras anotadas, sin implementarlas en P1

Hunter universal persistente (sin clases); skins como apariencia desbloqueable sin cambiar estadísticas base; KayKit humanoides hostiles como bandidos, guardianes o enemigos (IA propia de NPC); monstruos no humanoides con rig/animaciones específicos. Es un catálogo de contenido para fases posteriores, no una modificación a la base probada.

## Restricción

Las 40 entradas `KAYKIT_CC0_CANDIDATE` son **candidatas**; los 6.341 `BLOCKED_UNVERIFIED` son sin clasificar, **no 6.341 infracciones demostradas**. No usar la preview original para distribución pública. CI verde verifica scripts y política, no juego completo en Android.
