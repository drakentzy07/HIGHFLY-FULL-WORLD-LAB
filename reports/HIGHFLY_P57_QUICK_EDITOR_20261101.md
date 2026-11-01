# HIGHFLY ORIGIN P57 — EDITOR DE OBJETOS SIMPLE (ESTILO SIMS)

## Decisión del usuario
El usuario confirmó que el Editor de ClaudeCraft ya existe; quiere perfeccionarlo, no reemplazarlo, con clic en edificio, arrastrar, girar un botón, aumentar/reducir y botón de escala sugerida. Mantener editor especialista original de terreno, agua, vegetación y mapas. Además necesita conexión futura al mapa HIGHFLY original con guardado y sincronización de colisiones y NPC.

## Estado previo confirmado
- P55 aplicado, tests 5/5 y P9 build verde. Navegador con `/editor.html?hf_eastbrook_studio=1`.
- Con P55, el cono gigante quedó identificado inequívocamente por raycast: ID `eastbrook_realm_builder_monument`, centro (-14.75,-102), visual medido (13.84,23.98,14.56), altura física prevista 7.6. Se oculta con efecto reversible.
- «Tu nombre aquí» es el placeholder original `REALM_BUILDER_PLACEHOLDER_NAME = 'Your Name Here'` en `src/sim/content/realm_builders.ts`, no un NPC.
- Mini casitas aún necesitan identificación de origen; pueden venir de `BUILTIN_WORLD.props.buildings`, `decorProps`, grupos fusionados o representación de distancia. No borrar sin ID.
- P56 previo se publicó, **PERO EL USUARIO NO LO APLICÓ**. NO ejecutar `scripts/highfly_p56_editor_transform.py --apply`.

## P57 publicado
- `scripts/highfly_p57_quick_editor.py` es el instalador de **una sola aplicación sobre el P55 existente**. Usa funciones de transformación del script P56 como librería Python para crear los cambios, pero **no instala P56 primero** ni repite P46–P55.
- `tests/test_highfly_p57_quick_editor.py` prueba la extensión contra el Studio generado por P55; pipeline de comprobación `.github/workflows/highfly-p57-quick-editor.yml`.
- Interfaz nueva:
  - clic sobre una casa/modelo identificado para seleccionar;
  - clic izquierdo y arrastrar sobre el objeto para mover por X/Z;
  - flechas para mover 1 unidad;
  - ↶/↷ para rotar 15°;
  - −/+ para variar escala 10%;
  - Escala sugerida: compara dimensiones del render con medidas declaradas (incluidos `decorProps.hw/hd` cuando existen); **orientativa, no certifica colisión**;
  - campos exactos plegados en `<details>`;
  - ocultar/restaurar, revertir, copiar diagnóstico;
  - «Guardar borrador + JSON»: persiste **localmente en el navegador** y exporta JSON. Al recargar el mismo navegador puede restaurar identificadores estables. No es guardado del código fuente ni del mundo jugable.
- Amplía selección del editor a `BUILTIN_WORLD.props.buildings` y decorProps etiquetados; para mallas sin ID no exportar como modificación definitiva.
- Normaliza tamaño visual del GLB del monumento cuando excede el 150% de la altura declarada, deja intacto collider/click/FX; omite proyección de ganador placeholder sin bloquear el sistema de premios.
- No se publica ni se copia KayKit SOURCE.
- Respaldo completo de seis fuentes en `.workspace/reports/highfly-p57/backups`. Si P9 falla restaura archivos anteriores a P57.

## Instrucciones de VS Code
Dejar `P55` tal como está hasta correr P57; no modificar ni borrar `.workspace`.

```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git status --short
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p56_editor_transform.py' -v
python3 -m unittest discover -s tests -p 'test_highfly_p57_quick_editor.py' -v
python3 scripts/highfly_p57_quick_editor.py
python3 scripts/highfly_p57_quick_editor.py --apply
```

Si P9 sale GREEN, reiniciar servidor:
```bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
```
Mantener Port 4174 **Private**. Editor: `/editor.html?hf_eastbrook_studio=1`. Juego `/`.

## Pendiente importante, no afirmar logrado
- P57 aún no se ejecutó ni se compiló en el Codespace privado del usuario; GitHub Actions verifica fixtures/sintaxis Python, no WebGL real ni Vite.
- El editor **NO escribe permanentemente** en la simulación o los archivos de HIGHFLY: exporta borrador revisable y almacenamiento local. El paso siguiente es un aplicador de overrides al stage privado, **validador de colisiones, NPCs, misiones y licencias** y backup antes de tocar código jugable.
- Escala sugerida es basada en dimensiones; puede requerir intervención humana.
- Borrar definitivamente una estructura sólo tras identificar su fuente; `kind:mesh` no equivale a un ID estable.
- Probar PC y Samsung S23 Ultra horizontal por separado.
