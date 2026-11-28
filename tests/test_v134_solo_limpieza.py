# -*- coding: utf-8 -*-
"""v1.34: la app es solo de limpieza y detección de duplicados. No llama a
ninguna API; Tono_IA y Subtema_IA salen vacíos y el resto del
xlsx (Contexto analizado, texto, ID duplicada, FECHA INFORME, HORA B…) se
arma como siempre."""
import io
import json
import os
from unittest.mock import patch

from openpyxl import Workbook, load_workbook

import analyzer_tono_tema as az
import pipeline
from pipeline import columnas_boletin, construir_ai_config_custom, process_dossier

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VACIAS = ("Tono_IA", "Subtema_IA")


def _dossier():
    wb = Workbook()
    ws = wb.active
    ws.append(["NoticiaId", "Fecha", "Medio", "Tipo de Medio", "Título", "CuerpoEs",
               "URL Nota", "Menciones - Empresa", "Empresa rel."])
    cuerpo = ("La Defensoría del Pueblo emitió una alerta temprana en el Cauca. "
              "La entidad pidió proteger a 1.500 líderes sociales. "
              "El informe se entregó al Gobierno.")
    ws.append([101, "2026-11-27", "El Tiempo", "Internet",
               "Defensoría emite alerta temprana en el Cauca", cuerpo,
               "https://ejemplo.co/alerta", "Defensoría del Pueblo", "Defensoría del Pueblo"])
    # Misma URL y misma mención: duplicada.
    ws.append([102, "2026-11-27", "El Tiempo", "Internet",
               "Defensoría emite alerta temprana en el Cauca", cuerpo,
               "https://ejemplo.co/alerta", "Defensoría del Pueblo", "Defensoría del Pueblo"])
    ws.append([103, "2026-11-27", "Semana", "Internet",
               "Opinión: el metro de Bogotá", "Columna sobre la Defensoría del Pueblo.",
               "https://ejemplo.co/opinion/metro", "Defensoría del Pueblo", "Defensoría del Pueblo"])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _perfil():
    with open(os.path.join(RAIZ, "clientes",
                           "defensoria_del_pueblo.json"),
              encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["enabled"] = True  # aunque llegue activado, no se usa IA
    cfg["motor"] = "haiku"
    return cfg


def _hoja(res):
    ws = load_workbook(io.BytesIO(res["output_data"])).active
    filas = list(ws.iter_rows(values_only=True))
    return list(filas[0]), [dict(zip(filas[0], f)) for f in filas[1:]]


def _sin_api():
    return [
        patch.object(az, "llamar_llm", side_effect=AssertionError("sin API")),
        patch("requests.post", side_effect=AssertionError("sin API")),
        patch.object(az, "enrich_rows_with_ai", side_effect=AssertionError("sin IA")),
    ]


def _correr(cfg):
    ps = _sin_api()
    for p in ps:
        p.start()
    try:
        return process_dossier(io.BytesIO(_dossier()), {}, {}, ai_config=cfg)
    finally:
        for p in ps:
            p.stop()


def test_boletin_defensoria_columnas_y_clasificacion_vacia():
    res = _correr(_perfil())
    headers, filas = _hoja(res)
    assert headers == columnas_boletin(False)
    assert "TIPO" not in headers and "GÉNERO" not in headers
    assert len(filas) == 3
    for f in filas:
        for col in VACIAS:
            assert f[col] in (None, ""), (col, f[col])
        assert f["HORA B"]
        assert f["FECHA INFORME"] is not None


def test_detecta_duplicados_y_arma_contexto():
    res = _correr(_perfil())
    assert res["duplicates"] == 1
    _, filas = _hoja(res)
    por_id = {f["ID Noticia"]: f for f in filas}
    assert por_id[102]["ID duplicada"] == 101
    assert por_id[102]["Contexto analizado"] == "-"
    assert "Defensoría" in por_id[101]["Contexto analizado"]
    assert por_id[101]["texto"]
    assert res["vista"] == []
    assert res["analisis"] == {}


def test_sin_perfil_ni_marca_tambien_limpia():
    res = _correr(None)
    headers, filas = _hoja(res)
    for col in ("Tono_IA", "Subtema_IA"):
        assert col in headers
    assert "Tema_IA" not in headers
    assert all(f["Tono_IA"] in (None, "") for f in filas)


def test_config_personalizada_siempre_existe_sin_ia():
    cfg = construir_ai_config_custom("Marca", "", "", "General")
    assert cfg is not None
    assert cfg["enabled"] is False
    assert cfg["api_key"] is None
    assert cfg["preservar_columnas"] is True


def test_pipeline_no_importa_el_motor_de_ia():
    assert not hasattr(pipeline, "enrich_rows_with_ai")
    assert not hasattr(pipeline, "apply_pkl_classifiers")
