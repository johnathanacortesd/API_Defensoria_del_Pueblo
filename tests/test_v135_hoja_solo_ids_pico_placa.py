"""v1.35 (regla del cliente, caso real 2026-11-22).

IDs 62099263 (Eluniversal.com.co) y 62099331 (Co.headtopics.com): dos notas
de pico y placa en Cartagena salieron con el subtema «Hombres armados roban
camioneta de la Defensoría» (tomado de la hoja de notas analizadas) y tono
Positivo.

- La hoja de Google Sheets SOLO sirve para saber qué notas ya están
  analizadas (columna ID); sus TEMAS no clasifican notas nuevas.
- Las notas de pico y placa (la Defensoría solo aparece en la lista de
  vehículos exentos) van a «Excepciones pico y placa», tono Neutro (v1.36:
  la regla se decide por la oración que nombra a la Defensoría).
"""
import inspect
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_s = types.ModuleType('openai'); _s.OpenAI = object; sys.modules.setdefault('openai', _s)
import analyzer_tono_tema as az
import memoria_cliente
import perfil_cliente
import pipeline

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KM = {'titulo': 'Título', 'resumen': 'Resumen - Aclaracion'}
PERFIL = json.load(open(os.path.join(RAIZ, 'clientes', 'defensoria_del_pueblo.json'), encoding='utf-8'))
REGLAS = PERFIL['subtemas_fijos']
MARCA = dict(brand=PERFIL['brand'], aliases=PERFIL['aliases'], voceros=PERFIL['voceros'])
ROBO = 'Hombres armados roban camioneta de la Defensoría'


def _filas_reales():
    return [
        {'ID Noticia': '62099263',
         'Título': 'Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos',
         'Resumen - Aclaracion': 'Infórmate sobre las restricciones vehiculares del 23 de noviembre '
                                 'de 2026. Consulta los horarios, dígitos restringidos y excepciones '
                                 'vigentes. Evita sanciones.',
         'Contexto analizado': 'Vehículos de uso exclusivo de concejales del Distrito de Cartagena. '
                               'Vehículos al servicio de organismos de control como Procuraduría, '
                               'Contraloría, Defensoría del Pueblo y Personería Distrital.',
         'Subtema_IA': ROBO, 'Tono_IA': 'Positivo'},
        {'ID Noticia': '62099331',
         'Título': 'Pico y Placa en Cartagena el 23 de noviembre de 2026: Horarios y Dígitos',
         'Resumen - Aclaracion': 'Conozca los dígitos afectados por el pico y placa en Cartagena '
                                 'este 23 de noviembre de 2026.',
         'Contexto analizado': 'Los organismos de control y los servicios públicos esenciales están '
                               'autorizados para operar libremente. La Procuraduría, Contraloría, '
                               'Defensoría del Pueblo y Personería Distrital tienen vehículos exentos.',
         'Subtema_IA': ROBO, 'Tono_IA': 'Positivo'},
    ]


# --- la hoja solo filtra por ID ---------------------------------------------

def test_la_hoja_ya_no_aporta_subtemas():
    assert not hasattr(pipeline, 'cargar_hoja_analizadas')
    assert not hasattr(az, 'anclar_subtemas_hoja')
    assert not hasattr(memoria_cliente, 'buscar_referencia')
    assert not hasattr(memoria_cliente, 'referencias_de_tabla')
    # El analizador no lee referencias de la hoja aunque lleguen en `extra`.
    assert 'referencias_sheets' not in inspect.getsource(az)
    app = open(os.path.join(RAIZ, 'app.py'), encoding='utf-8').read()
    assert 'Retomar el subtema' not in app
    assert 'cargar_hoja_analizadas' not in app


def test_la_hoja_sigue_filtrando_por_id(tmp_path):
    p = tmp_path / 'hoja.csv'
    p.write_text('ID,TÍTULO,TEMA\n62099263,Pico y placa,%s\n61142011.0,Otra,No aplica\n' % ROBO,
                 encoding='utf-8')
    assert pipeline.cargar_ids_analizados_desde_sheets(str(p)) == {'62099263', '61142011'}


# --- regla de pico y placa ----------------------------------------------------

def test_perfil_trae_la_regla_y_la_conserva_al_normalizar():
    regla = next(r for r in REGLAS if r['subtema'] == 'Excepciones pico y placa')
    assert regla['tono'] == 'Neutro' and regla['frase_marca']
    assert perfil_cliente.validar_perfil(PERFIL) == []
    assert regla in perfil_cliente.normalizar_perfil(PERFIL)['subtemas_fijos']
    malo = dict(PERFIL, subtemas_fijos=[dict(regla, tono='Bueno')])
    assert perfil_cliente.validar_perfil(malo)


def test_caso_real_pico_y_placa_excepciones_neutro():
    rows = _filas_reales()
    n = az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={0: 1, 1: 1}, **MARCA)
    assert n == 2
    assert [r['Subtema_IA'] for r in rows] == ['Excepciones pico y placa'] * 2
    assert [r['Tono_IA'] for r in rows] == ['Neutro'] * 2


def test_cada_nota_por_si_sola_aunque_no_esten_agrupadas():
    rows = _filas_reales()
    az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={0: 1, 1: 2}, **MARCA)
    assert [(r['Subtema_IA'], r['Tono_IA']) for r in rows] == [
        ('Excepciones pico y placa', 'Neutro')] * 2


def test_pico_y_placa_al_fondo_de_otra_nota_no_cuenta():
    """La frase debe estar en el titular, la entrada o el pasaje de la
    Defensoría, no perdida al final de un cuerpo largo sobre otro asunto."""
    cuerpo = ('La Defensoría del Pueblo emitió un informe sobre la crisis humanitaria en el '
              'Catatumbo y pidió atención urgente para las familias desplazadas. ' * 12
              + 'En otras noticias, mañana rige el pico y placa habitual.')
    rows = [{'Título': 'Defensoría pide atención urgente para desplazados del Catatumbo',
             'Resumen - Aclaracion': cuerpo,
             'Contexto analizado': 'La Defensoría del Pueblo pidió atención urgente para las familias.',
             'Subtema_IA': 'Crisis humanitaria en el Catatumbo', 'Tono_IA': 'Positivo'}]
    assert az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={0: 1}, **MARCA) == 0
    assert rows[0]['Subtema_IA'] == 'Crisis humanitaria en el Catatumbo'
    assert rows[0]['Tono_IA'] == 'Positivo'


def test_alertas_tempranas_siguen_igual_y_no_tocan_el_tono():
    rows = [{'Título': 'Defensoría emite alerta temprana por reclutamiento en el Cauca',
             'Contexto analizado': 'La Defensoría emitió una alerta temprana.',
             'Subtema_IA': 'Reclutamiento en el Cauca', 'Tono_IA': 'Positivo'}]
    assert az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={0: 1}, **MARCA) == 1
    assert rows[0]['Subtema_IA'] == 'Alertas Defensoría del Pueblo'
    assert rows[0]['Tono_IA'] == 'Positivo'


def test_los_pases_anteriores_ignoran_la_regla_de_solo_final():
    """Solo la garantía final aplica pico y placa (con su `donde`)."""
    ajustes = az.aplicar_subtemas_fijos_final(_filas_reales(), {}, KM, REGLAS)
    assert ajustes == {}
    grupos = [{'grupo': 1, 'titulo': _filas_reales()[0]['Título']}]
    etiquetas = {1: {'sub_tema': ROBO, 'tono': 'Positivo'}}
    assert az.aplicar_subtemas_fijos(grupos, etiquetas, REGLAS, estricta=True) == 0


def test_duplicadas_no_se_tocan():
    rows = _filas_reales()
    rows[1].update(is_duplicate=True, Tono_IA='Duplicada', Subtema_IA='-')
    az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={0: 1, 1: 1}, **MARCA)
    assert (rows[1]['Tono_IA'], rows[1]['Subtema_IA']) == ('Duplicada', '-')
