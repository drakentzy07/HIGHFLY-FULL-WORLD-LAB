# HIGHFLY ORIGIN — cambio de estrategia P14: migración integral, no parches aislados

Fecha: 2026-10-30. Origen técnico: World of ClaudeCraft v0.44.7 fijado en 493c35a108cef6c8aa290e8793107b1cd117886e.

## Estado confirmado por terminal (no interpretar como jugabilidad)
- P12: 4/4 pruebas OK. 403 coincidencias de origen propias KayKit detectadas ANTES del lote; se importaron 40 GLB en HIGHFLY privado. 234 modelos de la familia auditada no tenían correspondencia automática o eran ambiguos.
- P13: 2/2 pruebas OK. El creador de personaje pasó a solicitar el visual KayKit del P4, pero NO hay captura posterior que pruebe render correcto.
- P9: Vite compiló con exit code 0, pero el juego no logró entrar a Eastbrook; mundo/IA/loot/inventario/guardado no fueron probados en HIGHFLY.
- La auditoría P5 inicial halló 6.456 archivos en public/ de la referencia, mientras que la etapa privada originalmente tenía solo 6. Se incorporaron modelos más tarde. No copiar public/ del original sin revisar licencias.

## Decisión de arquitectura
1. **Conservar la simulación RPG válida y su integración**: Eastbrook, mapa, NPC, monstruos y variantes, IA, combate, inventario, almacenamiento, loot de cadáveres, items, misiones, tiendas, portales, mazmorras, guardado. Mover código MIT con avisos; no confundir código y media.
2. **Reemplazar TODOS los recursos no aprobados que utilice nuestro juego**, no necesariamente reproducir 1:1 la biblioteca del proyecto original. Usar los assets KayKit Complete V7 adquiridos, packs CC0 correctamente verificados, arte original HIGHFLY y código con licencia compatible.
3. **No sustituir sistemas por maquetas** para que parezca que carga. Cada ID funcional del juego debe seguir asociado a objeto/NPC/monster/loot y los modelos reemplazados deben conservar escala, collider, interacciones, sockets y animaciones.
4. El editor de personaje definitivo es Hunter Universal (hombre/mujer), sin nueve clases. La etapa P13 sólo tiene Knight para verificar render privado, no completa la migración.
5. Desarrollo en directorios .workspace/ privados. Nada en GitHub Pages ni lanzamiento comercial sin informe de derechos y QA real.

## P14: auditoría de migración transversal
Ejecutar:
\`\`\`bash
cd /workspaces/HIGHFLY-FULL-WORLD-LAB
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_highfly_p14_full_migration_audit.py'
python3 scripts/highfly_p14_full_migration_audit.py
\`\`\`
La herramienta compara archivos de código de src/server/data, distingue cambios intencionales y no previstos, verifica sistemas RPG, cuenta todos los recursos de public/ por categorías, escanea referencias literales en el código y cruza faltantes de modelos del mundo con las coincidencias exactas de KayKit. Informa en:
- .workspace/reports/highfly-p14/MIGRATION_AUDIT_P14.md
- .workspace/reports/highfly-p14/MIGRATION_AUDIT_P14.json

No modifica el juego. Las URL generadas dinámicamente NO se detectan exhaustivamente por escaneo de literales; tampoco puede certificarse una licencia solo por nombre de archivo.

## Integración sistemática tras auditar
- Mundo base: terreno/caminos, murallas/torres, edificios y props de Eastbrook, NPC y spawn.
- Mundo exterior y mazmorras: modelos de biomas, vegetación, poblados, portales, props y optimización de precarga (solo recursos necesarios para el escenario inicial).
- Personajes y enemigos: todos los tipos y niveles, animaciones compatibles, aparición de Hunter y equipamiento visibles; preservación de IA/spawns/loot.
- Interfaz y objetos: iconos originales, menús táctiles, inventario, skills, loot, armaduras/armas visibles, español, audio.
- Verificación funcional obligatoria: offline → creación Hunter → Eastbrook → caminar/cámara → NPC → combate → cadáver/loot → inventario → equipo → misión/portal → guardado/recarga; PC y S23 Ultra horizontal.
- Cada bloque requiere: rutas disponibles, conversión válida, geometría/escala, texturas, procedencia/licencia, prueba de runtime. Sólo entonces se marca GREEN.

## Importación de siguientes lotes exactos (opcional, posterior a informe P14)
\`\`\`bash
python3 scripts/highfly_p12_world_kaykit_batch.py --apply --limit 120
python3 scripts/highfly_p14_full_migration_audit.py
python3 scripts/highfly_p9_private_build_smoke.py
\`\`\`
P12 es conservador: solo coincidencias con nombres controlados, no sobreescribe recursos existentes, detiene el lote si no puede convertir. Un match por nombre no certifica compatibilidad visual ni licencia de distribución. Los casos ambiguos se resuelven manualmente a nivel de categoría/pack, nunca asignando un objeto arbitrario.
