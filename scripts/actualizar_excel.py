# -*- coding: utf-8 -*-
"""
Pasa un Excel ya llenado a la plantilla más nueva, sin perder nada.

    python3 scripts/actualizar_excel.py mi_matriz.xlsx mi_matriz_actualizada.xlsx

Cuando la plantilla gana una columna («PDF para leer en Quórum», «Anexo de»),
el Excel que ya se venía llenando no la tiene. Esto arma la plantilla nueva
(con sus listas desplegables y notas) y copia cada dato por el NOMBRE de su
columna, no por su posición. Lo que no tiene lugar en la plantilla se dice
por pantalla, para que nada se pierda en silencio.

Si el Excel tiene contraseña, quítasela antes (o ábrelo y guárdalo sin ella):
este paso es local, en tu computadora; luego vuelve a ponérsela.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matriz import HOJAS, plano  # noqa: E402
import crear_plantilla  # noqa: E402


def leer(ruta):
    import openpyxl
    wb = openpyxl.load_workbook(ruta, data_only=True)
    datos, sobra = {}, []
    for hoja, cols in HOJAS.items():
        if hoja not in wb.sheetnames:
            continue
        ws = wb[hoja]
        encs = [plano(c.value) for c in ws[1]]
        mapa = {}
        for clave, enc, *_ in cols:
            e = plano(enc)
            j = next((j for j, h in enumerate(encs) if h == e or (h and h.startswith(e))), None)
            if j is not None:
                mapa[clave] = j
        sobra += [f"{hoja} → «{ws[1][j].value}»" for j, h in enumerate(encs) if h and j not in mapa.values()]
        filas = []
        for fila in ws.iter_rows(min_row=2, values_only=True):
            d = {k: fila[j] for k, j in mapa.items() if j < len(fila) and fila[j] not in (None, "")}
            if d:
                filas.append(d)
        datos[hoja] = filas
    return datos, sobra


if __name__ == "__main__":
    origen, destino = sys.argv[1], sys.argv[2]
    datos, sobra = leer(origen)
    crear_plantilla.libro(datos=datos).save(destino)
    for hoja, filas in datos.items():
        print(f"{hoja}: {len(filas)} renglones")
    if sobra:
        print("Columnas que la plantilla no tiene (no se copiaron):\n  " + "\n  ".join(sobra))
