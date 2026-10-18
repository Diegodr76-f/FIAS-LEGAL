# -*- coding: utf-8 -*-
"""
Del PDF de una norma a su texto vigente, partido en títulos y artículos.

    python3 scripts/texto.py norma.pdf            muestra lo que sacó (para revisar)
    python3 scripts/texto.py norma.pdf --json     el resultado tal como lo publica el robot

Es lo que hace que una norma se lea en Quórum como en Lexis: índice al costado,
artículo por artículo, con buscador. Solo el texto VIGENTE: el PDF que se le da
es el que rige hoy; no se guarda historia.

Dos clases de PDF, y se tratan distinto:
  - Nacido digital (exportado de Word): el texto sale exacto, y la negrita dice
    qué es título.
  - Escaneado: o no trae texto, o trae una capa de OCR vieja y mala («C6digo»,
    «lnterno»). Se mide eso, y si es malo se vuelve a leer con Tesseract en
    español, que en una página limpia acierta casi todo. Lo que sale de un OCR
    se marca como tal, para que la página avise que puede tener errores.

Cada página se trata por lo que es, no el documento entero: un manual digital
con dos páginas escaneadas (un anexo firmado) lee esas dos con OCR; las tablas
salen como tablas; un flujograma no se vuelve frases sueltas: queda como
«diagrama de la pág. N», con su enlace al PDF. Cada unidad lleva su página.

Y se mide lo que pasó: `control` dice qué fracción de las palabras del PDF llegó
al texto (descontando encabezados, pies e índice, que se quitan a propósito),
qué páginas se leyeron con OCR y con qué seguridad, cuáles son diagramas y
cuáles no traían texto legible. El robot avisa en «Revisión de la matriz»
cuando algo no pasó, y el lector lo dice arriba del texto.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

# Súbela cada vez que cambie lo que sale de `extraer()`: el robot guarda lo ya
# leído por la huella del PDF Y esta versión, así que con otra versión lo relee.
VERSION = "3"

ART = re.compile(r"^Art(?:[íi]culo|\.)?\s*(\d+)\s*(?:[.ºo°]\s*)?(?:[.\-–—:]+\s*)?", re.I)
# Una división lleva su número («CAPÍTULO IV»), o es una de las disposiciones con
# nombre, en mayúsculas. «las disposiciones de este Reglamento» no es un título.
DIVISION = re.compile(r"^(CAP[ÍI]TULO|T[ÍI]TULO|SECCI[ÓO]N)\s+([IVXLCil1\d]+[A-Z]?|[ÚU]NICO|PRIMERO|SEGUNDO|TERCERO)\b\.?\s*[:.\-–]?\s*(.*)$"
                      r"|^(DISPOSICI[ÓO]N(?:ES)?\s+(?:GENERAL|TRANSITORIA|FINAL|DEROGATORIA|REFORMATORIA)(?:ES|S)?(?:\s+[ÚU]NICA)?)\b\s*(.*)$")
NUMERADO = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
LISTA = re.compile(r"^(?:[a-zñ]\)|[a-zñ]\.\s|\d+(?:\.\d+)*\.?\s|[-•o▪●]\s|\((?:\d{1,2}|[a-z]|[ivx]{1,4})\)\s)", re.I)
VINETAS = "•▪●–"


# --------------------------------------------------------------- lectura
def _lineas_pagina(page, pn):
    """Renglones digitales de una página, con su posición y si van todos en negrita."""
    out, alto = [], page.rect.height
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            spans = [s for s in l["spans"] if s["text"].strip()]
            if not spans:
                continue
            t = re.sub(r"\s+", " ", "".join(s["text"] for s in l["spans"])).strip()
            for v in VINETAS:
                t = t.replace(v, "•")
            bold = all("bold" in s["font"].lower() or s["flags"] & 16 for s in spans)
            out.append({"p": pn, "x": l["bbox"][0], "y": l["bbox"][1], "y2": l["bbox"][3], "bbox": tuple(l["bbox"]),
                        "rel": l["bbox"][1] / alto, "t": t, "b": bold, "h": spans[0]["size"], "src": "d"})
    return out


def _lineas_digitales(doc):
    return [l for pn, page in enumerate(doc) for l in _lineas_pagina(page, pn)]


def _celda(c):
    """El texto de una celda; los saltos de renglón se conservan (tres personas en
    una celda son tres renglones, no una frase)."""
    renglones = [re.sub(r"[ \t\u00a0]+", " ", x).strip() for x in (c or "").splitlines()]
    return "\n".join(x for x in renglones if x)


def _es_indice_tabla(filas):
    """Un índice armado como tabla: la última columna con texto son números de página."""
    finales = [next((c for c in reversed(f) if c), "") for f in filas]
    numeros = sum(1 for c in finales if re.fullmatch(r"\d{1,3}", c))
    return numeros >= max(3, 0.6 * len(filas))


def _tablas(page):
    """Las tablas de verdad de una página: dos filas y dos columnas con texto, como mínimo."""
    try:
        encontradas = page.find_tables().tables
    except Exception:
        return []
    out = []
    for tb in encontradas:
        try:
            filas = [[_celda(c) for c in f] for f in tb.extract()]
        except Exception:
            continue
        filas = [f for f in filas if any(f)]
        if len(filas) < 2:
            continue
        cols = max(len(f) for f in filas)
        filas = [f + [""] * (cols - len(f)) for f in filas]
        vivas = [j for j in range(cols) if any(f[j] for f in filas)]
        filas = [[f[j] for j in vivas] for f in filas]
        llenas = sum(1 for f in filas for c in f if c)
        if len(vivas) < 2 or llenas < 0.35 * len(filas) * len(vivas):
            continue
        out.append({"bbox": tuple(tb.bbox), "filas": filas})
    return out


def _dentro(bb, caja):
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return caja[0] - 1 <= cx <= caja[2] + 1 and caja[1] - 1 <= cy <= caja[3] + 1


def _es_figura(page, lineas):
    """Un flujograma o un organigrama: muchos trazos de dibujo y renglones cortos
    (cajas con dos o tres palabras). En un manual del FIAS, las páginas de
    flujogramas tienen más de cien trazos; las de texto, menos de veinticinco."""
    if len(lineas) < 12:
        return False
    try:
        trazos = len(page.get_drawings())
    except Exception:
        return False
    largos = sorted(len(l["t"]) for l in lineas)
    mediana = largos[len(largos) // 2]
    apaisada = page.rect.width > page.rect.height
    return mediana < 25 and (trazos >= 100 and len(lineas) >= 40 or apaisada and trazos >= 30)


def calidad(texto):
    """Fracción de palabras raras: dígitos dentro de palabras (C6digo), «~», «lnterno»."""
    palabras = re.findall(r"\S+", texto)
    if len(palabras) < 50:
        return 1.0
    raras = sum(1 for w in palabras if re.search(r"[A-Za-zÁÉÍÓÚáéíóúñ][0-9~][A-Za-záéíóúñ]|~|^ln[a-z]{3,}", w))
    return raras / len(palabras)


def _ocr_pagina(page):
    """Texto de una página escaneada y la seguridad media de Tesseract (0-100)."""
    if not shutil.which("tesseract"):
        raise RuntimeError("El PDF es escaneado y falta Tesseract (apt install tesseract-ocr tesseract-ocr-spa).")
    png = page.get_pixmap(dpi=300, colorspace="gray").tobytes("png")
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "o")
        subprocess.run(["tesseract", "stdin", base, "-l", "spa", "--psm", "4", "txt", "tsv"],
                       input=png, capture_output=True, check=True)
        with open(base + ".txt", encoding="utf-8", errors="replace") as f:
            txt = f.read()
        confs = []
        with open(base + ".tsv", encoding="utf-8", errors="replace") as f:
            for r in f.read().splitlines()[1:]:
                c = r.split("\t")
                if len(c) >= 12 and c[11].strip():
                    try:
                        v = float(c[10])
                    except ValueError:
                        continue
                    if v >= 0:
                        confs.append(v)
    return txt, (sum(confs) / len(confs) if confs else 0.0)


def _ocr(doc):
    return [_ocr_pagina(page)[0] for page in doc]


def _lineas_ocr(paginas, numeros=None):
    out = []
    for k0, txt in enumerate(paginas):
        pn = numeros[k0] if numeros else k0
        lineas = txt.splitlines()
        n = len(lineas) or 1
        for k, t in enumerate(lineas):
            t = re.sub(r"\s+", " ", t).strip()
            if not t:
                out.append({"p": pn, "t": "", "vacio": True})
                continue
            letras = sum(c.isalpha() for c in t)
            # Ruido del escaneo: sellos, firmas, códigos QR, logos («0000 MINISTERI»).
            if re.search(r"(^|\s)[0oO]{4,}(\s|$)", t):
                continue
            if letras < 3 and not re.fullmatch(r"\d{1,3}", t):
                continue
            if len(t) <= 12 and letras / max(len(t), 1) < 0.6 and not LISTA.match(t + " "):
                continue
            out.append({"p": pn, "t": t, "b": False, "rel": k / n, "src": "o"})
    return out


def _sin_repetidos(lineas, paginas, quitadas=None):
    """Fuera encabezados y pies: lo que se repite en muchas páginas, y los números de página.
    Lo quitado va a `quitadas`, para no contarlo como perdido."""
    quitadas = [] if quitadas is None else quitadas
    if paginas < 3:
        out = []
        for l in lineas:
            (quitadas if re.fullmatch(r"\d{1,3}", l["t"]) else out).append(l)
        return out
    cuenta = Counter((l["t"], round(l.get("rel", 0), 2)) for l in lineas if l["t"])
    por_texto = Counter(l["t"] for l in lineas if l["t"] and (l.get("rel", 0.5) < 0.14 or l.get("rel", 0.5) > 0.88))
    out = []
    for l in lineas:
        t = l["t"]
        if t and (cuenta[(t, round(l.get("rel", 0), 2))] >= max(3, paginas * 0.3) or por_texto[t] >= max(3, paginas * 0.3)):
            quitadas.append(l)
            continue
        if re.fullmatch(r"(?:p[áa]g(?:ina)?\.?\s*)?\d{1,3}(?:\s*(?:de|/)\s*\d{1,3})?", t, re.I) and (l.get("rel", 0.5) > 0.85 or l.get("rel", 0.5) < 0.1):
            quitadas.append(l)
            continue
        out.append(l)
    return out


# ------------------------------------------------------------ párrafos
def _cierra(t):
    return bool(re.search(r"[.:;!?)»\"]$", t))


def _parrafos_digitales(lineas):
    """Junta renglones en párrafos: hay párrafo nuevo si cambia la negrita, si
    hay un salto vertical grande, o si el renglón empieza un artículo, un título
    o un elemento de lista. Una tabla o un diagrama es su propio párrafo."""
    return _parrafos(lineas)


def _parrafos_ocr(lineas):
    return _parrafos(lineas)


def _parrafos(lineas):
    pars, cur, prev, blanco = [], None, None, False
    for l in lineas:
        if l.get("tabla") is not None or l.get("figura"):
            par = {"t": "", "b": False, "pg": l["p"] + 1}
            if l.get("tabla") is not None:
                par["tabla"] = l["tabla"]
            else:
                par.update(figura=True, txt=l.get("txt", ""), tit=l.get("tit", ""))
            pars.append(par)
            cur, prev = None, None
            continue
        if l.get("vacio"):
            blanco = True
            continue
        t = l["t"]
        if l.get("src") == "o":
            cur_titulo = cur is not None and _es_mayus(cur["t"]) and not re.search(r"[a-záéíóúñ,]$", cur["t"])
            nuevo = (cur is None or prev is None or prev.get("src") != "o" or ART.match(t) or DIVISION.match(t) or LISTA.match(t)
                     or (blanco and _cierra(cur["t"]))
                     or (_es_mayus(t) != _es_mayus(cur["t"]) and (_cierra(cur["t"]) or cur_titulo)))
        else:
            nuevo = (cur is None or prev is None or prev.get("src") != "d"
                     or l["p"] != prev["p"] and _cierra(cur["t"]) or l["b"] != prev["b"]
                     or (l["p"] == prev["p"] and l["y"] - prev["y2"] > 0.9 * l["h"])
                     or ART.match(t) or DIVISION.match(t) or LISTA.match(t))
        if nuevo:
            cur = {"t": t, "b": l.get("b", False), "pg": l["p"] + 1, "o": l.get("src") == "o"}
            pars.append(cur)
        else:
            cur["t"] = _unir(cur["t"], t)
        prev, blanco = l, False
    return pars


def _vinetas(pars):
    """Varias viñetas pegadas en un renglón («• uno • dos») → un párrafo por viñeta."""
    out = []
    for p in pars:
        if p.get("tabla") is not None or p.get("figura"):
            out.append(p)
            continue
        partes = [x.strip() for x in re.split(r"\s+•\s+|^•\s*", p["t"]) if x.strip()]
        if len(partes) > 1 or p["t"].startswith("•"):
            out += [{"t": "• " + x, "b": p["b"], "pg": p.get("pg")} for x in partes]
        else:
            out.append(p)
    return out


# El índice del documento no es texto de la norma. Una entrada se reconoce por
# los puntos guía que llevan al número de página («2.1 Contribuciones ......... 4»);
# también se van el título «ÍNDICE» y los números de página romanos en minúscula
# («i», «iv») de las páginas preliminares.
_GUIA = re.compile(r"(?:\.\s?){4,}\s*\d{1,3}\s*$|…{2,}\s*\d{1,3}\s*$|_{4,}\s*\d{1,3}\s*$")
_TITULO_INDICE = re.compile(r"^(?:[ÍI]NDICE|CONTENIDOS?|TABLA DE CONTENIDOS?)(?:\s+GENERAL)?\s*:?$", re.I)
_PAGINA_ROMANA = re.compile(r"^[ivxlc]{1,6}$")


def _es_indice(t):
    t = t.strip()
    return bool(_TITULO_INDICE.match(t) or _PAGINA_ROMANA.match(t) or _GUIA.search(t)
                or len(re.findall(r"\.{4,}\s*\d{1,3}", t)) >= 2
                or (re.search(r"\bP[áa]gina\b", t) and len(re.findall(r"\s\d{1,3}(?=\s|$)", t)) >= 4))


def _sin_indice(pars, quitados=None):
    """Fuera la tabla de contenido (ver `_es_indice`). Lo quitado va a `quitados`."""
    out = []
    for p in pars:
        if p.get("tabla") is None and not p.get("figura") and _es_indice(p["t"]):
            if quitados is not None:
                quitados.append(p)
        else:
            out.append(p)
    return out


def _unir(a, b):
    if a.endswith("-") and not a.endswith(" -") and b[:1].islower():
        return a[:-1] + b
    return a + " " + b


def _es_mayus(t):
    letras = [c for c in t if c.isalpha()]
    return len(letras) >= 4 and sum(c.isupper() for c in letras) / len(letras) > 0.85


def _romano(s):
    return (s or "").replace("l", "I").replace("i", "I") if s and not s.isdigit() else (s or "")


# ---------------------------------------------------------- estructura
def estructurar(pars, ocr):
    """Párrafos → unidades: {t:'h1'|'h2', txt} · {t:'art', n, rub, p:[...]} · {t:'p', txt}.

    Si la numeración de artículos vuelve a empezar (la resolución que aprueba un
    reglamento trae su Art. 1 a 5, y luego el reglamento empieza otra vez en
    el 1), es otra parte del documento: los ids llevan la parte."""
    out, art, parte, ultimo = [], None, 0, 0
    pendiente_titulo, cont = None, None

    def pon(u, par):
        if par.get("pg"):
            u["pg"] = par["pg"]
        out.append(u)
        return u
    for par in pars:
        # Una tabla dentro de un artículo no lo corta: lo que sigue es del mismo
        # artículo («de»), aunque se pinte después de la tabla.
        if par.get("tabla") is not None:
            u = pon({"t": "tabla", "filas": par["tabla"]}, par)
            if art is not None or cont is not None:
                cont = art or cont
                u["de"] = cont["id"]
            art, pendiente_titulo = None, None
            continue
        if par.get("figura"):
            u = pon({"t": "fig", "txt": par.get("txt", "")}, par)
            if par.get("tit"):
                u["tit"] = par["tit"]
            art, cont, pendiente_titulo = None, None, None
            continue
        t = par["t"].strip()
        if not t:
            continue
        ocr_p = par.get("o", ocr)
        m = DIVISION.match(t)
        if m and m.group(4) and not _es_mayus(m.group(4)):
            m = None
        # «CAPÍTULO I» y en el renglón siguiente su título, aunque el título sea
        # «DISPOSICIONES GENERALES»: es el nombre del capítulo, no otra división.
        if pendiente_titulo is not None and _es_mayus(t) and len(t) < 140 and not ART.match(t) and not (m and m.group(1)):
            pendiente_titulo["txt"] += " · " + t
            pendiente_titulo = None
            continue
        if m and len(t) < 160:
            if m.group(4):
                rot, resto = m.group(4).upper(), (m.group(5) or "").strip(" .:-–")
            else:
                nombre = m.group(1).upper().replace("CAPITULO", "CAPÍTULO").replace("TITULO", "TÍTULO").replace("SECCION", "SECCIÓN")
                rot, resto = (nombre + " " + _romano(m.group(2))).strip(), m.group(3).strip(" .:-–")
            pon({"t": "h1", "txt": rot + (" · " + resto if resto else "")}, par)
            art, cont, pendiente_titulo = None, None, None if resto else out[-1]
            continue
        if pendiente_titulo is not None and _es_mayus(t) and len(t) < 140 and not ART.match(t):
            pendiente_titulo["txt"] += " · " + t
            pendiente_titulo = None
            continue
        pendiente_titulo = None
        a = ART.match(t)
        if a:
            n = int(a.group(1))
            if n <= ultimo and n == 1:
                parte += 1
            ultimo = n
            cuerpo = t[a.end():].strip()
            rub = None
            r = re.match(r"^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ,/()\-]{3,90}?)\s*[:.]\s+(.*)$", cuerpo) \
                or re.match(r"^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ,/()\-]{3,90}?)\s*[:.]?\s*()$", cuerpo)
            if r and _es_mayus(r.group(1)):
                rub, cuerpo = r.group(1).strip(), r.group(2)
            art = pon({"t": "art", "id": f"p{parte}-a{n}", "n": str(n), "rub": rub, "p": [cuerpo] if cuerpo else []}, par)
            cont = None
            continue
        es_titulo = (par["b"] and len(t) < 130 and not LISTA.match(t) or NUMERADO.match(t) and par["b"]) \
            or (ocr_p and _es_mayus(t) and len(t) < 110 and not t.endswith((",", ".")) or ocr_p and t.endswith(":") and _es_mayus(t))
        if es_titulo:
            num = NUMERADO.match(t)
            nivel = "h1" if (num and "." not in num.group(1)) or (not num and _es_mayus(t) and not out) else "h2"
            pon({"t": nivel, "txt": t}, par)
            art, cont = None, None
            continue
        if art is not None:
            art["p"].append(t)
        else:
            u = pon({"t": "p", "txt": t}, par)
            if cont is not None:
                u["de"] = cont["id"]
    for u in out:
        if u["t"] == "art" and not u["rub"]:
            u.pop("rub")
    return out


def _tokens(s):
    return re.findall(r"[^\W\d_]{4,}", (s or "").lower())



def _firma(filas):
    return "|".join(re.sub(r"\d+", "#", c) for f in filas for c in f)


def _titulo_figura(lineas):
    for l in lineas:
        if re.match(r"^(PROCESO|Proceso|PROCEDIMIENTO|Procedimiento|FLUJOGRAMA|Flujograma|ORGANIGRAMA|Organigrama)\b", l["t"]):
            return l["t"][:160]
    return ""


def _texto_unidad(u):
    if u["t"] == "art":
        return " ".join([u.get("rub") or ""] + u["p"])
    if u["t"] == "tabla":
        return " ".join(c for f in u["filas"] for c in f)
    if u["t"] == "fig":
        return ""
    return u.get("txt", "")


def extraer(contenido):
    """bytes del PDF → {'unidades': [...], 'paginas': n, 'ocr': bool, 'articulos': n, 'control': {...}}."""
    import pymupdf
    if hasattr(pymupdf, "no_recommend_layout"):
        pymupdf.no_recommend_layout()   # su aviso ensuciaba el registro del robot
    doc = pymupdf.open(stream=contenido, filetype="pdf")
    n = len(doc)
    pags = [_lineas_pagina(page, pn) for pn, page in enumerate(doc)]
    todo = " ".join(l["t"] for ls in pags for l in ls)
    # Si casi todo el PDF es un escaneo (o su capa de texto es un OCR viejo y malo),
    # se lee entero con OCR; si no, solo las páginas que lo necesitan.
    ocr_todo = len(todo) < 200 * max(n, 1) * 0.3 or calidad(todo) > 0.01
    modo = []
    for pn, page in enumerate(doc):
        txt = " ".join(l["t"] for l in pags[pn])
        if ocr_todo:
            m = "ocr"
        elif len(txt) < 60:
            m = "ocr" if page.get_images() else "vacia"
        elif len(re.findall(r"\S+", txt)) >= 80 and calidad(txt) > 0.03:
            m = "ocr"
        elif _es_figura(page, pags[pn]):
            m = "figura"
        else:
            m = "texto"
        modo.append(m)
    tablas = {pn: _tablas(doc[pn]) for pn in range(n) if modo[pn] == "texto"}
    veces = Counter(_firma(tb["filas"]) for tbs in tablas.values() for tb in tbs)
    lineas, quitadas, fuente, seguridad, sin_texto = [], [], {}, {}, []
    for pn, page in enumerate(doc):
        m = modo[pn]
        if m == "ocr":
            try:
                txt, conf = _ocr_pagina(page)
            except Exception:
                sin_texto.append(pn + 1)
                continue
            seguridad[pn + 1] = round(conf)
            fuente[pn] = Counter(_tokens(txt))
            ls = _lineas_ocr([txt], [pn])
            if len(_tokens(txt)) < 5 and page.get_images():
                sin_texto.append(pn + 1)
        elif m == "figura":
            ls = [{"p": pn, "t": "", "figura": True, "txt": " ".join(l["t"] for l in pags[pn]), "tit": _titulo_figura(pags[pn])}]
        elif m == "vacia":
            ls = []
        else:
            fuente[pn] = Counter(_tokens(" ".join(l["t"] for l in pags[pn])))
            tbs = tablas.get(pn, [])
            # La tabla del encabezado (código, versión, logo) se repite en cada página, y el
            # índice a veces viene como tabla: los dos, fuera (y no cuentan como perdidos).
            enc = [tb for tb in tbs if veces[_firma(tb["filas"])] >= max(3, n * 0.3) or _es_indice_tabla(tb["filas"])]
            utiles = [tb for tb in tbs if tb not in enc]
            ls = []
            for l in pags[pn]:
                if any(_dentro(l["bbox"], tb["bbox"]) for tb in enc):
                    quitadas.append(l)
                elif not any(_dentro(l["bbox"], tb["bbox"]) for tb in utiles):
                    ls.append(l)
            for tb in sorted(utiles, key=lambda tb: tb["bbox"][1]):
                marca = {"p": pn, "t": "", "tabla": tb["filas"], "y": tb["bbox"][1]}
                k = next((i for i, l in enumerate(ls) if l.get("tabla") is None and l["y"] > tb["bbox"][1]), len(ls))
                ls.insert(k, marca)
        lineas += ls
    lineas = _sin_repetidos(lineas, n, quitadas)
    sin_indice = []
    pars = _sin_indice(_vinetas(_parrafos(lineas)), sin_indice)
    uni = estructurar(pars, ocr_todo)

    # ¿Cuánto del PDF llegó? Palabras del PDF (sin lo quitado a propósito:
    # encabezados, pies, números de página, el índice) contra las del texto.
    quitado = Counter()
    for l in quitadas:
        quitado.update(_tokens(l.get("t", "")))
    for par in sin_indice:
        quitado.update(_tokens(par.get("t", "")))
    salida = Counter()
    for u in uni:
        salida.update(_tokens(_texto_unidad(u)))
    falta_total = Counter()
    for c in fuente.values():
        falta_total.update(c)
    falta_total.subtract(quitado)
    necesario = {w: k for w, k in falta_total.items() if k > 0}
    total = sum(necesario.values())
    llegan = sum(min(salida[w], k) for w, k in necesario.items())
    flojas = []
    for pn, c in fuente.items():
        propias = [w for w in c if necesario.get(w)]
        if len(propias) >= 30 and sum(1 for w in propias if salida[w]) / len(propias) < 0.85:
            flojas.append(pn + 1)
    ocr_pags = [pn + 1 for pn in range(n) if modo[pn] == "ocr"]
    control = {"cobertura": round(llegan / total, 3) if total else 1.0,
               "ocr": ocr_pags, "seguridad": seguridad,
               "dudosas": [pg for pg, c in seguridad.items() if c < 75],
               "figuras": [pn + 1 for pn in range(n) if modo[pn] == "figura"],
               "sin_texto": sorted(set(sin_texto)), "flojas": sorted(flojas),
               "tablas": sum(1 for u in uni if u["t"] == "tabla")}
    return {"unidades": uni, "paginas": n, "ocr": bool(ocr_pags),
            "articulos": sum(1 for u in uni if u["t"] == "art"), "control": control}


if __name__ == "__main__":
    import json
    with open(sys.argv[1], "rb") as f:
        r = extraer(f.read())
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"{r['paginas']} páginas · {'OCR' if r['ocr'] else 'texto digital'} · {r['articulos']} artículos · {len(r['unidades'])} unidades\n")
        for u in r["unidades"]:
            if u["t"] in ("h1", "h2"):
                print(("\n# " if u["t"] == "h1" else "## ") + u["txt"])
            elif u["t"] == "art":
                print(f"\nArt. {u['n']}" + (f" — {u['rub']}" if u.get("rub") else "") + ": " + " ¶ ".join(u["p"])[:220])
            elif u["t"] == "tabla":
                print(f"   [tabla, pág. {u.get('pg')}] " + " | ".join(u["filas"][0])[:140] + f" … ({len(u['filas'])} filas)")
            elif u["t"] == "fig":
                print(f"   [diagrama, pág. {u.get('pg')}] {u.get('tit', '')}")
            else:
                print("   " + u["txt"][:160])
        print("\ncontrol:", json.dumps(r["control"], ensure_ascii=False))
