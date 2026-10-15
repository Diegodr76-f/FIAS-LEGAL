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

Lo que NO hace: tablas y flujogramas salen como texto suelto o no salen. Para
eso queda siempre el botón del PDF.
"""
import io
import re
import shutil
import subprocess
import sys
from collections import Counter

# Súbela cada vez que cambie lo que sale de `extraer()`: el robot guarda lo ya
# leído por la huella del PDF Y esta versión, así que con otra versión lo relee.
VERSION = "2"

ART = re.compile(r"^Art(?:[íi]culo|\.)?\s*(\d+)\s*(?:[.ºo°]\s*)?(?:[.\-–—:]+\s*)?", re.I)
# Una división lleva su número («CAPÍTULO IV»), o es una de las disposiciones con
# nombre, en mayúsculas. «las disposiciones de este Reglamento» no es un título.
DIVISION = re.compile(r"^(CAP[ÍI]TULO|T[ÍI]TULO|SECCI[ÓO]N)\s+([IVXLCil1\d]+[A-Z]?|[ÚU]NICO|PRIMERO|SEGUNDO|TERCERO)\b\.?\s*[:.\-–]?\s*(.*)$"
                      r"|^(DISPOSICI[ÓO]N(?:ES)?\s+(?:GENERAL|TRANSITORIA|FINAL|DEROGATORIA|REFORMATORIA)(?:ES|S)?(?:\s+[ÚU]NICA)?)\b\s*(.*)$")
NUMERADO = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
LISTA = re.compile(r"^(?:[a-zñ]\)|[a-zñ]\.\s|\d+(?:\.\d+)*\.?\s|[-•o▪●]\s|\((?:\d{1,2}|[a-z]|[ivx]{1,4})\)\s)", re.I)
VINETAS = "•▪●–"


# --------------------------------------------------------------- lectura
def _lineas_digitales(doc):
    """Renglones del PDF con su página, posición y si van todos en negrita."""
    out = []
    for pn, page in enumerate(doc):
        alto = page.rect.height
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"] if s["text"].strip()]
                if not spans:
                    continue
                t = re.sub(r"\s+", " ", "".join(s["text"] for s in l["spans"])).strip()
                for v in VINETAS:
                    t = t.replace(v, "•")
                bold = all("bold" in s["font"].lower() or s["flags"] & 16 for s in spans)
                out.append({"p": pn, "x": l["bbox"][0], "y": l["bbox"][1], "y2": l["bbox"][3],
                            "rel": l["bbox"][1] / alto, "t": t, "b": bold, "h": spans[0]["size"]})
    return out


def calidad(texto):
    """Fracción de palabras raras: dígitos dentro de palabras (C6digo), «~», «lnterno»."""
    palabras = re.findall(r"\S+", texto)
    if len(palabras) < 50:
        return 1.0
    raras = sum(1 for w in palabras if re.search(r"[A-Za-zÁÉÍÓÚáéíóúñ][0-9~][A-Za-záéíóúñ]|~|^ln[a-z]{3,}", w))
    return raras / len(palabras)


def _ocr(doc):
    if not shutil.which("tesseract"):
        raise RuntimeError("El PDF es escaneado y falta Tesseract (apt install tesseract-ocr tesseract-ocr-spa).")
    paginas = []
    for page in doc:
        png = page.get_pixmap(dpi=300, colorspace="gray").tobytes("png")
        r = subprocess.run(["tesseract", "stdin", "stdout", "-l", "spa", "--psm", "4"],
                           input=png, capture_output=True, check=True)
        paginas.append(r.stdout.decode("utf-8", "replace"))
    return paginas


def _lineas_ocr(paginas):
    out = []
    for pn, txt in enumerate(paginas):
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
            out.append({"p": pn, "t": t, "b": False, "rel": k / n})
    return out


def _sin_repetidos(lineas, paginas):
    """Fuera encabezados y pies: lo que se repite en muchas páginas, y los números de página."""
    if paginas < 3:
        return [l for l in lineas if not re.fullmatch(r"\d{1,3}", l["t"])]
    cuenta = Counter((l["t"], round(l.get("rel", 0), 2)) for l in lineas if l["t"])
    por_texto = Counter(l["t"] for l in lineas if l["t"] and (l.get("rel", 0.5) < 0.14 or l.get("rel", 0.5) > 0.88))
    out = []
    for l in lineas:
        t = l["t"]
        if t and (cuenta[(t, round(l.get("rel", 0), 2))] >= max(3, paginas * 0.3) or por_texto[t] >= max(3, paginas * 0.3)):
            continue
        if re.fullmatch(r"(?:p[áa]g(?:ina)?\.?\s*)?\d{1,3}(?:\s*(?:de|/)\s*\d{1,3})?", t, re.I) and (l.get("rel", 0.5) > 0.85 or l.get("rel", 0.5) < 0.1):
            continue
        out.append(l)
    return out


# ------------------------------------------------------------ párrafos
def _cierra(t):
    return bool(re.search(r"[.:;!?)»\"]$", t))


def _parrafos_digitales(lineas):
    """Junta renglones en párrafos: hay párrafo nuevo si cambia la negrita, si
    hay un salto vertical grande, o si el renglón empieza un artículo, un título
    o un elemento de lista."""
    pars, cur, prev = [], None, None
    for l in lineas:
        t = l["t"]
        nuevo = (cur is None or l["p"] != prev["p"] and _cierra(cur["t"]) or l["b"] != prev["b"]
                 or (l["p"] == prev["p"] and l["y"] - prev["y2"] > 0.9 * l["h"])
                 or ART.match(t) or DIVISION.match(t) or LISTA.match(t))
        if nuevo:
            cur = {"t": t, "b": l["b"]}
            pars.append(cur)
        else:
            cur["t"] = _unir(cur["t"], t)
        prev = l
    return pars


def _parrafos_ocr(lineas):
    pars, cur, blanco = [], None, False
    for l in lineas:
        if l.get("vacio"):
            blanco = True
            continue
        t = l["t"]
        cur_titulo = cur is not None and _es_mayus(cur["t"]) and not re.search(r"[a-záéíóúñ,]$", cur["t"])
        nuevo = (cur is None or ART.match(t) or DIVISION.match(t) or LISTA.match(t)
                 or (blanco and _cierra(cur["t"]))
                 or (_es_mayus(t) != _es_mayus(cur["t"]) and (_cierra(cur["t"]) or cur_titulo)))
        if nuevo:
            cur = {"t": t, "b": False}
            pars.append(cur)
        else:
            cur["t"] = _unir(cur["t"], t)
        blanco = False
    return pars


def _vinetas(pars):
    """Varias viñetas pegadas en un renglón («• uno • dos») → un párrafo por viñeta."""
    out = []
    for p in pars:
        partes = [x.strip() for x in re.split(r"\s+•\s+|^•\s*", p["t"]) if x.strip()]
        if len(partes) > 1 or p["t"].startswith("•"):
            out += [{"t": "• " + x, "b": p["b"]} for x in partes]
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


def _sin_indice(pars):
    """Fuera la tabla de contenido (ver `_es_indice`)."""
    return [p for p in pars if not _es_indice(p["t"])]


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
    pendiente_titulo = None
    for par in pars:
        t = par["t"].strip()
        if not t:
            continue
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
            out.append({"t": "h1", "txt": rot + (" · " + resto if resto else "")})
            art, pendiente_titulo = None, None if resto else out[-1]
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
            art = {"t": "art", "id": f"p{parte}-a{n}", "n": str(n), "rub": rub, "p": [cuerpo] if cuerpo else []}
            out.append(art)
            continue
        es_titulo = (par["b"] and len(t) < 130 and not LISTA.match(t) or NUMERADO.match(t) and par["b"]) \
            or (ocr and _es_mayus(t) and len(t) < 110 and not t.endswith((",", ".")) or ocr and t.endswith(":") and _es_mayus(t))
        if es_titulo:
            num = NUMERADO.match(t)
            nivel = "h1" if (num and "." not in num.group(1)) or (not num and _es_mayus(t) and not out) else "h2"
            out.append({"t": nivel, "txt": t})
            art = None
            continue
        if art is not None:
            art["p"].append(t)
        else:
            out.append({"t": "p", "txt": t})
    for u in out:
        if u["t"] == "art" and not u["rub"]:
            u.pop("rub")
    return out


def extraer(contenido):
    """bytes del PDF → {'unidades': [...], 'paginas': n, 'ocr': bool, 'articulos': n}."""
    import pymupdf
    doc = pymupdf.open(stream=contenido, filetype="pdf")
    lineas = _lineas_digitales(doc)
    plano_txt = " ".join(l["t"] for l in lineas)
    ocr = len(plano_txt) < 200 * max(len(doc), 1) * 0.3 or calidad(plano_txt) > 0.01
    if ocr:
        lineas = _lineas_ocr(_ocr(doc))
    lineas = _sin_repetidos(lineas, len(doc))
    pars = _sin_indice(_vinetas(_parrafos_ocr(lineas) if ocr else _parrafos_digitales(lineas)))
    uni = estructurar(pars, ocr)
    return {"unidades": uni, "paginas": len(doc), "ocr": ocr,
            "articulos": sum(1 for u in uni if u["t"] == "art")}


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
            else:
                print("   " + u["txt"][:160])
