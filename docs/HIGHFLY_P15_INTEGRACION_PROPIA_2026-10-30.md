# HIGHFLY P15 — MIGRACIÓN PROPIA Y VERIFICADA (PRIVADA)

## Objetivo
Usar el mundo y los sistemas RPG MIT de ClaudeCraft v0.44.7 como base técnica modificable, con recursos visuales HIGHFLY/KayKit CC0 y sin medios restringidos, marcas originales ni dependencia del servidor online original.

## Qué hace P15
1. Revisa el commit original fijado, integridad RPG, P4/P8, ZIP KayKit Complete V7 y CREDITS.md.
2. Recupera archivos de código MIT faltantes sin pisar modificaciones HIGHFLY.
3. Integra solamente medios originales en una lista POSITIVA de licencias CC0 o Apache-2.0: Basis KTX2, materiales de terreno ambientCG, superficies ambientCG/Poly Haven, determinados HDRI CC0 y texturas CC0 de terreno. Mantiene hashes y procedencia.
4. Aplica un logo SVG HIGHFLY de primera parte y los títulos HIGHFLY a index.html/play.html sin alterar IDs del DOM. El sistema de traducciones, marketing, enlaces y menús antiguos todavía requiere una migración posterior.
5. Importa todas las coincidencias exactas restantes P12 de modelos propios KayKit por lotes de hasta 120. Omite los 234 casos ambiguos o sin equivalencia hasta revisar escala, geometría, colisiones y animaciones.
6. Corre auditoría P14 ANTES y DESPUÉS y compilación independiente P9. No publica ni copia arte no aprobado.

## Código Terminal 2
Detener servidor privado 4174 con Ctrl+C si sigue en ejecución; luego:

    cd /workspaces/HIGHFLY-FULL-WORLD-LAB
    git pull --ff-only && python3 -m unittest discover -s tests -p 'test_highfly_p15_takeover.py' && python3 scripts/highfly_p15_takeover.py --apply

Para solo diagnosticar y no modificar: python3 scripts/highfly_p15_takeover.py

## Reportes
- .workspace/reports/highfly-p15/P15_HIGHFLY_OWNERSHIP.json
- .workspace/reports/highfly-p15/before/MIGRATION_AUDIT_P14.md
- .workspace/reports/highfly-p15/after/MIGRATION_AUDIT_P14.md
- .workspace/reports/highfly-p9/VITE_BUILD_P9.log

## Lo que P15 NO afirma
Un Vite exit 0 NO prueba mundo jugable. Miles de referencias multimedia pueden seguir sin reemplazo y la primera entrada a Eastbrook puede bloquearse. No se ha implementado aún el Hunter Universal completo, nuevo HUD MOBA, todos los NPC/monstruos/armaduras ni una identidad UI final.

## QA obligatorio para declarar HIGHFLY jugable
OFFLINE -> Hunter visible -> Eastbrook -> movimiento/cámara -> NPC/quest -> monstruo/combate -> loot de cadáver -> inventario/equipamiento -> mazmorra/portal -> guardado/recarga -> Samsung S23 Ultra apaisado.

## Reglas legales
Todo código MIT debe conservar aviso de copyright. KayKit Complete V7 está indicado oficialmente como CC0. CREDITS.md tiene licencias particulares para multimedia; CraftPix, encargos y marcas no se copian. Las obras 'With the project only' también quedan fuera de este importador por priorizar MIT/CC0 como pidió HIGHFLY. Los visores Vercel son catálogos de consulta, no rutas que convenga consumir en tiempo real desde el motor. Usar ZIP propio y registrar mapeos locales.
