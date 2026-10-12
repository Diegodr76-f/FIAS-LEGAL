# Quórum · FIAS

Repositorio de las **actas y resoluciones** de los cuerpos colegiados del FIAS (Directorio
del FIAS, Junta Administrativa del FAP, Directorio del FEIG) y de su **normativa interna**,
con la vigencia de cada cosa al día: qué norma rige hoy —o regía cualquier día— después
de cada reforma, y qué resoluciones siguen vigentes o quedaron sin efecto por otra acta.

Funciona como el CLM: un Excel que se mantiene a mano, un robot que lo publica cifrado y
una página que lo descifra en el navegador.

```
Excel en OneDrive (protegido con contraseña)
   hojas: Fondos · Cuerpos · Actas · Resoluciones · Normativa · Cambios
        │  robot diario y botón «Run workflow» (GitHub Actions)
        ▼
un archivo cifrado por grupo de acceso  →  GitHub Pages, sin pasar por git
        ▼
index.html: pide la frase y descifra en el navegador
   panel · normativa con línea de tiempo · actas · resoluciones · buscador · notas
```

Para verlo sin configurar nada: abre la página y elige **«Ver con datos de ejemplo»**
(datos inventados).

## Cómo se llena el Excel

Se parte de [`plantilla/Quorum_matriz.xlsx`](plantilla/Quorum_matriz.xlsx). Su primera
hoja, **Instrucciones**, explica cada columna; cada encabezado tiene además una nota.
Lo esencial:

- **Cada fondo tiene sus cuerpos, y cada cuerpo sus actas.** La hoja Fondos trae el FIAS, el FAP
  y el FEIG (se añaden otros fondos, programas o proyectos que administre el FIAS), y en Cuerpos
  cada cuerpo dice de qué fondo es: la Junta Administrativa del FAP es del FAP. Las actas de todos
  van en la misma hoja, y en Quórum se elige arriba qué fondo ver, o todos.
- **Un acta** es un cuerpo y una fecha de sesión. Es **provisional** hasta que tiene enlace
  al acta definitiva o fecha de aprobación.
- **Una resolución** es un cuerpo, una fecha y un punto: «en la Junta Administrativa del
  8 de agosto de 2026, en el tercer punto» se escribe `JA-FAP · 08/08/2026 · 3`.
- **Una norma** lleva el órgano que la aprueba (el Manual de Ciclo, la JA-FAP) y la fecha.
- **La vigencia no se escribe: se deduce.** Cada vez que una resolución reforma, codifica,
  deroga, deja sin efecto o aclara una norma u otra resolución, se añade **un renglón en
  Cambios**. El renglón viejo no se toca. Quórum calcula de ahí el estado a cualquier
  fecha, la línea de tiempo y qué versión del texto regía.

Lo que no cuadra (una resolución sin su acta, un cambio que apunta a una norma que no
existe) no frena la publicación: aparece en **Revisión de la matriz**, con hoja y renglón.

## Confidencialidad

Las actas son más delicadas que los contratos, así que hay cinco diferencias con el CLM:

1. **Un archivo y una frase por grupo de acceso.** La columna *Grupo de acceso* de la hoja
   Cuerpos dice qué frase abre las actas de cada cuerpo. Si todos los abogados ven todo,
   basta un grupo (`legal`). Si el Directorio debe verlo solo una parte, se le pone otro
   grupo y otra frase, y esa frase no abre lo demás.
2. **Lo publicado no entra al historial de git.** El robot despliega directo a GitHub
   Pages. Así, cambiar la frase quita el acceso: lo anterior deja de estar en línea, y no
   quedan versiones viejas que se abran con la frase de antes.
3. **El Excel va protegido con contraseña.** El robot lo baja con un enlace; sin
   contraseña, ese enlace daría todo en claro. Si el Excel no está protegido, el robot no
   publica.
4. **La página no guarda nada.** Ni la frase ni lo descifrado. Al cerrar la pestaña, o
   tras 20 minutos sin uso, hay que volver a escribir la frase. Lo único que queda en el
   navegador son las notas de cada quien, cifradas con la frase.
5. **Los PDF no se publican.** Cada acta o norma enlaza a su documento en OneDrive, que
   conserva sus propios permisos.

Además, el registro del robot en GitHub (que es público) solo trae conteos y números de
fila, nunca el contenido de una celda. Y `scripts/vigilar_repo.py` impide en cada push que
entre al repositorio un Excel, un PDF o cualquier dato real.

**Lo que este modelo no puede hacer:** saber quién consultó qué, o impedir que alguien
comparta su frase. Si se necesita eso, hay que pasar a inicio de sesión con la cuenta de
Microsoft.

## Configuración (una sola vez)

1. **El Excel.** Copia la plantilla a tu carpeta de OneDrive, llénala y ponle contraseña, como
   a un PDF: en Excel de escritorio, *Archivo → Información → Proteger libro → Cifrar con
   contraseña*. La contraseña la inventas tú (anótala: Excel no la recupera). Es el secreto
   `EXCEL_CLAVE` del paso 4. Un libro con contraseña se edita en Excel de escritorio, no en el
   navegador.
2. **El enlace.** En OneDrive: *Compartir → Cualquier persona con el vínculo → puede ver*,
   y copia el enlace. Como el libro tiene contraseña, el enlace solo entrega un archivo
   cerrado.
3. **Las frases.** No hay que inventarlas: en la página de entrada, el botón «Generar una frase
   nueva» da seis palabras al azar. Una por grupo de acceso (con un solo grupo, `legal`, es una).
   Es la que se entrega a quienes van a consultar; no es la contraseña del Excel.
4. **Los secretos.** En GitHub: *Settings → Secrets and variables → Actions → New
   repository secret*:

   | Secreto | Qué lleva |
   |---|---|
   | `EXCEL_URL` | el enlace del paso 2 |
   | `EXCEL_CLAVE` | la contraseña del Excel |
   | `CLAVES` | una línea por grupo: `legal = palabra-palabra-palabra-palabra-palabra-palabra` |

5. **GitHub Pages.** *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
6. **Publicar.** *Actions → Publicar Quórum → Run workflow*. Después corre solo cada día
   a las 6:15, y cada vez que cambia el código.

Las frases se entregan **de palabra o en persona**: por correo o WhatsApp quedan escritas en
otro lado para siempre.

**Para quitarle el acceso a alguien:** genera una frase nueva para su grupo, cámbiala en
`CLAVES`, publica, y entrega la nueva a quienes siguen.

## El logo

Guarda el archivo junto a `index.html` como `logo.svg` (o `logo.png`) y escribe su nombre
en `MARCA.logo`, al inicio del script de `index.html`.

## Para quien mantiene el código

Ver [`CLAUDE.md`](CLAUDE.md). Las pruebas:

```bash
pip install openpyxl cryptography msoffcrypto-tool requests
npm install --no-save jsdom
python3 scripts/vigilar_repo.py     # ningún dato real en el repositorio
python3 scripts/probar_robot.py     # el robot
node scripts/probar_app.js          # la página
```
