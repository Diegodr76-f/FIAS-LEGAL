# -*- coding: utf-8 -*-
"""
Que en el repositorio no entre nunca un dato real.

    python3 scripts/vigilar_repo.py

El repositorio es público. Los datos se publican cifrados por otro camino (el
robot los despliega directo a GitHub Pages, sin commit), así que aquí solo
deben vivir el código, la plantilla vacía y la demostración con datos
ficticios. Esto lo comprueba sobre los archivos que git sigue, en cada push.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PERMITIDOS_XLSX = {"plantilla/Quorum_matriz.xlsx", "demo/matriz_demo.xlsx"}
PERMITIDOS_JSON = {"demo/datos-demo.json"}
PROHIBIDAS = (".pdf", ".docx", ".doc", ".xls", ".csv", ".zip")
SOBRE = re.compile(r'"q_enc"\s*:\s*1\s*,\s*"kdf"')


def main():
    archivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split()
    malos = []
    for a in archivos:
        bajo = a.lower()
        if bajo.startswith(("datos/", "_site/")):
            malos.append(f"{a}: lo publicado no se sube al repositorio (lo despliega el robot)")
        elif bajo.endswith(".xlsx") and a not in PERMITIDOS_XLSX:
            malos.append(f"{a}: un Excel que no es la plantilla ni la demostración")
        elif bajo.endswith(".json") and a not in PERMITIDOS_JSON:
            malos.append(f"{a}: un JSON que no es el de la demostración")
        elif bajo.endswith(PROHIBIDAS):
            malos.append(f"{a}: los documentos viven en OneDrive, no aquí")
        elif not a.startswith("scripts/") and os.path.isfile(os.path.join(RAIZ, a)):
            try:
                with open(os.path.join(RAIZ, a), encoding="utf-8") as f:
                    if SOBRE.search(f.read()):
                        malos.append(f"{a}: trae un sobre cifrado; ni cifrados entran al historial")
            except UnicodeDecodeError:
                pass

    import openpyxl
    from publicar import Matriz
    if "plantilla/Quorum_matriz.xlsx" in archivos:
        wb = openpyxl.load_workbook(os.path.join(RAIZ, "plantilla", "Quorum_matriz.xlsx"))
        m = Matriz().leer(wb)
        if m.actas or m.res or m.normas or m.cambios:
            malos.append("plantilla/Quorum_matriz.xlsx: la plantilla tiene datos; debe ir vacía")
    if "demo/matriz_demo.xlsx" in archivos:
        wb = openpyxl.load_workbook(os.path.join(RAIZ, "demo", "matriz_demo.xlsx"))
        if "FICTICIOS" not in (wb.properties.title or ""):
            malos.append("demo/matriz_demo.xlsx: no lleva la marca de datos ficticios")
    if "demo/datos-demo.json" in archivos:
        with open(os.path.join(RAIZ, "demo", "datos-demo.json"), encoding="utf-8") as f:
            if json.load(f).get("demo") is not True:
                malos.append("demo/datos-demo.json: no es la demostración")

    if malos:
        print("No pasa: el repositorio es público y esto no debe estar en él.\n")
        print("\n".join("  ✗ " + x for x in malos))
        sys.exit(1)
    print(f"  ✓ {len(archivos)} archivos revisados: ningún dato real en el repositorio")


if __name__ == "__main__":
    main()
