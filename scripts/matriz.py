# -*- coding: utf-8 -*-
"""
La forma del Excel de Quórum, escrita una sola vez.

La usan los dos lados: `crear_plantilla.py` arma con esto las hojas, los
encabezados, las listas desplegables y las notas de cada columna, y
`publicar.py` lee con esto lo que se llenó. Si una columna cambia de nombre
aquí, cambia en los dos, y no puede pasar que la plantilla diga una cosa y el
robot busque otra.

Cada columna es (clave, encabezado, ayuda, ancho, tipo):
  - clave: el nombre con el que viaja en el JSON publicado.
  - encabezado: el texto exacto de la fila 1 del Excel. El robot lo reconoce
    también sin tildes, en otro orden y con espacios de más: el Excel lo maneja
    una persona y se reordena.
  - tipo: 'texto', 'fecha', 'enlace', o 'lista:<NOMBRE>' (desplegable).
"""
import re
import unicodedata

ENTIDADES = ["FIAS", "FAP", "FEIG"]
TIPOS_SESION = ["Ordinaria", "Extraordinaria"]
TIPOS_PROG = ["Programa", "Proyecto"]
TIPOS_NORMA = ["Estatuto", "Reglamento", "Manual", "Política", "Procedimiento",
               "Instructivo", "Lineamiento", "Código", "Otro"]
MATERIAS = ["Normativa", "Presupuesto y finanzas", "Inversiones",
            "Proyectos y convocatorias", "Convenios y alianzas", "Talento humano",
            "Designaciones", "Gobierno corporativo", "Administrativo", "Otros"]

# Qué hace cada tipo de cambio con lo que toca. La vigencia NO se escribe en el
# Excel: se deduce de aquí, en el navegador, a la fecha que se pregunte.
TIPOS_CAMBIO = ["Reforma", "Reforma parcial", "Codificación", "Derogación",
                "Deja sin efecto", "Aclaración"]
TERMINAN = {"Derogación", "Deja sin efecto"}
NUEVA_VERSION = {"Reforma", "Reforma parcial", "Codificación"}

LISTAS = {
    "ENTIDADES": ENTIDADES,
    "TIPOS_SESION": TIPOS_SESION,
    "TIPOS_PROG": TIPOS_PROG,
    "TIPOS_NORMA": TIPOS_NORMA,
    "MATERIAS": MATERIAS,
    "TIPOS_CAMBIO": TIPOS_CAMBIO,
}

# Los tres que se conocen hoy. Se pueden añadir más filas en la hoja Cuerpos.
CUERPOS_INICIALES = [
    ("DIR-FIAS", "Directorio del FIAS", "FIAS", "legal"),
    ("JA-FAP", "Junta Administrativa del FAP", "FAP", "legal"),
    ("DIR-FEIG", "Directorio del FEIG", "FEIG", "legal"),
]

GRUPO_POR_OMISION = "legal"

HOJAS = {
    "Cuerpos": [
        ("sigla", "Sigla", "Corta y sin repetirse (p. ej. JA-FAP). Es como se escribe el cuerpo en las demás hojas.", 14, "texto"),
        ("nombre", "Nombre completo", "Como debe leerse en pantalla: «Junta Administrativa del FAP».", 40, "texto"),
        ("entidad", "Entidad", "FIAS, FAP o FEIG.", 12, "lista:ENTIDADES"),
        ("grupo", "Grupo de acceso", "Qué frase abre las actas y resoluciones de este cuerpo. Si todos los abogados ven todo, deja «legal» en todas las filas.", 18, "texto"),
        ("obs", "Observaciones", "", 40, "texto"),
    ],
    "Programas": [
        ("nombre", "Programa o proyecto", "Sin repetirse. Es como se escribe en las hojas Actas y Resoluciones.", 44, "texto"),
        ("tipo", "Tipo", "Programa o Proyecto.", 12, "lista:TIPOS_PROG"),
        ("entidad", "Entidad", "FIAS, FAP o FEIG.", 10, "lista:ENTIDADES"),
        ("obs", "Observaciones", "", 40, "texto"),
    ],
    "Actas": [
        ("cuerpo", "Cuerpo colegiado", "La sigla de la hoja Cuerpos.", 16, "lista:CUERPOS"),
        ("fecha", "Fecha de la sesión", "dd/mm/aaaa. Con el cuerpo, es lo que identifica al acta.", 14, "fecha"),
        ("tipo", "Tipo de sesión", "Ordinaria o Extraordinaria.", 14, "lista:TIPOS_SESION"),
        ("numero", "N.º de sesión", "Opcional. Solo si la sesión tiene número.", 11, "texto"),
        ("programa", "Programa o proyecto", "De cuál trata la sesión (como está en la hoja Programas). Si trata de varios, sepáralos con punto y coma. Vacío = asunto general.", 34, "texto"),
        ("provisional", "Acta provisional (enlace)", "Enlace al PDF en la carpeta. Opcional.", 34, "enlace"),
        ("definitiva", "Acta definitiva (enlace)", "Enlace al PDF firmado. Mientras esté vacío, el acta se muestra como provisional.", 34, "enlace"),
        ("aprobacion", "Fecha de aprobación del acta definitiva", "Cuándo se aprobó el acta definitiva (normalmente, en la sesión siguiente).", 18, "fecha"),
        ("obs", "Observaciones", "", 40, "texto"),
    ],
    "Resoluciones": [
        ("cuerpo", "Cuerpo colegiado", "La sigla de la hoja Cuerpos.", 16, "lista:CUERPOS"),
        ("fecha", "Fecha de la sesión", "La del acta donde se resolvió.", 14, "fecha"),
        ("punto", "Punto del orden del día", "El número del punto: 3, no «tercero». Cuerpo + fecha + punto identifican a la resolución.", 12, "texto"),
        ("texto", "Lo que se resolvió", "El texto o un resumen fiel de lo resuelto.", 70, "texto"),
        ("materia", "Materia", "Para filtrar. Se puede escribir otra si ninguna sirve.", 22, "lista:MATERIAS"),
        ("programa", "Programa o proyecto (solo si es distinto del acta)", "Por omisión, la resolución es del programa o proyecto de su acta. Escríbelo aquí solo si esta resolución trata de otro, o de uno solo entre varios. Varios: separados con punto y coma.", 34, "texto"),
        ("enlace", "Enlace (opcional)", "Si la resolución tiene documento propio (certificación, extracto).", 30, "enlace"),
        ("obs", "Observaciones", "", 40, "texto"),
    ],
    "Normativa": [
        ("nombre", "Nombre de la norma", "Sin repetirse. Es como se la nombra en la hoja Cambios.", 46, "texto"),
        ("tipo", "Tipo", "Reglamento, Manual, Política…", 14, "lista:TIPOS_NORMA"),
        ("entidad", "Entidad", "FIAS, FAP o FEIG.", 10, "lista:ENTIDADES"),
        ("organo", "Órgano que la aprueba", "Sigla del cuerpo competente (p. ej. el Manual de Ciclo lo aprueba la JA-FAP).", 16, "lista:CUERPOS"),
        ("fecha", "Fecha de aprobación", "Fecha de la sesión que la aprobó.", 14, "fecha"),
        ("punto", "Punto en que se aprobó", "Opcional. Con órgano + fecha + punto, la norma queda enlazada a su resolución.", 12, "texto"),
        ("enlace", "Texto original (enlace)", "PDF del texto aprobado.", 34, "enlace"),
        ("grupo", "Grupo de acceso", "Opcional. Vacío = el mismo grupo del órgano que la aprueba.", 16, "texto"),
        ("obs", "Observaciones", "", 40, "texto"),
    ],
    "Cambios": [
        ("norma", "Norma afectada", "Si lo que cambia es una norma: su nombre, igual que en la hoja Normativa. Si cambia una resolución, deja esto vacío y llena las tres columnas siguientes.", 40, "lista:NORMAS"),
        ("rcuerpo", "Resolución afectada: cuerpo", "Si lo que cambia es una resolución.", 16, "lista:CUERPOS"),
        ("rfecha", "Resolución afectada: fecha de la sesión", "", 16, "fecha"),
        ("rpunto", "Resolución afectada: punto", "", 12, "texto"),
        ("tipo", "Tipo de cambio", "Reforma, Reforma parcial y Codificación crean una versión nueva. Derogación y Deja sin efecto terminan la vigencia. Aclaración solo se anota.", 18, "lista:TIPOS_CAMBIO"),
        ("pcuerpo", "Resuelto por: cuerpo", "La resolución que hizo el cambio.", 16, "lista:CUERPOS"),
        ("pfecha", "Resuelto por: fecha de la sesión", "", 16, "fecha"),
        ("ppunto", "Resuelto por: punto", "", 12, "texto"),
        ("rige", "Rige desde", "Solo si el cambio rige desde otra fecha que la de la sesión.", 14, "fecha"),
        ("articulos", "Artículos", "Opcional, para reformas parciales: «arts. 12 y 15».", 18, "texto"),
        ("enlace", "Texto vigente después del cambio (enlace)", "El texto codificado o reformado. Desde esta fecha, es el que se abre como vigente.", 34, "enlace"),
        ("detalle", "Detalle", "Opcional.", 40, "texto"),
    ],
}

# Lo mínimo para que una fila tenga sentido. Si falta la COLUMNA entera, el
# robot no publica (mejor lo de ayer que algo a medias); si falta el dato en
# una fila, esa fila se salta con un aviso.
OBLIGATORIAS = {
    "Cuerpos": ["sigla"],
    "Programas": ["nombre"],
    "Actas": ["cuerpo", "fecha"],
    "Resoluciones": ["cuerpo", "fecha", "punto", "texto"],
    "Normativa": ["nombre", "organo", "fecha"],
    "Cambios": ["tipo"],
}


def plano(s):
    """Sin tildes, minúsculas y un solo espacio: para comparar lo que escribe una persona."""
    s = unicodedata.normalize("NFD", str(s if s is not None else ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def slug(s, largo=60):
    s = re.sub(r"[^a-z0-9]+", "-", plano(s)).strip("-")
    return s[:largo].strip("-")
