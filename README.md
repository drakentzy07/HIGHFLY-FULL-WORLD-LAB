# HIGHFLY ORIGIN — Comercial, independiente y KayKit-first

**Fuente base exclusiva: ClaudeCraft v0.44.7** (`493c35a108cef6c8aa290e8793107b1cd117886e`). **No** usamos la v0.45.4 como base. Mantener la 0.44.7 jugable intacta en `highfly-kaykit-v0447-lab`.

## Estado actual

- Código MIT de v0.44.7: candidato a reutilización legal manteniendo avisos.
- Multimedia original: **NO** aprobada para distribuir. 6.443 recursos, catalogados parcialmente.
- KayKit Complete v7: tenemos el listado de 23 packs; **todavía no importamos los modelos originales** al Codespace.
- Release comercial: **LOCKED**. La rama actual no entrega una build jugable propia.
- La publicación automática histórica de ClaudeCraft 0.45.4 fue retirada de **esta rama comercial**.

## Arquitectura

| Ruta | Función |
|---|---|
| `scripts/highfly_prepare_commercial_p0.sh` | Prepara copia privada de **código**, v0.44.7, sin multimedia original |
| `scripts/highfly_catalog_kaykit_v7.mjs` | Inventaría archivos KayKit reales cargados por el usuario en carpeta privada |
| `scripts/highfly_release_gate.mjs` | Bloquea releases hasta comprobar archivo, hash, licencia y controles finales |
| `config/highfly_approved_media.json` | Lista exacta de medios aprobados; **vacía** al empezar |
| `config/highfly_release_policy.json` | Aprobación final; **false** al empezar |

## Reconstrucción de KayKit Complete v7 a partir de 2 ZIP de fragmentos

Si los ZIP subidos contienen `fragmento_01.bin` y `fragmento_02.bin`, **no son ZIPs de packs independientes**. Son dos piezas de **un solo ZIP original**, almacenadas dentro de envoltorios ZIP. No hace falta volver a subir archivos.

Ejecutar desde `highfly-origin-commercial-p0`:

```bash
git pull --ff-only
python3 scripts/highfly_reassemble_kaykit_v7.py
```

El script comprueba nombre, orden, tamaño de ambas piezas, CRC de los envoltorios, índice ZIP reconstruido, rutas internas y duplicados; calcula SHA-256 y crea un inventario por pack. Guarda la colección **solo** en `.workspace/private-imports/KAYKIT_COMPLETE_V7_RECONSTRUIDO.zip` y el informe en `.workspace/reports/kaykit-v7/FULL_ARCHIVE_RECONSTRUCTION.json`. Por defecto no extrae ni publica ninguno de sus modelos. Si detecta un problema, no deja un ZIP aparentemente válido.

**Este resultado no aprueba licencias ni crea un juego comercial**. Luego se extraerán únicamente los packs/archivos necesarios para integrar una copia de desarrollo de HIGHFLY basada en **v0.44.7**.

## Código HIGHFLY independiente (Codespace privado de esta rama)

```bash
bash scripts/bootstrap_original.sh
bash scripts/highfly_prepare_commercial_p0.sh
```

La primera descarga la copia original v0.44.7 bajo `.workspace/` y la segunda genera `.workspace/highfly-origin-stage-p0/` sin copiar `public/`. **El resultado NO es un juego listo para probar**, ya que faltan los medios aprobados y las referencias que los usan.

Para catalogar KayKit v7, transferir desde el PC los modelos originales a:

`.workspace/private-imports/The Complete KayKit Collection v7/`

y ejecutar:

```bash
node scripts/highfly_catalog_kaykit_v7.mjs
```

No subir ZIPs ni carpetas del paquete a esta rama pública. Mantener todos los puertos de Codespaces en visibilidad **PRIVATE**. No cambiar puertos privados a públicos.

## Documentos

[Plan integral de independencia comercial y KayKit v7](docs/HIGHFLY_ORIGIN_COMMERCIAL_P0.md).

## Aviso legal

La licencia MIT del código requiere conservar los avisos correspondientes y no cubre automáticamente todas las dependencias ni archivos multimedia. No se autoriza distribución comercial hasta verificar los recursos y las marcas, además de probar el juego. Un workflow verde solo significa que los tests de políticas y scripts pasaron.
