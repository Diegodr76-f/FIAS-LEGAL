# Quórum — notas para trabajar en este repositorio

Actas, resoluciones y normativa de los cuerpos colegiados del FIAS. Es **la misma dinámica
del CLM** (`diegodr76-f/fap-contratos`, `clm/index.html`) aplicada a otro tema: un Excel que
se mantiene a mano, un robot que lo publica cifrado y una página estática que lo descifra.
Sin build, sin framework: `index.html` se abre tal cual. Sigue el estilo de código del CLM
(funciones sueltas, HTML como cadenas) y reutiliza sus piezas (`coincide()`, `edadBase()`,
`mientras()`, el router por id).

**La interfaz es «Mesa» y tiene su porqué escrito en `docs/diseno.md`.** Antes de tocar cómo se ve
algo, lee ese brief: sale de una investigación de las mejores interfaces de legislación, portales de
directorio y gestores de políticas, y es la tercera versión. Las dos anteriores se rechazaron: la
«biblioteca editorial» (pestañas, títulos con serifa, filtros al costado, fichas «Ma»/«Rg», pastillas
pastel) **se notaba hecha por una IA**, y la copia del CLM (menú azul, tarjetas de indicadores, tablas
con chips, «📖 Leer») **era el CLM**. Quien usa Quórum eligió «Mesa» entre dos prototipos completos.

Lo que la define, y no se negocia sin volver a preguntar:

- **Tres paneles**, como un buen cliente de correo: a la izquierda las **fuentes** (vistas con su
  conteo, el fondo como espacio de trabajo, «Al día» y Buscar), al centro la **lista**, a la derecha
  la **ficha**, que se abre al instante sin cambiar de página. Al pie de la ficha, la **barra de
  acción**: la acción principal con su tecla (↵ abrir el PDF, Ctrl ↵ copiar la cita). En el celular es
  una pila (fuentes → lista → ficha) con la acción principal fija abajo.
- **El estado se dice con una frase con fechas** (`fraseNorma()`, `fraseRes()`, `fraseActa()`), no con
  una insignia de color. El color se gana: solo ámbar para lo que pide atención; derogada va en gris.
- **Signos SVG, nunca emojis** (`ico()`, `sg()`). La letra es la del FIAS: **Arial Narrow** en la interfaz
  (con Archivo Narrow de respaldo donde no está instalada) y **Arial** para lo oficial —el texto de la norma
  y lo resuelto— (con Arimo de respaldo). Nada de serifas.
- **Buscar es un gesto**: Ctrl/⌘ K o «/» abren la paleta desde cualquier pantalla (`paletaHTML()`).
- **Buscar tiene que hallar.** Una sola regla (`consulta()` / `casa()` / `coincide()`): sin tildes, cada
  palabra en cualquier parte, singular o plural (`raiz()`: «combustible» halla «combustibles»; «informes» no
  se pasa a «información»). El buscador de arriba mira **todo el texto de cada norma** (`idxDe()`: artículos,
  párrafos, títulos, tablas y diagramas), no solo los artículos: un manual no los tiene, y así el Manual
  Financiero no se podía buscar. Lo más relevante va primero (palabras en el título o en la sección), hasta
  cuatro por norma y «N coincidencias más» que abre el lector con lo buscado ya marcado (`ST.qLector`). Si nada
  junta todas las palabras, ofrece lo que tiene alguna y lo dice. Los textos se bajan en segundo plano y la
  paleta dice cuántos faltan (`PRE`). El filtro de Normativa también mira el texto (`coincideNorma()`).
  Lo prueba la sección 4 de `probar_app.js` y la demostración, que trae párrafos, tabla y diagrama.
- **«Copiar cita» entrega la cita completa** (`citaDe()`), no «art. 14».
- **La marca es la del FIAS**, tomada de su hoja membretada y del template de diapositivas: el celeste
  `#00A4DC` y el lima `#BCD430` de las dos líneas del logo. El celeste puro da 2,9:1 sobre blanco, así que
  enlaces y botones van en el mismo celeste más profundo, `#006F94` (5,7:1); el puro y el lima quedan
  para la marca, la franja y lo grande (los números de punto, como los «Punto N» de las presentaciones al
  Directorio). Los logos van embebidos en `LOGO` (la CSP solo admite imágenes propias o `data:`). La
  franja tricolor amarilla, azul y roja no es del FIAS: no se usa.

Se mide en Chromium a 1366 y 390 px (y 1280, 1024, 900) con las barras de desplazamiento reales, sin
desbordes. Lo que la interfaz recuerda (recientes, panel plegado, tamaño de letra) vive en memoria, nunca
en el navegador.

**Un anexo es una norma completa.** Va en su propio renglón del catálogo, con su nombre propio
(`tituloNorma()` quita el «Anexo 8 al Manual Operativo:» del Excel) y una línea que dice de qué
manual es (`etiquetaAnexo()`); el manual lista sus anexos como documentos, no como notas al pie.

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

## Fondos

El FIAS administra fondos (FAP, FEIG…), programas y proyectos, cada uno con sus cuerpos
colegiados. La hoja Fondos los lista y la columna «Fondo» de Cuerpos dice de cuál es cada cuerpo;
las actas y resoluciones **heredan el fondo de su cuerpo**, no lo repiten. Una norma lleva el suyo
o, vacío, el de su órgano (`fondoNorma`). Todas las actas van en una sola hoja, a propósito: una
hoja por fondo obligaría a cambiar código cada vez que llega un fondo nuevo y partiría la hoja
Cambios, que cruza fondos. En la página, `ST.fondo` filtra panel y listados (`enFondo()`), con la
barra de arriba. Un Excel sin la hoja Fondos se publica igual, con la sigla escrita en Cuerpos.

## El texto de las normas: `scripts/texto.py`

Solo el texto **vigente**: el PDF que se da es el que rige hoy, y no se guarda historia (lo pidió así
quien lo usa). `texto.extraer()` saca el texto (PyMuPDF; la negrita marca títulos), mide si la capa
de texto es un OCR viejo y malo (`calidad()`: «C6digo», «lnterno») y entonces vuelve a leer con
Tesseract en español; quita encabezados y números de página y lo parte en `h1`/`h2`/`art`/`p`.
Si la numeración de artículos vuelve a 1 (la resolución que aprueba un reglamento trae su propio
Art. 1), es otra parte: los ids llevan la parte (`p1-a14`). El índice del propio PDF (renglones con
puntos guía y número de página, el título «ÍNDICE») no es texto de la norma y se descarta (`_es_indice`).

**Cada página se trata por lo que es** (`extraer()`): una página escaneada dentro de un PDF digital
(un anexo firmado) se lee con OCR —antes se perdía sin aviso—; las tablas salen como tablas (`tabla`,
celda por celda; la del encabezado que se repite y el índice armado como tabla, fuera); un flujograma
queda como `fig`, «diagrama de la pág. N» con su título y su enlace a esa página, en vez de frases
sueltas. Cada unidad lleva `pg`, su página en el PDF, para cotejar.

**Lo que pasó se mide** (`control`): qué fracción de las palabras del PDF llegó al texto (descontado lo
que se quita a propósito), qué páginas se leyeron con OCR y con qué seguridad, cuáles no pasaron. Si
algo no pasó, `revisar_paso()` lo pone en «Revisión de la matriz» con el detalle cifrado, y el lector lo
dice encima del texto con las páginas que hay que revisar. Una regla nueva del extractor se prueba con
`pdf_mixto()` de `probar_robot.py`, que junta lo difícil en cuatro páginas.

**Cada PDF se lee una sola vez.** El robot lo baja en cada corrida solo para sacarle la huella; si la
huella está en el caché, no lo vuelve a leer. La huella lleva `texto.VERSION`: **súbela** cuando cambie
lo que sale de `extraer()`, o las normas ya leídas se quedan con el texto viejo.

En el robot (`leer_textos`, `escribir_textos`): cada texto va en un archivo aparte, cifrado con una
llave al azar que viaja dentro del archivo del grupo, y con un nombre que no dice qué norma es. El
enlace de descarga («PDF para leer en Quórum») nunca se publica. Lo ya leído se guarda en el caché
de Actions, **cifrado con una llave de los secretos**: los pull requests de un fork pueden leer
cachés. En la página, `vTexto()` es el lector; las reformas con artículos de la hoja Cambios se
anotan al pie de cada uno (`artsDe`).

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
