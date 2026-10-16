# Diseño de Quórum

> **Elegida: dirección B «Mesa»** (§7), entre dos prototipos completos (A «Gaceta» y B «Mesa»),
> el 16 de octubre de 2026. Lo que sigue es el brief con el que se prototipó: los principios, la
> arquitectura y el vocabulario (§1–§6) valen para la interfaz actual.


Estado: provisional, para prototipar. Fecha: 16 de octubre de 2026.
Alcance: `quorum-fias/index.html` (un solo archivo, sin build, GitHub Pages).

---

## 0. El encargo en tres frases

1. La versión 1 («biblioteca editorial»: pestañas, serifa en los títulos, buscador gigante, facetas al
   costado, fichas «Ma»/«Rg», insignias pastel) **se veía hecha por una IA y costaba usarla**.
2. La versión 2 (piel del CLM: menú lateral azul, tarjetas de indicadores, tabla con chips, «Abrir» por
   fila, ficha en dos columnas) **era fácil, pero era el CLM**, y quedamos en que no lo fuera.
3. Se pide una **identidad propia y bella**, que no parezca de plantilla ni del CLM, con **la rapidez
   del CLM**: todo a uno o dos clics, el documento se abre directo y el estado se entiende sin pensar.

Del CLM se conserva **la lógica**, no la cara: `coincide()`/`pajar()` (buscar sin tildes, cada palabra
en cualquier parte), enlaces por identidad y nunca por posición, `mientras()` en los botones que
esperan, la fila que se abre con un clic. Del código de Quórum se conserva todo lo que decide:
`estado()`, `versiones()`/`versionA()`, `estadoActa()` (`PROVISIONAL_DIAS = 60`), `ST.aFecha`,
`ST.fondo` + `enFondo()`, `fusionar()`, `artsDe()`, `DB.generado` y las rutas actuales
(`#/norma/<id>`, `#/texto/<norma>~<art>`, `#/acta/<id>`, `#/resolucion/ja-fap_2026-08-08_p3`). Este
brief cambia **cómo se ve y cómo se recorre**, no qué se calcula.

**Sobre la investigación.** Cinco equipos estudiaron lectores de legislación (legislation.gov.uk, BOE,
EUR-Lex, LeyChile, NSW, NZ, eCFR, Laws.Africa, CourtListener, Westlaw/Lexis), portales de directorio
(Legistar, iBabs, ModernGov, BoardPro, eSCRIBE, congress.gov), gestores de políticas (PolicyStat,
PowerDMS, Document360, Guru, Confluence, GitBook, DocSearch, Raycast, Linear), oficio visual (GOV.UK,
USWDS, Primer, Carbon, Radix, Atlassian) y referencias latinoamericanas y de lectura. En esa sesión
WebFetch no resolvió dominios: lo descrito sale de los extractos de WebSearch, de documentación
oficial y del **código fuente** de los sistemas de diseño (leído en raw.githubusercontent.com y npm).
Lo del equipo «latam-y-lectura» es conocimiento previo **sin verificar**; se marca con (s/v). Las
medidas exactas citadas vienen del código fuente, no de capturas.

---

## 1. Principios

Diez reglas. Cada una nace de un patrón real; si un prototipo rompe una, hay que justificarlo.

### P1. El estado se dice con una frase con fechas, no con una insignia
Encima del documento va una línea completa que dice qué es, desde cuándo rige y qué lo cambia:
«Vigente, con 2 reformas; la última, del 14 de marzo de 2019 (Directorio del FIAS, punto 3).»
- Patrón: legislation.gov.uk «Point in time view as at…» y «Changes to legislation: … up to date with
  all changes known to be in force on or before…»
  (https://www.legislation.gov.uk/ukpga/1998/46/section/130/data.htm); Kenya Law «This is the version
  … as it was from 1 September 1970 to 30 December 2022»
  (https://new.kenyalaw.org/akn/ke/act/ln/1970/170/eng@1970-09-01); la cabecera de PolicyStat, con
  fechas de significado único (https://support.policystat.com/hc/en-us/articles/204564099).
- Por qué: The National Archives vio que la gente daba por vigente lo que leía. Una frase con fechas no
  se malinterpreta; una pastilla «Vigente» no dice desde cuándo ni qué viene.
- En Quórum: la frase sale de `estado()` y de `versionA()`; nunca se escribe a mano en una vista.
  Nunca «fecha» a secas: *Aprobada*, *Rige desde*, *Última reforma*, *Derogada*, *Datos al*.

### P2. El color se gana: pocos estados, forma + palabra, y color solo para lo que pide atención
- Patrón: KeyCite deja sin bandera las meras menciones
  (https://www.thomsonreuters.com/en-us/help/drafting-assistant/westcheck/keycite-status-flags);
  EUR-Lex usa las mismas palabras en lista y documento; Primer StateLabel pone **una** etiqueta fuerte
  por pantalla y en las listas solo ícono + palabra
  (https://raw.githubusercontent.com/primer/react/main/packages/react/src/StateLabel/StateLabel.module.css);
  GOV.UK pide etiquetas que sean adjetivos, no verbos ni botones
  (https://design-system.service.gov.uk/components/tag/).
- En Quórum: lo normal («vigente», «definitiva», «ordinaria») va en voz baja, sin color. Llevan color
  solo «por derogarse», «provisional con más de 60 días», «reforma sin incorporar» (ámbar) y lo que
  requiere acción (rojo). **Derogada no es un error: gris, nunca rojo, nunca tachada.** Máximo una
  marca de color por renglón. Ver el vocabulario común en §4.

### P3. La fila es la acción; el documento, a un clic desde la lista
- Patrón: Raycast, la primera acción de cada elemento se ejecuta con ↵ y la segunda con ⌘↵; el resto,
  en ⌘K (https://raw.githubusercontent.com/raycast/extensions/main/docs/api-reference/user-interface/action-panel.md);
  Legistar, columna fija «Minutes» que enlaza directo al archivo y dice «Not available» cuando falta
  (https://culver-city.legistar.com/Calendar.aspx).
- En Quórum: **dos blancos por renglón, ninguno es un botón «Abrir»**: el título (o el renglón entero)
  abre la página de Quórum; el nombre del documento («Acta definitiva», «PDF vigente») abre el PDF.
  ↵ = abrir, Ctrl/⌘ ↵ = copiar la cita, clic derecho o Ctrl/⌘ K = el resto. Ninguna acción vive solo
  en el menú contextual (Linear, https://linear.app/now/invisible-details).

### P4. Una cosa, una página: sin pestañas dentro de un documento
- Patrón: CourtListener quitó las pestañas en 2025 por una página continua con índice
  (https://free.law/2025/03/21/case-law-redesign/); la «item card» del nuevo legislation.govt.nz
  (https://legislation.govt.nz/learn-more/find-and-use-legislation/navigate-legislation/); Confluence
  sacó el árbol a una pestaña y tuvo que devolverlo al lateral (https://jira.atlassian.com/browse/CONFCLOUD-51524);
  Fastcase reconoció el error de esconder la línea de tiempo en una pestaña.
- En Quórum: la norma es **una página** (ficha arriba, texto debajo, lo relacionado al costado); el acta
  es **una página** (orden del día con lo resuelto bajo cada punto); la resolución, **una página**.

### P5. Cosido en el punto exacto
Lo resuelto va bajo su punto; la reforma, bajo su artículo; la relación, con verbo y en los dos sentidos.
- Patrón: iBabs pone el bloque «Besluit» (lo decidido) bajo cada punto del orden del día
  (https://berkelland.bestuurlijkeinformatie.nl/Agenda/Index/ad3b3444-1063-4125-964f-22d1d1c80025);
  BOE anota cada precepto modificado al pie, con enlace a la norma modificadora
  (https://www.boe.es/buscar/ayudas/legislacion_actualizada.php?lang=es); el bloque «Análisis» del BOE
  dice DEROGA / SE MODIFICA POR (https://www.boe.es/eli/es/rd/2012/02/03/302); EUR-Lex «Amended by».
- En Quórum: una fila de la hoja Cambios produce sus dos caras («Reforma a…» y «Reformada por…»), y
  aparece en la norma, en el artículo (`artsDe`), en la resolución y en el acta de la sesión que la
  resolvió. El verbo en versalitas reales (`font-variant-caps: all-small-caps`) es el único uso
  permitido de mayúsculas pequeñas.

### P6. El tiempo es un control a la vista, no una búsqueda avanzada
- Patrón: CFPB eRegulations, selector de fecha junto a las versiones (https://acus.gov/node/2571);
  NSW «Enter the exact version date» (https://legislation.nsw.gov.au/view/html/2022-11-03/act-2017-066);
  PolicyStat Timeline (https://icontracts.com/?p=857). Contraejemplo: legislation.gov.uk lo esconde en
  «Advanced Features».
- En Quórum: `ST.aFecha` deja de ser un campo escondido y se vuelve un control **global y visible**
  («Al día: hoy ▾»). Al cambiarlo, toda la aplicación (estado, filtros, listas, frase de vigencia,
  versión del PDF) se recalcula, y una franja ámbar lo dice hasta que se vuelve a hoy.

### P7. Buscar es un gesto, no una portada
- Patrón: Algolia DocSearch (modal ⌘K / «/», grupos con encabezado pegajoso, líneas de árbol, recientes,
  pie con teclas; https://raw.githubusercontent.com/algolia/docsearch/main/packages/docsearch-css/src/modal.css);
  búsqueda dentro del documento de los LII, donde el índice se convierte en la lista de resultados
  (https://liiguide.docs.laws.africa/working-with-a-document/search-inside-a-document); Algolia
  recomienda una sección por tipo de fuente.
- En Quórum: no hay buscador gigante en el inicio. Un campo compacto en la cabecera abre la paleta;
  dentro de una norma, el buscador vive sobre el índice.

### P8. Dos voces: lo oficial en serifa, lo de Quórum en sans
- Patrón: Laws.Africa recomienda serifa para el texto legislativo porque distingue 1/l/I y 0/O
  (https://laws.africa/publications/best-practices-online-legislation/); Lexis+ marca su resumen con
  otra voz visual para que nadie lo cite como norma; Butterick: 45–90 caracteres por línea e
  interlineado del 120 al 145 % (https://practicaltypography.com/line-length.html); USWDS mide 68ex.
- En Quórum: la serifa aparece **solo** en el texto de la norma (lector) y en el texto literal de lo
  resuelto. Títulos, rótulos, frases de estado, notas, avisos y botones van en sans. Esto es lo que
  separa a la tercera versión de la primera (serifa decorativa en títulos).

### P9. Los huecos se nombran
- Patrón: Legistar escribe «Not available» y la columna no desaparece; EUR-Lex avisa qué modificaciones
  aún no incluye el consolidado (https://eur-lex.europa.eu:443/content/development/developmentLatest.html);
  iBabs publica lo decidido («Als de hamer valt») antes que el acta.
- En Quórum: «Sin PDF», «Acta en elaboración: lo resuelto viene de la matriz», «La última reforma no
  trae su texto en la matriz» (`versionA().sinTextoUltima`). Nunca una celda vacía, «s/d», «undefined»
  ni una ficha en blanco. Lo que la matriz no trae (votación, páginas), simplemente no se muestra.

### P10. Todo se cita y se enlaza por su identidad
- Patrón: intro.nyc usa el número oficial como URL (https://intro.nyc/0175-2026+); la «Permanente link»
  de lokaleregelgeving.overheid.nl ofrece dos enlaces, a la versión vigente y a la que se lee
  (https://lokaleregelgeving.overheid.nl/CVDR625704/1); citeblog mostró que «Copy with reference» de
  Westlaw/Lexis entrega solo «§ 14», y entonces sobra (https://citeblog.access-to-law.com/?p=1103).
- En Quórum: cada artículo, acta y resolución tiene «Copiar enlace» y «Copiar cita» con la cita
  **completa** (formatos en §4). Los enlaces siguen siendo por id.

---

## 2. Arquitectura de información y navegación

### 2.1 Pantallas y rutas

| Pantalla | Ruta (se mantiene) | Para qué |
|---|---|---|
| Inicio («Lo último») | `#/panel` | Qué cambió y qué está pendiente |
| Normativa | `#/normativa` | Catálogo de normas y anexos |
| Norma (ficha + lector) | `#/norma/<id>` y `#/texto/<id>~<art>` | Una sola página; `texto` sigue funcionando para los enlaces ya compartidos y abre la misma página en el artículo |
| Actas | `#/actas` | Sesiones, con el PDF a un clic |
| Acta (sesión) | `#/acta/<id>` | Orden del día con lo resuelto |
| Resoluciones | `#/resoluciones` | Registro transversal de todo lo resuelto |
| Resolución | `#/resolucion/<id>` | Lo resuelto, su estado y su historia |
| Mis notas | `#/notas` | Notas privadas cifradas |
| Revisión de la matriz | `#/revision` | Cola de lo que falta en el Excel |

Fecha consultada: cuando `ST.aFecha` no es hoy, el enlace la lleva como sufijo `@AAAA-MM-DD`
(`#/norma/<id>@2019-08-08`, `#/normativa@2019-08-08`) para que «lo que regía» se pueda compartir.
Requiere ampliar `leerHash()`/`hashDe()`; sin sufijo, todo funciona como hoy.

### 2.2 El armazón, en tres niveles (común a las tres direcciones)

1. **Global**: marca, las cuatro secciones (Inicio, Normativa, Actas, Resoluciones), el **ámbito**
   (fondo + fecha), «Buscar Ctrl K» y un menú «Más» (Mis notas, Revisión de la matriz, Cerrar sesión).
2. **Pantalla**: título, frase de estado (P1), acción principal (Leer / Abrir el PDF), «Copiar cita».
3. **Contenido**: renglones, secciones con filete y título, texto.

Nada más compite con el contenido: sin tarjetas de indicadores, sin barra de color maciza, sin íconos
de color delante de cada sección.

### 2.3 Todo a uno o dos clics

| Tarea | Recorrido | Cuenta |
|---|---|---|
| Abrir el acta definitiva del Directorio del 30 sep | Actas → clic en «Acta definitiva» de su renglón | 2 clics |
| Lo mismo, con teclado | Ctrl K «dir 30 sep» ↵ (el resultado de un acta trae su PDF como acción principal) | 1 gesto |
| Leer el art. 14 del Reglamento de Adquisiciones | Ctrl K «art 14 adquisiciones» ↵ (abre el lector en el ancla, resaltado en amarillo) | 1 gesto |
| ¿Sigue vigente «JA 8 ago 2026, punto 3»? | Ctrl K «ja 8 ago 3»: el resultado ya dice su estado | 0 clics |
| ¿Qué normas regían el 8 ago 2019? | Clic en «Al día: hoy» → elegir la fecha; Normativa se recalcula | 2 clics |
| ¿Qué tenemos vigente sobre viáticos del FAP? | Resoluciones → fondo FAP → escribir «viáticos» (filtro Vigentes ya puesto) | 2 clics + escribir |
| Copiar la cita de una resolución | En la lista: seleccionar y Ctrl ↵; en la ficha: «Copiar cita» | 1 clic |
| Ver qué falta en el Excel | Inicio → «Pendiente» → la cola de revisión | 1–2 clics |

### 2.4 Elegir el fondo

- Un solo control global, **Fondo**: «Todos», y luego los de la hoja Fondos en su orden (FIAS, FAP,
  FEIG, PPD…), cada uno con su nombre completo al desplegar. Filtra Inicio y los tres listados
  (`enFondo()`); dentro de un fondo, Actas y Resoluciones ofrecen los **cuerpos** de ese fondo como
  segundo nivel (control segmentado de texto, no chips de color).
- Vive en memoria (`ST.fondo`). **No va a `localStorage`**: Quórum no guarda nada en el navegador salvo
  las notas cifradas (CLAUDE.md de quorum-fias). Tampoco va en el enlace de una ficha: un enlace a un
  acta abre esa acta aunque quien lo recibe tenga otro fondo puesto.
- Se repite dentro de la paleta de búsqueda como pastilla «en FAP ×», para que se vea que acota.
- Si la frase abierta solo da acceso a un fondo, el control no aparece y el nombre del fondo va junto
  a la marca.
- Las fichas no se filtran, pero dicen su fondo en los datos.

### 2.5 El buscador global (Ctrl/⌘ K y «/»)

Medidas de base, tomadas del CSS de DocSearch: modal de 760 px de ancho máximo, a 64 px del borde
superior, radio 10 px; campo de 56 px; resultados de 52–56 px; pie de 44 px con las teclas
(↵ abrir · ↑↓ moverse · Esc cerrar · Ctrl ↵ copiar cita). En 768 px o menos, pantalla completa y sin
pistas de teclado.

- **Grupos, en este orden** (y reordenados por contexto, como en Linear: dentro de una norma va primero
  «En esta norma»): Normas · Artículos · Actas · Resoluciones · Ir a… (comandos: «Ir a Actas»,
  «Cambiar fondo», «Ver todo al…»).
- Los **artículos cuelgan de su norma** con líneas de árbol (├ └) en SVG al 50 % de opacidad:
  «Manual Operativo › Anexo 3 › Art. 12».
- Cada resultado dice **su estado en palabras** (P2) y su acción principal a la derecha («PDF», «Leer»).
- Entiende **citas cortas**: siglas de cuerpos y fondos (JA, DIR, FAP, FEIG), fechas en cualquier
  forma («8 ago 2026», «2026-08-08», «8/8/2026») y «p. 3»/«punto 3». Reutiliza `coincide()`/`pajar()`
  para que dé lo mismo que el buscador de cada listado; comillas = frase exacta.
- Coincidencia: en negrita y subrayada con el color de acento (`text-underline-offset: .3em`), sin fondo
  amarillo: el amarillo queda para el texto de la norma (§4).
- Vacío: los abiertos en esta sesión (en memoria, nunca en el navegador) y los comandos.
  Sin resultados: «No hay nada para “x”» + sugerencias clicables («Prueba con “JA agosto 2026”»).

### 2.6 Abrir el documento directo

- El PDF se abre en pestaña nueva, con `#page=N` cuando se sepa la página.
- El enlace al PDF dice **qué** abre: «Acta definitiva», «Acta provisional», «PDF vigente», «Texto
  original (18 may 2017)». Si la matriz llega a traer peso y páginas, se añaden («PDF · 1,2 MB ·
  14 págs.»), como el componente Attachment de GOV.UK; hoy se tienen las páginas del texto leído
  (`texto.paginas`), no de las actas.
- Sin miniaturas (CSP `img-src 'self' data:`; además no se publica la imagen de un acta).
- En la ficha, el documento es el **primer** botón; en el celular, va fijo abajo.

### 2.7 Teclado (opcional, nunca indispensable)

`/` o Ctrl K buscar · ↑↓ (o j/k) moverse en una lista · ↵ abrir · Ctrl ↵ copiar cita · Esc cerrar o
limpiar · `[` plegar el índice del lector · `F` modo lectura · `Alt ←` volver. El menú contextual
(clic derecho) muestra cada acción con su atajo al lado, así se aprenden sin manual.

### 2.8 Celular (390 px)

Margen lateral de 16 px, sin desplazamiento horizontal, objetivos táctiles de 44–48 px. Los listados son
renglones de dos o tres líneas (nada de tablas); la acción principal de una ficha va en una barra fija
inferior; el índice del lector es una hoja que sube desde abajo («Art. 14 ▾»); la paleta ocupa toda la
pantalla. Se mide en Chromium (Playwright) a 1366 y 390 px con barras de desplazamiento reales
(`ignoreDefaultArgs: ['--hide-scrollbars']`), como en el CLM.

---

## 3. Pantalla por pantalla

Lo que sigue vale para las tres direcciones; cada dirección (§7) dice cómo se ve.

### 3.1 Inicio — «Lo último»

**Para qué**: responder «¿qué cambió desde la última vez?» y «¿qué falta?». Es lo que abre el Director
Ejecutivo o su asistente.

**Contenido, en orden**
1. Una línea de totales escrita como frase, con cifras que enlazan a su lista ya filtrada: «18 normas
   (15 vigentes), 32 actas y 214 resoluciones del FAP». Sin tarjetas.
2. **Lo último** (columna principal): bitácora agrupada por fecha, con encabezados en lenguaje humano
   («jueves 8 de octubre»), y debajo oraciones enlazadas, cada una con su tipo implícito en el verbo:
   - «El Directorio del FIAS aprobó como definitiva el acta del 30 de septiembre.»
   - «La Junta Administrativa del FAP resolvió 3 puntos en la sesión del 2 de octubre.»
   - «Se reformó el Reglamento de Adquisiciones (arts. 12 y 15) — Directorio, 2 oct, punto 3.»
   Salen de las fechas de la propia matriz: `acta.fecha`, `acta.aprobacion`, `cambio.fecha`,
   `norma.fecha`. Se muestran las últimas 6–8 semanas con «Ver más».
3. **Pendiente** (columna lateral en escritorio, debajo en el celular), como cola de tareas al estilo
   Guru, no como indicadores: actas provisionales con más de 60 días, reformas cuyo texto no está en
   la matriz, normas «por derogarse» con su fecha, avisos del robot (`DB.avisos`, solo `generico`).
   Cada renglón lleva a su elemento.
4. Al pie: «Datos publicados el 16 oct 2026, 06:12» (`DB.generado`), que es la fecha «al día» de
   Justice Laws de Canadá (https://laws-lois.justice.gc.ca/eng/FAQ/).

**Interacción clave**: un clic en cualquier oración abre la cosa; el fondo global filtra la bitácora.
**Inspira**: intro.nyc/recent (https://intro.nyc/recent), tableros de iBabs (Titel · Soort · Datum
wijziging), la portada de bills.parliament.uk, la cola de verificación de Guru.

### 3.2 Normativa

**Para qué**: encontrar una norma y abrirla, y saber de un vistazo si rige y cuándo cambió.

**Contenido**
- Arriba: título «Normativa», buscador local (filtra mientras se escribe) y tres controles en texto:
  Tipo (Todos, Reglamento, Manual, Política, Código, Estatuto), Estado («Vigentes» por defecto) y la
  fecha global si no es hoy.
- Lista agrupada por **familia**: las normas sueltas y, bajo el Manual Operativo, sus anexos anidados con
  líneas de árbol (├ └), cada anexo con su nombre propio (`tituloNorma()`) y su número.
- Cada renglón: **nombre** (16 px, peso 600) · segunda línea en secundario: «Directorio del FIAS ·
  aprobada el 18 may 2017 · última reforma 14 mar 2019» o «sin reformas» · a la derecha: estado
  (§4) y el enlace «PDF vigente».
- Las derogadas, plegadas al final: «Ver las 3 derogadas».
- Al pie: «Datos al 16 oct 2026».

**Interacción clave**: clic en el nombre = la página de la norma (en el lector si hay texto); clic en
«PDF vigente» = el PDF que rige a la fecha consultada (`versionA().conTexto.enlace`).
**Estados**: «reforma sin incorporar» lleva el punto ámbar y esa frase en el renglón.
**Inspira**: «Leyes Federales Vigentes» de la Cámara de Diputados de México con «Última reforma» en cada
renglón (s/v); el control «Estado al» de NSW; las listas de contenidos de GOV.UK; el árbol de DocSearch.

### 3.3 Ficha de la norma (cabecera de la página de la norma)

**Para qué**: saber qué es, si rige, quién la aprobó y qué le pasó, en menos de cinco segundos.

**Contenido, en orden de jerarquía**
1. Migas cortas si es anexo: «Manual Operativo › Anexo 4».
2. **Título** (nombre propio).
3. **Frase de vigencia** (P1), con el signo de estado (§4) delante.
4. Si aplica, aviso ámbar: «La reforma del 14 mar 2019 no trae su texto en la matriz: el PDF que se
   abre es el de la versión anterior.» (`versionA().sinTextoUltima`).
5. **Acciones**: «Leer el texto vigente» (si hay texto) y «PDF vigente»; «Copiar enlace», «Copiar cita».
6. **Datos** (lista clave–valor, GOV.UK Summary list): De (órgano, enlazado a su sesión y punto) ·
   Fondo · Tipo · Aprobada · Rige desde · Última reforma · Parte de / Anexos · Grupo de acceso ·
   Datos al.
7. «En pocas palabras» (opcional, solo si la matriz trae una columna nueva que escribe el equipo legal):
   2–4 líneas en sans, sobre un fondo tenue, rotuladas «Nota del equipo legal, no es texto oficial».
   Nunca generado con IA.
8. **Historia**: línea de tiempo vertical de la hoja Cambios. Marcador relleno = cambió el texto
   (aprobación, reforma, codificación); hueco = aclaración sin cambio de texto; con aspa = derogación;
   línea «hoy». Cada hito: fecha de vigencia en cifras tabulares, qué pasó, «Directorio del FIAS,
   punto 3» enlazado; la fecha de aprobación en gris si difiere (`rige`).
9. **Versiones**: lista corta, de la más nueva a la más vieja, cada renglón un tramo («14 mar 2019 –
   hoy», «18 may 2017 – 13 mar 2019») + origen + enlace a su PDF (`versiones()`). La vigente en
   negrita; la que corresponde a la fecha consultada, con fondo. La original se rotula «Texto
   original». Nada de desplegables.
10. **Relaciones** con verbo y en los dos sentidos: «Esta norma: DEROGA …», «Sobre esta norma: SE
    REFORMA por …», «ES ANEXO DE …», «la mencionan 5 resoluciones».
11. Mis notas sobre la norma.

**Interacción clave**: un clic en un hito o en una versión abre ese PDF; «Ver cómo estaba el…» sobre las
versiones cambia la fecha global.
**Inspira**: cabecera de PolicyStat; Metadata + Published dates de GOV.UK («See all updates»); eCFR
Timeline (relleno/hueco); EUR-Lex (vigente en negrita, la vista con fondo); BOE «Análisis».

**Límite honesto**: solo se guarda el texto **vigente** (CLAUDE.md de quorum-fias). No hay «redacción
anterior» en el lector ni comparación palabra a palabra; las versiones viejas se abren en su PDF. No
prometerlo en la interfaz.

### 3.4 Lector del texto vigente (cuerpo de la página de la norma)

**Para qué**: leer, saltar a un artículo, buscar dentro y citar. Es la pieza que más distingue a Quórum.

**Contenido** (escritorio, 1280 px o más: tres zonas)
- **Izquierda, índice** (≈ 240–260 px, pegajoso): arriba «Buscar en esta norma»; debajo, capítulos en
  peso 600 y artículos con su número en columna tabular («Art. 9», «Art. 10» alineados) y su rúbrica;
  si es anexo, arriba la familia (Manual Operativo › anexos 1, 2, 3…) con el actual marcado. El
  artículo en pantalla se marca con scroll-spy (`IntersectionObserver`), con color de texto y una raya
  fina, nunca con pastilla de fondo.
- **Centro, texto**: serifa a 18–19 px, interlineado 1,55–1,6, medida de 64–68 caracteres. El número de
  artículo **cuelga en el margen** (sangría francesa) en sans tabular; la rúbrica, que llega en
  mayúsculas («CONCURSO»), en versalitas. Bajo cada artículo reformado, una nota en cuerpo menor y en
  sans: «Reformado por el Directorio del FIAS, sesión del 14 de marzo de 2019, punto 3», enlazada; con
  más de una, se ve la última y «+2 anteriores» plegado (`<details>`). Un artículo derogado según la
  hoja Cambios no desaparece: número y nota «Derogado por…» en gris.
- **Derecha, «En esta norma»** (≈ 280–300 px): frase de vigencia corta, Versiones (con PDF), Relaciones,
  resoluciones que la reforman y Mis notas sobre el artículo visible. En la dirección C, las notas de
  reforma suben a este margen, alineadas a la altura de su artículo.
- **Barra del lector**, pegajosa: migas, «Art. 14 de 52», Buscar, Aa (tamaño 3 pasos y ancho de
  columna, en memoria), Modo lectura (`F`: oculta cabecera e índice), PDF vigente.

**Interacciones clave**
- Al pasar por el número de un artículo aparece un ancla con dos acciones: «Copiar enlace» (siempre al
  vigente: `#/texto/<id>~<art>`) y «Copiar cita» (formato en §4). En el celular: pulsación larga.
- Buscar dentro: al escribir, **el índice se convierte en la lista de resultados** agrupada por
  artículo («Art. 14 — Concurso · 3»), con fragmento; el texto resalta todas las coincidencias en
  amarillo claro y la actual en amarillo pleno; «3 de 17» con ↑↓, Enter / Mayús+Enter, Esc limpia.
  Ignora tildes. Ve también lo plegado, cosa que Ctrl F no hace.
- Llegar por enlace a un artículo: salto y resaltado amarillo durante 2 s (respetando
  `prefers-reduced-motion`).
- Remisiones internas («artículo 22», «Anexo 4») como enlaces punteados con globo del texto vigente:
  **opcional, fase 2**.
- Impresión: sin cabecera ni índice, con «Reglamento X — texto vigente al 16 de octubre de 2026,
  impreso desde Quórum» y las notas de reforma como notas al pie.

**Celular**: una columna; barra inferior fija «Índice · Art. 14 ▾ · Buscar · PDF»; el índice y los
resultados en hoja desde abajo; las notas, debajo de cada artículo.
**Inspira**: CourtListener (página continua con índice), NZ legislation (contenidos plegables),
Laws.Africa (buscar dentro), BOE (nota al pie del precepto), LeyChile (marginalia, s/v), Document360 y
GitBook (tres zonas, herramientas fijas), GOV.UK Contents list (números como marcador).

### 3.5 Actas

**Para qué**: encontrar una sesión y abrir su acta en dos clics; ver de un vistazo qué actas faltan.

**Contenido**
- Arriba: título, buscador local, control de **cuerpo** (los del fondo elegido), año.
- Lista agrupada por **año**, con el encabezado pegajoso «2026 · 6 sesiones». Cinco datos por renglón,
  como máximo, en columnas fijas (la rejilla no se descuadra cuando falta algo):
  fecha («vie 8 ago», sin año: lo dice el grupo) · cuerpo · «Ordinaria n.º 7» en texto plano (solo
  «Extraordinaria» puede llevar un rótulo discreto) · **Acta** («Acta definitiva», «Provisional»,
  «En elaboración», «Sin PDF» en gris, siempre con el mismo ancho) · Resoluciones («4»).
- Provisional con más de 60 días: punto ámbar y «hace 74 días» al pasar el cursor.

**Interacción clave**: clic en el renglón = la sesión; clic en la celda Acta = el PDF. Sin botón «Abrir».
**Inspira**: los calendarios de Legistar (columna «Minutes», «Not available»; «Approved Minutes» de
Culver City), los dos ejes separados de eSCRIBE (etapa y resultado no comparten insignia).

### 3.6 Acta (sesión)

**Para qué**: «¿qué se resolvió en el punto 3?» sin abrir 40 páginas de PDF.

**Contenido**
1. Título: «Junta Administrativa del FAP — Sesión ordinaria n.º 7»; debajo, la fecha larga con día de
   la semana: «viernes 8 de agosto de 2026».
2. **Estado del acta en una línea** (P1): «Acta definitiva, aprobada en la sesión del 12 de septiembre
   de 2026» (enlace a esa sesión, que se deduce de `acta.aprobacion` + mismo cuerpo) o «Acta
   provisional: falta el PDF firmado; lleva 74 días así».
3. **Recorrido de tres pasos**, en palabras: «Sesión celebrada · 8 ago» → «Acta provisional» →
   «Acta definitiva · 12 sep»; lo que no ha pasado dice «pendiente», nunca una fecha inventada.
   Vertical en el celular.
4. **Documentos**: «Acta definitiva» (botón principal) y «Acta provisional» si existe.
5. **Orden del día**: un bloque por punto con resolución. El **número del punto, grande y en cifras
   tabulares, cuelga a la izquierda** y es el ancla visual; a su derecha, la materia en sans y el texto
   literal de lo resuelto en serifa (oficial); debajo, solo si no está vigente: «Reformada por la JA
   del 14 nov 2026, punto 5» o «Sin efecto desde…»; si reforma una norma: «REFORMA el Reglamento de
   Adquisiciones, arts. 12 y 15». Cada punto: «Copiar cita» y enlace propio.
6. Si alguna ya no rige: «De esta sesión, 1 resolución ya no está vigente.»
7. Si el acta es «stub» (`estadoActa().key === "stub"`) o no tiene PDF: la ficha no queda vacía; nota
   sobria «El acta está en elaboración; lo resuelto se tomó de la matriz».
8. Mis notas de la sesión.

**Inspira**: iBabs (Besluit bajo cada punto, título con día y hora), ModernGov (texto del acta bajo cada
punto), BoardPro («Confirm previous minutes»: el acta se vuelve definitiva en otra sesión), recorrido de
congress.gov con la etapa dicha en texto, el sumario del BOE (s/v).

### 3.7 Resoluciones

**Para qué**: la resolución es la unidad que se consulta: «¿qué tenemos vigente sobre X?».

**Contenido**
- Arriba: buscador local; controles de fondo (global), cuerpo, año («Todos los años»), materia y
  vigencia («Vigentes» por defecto); **contador vivo** en frase: «214 resoluciones, 171 vigentes».
- Vistas con nombre como enlaces de texto: «Vigentes del FAP», «Dejadas sin efecto este año»,
  «Reformadas».
- Renglón (40–48 px, extracto hasta en dos líneas): identificador corto en cifras tabulares
  («JA-FAP · 8 ago 2026 · p. 3») · extracto de lo resuelto · materia en secundario · estado solo si no
  es vigente («Reformada», «Sin efecto» con el título atenuado y la línea «sin efecto por Directorio
  FIAS, 3 mar 2027»).
- En 1440 px o más, opcional: lista a la izquierda y vista previa a la derecha (Raycast List + Detail):
  ↑↓ cambia la vista previa sin abrir nada; lo que está en el detalle no se repite en la fila.

**Interacción clave**: ↵/clic = la resolución; Ctrl ↵ = copiar la cita; en el menú: «Abrir el acta en
PDF», «Ver la sesión».
**Inspira**: los «Overzichten» de iBabs, el registro central de BoardPro, la búsqueda de Legistar
(contador arriba, filtros por año), Raycast List con detalle.

### 3.8 Resolución

**Para qué**: saber qué se resolvió, si rige, y de dónde viene ese estado.

**Contenido, en orden**
1. Título = la cita: «Junta Administrativa del FAP · 8 de agosto de 2026 · punto 3».
2. **Frase de estado** (P1): «Vigente.» / «Reformada por la JA del FAP el 14 de noviembre de 2026,
   punto 5.» / «Sin efecto desde el 3 de marzo de 2027 por el Directorio del FIAS, punto 2.»
3. **Lo resuelto**, en serifa, a cuerpo de lectura cómodo (es lo importante, va primero).
4. Acciones: «Abrir el acta (PDF)», «Ver la sesión», «Copiar cita», «Copiar enlace»; si la resolución
   tiene documento propio (`enlace`), ese primero.
5. **Datos** (clave–valor): Órgano · Fondo · Sesión (enlace, con Ordinaria/Extraordinaria y n.º) ·
   Punto · Fecha · Materia · Vigencia · Normas que aprobó (`normasDeRes`).
6. **Historia**: tabla corta de cuatro columnas (fecha · órgano · acto · dónde), en orden cronológico
   ascendente porque se lee como relato; la fila que fija el estado actual, resaltada. Sale de la hoja
   Cambios (`cambiosA`, `cambiosPor`).
7. **Relaciones** en los dos sentidos: «REFORMA A: Reglamento X, arts. 12 y 15» / «SE DEJA SIN EFECTO
   POR: …».
8. Votación («Aprobada por unanimidad, 5 de 5»): **solo si algún día la matriz trae la columna**; si
   no, no se muestra nada.
9. Mis notas.

**Inspira**: «Decision details» de ModernGov (tres fechas distintas, lo decidido primero), Summary list de
GOV.UK, Historia de Legistar y Timeline del MOJ, EUR-Lex en los dos sentidos.

### 3.9 Pantallas secundarias

- **Entrada (frase)**: una sola columna, la marca, «Frase de acceso», «Abrir» y una línea de por qué
  es así («Los datos viajan cifrados y no se guardan en este navegador»). Nada de ilustraciones.
- **Revisión de la matriz**: cola de tareas agrupada por hoja y cuerpo, cada renglón con lo que falta
  y dónde, en el estilo de la cola del verificador de Guru, no con indicadores.
- **Mis notas**: lista por fecha con enlace a lo anotado; nota con el mismo tratamiento de «voz de
  Quórum» (sans sobre fondo tenue).

---

## 4. Vocabulario común (las tres direcciones lo comparten)

### 4.1 Estados: palabra + forma; el color, solo si pide atención

Signos en SVG de 10 × 10 px, `currentColor`, alineados a la altura de la x:

| Estado | Signo | Color en listas | Texto en lista |
|---|---|---|---|
| Vigente | círculo lleno | ninguno (secundario) | nada, o «vigente» en secundario |
| Vigente con reformas | círculo lleno | ninguno | «2 reformas» |
| Por derogarse / pierde efecto | medio círculo | ámbar | «se deroga el 1 ene 2027» |
| Derogada / Sin efecto | círculo hueco con diagonal | gris secundario; título atenuado | «derogada en 2024» |
| Aún no existía (fecha consultada) | círculo punteado | gris | «aún no existía» |
| Acta definitiva | círculo lleno | ninguno | «Acta definitiva» |
| Acta provisional | círculo hueco | ninguno; ámbar si > 60 días | «Provisional» |
| Reforma sin incorporar | triángulo | ámbar | «reforma sin incorporar» |
| Requiere acción | triángulo | rojo | la acción en palabras |

Línea de tiempo (eCFR): cuadrado relleno = cambió el texto; cuadrado hueco = sin cambio de texto
(aclaración); cuadrado con aspa = terminó la vigencia; línea vertical «hoy».

El mapa `ICONO` de `estado` (✏️ 📚 ⛔ 💬) y los demás emojis del archivo (hoy ~18 tipos) se sustituyen
por estos signos y por la familia de íconos de §6.

### 4.2 Frases de vigencia (plantillas)

- Vigente sin reformas: «Vigente desde el 18 de mayo de 2017. No tiene reformas.»
- Con reformas: «Vigente, con 2 reformas; la última, del 14 de marzo de 2019 (Directorio del FIAS,
  punto 3).»
- Por derogarse: «Vigente hasta el 1 de enero de 2027: la deroga el Directorio del FIAS, sesión del 20
  de septiembre de 2026, punto 4.»
- Derogada: «Derogada desde el 3 de marzo de 2024 por la Junta Administrativa del FAP, punto 5.» y,
  si hay relación, «Ver la norma que la reemplaza».
- Fecha consultada distinta de hoy: «Así regía el 8 de agosto de 2019. Volver a hoy.»
- Aún no existía: «El 8 de agosto de 2015 esta norma aún no existía: se aprobó el 18 de mayo de 2017.»

### 4.3 Fechas

- Listas: «8 ago 2026»; en el año en curso, «8 ago»; en listas agrupadas por año, sin año. En actas, con
  día de la semana abreviado: «vie 8 ago».
- Títulos y frases: «viernes 8 de agosto de 2026».
- Enlaces y anclas: `AAAA-MM-DD`.
- Siempre en cifras tabulares. Nunca «08/08/2026».

### 4.4 Citas canónicas («Copiar cita»)

- Resolución: «Junta Administrativa del FAP, sesión ordinaria del 8 de agosto de 2026, punto 3.»
- Acta: «Acta de la sesión ordinaria n.º 7 de la Junta Administrativa del FAP, de 8 de agosto de 2026.»
- Artículo: «Reglamento de Adquisiciones del FIAS, art. 14 (texto vigente al 16 de octubre de 2026;
  última reforma: Directorio del FIAS, 14 de marzo de 2019, punto 3).»
- Al copiar: aviso breve «Cita copiada» (1,5 s), nada más.

### 4.5 Llamadas de reforma en el texto

Número voladito simple (¹ ² ³) junto al número del artículo, que lleva a su nota. La nota empieza por la
palabra del tipo: «Reforma», «Derogación parcial», «Rige desde». **Sin códigos crípticos** como F1, C1,
R1 o «(act | ant)».

### 4.6 Voz de Quórum frente a texto oficial

Oficial (texto de la norma, lo resuelto): serifa, sobre el papel. Quórum (frases de estado, notas,
avisos, «En pocas palabras», notas privadas): sans; los avisos y notas, sobre un fondo tenue propio
de cada dirección.

---

## 5. Rasgos a evitar

### 5.1 Lo que delata una interfaz genérica de IA
- Emojis como íconos o delante de títulos (📖 Leer, 📄 Abrir, 🏛, 🗂…). Hoy hay ~18 tipos en `index.html`.
- Violeta e índigo (`#6366f1`), cualquier degradado, texto con degradado, resplandores de color.
- Inter, Plus Jakarta Sans o Geist como letra de la aplicación; y Titillium Web, que es la del CLM.
- Fondo crema (≈ `#F4F1EA`) + títulos en serifa de alto contraste + acento terracota (≈ `#D97757`).
- El kit de tarjetas SaaS: todo en tarjetas redondeadas iguales, tarjetas dentro de tarjetas, sombra +
  borde + fondo teñido a la vez, el mismo radio en todo.
- Cromo de plantilla: rótulos en MAYÚSCULAS espaciadas encima de cada título, cadenas «A · B · C» por
  todas partes (se permiten en una sola línea de metadatos; en lo demás, frases), «→» decorativo al final
  de cada enlace, monoespaciada para datos pequeños, numeración 01/02/03 donde no hay secuencia.
- Borde lateral grueso de color en tarjetas o avisos redondeados.
- Fila de 3–4 tarjetas de indicadores con un ícono dentro de un cuadrado de color.
- Héroe centrado con buscador gigante («¿Qué necesitas encontrar?»).
- Negro o grises puros (`#000`, `#111`, `#888`) y gris sobre fondos de color; texto fino y claro sobre
  blanco brillante (la queja documentada contra legislation.gov.uk).
- Fundidos con desplazamiento al hacer scroll, rebotes, animaciones de 600 ms en acciones rutinarias.
- Datos de relleno («Juan Pérez», «Acme»): la demo usa cuerpos y normas del FIAS, con fechas verosímiles.

### 5.2 El calco del CLM
- Menú lateral azul macizo (`--navy #00249C`) y fondo `#F4F6FB` con tarjetas blancas.
- Tarjetas de indicadores en el panel.
- Tabla con chips de estado arriba («cuántos dejan»), columna final «📖 Leer / 📄 Abrir» fija a la derecha.
- Ficha en dos columnas de tarjetas, con acciones y notas a la derecha.
- Titillium Web en todo, incluido el lector.

### 5.3 La repetición de la versión 1
- Pestañas que parten un documento (Ficha / Texto / Versiones / Cambios).
- Serifa en títulos de pantalla, pestañas o tarjetas.
- Fichas de dos letras («Ma», «Rg») y pastillas pastel en cada renglón.
- Filtros facetados en una columna lateral permanente.

### 5.4 Errores funcionales que la investigación documenta
- Elegir versión con desplegable + botón «Elegir» (BOE «Seleccionar redacción»): con 1–5 versiones, lista
  visible.
- Esconder el «punto en el tiempo» en opciones avanzadas (legislation.gov.uk).
- Diferencias solo por color (si algún día hay comparación: tachado + subrayado, y paleta alternativa
  como eCFR).
- Rejillas con una columna por variante de documento (las 14 columnas del JCC en Legistar).
- Navegar por carpetas o «cuadernos» para llegar a una resolución (reseñas de BoardEffect y Diligent).
- Repetir el mismo dato en la fila y en el panel de detalle (Raycast lo desaconseja).
- «Copiar cita» que entrega solo «art. 14».
- Resúmenes generados por IA presentados como si fueran la norma.
- Visualizaciones de lujo (grafos de relaciones, mapas de burbujas) para 18 normas.
- Celdas vacías, «s/d», «undefined», fichas vacías mientras el acta está en elaboración.
- Estado solo por color; verde para algo incompleto; etiquetas clicables o con verbos.

---

## 6. Restricciones técnicas y de marca

### 6.1 Técnicas (no negociables)
- **Un solo `index.html`**, sin build, sin frameworks ni librerías de componentes, CSS propio. JavaScript
  de navegador al estilo actual (funciones sueltas, HTML como cadenas, todo dato por `esc()`, todo
  enlace por `seguro()`).
- **CSP vigente**: `script-src 'self' 'unsafe-inline'` (ningún script de CDN); `style-src` solo
  `fonts.googleapis.com`; `font-src` solo `fonts.gstatic.com`; `img-src 'self' data:` (ninguna imagen
  remota; la marca va en SVG en línea).
- **Fuentes**: solo Google Fonts, dos familias como máximo, con `display=swap` y respaldo de sistema
  (`system-ui`, `Georgia`/`"Times New Roman"` para la serifa) para que la página se lea sin conexión
  a Google.
- **Íconos**: una sola familia SVG de línea, en línea en el HTML, trazo 1,5 px a 16 y 20 px,
  `stroke-linecap: round`, `currentColor`. Pueden dibujarse a mano o copiarse los trazados de Lucide
  (licencia ISC) dentro del archivo. Juego mínimo: buscar, documento, abrir fuera, enlace, copiar, cita,
  índice, Aa, modo lectura, calendario, historia, nota, candado, más, cerrar, chevrón, volver, aviso,
  hecho. **Nada de emojis como íconos.** Íconos solo donde tienen función, no delante de cada título.
- **Nada guardado en el navegador** salvo las notas cifradas: ni la frase, ni lo descifrado, ni
  recientes, ni preferencias (fondo, tamaño de letra, densidad viven en memoria y se olvidan al cerrar
  o tras `BLOQUEO_MIN`).
- **Anchos**: sin desbordes a 1366 px (con barra de desplazamiento real) ni a 390 px (margen de 16 px,
  sin scroll horizontal). Cortes: 1440 (vista previa opcional en Resoluciones), 1280 (tres zonas del
  lector), 900 (listas → renglones apilados, como hoy), 600.
- **Accesibilidad**: texto 4,5:1 como mínimo, bordes de controles e íconos sueltos 3:1; foco siempre
  visible; `prefers-reduced-motion`; objetivos de 44 px en táctil; landmarks (`nav` con
  `aria-label`, `main`), `<time datetime>`, `<dl>` para las listas clave–valor, `aria-current` en el
  índice.
- **Sistema de tokens** en `:root` (paleta, escala tipográfica, espacios 4/8/12/16/24/32/48, radios,
  alturas). Hoy hay 12 tamaños de letra entre 10,5 y 24 px, 8 radios y ningún `tabular-nums`: se reduce
  a una escala de 5–6 tamaños, 3 radios y cifras tabulares en fechas, números e índice.
- **Movimiento**: 100–150 ms en lo rutinario y 200–250 ms en cambios de vista, con
  `cubic-bezier(.2,0,0,1)`; solo se anima lo que responde a una acción.
- **Documentación**: el párrafo «La interfaz es la del CLM» y la línea «Una sola letra, Titillium Web,
  también en el lector» de `quorum-fias/CLAUDE.md` deben reescribirse con la dirección elegida, en el
  mismo commit que el cambio.
- **Columnas nuevas** (votación, páginas del acta, «En pocas palabras», artículos que aplica una
  resolución): opcionales, en `scripts/matriz.py`, y la prueba es que **sin ellas se publique lo mismo**.
  El diseño nunca depende de ellas.

### 6.2 Marca FIAS
fias.org.ec no abrió; los colores se midieron en el membrete oficial de las plantillas Word de
fap-contratos (`generador/plantillas/11_Inicio_compra_directa.docx`, `word/media/image2.jpeg`; FAP en
`16_Orden_de_compra_director.docx`). Son aproximados (JPEG).

| Color | Hex | Contraste sobre blanco | Uso permitido |
|---|---|---|---|
| Celeste FIAS | `#18A1D1` | 2,98:1 | solo marca y trazos gráficos; nunca texto |
| Lima FIAS | `#BBD13D` | 1,71:1 | solo trazo gráfico (filetes, la marca) |
| Azul tinta del membrete | `#213772` | 11,3:1 | texto, acento |
| Franja: amarillo | `#FECD00` | 1,51:1 | foco y «aquí» (con texto oscuro encima: 9,9:1) |
| Franja: azul | `#213A80` | — | franja tricolor |
| Franja: rojo | `#E3001F` | 4,9:1 | franja tricolor (no como alerta) |
| Azul FAP (jaguar) | `#243A8E` | — | solo si se usa la marca FAP |

Derivados para la interfaz, mismo matiz en OKLCH: **celeste oscuro `#006E99`** (5,7:1, enlaces y acento)
y **verde `#2B7440`** (5,7:1). El logotipo oficial no se redibuja «de memoria»: hasta tener su SVG, la
marca es la palabra «Quórum» + «FIAS» + la franja tricolor del membrete. El amarillo de la franja es el
recurso de marca común a las tres direcciones: significa **«aquí»** (foco del teclado, coincidencias
dentro del texto de una norma, artículo de destino) y no aparece en ningún otro sitio; en la paleta de
búsqueda la coincidencia va en negrita subrayada, sin amarillo (§2.5).

---

## 7. Tres direcciones visuales

Las tres cumplen §1–§6. Cambian el armazón, la densidad, la temperatura de la paleta y la voz tipográfica.

| | A «Gaceta» | B «Mesa» | C «Anotada» |
|---|---|---|---|
| Idea | Registro oficial bien compuesto | Mesa de trabajo de secretaría | Edición anotada del abogado |
| Armazón | Cabecera con fechador; una columna | Tres paneles: fuentes · lista · vista previa | Hoja con márgenes: llaves a la izquierda, anotaciones a la derecha |
| Temperatura | Fría, celeste | Cálida, grafito + tinta azul | Salvia, verde FIAS + tinta |
| Letra | Public Sans + Literata | IBM Plex Sans + IBM Plex Serif | Hanken Grotesk + Newsreader |
| Densidad | Media (48 px) | Alta (36/56 px) | Baja-media (56–64 px) |
| Fuerte en | Legibilidad, celular, claridad del estado | Velocidad con teclado, consulta diaria | Lectura y belleza del lector y del acta |

---

### Dirección A — «Gaceta»

**Idea.** Quórum como un registro oficial impecable: la cabecera es un **fechador** («al día de hoy»)
que además es la máquina del tiempo; todo es renglón con filete y frase; la marca entra por la franja
tricolor del membrete, el celeste y el foco amarillo. Bella por tipografía, contraste y ritmo, sin
adornos.

**Referencias.** GOV.UK (Summary list, Contents list, Metadata block, foco amarillo, títulos grandes en
peso 600 y enlaces subrayados), legislation.gov.uk (frase de punto en el tiempo), Federal Register
(«Document Details» al costado), Legistar (columna de documento), la «item card» de legislation.govt.nz.

**Paleta (tokens)**

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `--papel` | `#FFFFFF` | fondo de página | — |
| `--n1` | `#FAFCFD` | cabecera | — |
| `--n2` | `#F3F7F9` | barra de ámbito, índice del lector, avisos neutros | — |
| `--n3` | `#ECF1F4` | hover de renglón | — |
| `--n4` | `#E2E9ED` | renglón seleccionado, versión consultada | — |
| `--n6` | `#C9D3D7` | filetes y bordes no interactivos | — |
| `--n7` | `#B5C0C5` | bordes de campos | — |
| `--n8` | `#7C888F` | íconos inactivos, borde fuerte | 3,6:1 |
| `--n11` | `#5E6B72` | texto secundario | 5,5:1 |
| `--n12` | `#192930` | texto | 15,0:1 |
| `--acento` | `#006E99` | enlaces, ítem activo del índice, botón principal | 5,7:1 |
| `--acento-2` | `#00577A` | hover | 7,9:1 |
| `--acento-tinte` | `#E5F3F9` | fondo de «voz de Quórum» (notas, En pocas palabras) | — |
| `--ok` | `#2B7440` | solo el signo de la frase en la ficha | 5,7:1 |
| `--aqui` / `--aqui-suave` | `#FECD00` / `#FFE680` | foco, coincidencia actual / demás coincidencias | texto `#192930`: 9,9:1 / 12,1:1 |
| `--aviso` / `--aviso-tinte` | `#9D6300` / `#FFF4DA` | por derogarse, provisional > 60 d, fecha distinta de hoy | 5,0:1 |
| `--alerta` / `--alerta-tinte` | `#B42318` / `#FDECEA` | solo lo que requiere acción | 6,6:1 |
| `--franja` | `#FECD00` 50 % · `#213A80` 25 % · `#E3001F` 25 % | banda de 4 px arriba de todo | — |
| `--marca` | `#18A1D1`, `#BBD13D` | solo en la marca | — |

**Tipografía.** Interfaz: **Public Sans** 400 / 500 / 600 + 400 itálica (la del gobierno de EE. UU.,
cívica y no de plantilla; cifras tabulares con `font-variant-numeric: tabular-nums`). Texto oficial:
**Literata** (eje `opsz` 7–72) 400 / 600 + 400 itálica, pensada para leer en pantalla.
`https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap`
Escala: 13/18 metadatos · 15/22 interfaz base · 17/26 nombres en listas y frase de vigencia ·
20/28 títulos de sección · 30/36 título de página (24/30 en el celular), peso 600 y `letter-spacing:
-0.01em` desde 20 px. Lector: Literata 19/30, medida 66ch. Lo resuelto en fichas: Literata 18/29.

**Armazón (1366 px).**
- Franja tricolor de 4 px a todo lo ancho.
- Cabecera de 56 px sobre `--n1`, filete inferior `--n6`: a la izquierda «Quórum» (Public Sans 600,
  20 px) y «FIAS» en `--n11`; luego las cuatro secciones como texto (15 px, 500; la activa en `--n12`,
  600, con subrayado de 3 px en `--acento` pegado al filete, como la navegación de servicio de GOV.UK);
  a la derecha, campo falso «Buscar  Ctrl K» de 280 × 36 px (borde `--n7`, radio 6) y «Más».
- **Barra de ámbito** de 40 px sobre `--n2`, escrita como frase: «Fondo: **Todos** ▾  Al día: **viernes
  16 de octubre de 2026** ▾» y, a la derecha, «Datos publicados el 16 oct, 06:12». Si la fecha no es
  hoy, la barra entera pasa a `--aviso-tinte` y dice «Estás viendo cómo regía todo el jueves 8 de agosto
  de 2019. Volver a hoy».
- Contenido en una columna de 1120 px como máximo, centrada; fichas con columna principal de 720 px
  y lateral de 320 px (datos y relaciones); el lector se abre hasta 1300 px, en tres zonas: índice 260 ·
  texto ≈ 700 (incluido el número colgado) · margen 300.

**Listados.** Renglones con filete inferior de 1 px `--n6`, sin cebra ni tarjetas; encabezados de grupo
pegajosos en 13 px 600 `--n11` con su conteo. Actas como rejilla de columnas fijas (fecha tabular ·
cuerpo · tipo · Acta · Resoluciones), 48 px por fila. Normativa en dos líneas (nombre 17/600, metadatos
13 `--n11`), 64 px, con los anexos en árbol. Resoluciones en dos líneas (identificador tabular arriba,
extracto debajo). Los títulos no van subrayados; se subrayan al pasar. Los enlaces a documentos van
siempre subrayados (1 px, `text-underline-offset: .18em`; 2 px al pasar) con el ícono de documento.

**Ficha.** Título 30/36; debajo, «De: Directorio del FIAS   Parte de: Manual Operativo, anexo 4» en
15 px; la **frase de vigencia** en 17/26, peso 500, con el signo en `--ok`; botón principal sólido
`--acento` (40 px, radio 6, texto blanco) y secundarios de borde. Debajo, la lista clave–valor de GOV.UK
(clave al 30 % en 600, valor, acción a la derecha, filete de 1 px, 10 px de relleno vertical). Secciones
con título de 20 px y filete superior; sin cajas.

**Lector.** Índice sobre `--n2`, artículos en columna tabular, el activo con texto `--acento` y raya
de 2 px a la izquierda del número (la raya del Contents list de GOV.UK, no un borde de tarjeta). Texto
sobre `--papel`, número de artículo colgado en Public Sans 13/600 `--n11`, rúbrica en versalitas de
Literata. Notas de reforma bajo el artículo en Public Sans 14/21 `--n11`, separadas por un filete fino.
Margen derecho: «En esta norma».

**Densidad.** Media: filas de 48 px (una línea) y 64 px (dos), controles de 36–40 px, base 15 px.

**Detalles de oficio.**
1. El fechador como máquina del tiempo, siempre visible y siempre honesto (franja ámbar).
2. Foco de GOV.UK: enlace con foco = fondo `#FECD00`, texto `--n12` y subrayado grueso de 3 px; control
   con foco = anillo de 3 px `#FECD00` + 1 px `--n12`.
3. Franja tricolor de 4 px: único elemento cromático del armazón.
4. `text-wrap: balance` en títulos y `pretty` en párrafos; comillas «» y “”.
5. Árbol de anexos con líneas ├ └ en `--n6`.
6. Cifras tabulares en toda fecha y número; año omitido cuando lo dice el grupo.
7. Hoja de impresión del lector con encabezado «texto vigente al…».

**Celular (390 px).** Franja + cabecera de 52 px con marca, «Buscar» y «Menú»; la barra de ámbito se
reduce a una línea «Todos · hoy ▾» que abre una hoja; renglones a ancho completo con el enlace al
documento al final de la segunda línea; botón principal fijo abajo en las fichas.

**Riesgos.** Puede leerse «seco» o demasiado gubernamental; la navegación de texto arriba podría
recordar las pestañas de la v1 si se le ponen cajas. Mitigación: Literata en lo oficial, la franja,
ritmo vertical cuidado, ningún contenedor alrededor de la navegación.

---

### Dirección B — «Mesa»

**Idea.** Quórum como la mesa de trabajo de la secretaría: tres paneles, como un buen cliente de correo.
A la izquierda las **fuentes** (vistas con su conteo), en el centro la **lista**, a la derecha la
**vista previa**, que ya es la ficha. Se recorre con flechas, se abre con ↵, y una barra al pie dice
siempre qué va a pasar. La más rápida para quien consulta todos los días (la asistente del Director,
los abogados).

**Referencias.** Raycast List + Detail + ActionPanel (barra de acción con la tecla dibujada), Linear
(cromo atenuado, grises cálidos, menú contextual con atajos, comandos según el contexto), DocSearch
(paleta), Confluence (árbol en el lateral, plegado con `[`), Legistar (el documento como columna).

**Por qué no es el CLM.** El panel de fuentes va sobre el mismo fondo que el contenido, sin bloque de
color ni íconos de color: es una lista de **consultas con conteo** («Normativa vigente 15»), no un menú
de secciones. No hay tablas, ni tarjetas de indicadores, ni botón «Abrir», ni ficha en dos columnas: la
ficha es la vista previa, en una columna.

**Paleta (tokens)**

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `--fondo` | `#F6F6F3` | aplicación, panel de fuentes | — |
| `--panel` | `#FBFBF9` | panel de lista | — |
| `--hoja` | `#FFFFFF` | vista previa y lector | — |
| `--g3` | `#EFEEEA` | hover | — |
| `--g4` | `#E6E5E0` | seleccionado sin foco | — |
| `--g6` | `#D9D7D0` | separadores de panel y filetes | — |
| `--g7` | `#C6C3BA` | bordes de campo, teclas dibujadas | — |
| `--g8` | `#8C887E` | íconos inactivos | 3,4:1 |
| `--g11` | `#625F57` | texto secundario, conteos | 5,9:1 |
| `--g12` | `#1F1E1B` | texto | 15,4:1 |
| `--acento` | `#213772` | enlaces, texto de la fila seleccionada (la tinta del membrete) | 11,3:1 |
| `--acento-2` | `#182A5C` | hover | — |
| `--acento-tinte` | `#E8EBF5` | fila seleccionada con foco, voz de Quórum | texto secundario 5,4:1 |
| `--lima` | `#BBD13D` | solo el punto de la marca | — |
| `--aqui` / `--aqui-suave` | `#FECD00` / `#FFE680` | foco y coincidencias | — |
| `--aviso` / `--aviso-tinte` | `#9D6300` / `#FFF4DA` | | 5,0:1 |
| `--alerta` / `--alerta-tinte` | `#B42318` / `#FDECEA` | | 6,6:1 |

Modo oscuro diseñado (opcional, no invertido), bajo `prefers-color-scheme: dark`: `--fondo #161614`,
`--panel #1C1C1A`, `--hoja #22221F`, `--g6 #34332F`, `--g11 #A8A59C` (6,9:1), `--g12 #ECEBE6` (14,3:1),
`--acento #9DB0EA` (7,5:1), `--acento-tinte #2A3150` (texto 10,6:1), `--aqui #FECD00` con texto `#161614`.

**Tipografía.** **IBM Plex Sans** (ejes `wdth` 85–100 y `wght` 400–600, + 400 itálica): ancho 100 para
el texto y ancho 85 —condensada, eco del logotipo del FIAS— para conteos, fechas y metadatos. Texto
oficial: **IBM Plex Serif** 400 / 600 + 400 itálica. Las dos traen cifras tabulares de serie.
`https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wdth,wght@0,85..100,400..600;1,100,400&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap`
Escala: 12/16 · 13/18 metadatos · 14/20 base (Carbon body-01) · 16/24 · 20/28 títulos de vista
previa (600) · 24/32 título del lector. Lector: Plex Serif 18/28, medida 68ch.

**Armazón (1366 px).**
- **Fuentes** 232 px sobre `--fondo`, separador `--g6`: arriba el **conmutador de fondo** como espacio de
  trabajo («FIAS · todos los fondos ▾», 40 px); debajo «Buscar  Ctrl K»; luego grupos con título de
  12 px 600 `--g11`: Inicio · Normativa (Vigentes 15, Por derogarse 1, Derogadas 3) · Actas (un renglón
  por cuerpo del fondo, con conteo) · Resoluciones (Vigentes, Reformadas, Sin efecto) · Mis notas ·
  Revisión de la matriz (3). Renglones de 32 px, conteo a la derecha en ancho 85 tabular; activo con
  fondo `--g4`, texto `--g12` 600. Se pliega con `[`.
- **Lista** 420 px sobre `--panel`: cabecera de 48 px con el nombre de la vista y su conteo («Actas ·
  28»), filtro de año y orden; encabezados de sección pegajosos («2026 · 6 sesiones»); renglones de dos
  líneas de 56 px (o una línea de 36 px en modo compacto).
- **Vista previa** fluida sobre `--hoja` (≈ 700 px a 1366): es la ficha completa (§3.3, §3.6, §3.8) en
  una columna de 640 px como máximo.
- **Barra de acción** de 44 px al pie de la vista previa: a la izquierda la acción principal con su
  tecla («↵ Abrir acta definitiva»), luego «Ctrl ↵ Copiar cita», a la derecha «Acciones Ctrl K».
- El **lector** ocupa la mesa entera: el panel de lista se convierte en el índice (con «Buscar en esta
  norma»), las fuentes se pliegan, y a 1440 px o más aparece la tercera columna «En esta norma».

**Listados.** Sin tablas. Línea 1: título (14/500 `--g12`) y, a la derecha, la fecha en ancho 85
`--g11`. Línea 2: lo secundario (13 px `--g11`: «Ordinaria n.º 7 · 4 resoluciones») y el signo de
estado. Selección: fondo `--acento-tinte` y texto `--acento`, sin borde de color. Con la vista previa
visible, la fila no repite lo que ya dice el detalle.

**Ficha (vista previa).** Título 20/28 600; frase de estado 14/20 en `--g12` con su signo; documentos
como lista corta con ícono; datos en `<dl>` de dos columnas estrechas (clave 30 % en `--g11`); secciones
separadas por filete `--g6` con título de 13 px 600. Todo cabe en un vistazo sin desplazarse en el caso
típico.

**Lector.** Índice en el panel de lista; texto en Plex Serif sobre `--hoja`; número de artículo colgado
en Plex Sans ancho 85, 13/600; notas de reforma bajo el artículo en 13/19 `--g11`; barra del lector
integrada en la barra de acción («↵ Copiar enlace al art. 14 · Ctrl ↵ Copiar cita · F Lectura»).

**Densidad.** Alta: 32 px en fuentes, 36/56 px en listas, controles de 32 px, base 14 px. Un modo
«cómodo» (40/64 px, base 15) en memoria.

**Detalles de oficio.**
1. Teclas dibujadas (`<kbd>` de 20 × 20, radio 4, borde `--g7`) en la barra de acción y en el menú
   contextual: el ratón enseña los atajos.
2. Menú contextual con clic derecho en cualquier fila, con las mismas acciones que la paleta.
3. Conmutador de fondo como espacio de trabajo, con el nombre completo del fondo en el menú.
4. Plex condensada (ancho 85) para cifras: columnas de conteos y fechas que alinean como un libro mayor.
5. Selección por fondo, nunca por borde; transición de la vista previa de 120 ms, solo opacidad.
6. Los separadores de panel son de 1 px y se pueden arrastrar (lista de 360 a 520 px), en memoria.
7. Modo oscuro diseñado con tokens propios.

**Celular (390 px).** Pila de navegación: Fuentes → Lista → Ficha, con «‹ Actas» arriba para volver; la
barra de acción se queda abajo con la acción principal en grande (48 px); la paleta ocupa la pantalla.

**Riesgos.** Es la estructura de las herramientas SaaS de moda: si se cuela Inter, el índigo o las
sombras, se vuelve «otra app genérica». Tres paneles aprietan a 1366 px y no existen en el celular (allí
es otra navegación). El panel de fuentes, mal hecho, recuerda el menú del CLM. Es la que más estado de
interfaz añade al código.

---

### Dirección C — «Anotada»

**Idea.** Quórum como una edición anotada, el código comentado que el abogado tiene en la mesa: cada
pantalla es una **hoja** con un margen izquierdo donde **cuelgan las llaves** (fechas, números de punto,
números de artículo) y un margen derecho donde van las **anotaciones** (reformas, relaciones, notas). El
inicio es un **sumario** fechado, como el del diario oficial. La más bella para leer, la que más
identidad propia tiene.

**Referencias.** BOE (sumario diario; notas bajo el precepto) (s/v), LeyChile (citas de reforma en el
margen) (s/v), CourtListener (página continua con marginalia), iBabs y ModernGov (lo resuelto bajo cada
punto), Primer Timeline (hilo fino con marcadores), Medium y Readwise Reader (columna de lectura, modo
lectura) (s/v).

**Por qué no es la v1.** La v1 era «biblioteca»: serifa en títulos, pestañas, facetas, fichas de dos
letras. C pone la serifa solo en lo oficial, los títulos en grotesca, no tiene pestañas ni facetas, y su
identidad está en la **estructura de márgenes**, no en el adorno.

**Paleta (tokens)**

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `--fondo` | `#F5F7F4` | mostrador alrededor de la hoja (salvia muy leve, no crema) | — |
| `--hoja` | `#FFFFFF` | hoja de contenido, con filete, sin sombra | — |
| `--s3` | `#EDF1EC` | hover | — |
| `--s4` | `#E4EAE3` | seleccionado, versión consultada | — |
| `--s6` | `#D3DBD2` | filetes | — |
| `--s7` | `#BCC6BB` | bordes de campo | — |
| `--s8` | `#86908A` | íconos inactivos | 3,3:1 |
| `--s11` | `#59635C` | texto secundario, llaves de fecha | 6,2:1 |
| `--s12` | `#18211C` | texto | 16,5:1 |
| `--acento` | `#22663F` | enlaces, activo (verde FIAS profundo) | 6,9:1 |
| `--acento-2` | `#184F30` | hover | — |
| `--acento-tinte` | `#E6F2E9` | voz de Quórum (notas, avisos neutros) | — |
| `--tinta` | `#213772` | números colgados de artículos y puntos | 11,3:1 |
| `--lima` | `#BBD13D` | filete de marca de 2 px bajo «Quórum» y regla vertical del margen del lector (decorativo) | — |
| `--aqui` / `--aqui-suave` | `#FECD00` / `#FFE680` | foco y coincidencias | — |
| `--aviso` / `--aviso-tinte` | `#9D6300` / `#FFF4DA` | | 5,0:1 |
| `--alerta` / `--alerta-tinte` | `#B42318` / `#FDECEA` | | 6,6:1 |

**Tipografía.** Interfaz: **Hanken Grotesk** 400 / 500 / 600 + 400 itálica (cifras tabulares de serie,
grotesca cálida, fuera de las listas de «letra de IA»). Texto oficial: **Newsreader** (eje `opsz` 6–72)
400 / 500 + 400 itálica.
`https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,400;0,500;0,600;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap`
Escala: 13/18 · 15/22 base · 17/26 · 20/28 · 28/34 título y números de punto colgados (600, tabular,
`--tinta`). Lector: Newsreader 19/31, medida 64ch. Lo resuelto: Newsreader 18/29.

**Armazón (1366 px).**
- Línea superior de 52 px sobre `--fondo`: «Quórum» (Hanken 600, 18 px) con su filete lima de 2 px;
  en el centro, el **omnibox** de 440 px «Buscar o ir a…  Ctrl K», que es la navegación principal; a la
  derecha, «Normativa  Actas  Resoluciones  Más» en 15 px.
- Debajo, la **línea de ámbito como frase con huecos**: «Mostrando **todos los fondos**, al día de
  **hoy**.» — cada parte subrayada es un control.
- La **hoja** centrada de 1040 px (blanca, filete `--s6`, sin radio ni sombra: es papel), con márgenes
  internos: llaves 168 px · cuerpo 600 px · anotaciones 224 px (más 24 px de relleno a cada lado).
  Bajo 1100 px, las anotaciones bajan bajo el cuerpo; bajo 700 px, las llaves se vuelven una línea
  encima del renglón.
- En el lector, la hoja se desplaza a la derecha para dejar el índice (232 px, pegajoso) sobre el
  mostrador: 232 + 24 + hoja (96 + 600 + 240 + 48) = 1240 px.

**Listados (sumarios).**
- Actas: el **año** cuelga en el margen (28 px, `--s11`, tabular); cada sesión, con su fecha «8 ago»
  colgada en la columna de llaves; en el cuerpo, «Junta Administrativa del FAP, sesión ordinaria n.º 7» y
  debajo «4 resoluciones · Acta definitiva» (enlace al PDF); en el margen derecho, solo lo que pide
  atención («provisional desde hace 74 días»).
- Resoluciones: la llave es el identificador «JA-FAP · p. 3» con su fecha; el cuerpo, el extracto de lo
  resuelto en Newsreader 17; el margen, su estado si no es vigente.
- Normativa: la llave es el año de aprobación; el cuerpo, el nombre y «Directorio del FIAS»; el
  margen, la última reforma y el estado.

**Ficha.** La lista clave–valor **usa las columnas de la hoja**: la clave cuelga en el margen de llaves,
el valor en el cuerpo (un registro impreso, sin cajas). La frase de vigencia, primera línea del
cuerpo, en 17/26. Relaciones y Mis notas en el margen derecho. La historia, como hilo fino vertical
(Primer Timeline: 2 px `--s6`, marcadores de 20 px) con la fecha en la columna de llaves.

**Lector.** La pieza central de la dirección: número de artículo colgado en `--tinta` 15/600 tabular,
con una regla vertical lima de 1 px que separa la columna de llaves del texto; texto en Newsreader;
**notas de reforma en el margen derecho, alineadas a la altura de su artículo** (en sans 13/19
`--s11`, con su llamada voladita), y las notas privadas también allí, sobre `--acento-tinte`. Modo
lectura (`F`) deja solo la hoja.

**Acta.** El número de cada punto cuelga en 28/34 `--tinta`; a su derecha la materia en Hanken 600 y lo
resuelto en Newsreader; las relaciones («REFORMA el Reglamento…») y el estado, en el margen. Es la
lectura del orden del día como un sumario.

**Inicio.** Sumario fechado: los días cuelgan en la columna de llaves («jue 8 oct»), las oraciones de lo
último van en el cuerpo, y «Pendiente» ocupa el margen derecho.

**Densidad.** Baja-media: renglones de 56–64 px, más aire entre grupos (32–48 px), base 15 px.

**Detalles de oficio.**
1. Llaves colgadas en cifras tabulares, alineadas a la línea base del primer renglón de su bloque.
2. Anotaciones al margen alineadas con su artículo o su punto; en el celular, debajo.
3. La frase de ámbito con huecos («Mostrando todos los fondos, al día de hoy») como control.
4. Versalitas reales en los verbos de relación (DEROGA, SE REFORMA POR).
5. Hoja de papel sin sombra; el único color de marca son dos filetes lima.
6. Imprimir da exactamente la misma hoja.
7. Llamadas voladitas simples (¹ ²) que unen el texto y su nota del margen.

**Celular (390 px).** Sin márgenes laterales: la llave se vuelve una línea pequeña encima de cada
bloque («8 ago · 2026»), las anotaciones van debajo con filete a la izquierda, el omnibox se convierte en
un botón «Buscar» a pantalla completa, y las secciones en una fila de tres palabras bajo la cabecera.

**Riesgos.** Es la que más cerca puede quedar de la v1 si la serifa se sube a los títulos o vuelven las
pastillas. Escanea más despacio que A o B con 200+ resoluciones. Los márgenes comen ancho a 1366 px, y en
el celular pierde parte de su identidad. Alinear notas al margen con su artículo exige JavaScript de
posicionamiento (o `position: sticky` por bloque) y pruebas cuidadosas.

---

## 8. Recomendación provisional

**Prototipar las tres sobre los mismos datos de demo** y las mismas tres pantallas (Inicio, Acta,
Lector), y decidir con cinco tareas cronometradas con quien usa Quórum: abrir el acta definitiva del
Directorio del 30 sep; decir si sigue vigente «JA 8 ago 2026, punto 3»; leer y citar el art. 14 del
Reglamento de Adquisiciones; decir qué normas regían el 8 ago 2019; encontrar lo vigente sobre viáticos
del FAP.

**Apuesta provisional: A «Gaceta» como base, con dos préstamos.**
- De **B**, el modelo de acción: fila = ↵, Ctrl ↵ = cita, menú contextual con atajos, barra de acción
  fija en las fichas del celular y, a 1440 px o más, la vista previa en Resoluciones.
- De **C**, los números de punto colgados en el Acta y las llaves colgadas del lector.

**Por qué A.**
1. Es la que más se aleja **a la vez** del CLM (no hay menú lateral, ni tarjetas, ni tabla con chips) y
   de la v1 (serifa solo en lo oficial, sin pestañas en el documento, sin pastillas, sin héroe).
2. Su identidad sale del FIAS (franja tricolor, celeste, foco amarillo) y de una **función** —el fechador
   que es máquina del tiempo—, no de adorno: eso es lo contrario de «hecho por IA».
3. Una columna se comporta igual a 1366 y a 390 px: hay menos que aprender y menos riesgo de desborde.
4. Es la más legible para gerentes y el Director (base 15–17 px, contraste 15:1, enlaces subrayados).
5. Es la de menor riesgo de implementación en un solo `index.html` con HTML en cadenas.

B es más rápida para el uso intensivo diario, pero su estructura es la de las apps SaaS de moda y no
existe en el celular; C es la más bella para leer, pero escanea más despacio y es la que más fácil
recae en la v1. Si en la prueba con usuarios la asistente del Director (uso diario, teclado) gana con
B, se toma B para Actas y Resoluciones y se mantiene el lector de A.

---

## 9. Fuentes principales

Lectores: legislation.gov.uk (https://www.legislation.gov.uk/ukpga/1972/49/section/4), BOE
(https://www.boe.es/buscar/ayudas/legislacion_actualizada.php?lang=es), EUR-Lex
(https://eur-lex.europa.eu/content/online-learning/eurlex-content/finding-consolidated-texts-transcript-en.pdf),
NSW (https://legislation.nsw.gov.au/help/show-hits), NZ
(https://legislation.govt.nz/learn-more/find-and-use-legislation/navigate-legislation/), eCFR
(https://www.ecfr.gov/reader-aids/ecfr-recent-updates/introducing-timeline-filtering), Laws.Africa
(https://liiguide.docs.laws.africa/working-with-a-document/search-inside-a-document,
https://laws.africa/publications/best-practices-online-legislation/), CourtListener
(https://free.law/2025/03/21/case-law-redesign/), Justice Laws Canadá
(https://laws-lois.justice.gc.ca/eng/FAQ/), lokaleregelgeving (https://lokaleregelgeving.overheid.nl/CVDR625704/1),
citeblog (https://citeblog.access-to-law.com/?p=1103), Butterick (https://practicaltypography.com/line-length.html).

Directorio: Legistar (https://culver-city.legistar.com/Calendar.aspx), iBabs
(https://berkelland.bestuurlijkeinformatie.nl/Agenda/Index/ad3b3444-1063-4125-964f-22d1d1c80025),
ModernGov (https://democracy.plymouth.gov.uk/ieDecisionDetails.aspx?ID=4770), BoardPro
(https://help.boardpro.io/en/articles/1248180-confirm-previous-minutes), intro.nyc (https://intro.nyc/recent),
congress.gov (https://www.congress.gov/help/legislation), MOJ Timeline
(https://design-patterns.service.justice.gov.uk/components/timeline/).

Políticas y herramientas: PolicyStat
(https://support.policystat.com/hc/en-us/articles/204564099-What-do-the-Sections-on-the-Policy-Header-Mean-),
PowerDMS, Document360 (https://docs.document360.com/docs/revision-history.md), Guru
(https://www.getguru.com/features/verification), Confluence
(https://support.atlassian.com/confluence-cloud/docs/get-to-know-the-new-and-simplified-content-layout/),
DocSearch (https://raw.githubusercontent.com/algolia/docsearch/main/packages/docsearch-css/src/modal.css),
Raycast (https://raw.githubusercontent.com/raycast/extensions/main/docs/api-reference/user-interface/list.md),
Linear (https://linear.app/now/invisible-details).

Oficio visual: GOV.UK Frontend
(https://raw.githubusercontent.com/alphagov/govuk-frontend/main/packages/govuk-frontend/src/govuk/components/summary-list/_mixin.scss,
.../settings/_colours-functional.scss), GOV.UK Publishing Components (metadata, published_dates,
attachment, contents_list), USWDS (tokens de medida e interlineado), Primer (StateLabel, Timeline),
Carbon (@carbon/type, @carbon/layout), Radix Colors (understanding-the-scale), Atlassian Lozenge;
listas contra el «aspecto de IA»: skill frontend-design de Anthropic, Impeccable, Laith0003/ux-skill.

Marca: membrete y logos medidos en `fap-contratos/generador/plantillas/11_Inicio_compra_directa.docx`,
`16_Orden_de_compra_director.docx` y `crm/plantillas/14_Informe_adenda.docx`.
Fuentes tipográficas verificadas el 16 oct 2026 en fonts.googleapis.com (las seis familias y ejes de §7
responden 200).
