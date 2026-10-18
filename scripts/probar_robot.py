# -*- coding: utf-8 -*-
"""
Comprobaciones del robot (scripts/publicar.py) y de la plantilla.

    pip install openpyxl cryptography msoffcrypto-tool
    python3 scripts/probar_robot.py
    python3 scripts/probar_robot.py --sitio <carpeta>   prepara datos cifrados para probar_app.js

Lo que más importa aquí no es que se lea bien el Excel, sino lo que NO debe
pasar: que algo se publique en claro, que un grupo vea lo de otro, que un
«javascript:» llegue a un enlace, o que el contenido de una celda aparezca en
el registro público de GitHub Actions. Sale con código 1 si algo falla.
"""
import base64
import contextlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crear_plantilla  # noqa: E402
import publicar  # noqa: E402
from matriz import HOJAS  # noqa: E402

FRASE_LEGAL = "prueba-legal-tortuga-cobre-lienzo-sal"
FRASE_DIR = "prueba-directorio-faro-trueno-jade-miel"
fallos = pruebas = 0


def ok(cond, msg, extra=None):
    global fallos, pruebas
    pruebas += 1
    print(("  ✓ " if cond else "  ✗ ") + msg + ("" if cond or extra is None else f"  → {extra}"))
    if not cond:
        fallos += 1


def seccion(t):
    print("\n" + t)


def guardar(wb, carpeta, nombre="libro.xlsx"):
    ruta = os.path.join(carpeta, nombre)
    wb.save(ruta)
    return ruta


def col(ws, clave, hoja):
    return [c[0] for c in HOJAS[hoja]].index(clave) + 1


def libro_dos_grupos():
    """El de ejemplo, con el Directorio del FIAS en su propio grupo de acceso."""
    wb = crear_plantilla.libro(demo=True)
    ws = wb["Cuerpos"]
    for fila in ws.iter_rows(min_row=2):
        if fila[0].value == "DIR-FIAS":
            fila[col(ws, "grupo", "Cuerpos") - 1].value = "directorio"
    return wb


def libro_dos_grupos_matriz():
    return publicar.Matriz().leer(libro_dos_grupos())


def descifrar(env, frase):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    b = base64.b64decode
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b(env["salt"]), iterations=env["iter"]).derive(frase.encode())
    return json.loads(AESGCM(k).decrypt(b(env["iv"]), b(env["ct"]), None))


def correr(args, env):
    """Corre publicar.main capturando TODO lo que imprimiría en el registro."""
    viejo = dict(os.environ)
    os.environ.update(env)
    salida = io.StringIO()
    codigo, error = None, None
    try:
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(salida):
            codigo = publicar.main(args)
    except publicar.Alto as e:
        error = str(e)
    finally:
        os.environ.clear()
        os.environ.update(viejo)
    return codigo, error, salida.getvalue()


def pdf_mixto(escaneada=True):
    """Lo difícil de los PDF reales, en cuatro páginas: una tabla dentro de un
    artículo, una página escaneada en medio de un PDF digital (un anexo firmado),
    un flujograma apaisado y una página digital más."""
    import pymupdf
    doc = pymupdf.open()
    # 1: digital, con una tabla de verdad
    p = doc.new_page(width=595, height=842)
    y = 80
    for t in ["CAPÍTULO I", "DE LOS VIÁTICOS", "Art. 1.- OBJETO. Este reglamento fija los viáticos del personal del fondo en comisión de servicios."]:
        p.insert_text((60, y), t, fontsize=11, fontname="hebo" if t.isupper() else "helv"); y += 22
    filas = [["Destino", "Monto diario", "Movilización"], ["Quito", "USD 40", "Taxi"], ["Galápagos", "USD 90", "Avioneta"], ["Amazonía", "USD 60", "Lancha"]]
    x0, y0, w, h = 60, y + 10, 160, 22
    for i in range(len(filas) + 1):
        p.draw_line((x0, y0 + i * h), (x0 + 3 * w, y0 + i * h))
    for j in range(4):
        p.draw_line((x0 + j * w, y0), (x0 + j * w, y0 + len(filas) * h))
    for i, f in enumerate(filas):
        for j, c in enumerate(f):
            p.insert_text((x0 + j * w + 6, y0 + i * h + 15), c, fontsize=10, fontname="helv")
    y = y0 + len(filas) * h + 30
    p.insert_text((60, y), "Art. 2.- PAGO. El pago se hace antes de la comisión, contra el informe de la jefatura.", fontsize=11, fontname="helv")
    # 2: escaneada (una imagen con texto, sin capa de texto)
    if escaneada:
        tmp = pymupdf.open(); q = tmp.new_page(width=595, height=842)
        yy = 90
        for t in ["Art. 3.- VACACIONES. El personal goza de quince días de vacaciones", "anuales pagadas, que se programan con la jefatura inmediata", "en el mes de enero de cada año."]:
            q.insert_text((60, yy), t, fontsize=13, fontname="helv"); yy += 26
        pix = q.get_pixmap(dpi=200)
        p2 = doc.new_page(width=595, height=842); p2.insert_image(p2.rect, pixmap=pix)
    # 3: un flujograma apaisado
    p3 = doc.new_page(width=842, height=595)
    p3.insert_text((40, 40), "PROCESO: Pago de viáticos", fontsize=12, fontname="hebo")
    etiquetas = ["Inicio", "Solicitar", "Revisar", "Aprobar", "Pagar", "Archivar", "Fin", "Informe", "Factura", "Validar", "Registrar", "Notificar"]
    k = 0
    for fila in range(4):
        for col in range(5):
            r = pymupdf.Rect(40 + col * 155, 70 + fila * 120, 150 + col * 155, 120 + fila * 120)
            p3.draw_rect(r); p3.draw_line((r.x1, r.y0 + 25), (r.x1 + 5, r.y0 + 25))
            for d in range(3):
                p3.draw_line((r.x0 + 5 + d * 3, r.y1 + 3), (r.x0 + 8 + d * 3, r.y1 + 8))
            p3.insert_text((r.x0 + 8, r.y0 + 28), etiquetas[k % len(etiquetas)], fontsize=9, fontname="helv"); k += 1
    # 4: digital
    p4 = doc.new_page(width=595, height=842)
    p4.insert_text((60, 80), "Art. 4.- VIGENCIA. Este reglamento rige desde su aprobación por el Directorio.", fontsize=11, fontname="helv")
    return doc.tobytes()

def pdf_prueba(escaneado=False):
    """Un reglamento inventado de tres páginas, con encabezado repetido, número
    de página, capítulos y artículos con rubro en negrita. Con `escaneado`, cada
    página va como imagen, sin texto: lo tiene que leer el OCR."""
    import pymupdf
    doc = pymupdf.open()
    arts = [(1, "OBJETO", "Este reglamento de prueba regula el uso de los vehículos de la institución."),
            (2, "ÁMBITO", "Se aplica a todo el personal que conduzca un vehículo institucional."),
            (3, "RESPONSABLE", "La Dirección Administrativa lleva el registro de los vehículos y sus conductores."),
            (4, "SALIDAS", "Toda salida requiere una orden de movilización firmada por el jefe inmediato."),
            (5, "COMBUSTIBLE", "El combustible se carga solo en las estaciones autorizadas, con factura a nombre de la institución."),
            (6, "SANCIONES", "El incumplimiento de este reglamento se sanciona conforme el Reglamento Interno de Trabajo.")]
    for k in range(3):
        pg = doc.new_page()
        pg.insert_text((60, 40), "FONDO DE PRUEBA · REGLAMENTO DE VEHÍCULOS", fontname="helv", fontsize=9)
        pg.insert_text((540, 800), str(k + 1), fontname="helv", fontsize=9)
        y = 90
        pg.insert_text((230, y), ["CAPÍTULO I", "CAPÍTULO II", "CAPÍTULO III"][k], fontname="hebo", fontsize=12)
        y += 18
        pg.insert_text((190, y), ["DISPOSICIONES GENERALES", "DE LA OPERACIÓN", "DEL RÉGIMEN DISCIPLINARIO"][k], fontname="hebo", fontsize=12)
        y += 40
        for n, rub, txt in arts[2 * k:2 * k + 2]:
            pg.insert_text((60, y), f"Art. {n}.- {rub}:", fontname="hebo", fontsize=11)
            pg.insert_textbox(pymupdf.Rect(60, y + 6, 540, y + 80), txt, fontname="helv", fontsize=11)
            y += 110
    if not escaneado:
        return doc.tobytes()
    img = pymupdf.open()
    for pg in doc:
        pix = pg.get_pixmap(dpi=200)
        p2 = img.new_page(width=pg.rect.width, height=pg.rect.height)
        p2.insert_image(p2.rect, pixmap=pix)
    return img.tobytes()


def sitio(carpeta):
    """Datos cifrados de dos grupos, para la prueba de la página. Una norma de
    legal trae su «PDF para leer en Quórum»: la página prueba el lector con un
    texto cifrado de verdad."""
    wb = libro_dos_grupos()
    wn = wb["Normativa"]
    fila = next(i for i in range(2, wn.max_row + 1) if wn.cell(row=i, column=1).value == "Manual Operativo del Ciclo de Proyectos del FAP")
    wn.cell(row=fila, column=col(wn, "pdf", "Normativa")).value = "https://ejemplo.invalid/manual.pdf"
    pdf = pdf_prueba()
    publicar.descargar_pdf = lambda url: pdf
    with tempfile.TemporaryDirectory() as t:
        ruta = guardar(wb, t)
        codigo, error, _ = correr(["--excel", ruta, "--salida", carpeta, "--permitir-sin-clave"],
                                  {"CLAVES": f"legal = {FRASE_LEGAL}\ndirectorio = {FRASE_DIR}"})
    if error:
        sys.exit("No se pudo preparar el sitio: " + error)
    print(json.dumps({"legal": FRASE_LEGAL, "directorio": FRASE_DIR}))


def main():
    with tempfile.TemporaryDirectory() as t:
        seccion("1. La plantilla tiene las hojas y encabezados que el robot busca")
        wb = crear_plantilla.libro()
        for hoja, cols in HOJAS.items():
            encs = [c.value for c in wb[hoja][1]]
            ok(encs[:len(cols)] == [c[1] for c in cols], f"hoja {hoja}: encabezados en orden", encs)
        ok([c.value for c in wb["Cuerpos"]["A"][1:4]] == ["DIR-FIAS", "JA-FAP", "DIR-FEIG"], "trae los tres cuerpos conocidos")
        ok([c.value for c in wb["Fondos"]["A"][1:4]] == ["FIAS", "FAP", "FEIG"] and wb["Cuerpos"]["C"][2].value == "FAP",
           "y el FIAS con sus fondos; la Junta Administrativa es del FAP")
        ok(all(wb[h].max_row <= 2 for h in ("Actas", "Resoluciones", "Normativa", "Cambios")), "y ninguna sesión, resolución ni norma")
        ok("FICTICIOS" not in (wb.properties.title or ""), "la plantilla vacía NO lleva la marca de datos ficticios")
        m = publicar.Matriz().leer(wb)
        ok(not m.avisos and len(m.cuerpos) == 3, "el robot la lee sin avisos", m.avisos)

        seccion("2. El libro de ejemplo se lee completo")
        m = publicar.Matriz().leer(crear_plantilla.libro(demo=True))
        ok(len(m.normas) == 10 and len(m.cambios) == 13, "10 normas y 13 cambios", (len(m.normas), len(m.cambios)))
        ok("ja-fap_2026-08-08_p3" in m.res, "la resolución se identifica por cuerpo + fecha + punto")
        ok(m.normas["manual-operativo-del-ciclo-de-proyectos-del-fap"]["res"] == "ja-fap_2018-02-20_p5", "la norma queda enlazada a la resolución que la aprobó")
        stub = [a for a in m.actas.values() if a.get("stub")]
        ok(len(stub) == 1 and len(m.avisos) == 1, "una resolución sin su acta crea un acta incompleta y UN aviso", m.avisos)
        tele = [c for c in m.cambios if c["a"]["id"] == "lineamientos-de-teletrabajo"][0]
        ok(tele["fecha"] == "2027-01-01" and tele["por"]["fecha"] == "2026-09-17", "«Rige desde» manda sobre la fecha de la sesión")

        seccion("3. El Excel protegido con contraseña")
        plano_ruta = guardar(crear_plantilla.libro(demo=True), t, "plano.xlsx")
        import msoffcrypto
        cif = os.path.join(t, "cifrado.xlsx")
        with open(plano_ruta, "rb") as f, open(cif, "wb") as g:
            of = msoffcrypto.OfficeFile(f)
            of.encrypt("clave-del-excel", g)
        with open(cif, "rb") as f:
            datos = f.read()
        ok(publicar.abrir_libro(datos, "clave-del-excel", False)["Normativa"].max_row == 11, "se abre con la contraseña correcta")
        for clave, msg in ((None, "sin EXCEL_CLAVE"), ("otra", "con la contraseña equivocada")):
            try:
                publicar.abrir_libro(datos, clave, False)
                ok(False, f"{msg}: no publica")
            except publicar.Alto:
                ok(True, f"{msg}: no publica")
        with open(plano_ruta, "rb") as f:
            try:
                publicar.abrir_libro(f.read(), None, False)
                ok(False, "un Excel SIN contraseña no se publica")
            except publicar.Alto as e:
                ok("Cifrar con contraseña" in str(e), "un Excel SIN contraseña no se publica, y dice cómo protegerlo")

        seccion("4. Cada grupo recibe solo lo suyo")
        ruta = guardar(libro_dos_grupos(), t, "dos.xlsx")
        sal = os.path.join(t, "datos")
        claves = {"CLAVES": f"legal = {FRASE_LEGAL}\ndirectorio = {FRASE_DIR}"}
        codigo, error, log = correr(["--excel", ruta, "--salida", sal, "--permitir-sin-clave"], claves)
        ok(codigo == 0 and not error, "publica", error)
        indice = json.load(open(os.path.join(sal, "indice.json")))
        ok([g["id"] for g in indice["grupos"]] == ["directorio", "legal"], "un archivo por grupo", indice)
        sobres = {g["id"]: json.load(open(os.path.join(sal, g["archivo"]))) for g in indice["grupos"]}
        ok(all(s.get("q_enc") == 1 and set(s) == {"q_enc", "kdf", "iter", "salt", "iv", "ct"} for s in sobres.values()),
           "cada archivo es solo el sobre cifrado")
        crudo = open(os.path.join(sal, "g-legal.json")).read() + open(os.path.join(sal, "g-directorio.json")).read()
        ok("Junta" not in crudo and "Manual" not in crudo and "Reglamento" not in crudo, "nada legible en lo publicado")
        leg, dire = descifrar(sobres["legal"], FRASE_LEGAL), descifrar(sobres["directorio"], FRASE_DIR)
        ok(all(a["cuerpo"] != "DIR-FIAS" for a in leg["actas"]) and all(r["cuerpo"] != "DIR-FIAS" for r in leg["resoluciones"]),
           "legal no recibe actas ni resoluciones del Directorio del FIAS")
        ok(all(n["organo"] != "DIR-FIAS" for n in leg["normas"]), "ni sus normas (van con el grupo de su órgano)")
        ok(all(a["cuerpo"] == "DIR-FIAS" for a in dire["actas"]) and len(dire["normas"]) == 7, "directorio recibe lo suyo", len(dire["normas"]))
        try:
            descifrar(sobres["directorio"], FRASE_LEGAL)
            ok(False, "la frase de legal NO abre el archivo del directorio")
        except Exception:
            ok(True, "la frase de legal NO abre el archivo del directorio")
        textos = [r["texto"] for r in dire["resoluciones"]] + [n["nombre"] for n in dire["normas"] + leg["normas"]]
        ok(not any(x in log for x in textos), "el registro no trae ni un texto de resolución ni un nombre de norma")
        ok("DIR-FEIG" not in log and "2022-11-10" not in log and "10/11/2022" not in log, "ni siglas ni fechas de lo que avisa")
        ok("fila 58" in log, "solo la hoja y el renglón del aviso", log)

        seccion("5. Sin frase, ese grupo no se publica (y nada sale en claro)")
        sal2 = os.path.join(t, "datos2")
        codigo, error, log = correr(["--excel", ruta, "--salida", sal2, "--permitir-sin-clave"], {"CLAVES": f"legal = {FRASE_LEGAL}"})
        ind = json.load(open(os.path.join(sal2, "indice.json")))
        ok(codigo == 0 and [g["id"] for g in ind["grupos"]] == ["legal"] and not os.path.exists(os.path.join(sal2, "g-directorio.json")),
           "falta la frase del directorio: se publica legal, el directorio no", ind)
        ok("«directorio» no tiene frase" in log, "y el registro lo dice", log[-300:])
        sal2b = os.path.join(t, "datos2b")
        codigo, error, log = correr(["--excel", ruta, "--salida", sal2b, "--permitir-sin-clave"], {"CLAVES": ""})
        ok(error and "ningún grupo" in error and not os.path.exists(sal2b), "sin ninguna frase no se escribe NADA", error)
        codigo, error, log = correr(["--excel", ruta, "--salida", sal2b, "--permitir-sin-clave"], {"CLAVES": "legal = corta\ndirectorio = corta"})
        ok(error and "corta" in error and not os.path.exists(sal2b), "una frase corta tampoco", error)
        codigo, error, log = correr(["--salida", sal2, "--si-falta-config"], {"EXCEL_URL": ""})
        ind = json.load(open(os.path.join(sal2, "indice.json")))
        ok(codigo == 0 and ind["grupos"] == [] and ind["pendiente"] == "configuracion", "sin configurar aún: la herramienta sale sin datos")

        seccion("6. Renglones que no cuadran: se saltan y se avisan")
        wb = crear_plantilla.libro(demo=True)
        ws = wb["Resoluciones"]
        n = ws.max_row + 1
        for k, v in {"cuerpo": "DIR-FAIS", "fecha": "2025-01-01", "punto": "1", "texto": "Con sigla mal escrita"}.items():
            ws.cell(row=n, column=col(ws, k, "Resoluciones"), value=v)
        for k, v in {"cuerpo": "JA-FAP", "fecha": "el martes", "punto": "1", "texto": "Con fecha mala"}.items():
            ws.cell(row=n + 1, column=col(ws, k, "Resoluciones"), value=v)
        for k, v in {"cuerpo": "JA-FAP", "fecha": "2018-02-20", "punto": "9", "texto": "<img src=x onerror=alert(1)>",
                     "enlace": "javascript:alert(1)"}.items():
            ws.cell(row=n + 2, column=col(ws, k, "Resoluciones"), value=v)
        wc = wb["Cambios"]
        m2 = wc.max_row + 1
        for k, v in {"norma": "Norma que no existe", "tipo": "Derogación", "pcuerpo": "JA-FAP", "pfecha": "2018-02-20", "ppunto": "5"}.items():
            wc.cell(row=m2, column=col(wc, k, "Cambios"), value=v)
        for k, v in {"norma": "Manual de Operaciones del FEIG", "rcuerpo": "JA-FAP", "rfecha": "2018-02-20", "rpunto": "5", "tipo": "Reforma"}.items():
            wc.cell(row=m2 + 1, column=col(wc, k, "Cambios"), value=v)
        for k, v in {"norma": "manual de operaciones del  FEIG", "tipo": "derogacion", "rige": "2030-01-01"}.items():
            wc.cell(row=m2 + 2, column=col(wc, k, "Cambios"), value=v)
        m = publicar.Matriz().leer(wb)
        filas = {(a["hoja"], a["fila"]) for a in m.avisos}
        ok(("Resoluciones", n) in filas and not any(r["texto"] == "Con sigla mal escrita" for r in m.res.values()), "cuerpo desconocido: aviso y fuera")
        ok(("Resoluciones", n + 1) in filas and not any(r["texto"] == "Con fecha mala" for r in m.res.values()), "fecha que no es fecha: aviso y fuera")
        mala = m.res.get("ja-fap_2018-02-20_p9")
        ok(mala and mala["enlace"] is None and ("Resoluciones", n + 2) in filas, "un enlace «javascript:» no llega a publicarse")
        ok(("Cambios", m2) in filas and ("Cambios", m2 + 1) in filas, "cambio a una norma inexistente, o a norma Y resolución: aviso y fuera")
        fut = [c for c in m.cambios if c["fila"] == m2 + 2]
        ok(fut and fut[0]["tipo"] == "Derogación" and fut[0]["fecha"] == "2030-01-01",
           "nombre y tipo se reconocen sin tildes, mayúsculas ni espacios de más; sin «Resuelto por» vale «Rige desde»")

        seccion("7. El Excel se reordena: los encabezados se reconocen igual")
        wb = crear_plantilla.libro(demo=True)
        ws = wb["Resoluciones"]
        ws.insert_cols(1)
        ws.cell(row=1, column=1, value="Columna nueva de la Secretaría")
        ws.cell(row=1, column=col(ws, "fecha", "Resoluciones") + 1, value="FECHA DE LA SESION (dd/mm/aaaa)")
        m = publicar.Matriz().leer(wb)
        ok(len(m.res) == 59, "una columna de más al inicio y un encabezado sin tildes y con añadido", len(m.res))
        ws.delete_cols(col(ws, "texto", "Resoluciones") + 1)
        try:
            publicar.Matriz().leer(wb)
            ok(False, "sin la columna «Lo que se resolvió» no se publica")
        except publicar.Alto as e:
            ok("Lo que se resolvió" in str(e), "sin la columna «Lo que se resolvió» no se publica, y dice cuál falta")

        seccion("8. La demostración: solo el libro de ejemplo sale sin cifrar")
        real = guardar(crear_plantilla.libro(), t, "real.xlsx")
        codigo, error, log = correr(["--demo", "--excel", real], {})
        ok(error and "nunca se publica sin cifrar" in error, "--demo rechaza un libro que no es el de ejemplo", error)
        demo = json.load(open(os.path.join(publicar.RAIZ, "demo", "datos-demo.json")))
        ok(demo.get("demo") is True and len(demo["normas"]) == 10, "demo/datos-demo.json es el de ejemplo y está al día")

        seccion("9. Fondos: cada cuerpo es de un fondo, y sus actas con él")
        m = publicar.Matriz().leer(crear_plantilla.libro(demo=True))
        ok(list(m.fondos) == ["FIAS", "FAP", "FEIG", "PPD"], "la hoja Fondos se lee", list(m.fondos))
        ok(m.cuerpos["JA-FAP"]["entidad"] == "FAP" and m.cuerpos["CD-PPD"]["entidad"] == "PPD", "cada cuerpo con su fondo")
        ok(m.normas["manual-de-operaciones-del-feig"]["entidad"] == "FEIG", "la norma, con el suyo")
        wb = crear_plantilla.libro(demo=True)
        wn = wb["Normativa"]
        fila = next(i for i in range(2, wn.max_row + 1) if wn.cell(row=i, column=1).value == "Manual de Operaciones del FEIG")
        wn.cell(row=fila, column=col(wn, "entidad", "Normativa")).value = None  # value=None no borra
        wc = wb["Cuerpos"]
        wc.cell(row=3, column=col(wc, "entidad", "Cuerpos"), value="fap")
        wc.cell(row=4, column=col(wc, "entidad", "Cuerpos"), value="FONDO NUEVO")
        m = publicar.Matriz().leer(wb)
        ok(m.normas["manual-de-operaciones-del-feig"]["entidad"] == "FONDO NUEVO", "una norma sin fondo toma el de su órgano")
        ok(m.cuerpos["JA-FAP"]["entidad"] == "FAP", "la sigla del fondo se reconoce en minúsculas")
        ok(("Cuerpos", 4) in {(a["hoja"], a["fila"]) for a in m.avisos} and m.cuerpos["DIR-FEIG"]["entidad"] == "FONDO NUEVO",
           "un fondo que no está en la hoja Fondos se avisa, y se respeta")
        wb = crear_plantilla.libro(demo=True)
        del wb["Fondos"]
        m = publicar.Matriz().leer(wb)
        ok(len(m.res) == 59 and len(m.avisos) == 1 and m.cuerpos["JA-FAP"]["entidad"] == "FAP",
           "un Excel sin la hoja Fondos se publica igual, con la sigla escrita en Cuerpos")
        pl, pd = libro_dos_grupos_matriz().payload("legal", "x"), libro_dos_grupos_matriz().payload("directorio", "x")
        ok({f["sigla"] for f in pl["fondos"]} == {"FIAS", "FAP", "FEIG", "PPD"} and {f["sigla"] for f in pd["fondos"]} >= {"FIAS"},
           "cada archivo trae los fondos con que nombrar a sus cuerpos y normas")
        ruta = guardar(libro_dos_grupos(), t, "fondos.xlsx")
        codigo, error, log = correr(["--excel", ruta, "--salida", os.path.join(t, "d3"), "--permitir-sin-clave"], claves)
        ok("fondos: 4" in log and "Pequeñas Donaciones" not in log, "el registro cuenta los fondos pero no nombra nada")

        seccion("10. El texto vigente de una norma, por artículos")
        import texto
        pars = [{"t": x, "b": False} for x in ["CAPÍTULO lll", "DE LAS VACACIONES", "Art. 1.- VIGENCIA: Rige desde hoy.",
                                                  "Cumpliendo las disposiciones de este Reglamento, se aplica.",
                                                  "Art. 2.- Sin rubro, solo texto.", "a) un literal", "DISPOSICIONES GENERALES",
                                                  "PRIMERA.- Lo no previsto lo resuelve la Dirección.",
                                                  "REGLAMENTO", "Art. 1.- Otra numeración que vuelve a empezar."]]
        u = texto.estructurar(pars, True)
        ok(u[0] == {"t": "h1", "txt": "CAPÍTULO III · DE LAS VACACIONES"}, "capítulo con su título; «lll» del OCR se lee como III", u[0])
        ok(u[1]["t"] == "art" and u[1]["rub"] == "VIGENCIA" and u[1]["p"] == ["Rige desde hoy.", "Cumpliendo las disposiciones de este Reglamento, se aplica."],
           "artículo con rubro, y el párrafo siguiente es suyo (aunque diga «disposiciones de»)", u[1])
        ok(u[2]["n"] == "2" and "rub" not in u[2] and u[2]["p"][-1] == "a) un literal", "artículo sin rubro, con su literal")
        ok(u[3] == {"t": "h1", "txt": "DISPOSICIONES GENERALES"}, "«DISPOSICIONES GENERALES» sí es un título", u[3])
        ok([x["id"] for x in u if x["t"] == "art"] == ["p0-a1", "p0-a2", "p1-a1"], "si la numeración vuelve a 1, es otra parte del documento")
        indice = [{"t": x, "b": True} for x in ["i", "ÍNDICE", "1 EL PROGRAMA DE ÁREAS PROTEGIDAS ............................ 1",
                                                 "1.1 Conceptos y objetivos generales .................1", "2 CAPITALIZACIÓN DEL FAP ..... 4",
                                                 "1 EL PROGRAMA DE ÁREAS PROTEGIDAS", "En 1998 se crearon las áreas.... y los guardaparques."]]
        ok([p["t"] for p in texto._sin_indice(indice)] == ["1 EL PROGRAMA DE ÁREAS PROTEGIDAS", "En 1998 se crearon las áreas.... y los guardaparques."],
           "el índice del PDF (puntos guía y número de página, «ÍNDICE», la «i» de la página) no pasa al texto")
        r = texto.extraer(pdf_prueba())
        ok(not r["ocr"] and r["articulos"] == 6 and r["paginas"] == 3, "un PDF digital: 6 artículos, sin OCR", (r["ocr"], r["articulos"]))
        plano_t = json.dumps(r, ensure_ascii=False)
        ok("FONDO DE PRUEBA" not in plano_t and not any(x.get("txt") in ("1", "2", "3") for x in r["unidades"]),
           "fuera el encabezado que se repite y los números de página")
        ok([x["txt"] for x in r["unidades"] if x["t"] == "h1"][1] == "CAPÍTULO II · DE LA OPERACIÓN", "capítulos con su título")
        a5 = next(x for x in r["unidades"] if x.get("n") == "5")
        ok(a5["rub"] == "COMBUSTIBLE" and a5["p"][0].startswith("El combustible se carga"), "rubro y texto de cada artículo", a5)
        import shutil
        if shutil.which("tesseract"):
            r2 = texto.extraer(pdf_prueba(escaneado=True))
            ok(r2["ocr"] and r2["articulos"] == 6, "un PDF escaneado se lee con OCR: los mismos 6 artículos", (r2["ocr"], r2["articulos"]))
        else:
            print("  · (sin Tesseract aquí: la prueba del escaneado corre en GitHub)")
        rm = texto.extraer(pdf_mixto())
        tb = next((u for u in rm["unidades"] if u["t"] == "tabla"), None)
        ok(tb and tb["filas"][0] == ["Destino", "Monto diario", "Movilización"] and tb["filas"][2] == ["Galápagos", "USD 90", "Avioneta"],
           "una tabla del PDF sale como tabla, celda por celda", tb)
        ok(tb and tb.get("de") == "p0-a1", "y queda unida al artículo donde estaba", tb and tb.get("de"))
        fg = next((u for u in rm["unidades"] if u["t"] == "fig"), None)
        ok(fg and fg.get("pg") == 3 and fg.get("tit") == "PROCESO: Pago de viáticos" and rm["control"]["figuras"] == [3],
           "un flujograma no se vuelve frases sueltas: queda como diagrama de su página, con su título", fg and {k: fg.get(k) for k in ("pg", "tit")})
        ok(all(u.get("pg") for u in rm["unidades"]), "cada parte del texto dice de qué página del PDF viene")
        if shutil.which("tesseract"):
            ok(rm["control"]["ocr"] == [2] and "3" in [u.get("n") for u in rm["unidades"] if u["t"] == "art"],
               "una página escaneada en medio de un PDF digital se lee con OCR (antes se perdía sin aviso)", rm["control"])
            ok(rm["control"]["cobertura"] >= 0.97 and not rm["control"]["flojas"] and not rm["control"]["sin_texto"],
               "y se mide lo que pasó: todo el texto del PDF llegó", rm["control"])
        orig = texto._ocr_pagina
        texto._ocr_pagina = lambda page: (_ for _ in ()).throw(RuntimeError("sin tesseract"))
        try:
            rs = texto.extraer(pdf_mixto())
        finally:
            texto._ocr_pagina = orig
        ok(rs["control"]["sin_texto"] == [2], "si una página no se puede leer, el control lo dice con su número", rs["control"])
        ms = publicar.Matriz()
        ms.avisos = []
        publicar.revisar_paso(ms, {"nombre": "Reglamento de Viáticos", "fila": 7, "grupos": ["legal"]}, rs)
        publicar.revisar_paso(ms, {"nombre": "Manual Escaneado", "fila": 8, "grupos": ["legal"]},
                              {"control": {"cobertura": 1.0, "dudosas": [5, 6, 7]}})
        publicar.revisar_paso(ms, {"nombre": "Código de Ética", "fila": 9, "grupos": ["legal"]},
                              {"control": {"cobertura": 1.0, "figuras": [3], "ocr": [2]}})
        ok([(a["fila"], "la pág. 2" in a["texto"]) for a in ms.avisos][:1] == [(7, True)] and "Viáticos" not in ms.avisos[0]["generico"],
           "el robot lo avisa en «Revisión de la matriz»: el detalle cifrado, y en el registro solo que hay algo que revisar", ms.avisos[:1])
        ok(len(ms.avisos) == 2 and "las págs. 5 a 7" in ms.avisos[1]["texto"],
           "también las páginas leídas de un escaneo de baja calidad; un diagrama o un OCR limpio no es un aviso", [a["texto"] for a in ms.avisos])
        ok(texto.calidad("El C6digo del Trabajo y el reglamento lnterno de la organizaci~n " * 10) > 0.01
           and texto.calidad("El Código del Trabajo y el reglamento interno de la organización " * 10) == 0,
           "una capa de OCR mala se reconoce («C6digo», «lnterno»)")

        wb = libro_dos_grupos()
        wn = wb["Normativa"]
        fila = next(i for i in range(2, wn.max_row + 1) if wn.cell(row=i, column=1).value == "Manual Operativo del Ciclo de Proyectos del FAP")
        fila2 = next(i for i in range(2, wn.max_row + 1) if wn.cell(row=i, column=1).value == "Manual de Operaciones del FEIG")
        wn.cell(row=fila, column=col(wn, "pdf", "Normativa")).value = "https://ejemplo.invalid/bueno.pdf"
        wn.cell(row=fila2, column=col(wn, "pdf", "Normativa")).value = "https://ejemplo.invalid/pide-sesion"
        pdf = pdf_prueba()
        bajadas, lecturas = [], []

        def bajar(url):
            bajadas.append(url)
            if "pide-sesion" in url:
                raise ValueError("no es un PDF")
            return pdf

        def leer(b):
            lecturas.append(1)
            return texto.extraer(b)
        cache = os.path.join(t, "cache")
        m = publicar.Matriz().leer(wb)
        publicar.leer_textos(m, cache, "secreto-de-prueba", bajar, leer)
        nm = m.normas["manual-operativo-del-ciclo-de-proyectos-del-fap"]
        ok(nm.get("_texto", {}).get("articulos") == 6, "el robot baja el PDF y lo parte en artículos")
        ok(("Normativa", fila2) in {(a["hoja"], a["fila"]) for a in m.avisos} and not m.normas["manual-de-operaciones-del-feig"].get("_texto"),
           "un enlace que no entrega un PDF (pide iniciar sesión) se avisa")
        cache_txt = "".join(open(os.path.join(cache, f), "rb").read().decode("latin-1") for f in os.listdir(cache))
        ok(len(os.listdir(cache)) == 1 and "combustible" not in cache_txt.lower(), "lo leído se guarda en el caché, cifrado")
        m2 = publicar.Matriz().leer(wb)
        publicar.leer_textos(m2, cache, "secreto-de-prueba", bajar, leer)
        ok(len(lecturas) == 1 and m2.normas["manual-operativo-del-ciclo-de-proyectos-del-fap"].get("_texto"), "la segunda vez sale del caché: el PDF no se vuelve a leer")
        m3 = publicar.Matriz().leer(wb)
        publicar.leer_textos(m3, cache, "otro-secreto", bajar, leer)
        ok(len(lecturas) == 2, "con otro secreto el caché no se puede abrir, y se vuelve a leer")
        texto.VERSION, antes = "otra", texto.VERSION
        publicar.leer_textos(publicar.Matriz().leer(wb), cache, "secreto-de-prueba", bajar, leer)
        texto.VERSION = antes
        ok(len(lecturas) == 3, "si cambia la versión del extractor, lo ya leído se vuelve a leer")
        sal = os.path.join(t, "t1")
        archivos, clave = publicar.escribir_textos(m2, "legal", sal)
        nombre = archivos.get("manual-operativo-del-ciclo-de-proyectos-del-fap", "")
        ok(re.fullmatch(r"t-[0-9a-f]{24}\.json", nombre) and "manual" not in nombre, "el archivo del texto no dice qué norma es", nombre)
        crudo = open(os.path.join(sal, nombre)).read()
        ok("combustible" not in crudo.lower(), "y va cifrado")
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        env = json.load(open(os.path.join(sal, nombre)))
        claro = json.loads(AESGCM(clave).decrypt(base64.b64decode(env["iv"]), base64.b64decode(env["ct"]), b"manual-operativo-del-ciclo-de-proyectos-del-fap"))
        ok(claro["articulos"] == 6, "con la llave del grupo y el id de la norma se abre")
        pl = m2.payload("legal", "x", archivos, clave)
        nm = next(n for n in pl["normas"] if n["id"] == "manual-operativo-del-ciclo-de-proyectos-del-fap")
        ok(nm["texto"] == nombre and nm["textoInfo"]["articulos"] == 6 and "pdf" not in nm and pl.get("claveTextos"),
           "el archivo del grupo trae el nombre, el resumen y la llave; el enlace del PDF no se publica")
        ok(all("pdf" not in n and "_texto" not in n for n in pl["normas"]), "ninguna norma publica su enlace de descarga")
        pd = m2.payload("directorio", "x", *publicar.escribir_textos(m2, "directorio", os.path.join(t, "t2")))
        ok("claveTextos" not in pd, "un grupo sin textos no recibe llave")
        publicar.descargar_pdf = bajar
        codigo, error, log = correr(["--excel", guardar(wb, t, "tx.xlsx"), "--salida", os.path.join(t, "t3"), "--permitir-sin-clave",
                                     "--cache", os.path.join(t, "cache3")], claves)
        ok(codigo == 0 and "con texto: 1" in log and "combustible" not in log.lower() and "bueno.pdf" not in log,
           "el registro cuenta las normas con texto, sin texto ni enlaces", error or log[-300:])

        seccion("11. Como se llena de verdad: varios grupos, puntos en palabras, anexos")
        ok(publicar.grupos_de_texto("Legal y financiero") == ["legal", "financiero"]
           and publicar.grupos_de_texto("Legal, administrativo, programas y proyectos y FAP") == ["legal", "administrativo", "programas-y-proyectos", "fap"]
           and publicar.grupos_de_texto("Legal y RR.HH.") == ["legal", "rr-hh"], "«Legal y financiero» son dos grupos; «programas y proyectos», uno")
        ok([publicar.punto(x) for x in ("Cuatro", "cuarto", "Dos", "-", "Punto 3", "s/n")] == ["4", "4", "2", None, "3", None],
           "el punto escrito con palabras («Cuatro», «cuarto») se entiende; «-» es sin punto")
        wb = crear_plantilla.libro(demo=True)
        wn = wb["Normativa"]
        n0 = wn.max_row + 1
        filas_n = [{"nombre": "Reglamento de Seguridad y Salud Ocupacional", "tipo": "Reglamento", "fecha": "2025-01-10", "grupo": "Legal y RR.HH."},
                   {"nombre": "Manual de prueba con punto en palabras", "organo": "DIR-FIAS", "fecha": "2018-08-16", "punto": "Cinco", "grupo": "Legal y financiero"},
                   {"nombre": "Anexo 1 del Manual de prueba", "anexo": "manual de prueba con PUNTO en palabras", "organo": "DIR-FIAS", "fecha": "2018-08-16"},
                   {"nombre": "Anexo huérfano", "anexo": "Norma que no existe", "organo": "DIR-FIAS", "fecha": "2018-08-16"},
                   {"nombre": "Sin órgano ni grupo", "fecha": "2020-01-01"}]
        for k, f in enumerate(filas_n):
            for c, v in f.items():
                wn.cell(row=n0 + k, column=col(wn, c, "Normativa")).value = v
        m = publicar.Matriz().leer(wb)
        sso = m.normas.get("reglamento-de-seguridad-y-salud-ocupacional")
        ok(sso and sso["grupos"] == ["legal", "rr-hh"] and not sso["organo"], "sin órgano (la aprobó el Ministerio) se publica, si dice quién la ve")
        ok("sin-organo-ni-grupo" not in m.normas and ("Normativa", n0 + 4) in {(a["hoja"], a["fila"]) for a in m.avisos},
           "sin órgano ni grupo, no: no se sabe quién la puede ver")
        ok(m.normas["manual-de-prueba-con-punto-en-palabras"]["res"] == "dir-fias_2018-08-16_p5", "el punto «Cinco» enlaza con la resolución del punto 5")
        ok(m.normas["anexo-1-del-manual-de-prueba"].get("anexo") == "manual-de-prueba-con-punto-en-palabras", "«Anexo de» enlaza con su norma, escrita como sea")
        ok("anexo" not in m.normas["anexo-huerfano"] and ("Normativa", n0 + 3) in {(a["hoja"], a["fila"]) for a in m.avisos}, "un anexo de una norma que no existe se avisa")
        ok("financiero" in m.grupos() and "rr-hh" in m.grupos(), "cada grupo nombrado es un grupo de acceso")
        pf = m.payload("financiero", "x")
        ok([n["id"] for n in pf["normas"]] == ["manual-de-prueba-con-punto-en-palabras"] and not pf["actas"],
           "la frase de financiero abre solo lo marcado para financiero")
        ok(any(n["id"] == "manual-de-prueba-con-punto-en-palabras" for n in m.payload("legal", "x")["normas"]), "y lo mismo lo abre legal")
        wb = crear_plantilla.libro()
        wn = wb["Normativa"]
        for k in range(3):
            for c, v in {"nombre": f"Norma {k}", "organo": "DIR-FIAS", "fecha": "2018-03-12", "punto": "Cuatro"}.items():
                wn.cell(row=2 + k, column=col(wn, c, "Normativa")).value = v
        m = publicar.Matriz().leer(wb)
        ok(len(m.avisos) == 1 and m.avisos[0]["fila"] is None and "3 normas" in m.avisos[0]["texto"],
           "normas cuyas sesiones aún no se cargaron: un solo aviso, no uno por norma", [a["texto"][:60] for a in m.avisos])

    print(f"\n{pruebas - fallos} de {pruebas} comprobaciones bien" + (f" · {fallos} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--sitio":
        sitio(sys.argv[2])
    else:
        main()
