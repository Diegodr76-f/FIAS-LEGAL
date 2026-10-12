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


def sitio(carpeta):
    """Datos cifrados de dos grupos, para la prueba de la página."""
    with tempfile.TemporaryDirectory() as t:
        ruta = guardar(libro_dos_grupos(), t)
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
        ok("fila 57" in log, "solo la hoja y el renglón del aviso", log)

        seccion("5. Sin frase, nada se publica")
        sal2 = os.path.join(t, "datos2")
        codigo, error, log = correr(["--excel", ruta, "--salida", sal2, "--permitir-sin-clave"], {"CLAVES": f"legal = {FRASE_LEGAL}"})
        ok(error and "directorio" in error and not os.path.exists(sal2), "falta la frase de un grupo: no se escribe NADA", error)
        codigo, error, log = correr(["--excel", ruta, "--salida", sal2, "--permitir-sin-clave"], {"CLAVES": "legal = corta\ndirectorio = corta"})
        ok(error and "corta" in error and not os.path.exists(sal2), "una frase corta tampoco", error)
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
        ok(len(m.res) == 56, "una columna de más al inicio y un encabezado sin tildes y con añadido", len(m.res))
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

    print(f"\n{pruebas - fallos} de {pruebas} comprobaciones bien" + (f" · {fallos} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--sitio":
        sitio(sys.argv[2])
    else:
        main()
