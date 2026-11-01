# HIGHFLY ORIGIN — P54 EASTBROOK SOURCE FIX (2026-11-01)

## Confirmaciones de origen
Referencia oficial v0.44.7: commit 493c35a108cef6c8aa290e8793107b1cd117886e.

- src/sim/content/zone1.ts, ZONE1_PROPS.decorProps: **kmedBlacksmith x=2,z=-112,rot=-pi/2,scale=6.5,r=4.5,h=9,hw=4.2,hd=4.05**. Es una herrería visual de Smith Haldren (no una casa oficial). A diferencia de los 11 edificios de EASTBROOK_LAYOUT, se renderiza por el loop de decorProps.
- src/render/props.ts: el loop decorProps usa addParts(..., d.key, {scale:d.scale}); el coleccionador collectBuildingImpostors usa el mismo origen para la vista lejana. El filtro isEastbrookRebuildBuilding sólo afecta buildings, NO este decorProp.
- El bloque P53 tenía materiales kmed:* cerca de (-3.9,-112): **el registro anterior es el primer candidato específico, no una prueba aún de identidad del grupo de meshes**.
- Las mini casitas sí pueden ser edificios oficiales: conservar los 11 IDs de BUILDINGS + weekly vault. P54 inventaría sus IDs y props sin eliminarlos.
- El cono dorado puede ser el cuerpo/FX del Realm Builder Monument en (-14.75,-102), pero su identidad todavía requiere comparar las URLs reversibles P51. P54 sólo añade dimensiones reales al diagnóstico.

## Alcance de P54 publicado
- scripts/highfly_p54_eastbrook_fix.py, tests/test_highfly_p54_eastbrook_fix.py.
- Sustitución **sólo en render**, sólo para el decorProp kmedBlacksmith exactamente x=2 z=-112, por hexbWorkshop (P8, GLB privado ya auditado) normalizado a visual 8.4x9.0x8.1, con sprite/impostor lejano coherente.
- La definición de simulación, NPC, misión, interacción, colisión, save y datos de ZONE1_PROPS quedan intactos.
- Inspector opt-in: ?hf_p54_inventory=1; su tabla se puede copiar como JSON desde window.__HIGHFLY_P54_EASTBROOK. El P50 ?hf_audit_eastbrook=1 sirve para comparar dimensiones de las construcciones oficiales.
- UI: native loading #ls-fill, consejo centrado en la zona inferior, badges de depuración ocultos salvo ?hf_debug_ui=1. Sin gráficos nuevos ni barras falsas.
- P54 opera en .workspace/highfly-origin-stage-p0; cada archivo editado se respalda bajo .workspace/reports/highfly-p54/backups. Hace rollback si falla P9.
- NO sube KayKit SOURCE ni ningún GLB al repositorio público.

## Ejecución en el Codespace CON el stage P53 existente
~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p54_eastbrook_fix.py' -v
python3 scripts/highfly_p54_eastbrook_fix.py
python3 scripts/highfly_p54_eastbrook_fix.py --apply
~~~

Luego, para la vista privada ya compilada:
~~~bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB/.workspace/highfly-origin-stage-p0
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
~~~

No añadir el flag P53 de ocultar kmed al test de solución permanente. Se puede probar ?hf_p54_inventory=1&hf_audit_eastbrook=1. Comparar monumento por separado con ?hf_probe_monument=hide. Revisión en PC y después S23 Ultra horizontal.

## Estado real al publicar
- GitHub: **script y tests COMMITTEADOS**.
- Pruebas de transformación local: 4/4 PASS, contra fixtures, compilación Python OK.
- Anchors buscados en el source original v0.44.7: presentes.
- Codespace/Stage: **NO EJECUTADO DESDE ESTA SESIÓN**; sin acceso remoto a su terminal/archivos privados.
- P9 Vite build, navegador privado, visual PC, Android S23: **PENDIENTES**.
- No se declara solución definitiva de la pared o cono hasta la comparación visual y/o auditoría de meshes reales.

## Próximo tramo
1. Comparar mesh KMED y caja visual tras el apply; asegurar desaparición del gigante sin ocultar KMED global.
2. Conservar los IDs/props legítimos del barrio; solucionar escalas sólo tras inventario y capturas.
3. Identificar monumento por P51, revisar fuente legal de su GLB antes de recolocar/ajustar.
4. Después: jabalíes con GLB aprobado, tablón de tutorial y FURY 360 Android.
