# Quórum — notas para trabajar en este repositorio

Actas, resoluciones y normativa de los cuerpos colegiados del FIAS. Es **la misma dinámica
del CLM** (`diegodr76-f/fap-contratos`, `clm/index.html`) aplicada a otro tema: un Excel que
se mantiene a mano, un robot que lo publica cifrado y una página estática que lo descifra.
Sin build, sin framework: `index.html` se abre tal cual. Sigue el estilo del CLM: funciones
sueltas, HTML como cadenas, el mismo CSS (letra Titillium Web, paleta navy). Si una pieza
ya existe en el CLM (`coincide()`, `edadBase()`, `mientras()`, el router por id), se copia
de allí en vez de rehacerla.

Todo en español: interfaz, comentarios, mensajes de commit y documentación.

## Lo que no se negocia: confidencialidad

Son actas de directorio. Antes de tocar cualquier cosa que lea, guarde o publique datos:

- **Nada en claro, en ningún lado.** El robot no publica si falta la frase de un grupo, si el
  Excel no tiene contraseña o si falta una columna obligatoria (`Alto` en `publicar.py`).
- **Nada en el historial de git.** Lo publicado se despliega directo a Pages
  (`.github/workflows/publicar.yml`), nunca con commit. Eso es lo que hace que cambiar una
  frase quite el acceso. `scripts/vigilar_repo.py` lo vigila en cada push.
- **Nada en los registros.** Los registros de Actions son públicos. El robot imprime
  conteos, hojas y filas; el detalle de un aviso (`texto`) va solo dentro del archivo
  cifrado, y `generico` es lo único que se imprime. `probar_robot.py` lo comprueba buscando
  textos reales en la salida.
- **Nada guardado en el navegador**, salvo las notas, cifradas con la frase del grupo. Ni la
  frase ni lo descifrado van a `localStorage`/`sessionStorage`: el origen
  `diegodr76-f.github.io` lo comparten todas las herramientas de esa cuenta. Al cerrar
  (`cerrarSesion()`) o tras `BLOQUEO_MIN` sin uso se olvida todo.
- **Un dato del Excel nunca es código.** Todo pasa por `esc()`; todo enlace, por `seguro()`
  (solo http/https), y el robot ya descarta lo demás.

## La forma del Excel: `scripts/matriz.py`

Una sola definición de hojas y columnas que usan la plantilla (`crear_plantilla.py`) y el
robot (`publicar.py`). Una columna nueva se añade **ahí**, nunca en uno solo de los dos.
Después: `python3 scripts/crear_plantilla.py` y `--demo`, y `python3 scripts/publicar.py --demo`
para regenerar `demo/datos-demo.json`, en el mismo commit.

Toda columna que no esté en `OBLIGATORIAS` es opcional: el Excel lo maneja una persona y se
reordena. La prueba que importa al añadir una es que **sin ella se publique lo mismo que antes**.

## Programas y proyectos

Las actas se organizan por programa o proyecto, y se llenan en la hoja Programas. La columna
«Programa o proyecto» de Actas y Resoluciones es **opcional y de varios valores** (separados con
`;`): vacía = asunto general. La resolución hereda los de su acta salvo que diga otros
(`publicar.py`, `_programas_de`). En la página, un acta pertenece a un programa si ella lo nombra
**o** si alguna de sus resoluciones lo hace (`progsActa`), así el proyecto muestra la sesión donde
se resolvió algo suyo. Cada grupo de acceso recibe solo los programas que usa: el nombre de un
proyecto también es información. Un Excel sin la hoja ni las columnas se publica igual.

## La vigencia se deduce, no se marca

No hay columna «vigente». `estado()` en `index.html` la calcula de la hoja Cambios a la fecha
que se le pida (`ST.aFecha` o hoy), y de ahí cuelgan la insignia, los filtros, el panel, la
línea de tiempo y «¿qué regía en una fecha?». `versionA()` hace lo mismo con el texto. Una
regla nueva sobre vigencia va en `estado()`, no en una vista.

Identidades: un acta es `cuerpo + fecha`; una resolución, `cuerpo + fecha + punto` (así se
citan: «JA del 8 de agosto de 2026, punto 3»); una norma, su nombre. Los enlaces de la página
llevan ese id (`#/resolucion/ja-fap_2026-08-08_p3`), nunca una posición en una lista.

## Grupos de acceso

Cada cuerpo tiene un grupo (columna de la hoja Cuerpos); cada norma, el de su órgano salvo
que diga otro. Un archivo cifrado por grupo. Un cambio que toca dos grupos va en los dos
archivos, con lo mínimo del otro lado para nombrarlo (cuerpo, fecha, punto o nombre de la
norma), y la página los une por id en `fusionar()`.

## Probar

```bash
pip install openpyxl cryptography msoffcrypto-tool requests
npm install --no-save jsdom
python3 scripts/vigilar_repo.py
python3 scripts/probar_robot.py
node scripts/probar_app.js       # usa probar_robot.py --sitio: cifra Python, descifra WebCrypto
```

Los tres corren en `.github/workflows/comprobaciones.yml`. Si añades comportamiento, añade la
comprobación. Las pantallas se miran en Chromium (Playwright) a 1366 y a 390 px de ancho; jsdom
no tiene anchos.
