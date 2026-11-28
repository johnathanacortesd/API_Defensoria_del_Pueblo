# -*- coding: utf-8 -*-
"""La columna «texto» no empieza con guiones, espacios ni «:», y solo la
primera letra de la primera palabra va en mayúscula (el resto se conserva)."""
import io

from openpyxl import Workbook, load_workbook

from pipeline import inicio_texto, process_dossier


def test_quita_guiones_espacios_y_dos_puntos():
    assert inicio_texto("- : la alcaldía anunció") == "La alcaldía anunció"
    assert inicio_texto("  — el Distrito dijo") == "El Distrito dijo"
    assert inicio_texto(":: --  texto") == "Texto"


def test_solo_la_primera_letra_el_resto_igual():
    assert inicio_texto("el IDU y la Secretaría de Movilidad") == "El IDU y la Secretaría de Movilidad"
    assert inicio_texto("Ya Empieza Así") == "Ya Empieza Así"
    assert inicio_texto("éxito en la jornada") == "Éxito en la jornada"


def test_apertura_y_numeros():
    assert inicio_texto(": ¿qué pasó?") == "¿Qué pasó?"
    assert inicio_texto('"la frase" dijo') == '"La frase" dijo'
    assert inicio_texto("1.500 personas") == "1.500 personas"
    assert inicio_texto("") == ""
    assert inicio_texto(" - ") == ""


def test_columna_texto_en_el_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.append(["NoticiaId", "Fecha", "Medio", "Tipo de Medio", "Título", "CuerpoEs", "URL Nota"])
    ws.append([1, "2026-11-28", "El Tiempo", "Internet", "Titular de la nota",
               "- : la entidad anunció una jornada de atención en la localidad de Bosa "
               "para los habitantes del sector y sus familias este fin de semana.",
               "https://ejemplo.co/n1"])
    bio = io.BytesIO()
    wb.save(bio)
    res = process_dossier(io.BytesIO(bio.getvalue()), {}, {}, ai_config=None)
    out = load_workbook(io.BytesIO(res["output_data"])).active
    filas = list(out.iter_rows(values_only=True))
    texto = dict(zip(filas[0], filas[1]))["texto"]
    assert texto.startswith("La entidad anunció una jornada")
