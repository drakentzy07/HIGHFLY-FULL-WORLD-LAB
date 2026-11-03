# HIGHFLY — ORIGINAL SKIN STUDIO (P0)

Interfaz visual para el motor genuino de skins de World of ClaudeCraft v0.45.4, conservando sin cambios su pipeline MIT.

## Abrir en Codespaces privado

1. Entrar a https://github.com/drakentzy07/HIGHFLY-FULL-WORLD-LAB/tree/highfly-original-skin-studio-p0
2. Pulsar Code > Codespaces > Create codespace on highfly-original-skin-studio-p0.
3. Esperar a que el postCreateCommand descargue el origen ClaudeCraft. Si falta la carpeta original, ejecutar: bash scripts/bootstrap_original.sh
4. Ejecutar desde la raíz de HIGHFLY-FULL-WORLD-LAB: bash scripts/start_skin_studio.sh
5. Abrir Ports > 5185 > Open in Browser. La visibilidad del puerto debe mantenerse PRIVATE.

## Cuatro motores originales disponibles

- Tripo skin: --tripo --prompt; genera texturas nuevas para el modelo existente, compuestas en un atlas UV.
- Skinmodel: crea un GLB 3D nuevo y lo riggea/anima para el sistema KayKit; requiere más tiempo y créditos.
- Repintado por OpenAI: --prompt; crea un atlas nuevo basado en la textura original, que requiere revisión.
- Recolor local: --recolor hue=...,sat=...,light=...; gratuito, únicamente cambia parámetros de color.

## Claves API

Para IA, agregar TRIPO_API_KEY y/o OPENAI_API_KEY al archivo local:

    .workspace/claudecraft-v0.45.4/.env

Ejemplo de formato; no reemplazar con claves reales en GitHub ni en el chat:

    TRIPO_API_KEY=CLAVE_CONFIGURADA_EN_EL_CODESPACE
    OPENAI_API_KEY=CLAVE_CONFIGURADA_EN_EL_CODESPACE

El proceso original carga estas variables desde ese archivo. Este laboratorio no solicita ni envía las claves al navegador. El modo Recolor no necesita claves API.

## Archivos y seguridad

- scripts/highfly_original_skin_studio.mjs: servidor con validaciones, control de concurrencia y lanzamiento del pipeline real.
- scripts/highfly_skin_studio.html: editor web con modelos, atlas, selección de clases, vista previa y descargas.
- scripts/start_skin_studio.sh: arranque con un solo comando.
- Los outputs se generan en .workspace/claudecraft-v0.45.4/tmp/asset_pipeline/.
- No se ejecuta --apply: el motor no registra el resultado en el juego ni modifica SKINS/SKIN_COUNTS.
- No se publica el SOURCE de KayKit ni recursos de ClaudeCraft. El puerto 5185 debe seguir privado.
- Tripo y OpenAI son servicios externos con costos y condiciones propias.
- Los modelos base tienen sus propias licencias en CREDITS.md; el MIT del código no se extiende al arte.

## Alcance

Este es un FRONTEND nuevo que llama a los comandos originales; upstream no posee un editor autónomo de skins listo para desplegar en un sitio estático. Es necesario ejecutar Node en Codespaces y tener el árbol del proyecto original descargado. No es equivalente al Skin Forge de tintes de Vercel ni está integrado con HIGHFLY.

Motor upstream utilizado: https://github.com/levy-street/world-of-claudecraft/blob/ebd3aa444352952321e0108b335722fe26d35716/scripts/asset_pipeline/pipeline.mjs
Licencia upstream: https://github.com/levy-street/world-of-claudecraft/blob/ebd3aa444352952321e0108b335722fe26d35716/LICENSE

Estado: código preparado en rama aislada; pendiente prueba de arranque WebGL y de ejecución de las APIs dentro del Codespace del usuario.
