"""v1.37 (regla del cliente, dossier real 2026-11-22): los resúmenes de
noticiero («Titulares») toman el subtema de la noticia de la que habla su
frase sobre la Defensoría. Casos reales 12015267 (La FM) y 12015332 (Canal
RCN), que salían con «Cifras de violencia en Catatumbo»."""
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_s = types.ModuleType('openai'); _s.OpenAI = object; sys.modules.setdefault('openai', _s)
import analyzer_tono_tema as az

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERFIL = json.load(open(os.path.join(RAIZ, 'clientes', 'defensoria_del_pueblo.json'), encoding='utf-8'))
MARCA = dict(brand=PERFIL['brand'], aliases=PERFIL['aliases'], voceros=PERFIL['voceros'])
KM = {'titulo': 'Título', 'resumen': 'Resumen - Aclaracion'}
ALERTAS = 'Alertas Defensoría del Pueblo'
CESAR = 'Atentado con explosivos contra batallón en Cesar'


def _f(tit, ctx, sub, tono='Positivo', resumen=''):
    return {'Título': tit, 'Contexto analizado': ctx, 'Resumen - Aclaracion': resumen,
            'Subtema_IA': sub, 'Tono_IA': tono}


def _dossier():
    return [
        _f('Catatumbo: cinco muertos y 17 heridos en diez días de escalada violenta, alerta la Defensoría',
           'La Defensoría del Pueblo volvió a emitir una alerta y advierte sobre el incremento de las '
           'acciones armadas en el Catatumbo: 17 hechos de violencia en diez días y cinco personas muertas.',
           ALERTAS),
        _f('Defensoría alerta por escalada de violencia en el Catatumbo: estos son los crímenes atroces',
           'La Defensoría del Pueblo reveló que, en apenas diez días, se registraron al menos 17 nuevos '
           'hechos de violencia en el Catatumbo.', ALERTAS),
        _f('Ataque con explosivos contra batallón en Cesar deja un soldado muerto',
           'La Defensoría del Pueblo lamentó la muerte del soldado en el ataque al batallón en La Jagua '
           'de Ibirico, Cesar.', CESAR),
        _f('En Tibú piden intervención del Gobierno ante el conflicto armado en el Catatumbo',
           'Los líderes solicitan la presencia del Gobierno y garantías para las comunidades de Tibú.',
           'Solicitud de intervención por conflicto en Tibú', 'Neutro'),
    ]


def _correr(rows):
    det = []
    n = az.asignar_subtema_resumen_noticiero(rows, KM, reglas=PERFIL['subtemas_fijos'],
                                             detalle=det, **MARCA)
    return n, det


def test_deteccion_de_resumen_de_noticiero():
    for t in ('Titulares', 'Titulares- 22 NOV 2026', 'TITULARES', 'Resumen de noticias',
              'Principales titulares de hoy'):
        assert az.es_resumen_noticiero(t), t
    for t in ('Defensoría alerta por escalada de violencia en el Catatumbo',
              'Los titulares de la semana en el Congreso', 'Ataque contra base militar en el Cesar'):
        assert not az.es_resumen_noticiero(t), t


def test_titulares_la_fm_toma_el_subtema_del_informe():
    rows = _dossier() + [_f(
        'Titulares',
        'El presidente también lo rechazó. La Defensoría del Pueblo reportó 17 nuevos hechos de '
        'violencia en el Catatumbo durante los últimos 10 días, con cinco personas asesinadas. El '
        'Ministerio de las TIC abrió investigaciones contra cinco operadores.',
        'Cifras de violencia en Catatumbo',
        resumen='El soldado que murió tras el atentado contra el batallón en La Jagua de Ibirico fue '
                'identificado.\n\nLa Defensoría del Pueblo reportó 17 nuevos hechos de violencia en el '
                'Catatumbo durante los últimos 10 días, con cinco personas asesinadas.')]
    n, det = _correr(rows)
    assert n == 1 and rows[-1]['Subtema_IA'] == ALERTAS
    # Las demás notas no cambian.
    assert [r['Subtema_IA'] for r in rows[:4]] == [r['Subtema_IA'] for r in _dossier()]


def test_titulares_rcn_lista_numerada():
    rows = _dossier() + [_f(
        'Titulares- 22 NOV 2026',
        '1. La Defensoría del Pueblo advierte sobre continuos ataques en el Catatumbo que dejan cinco '
        'personas muertas 2. Ofensiva contra el ELN en Valle del Cauca. 3. Crisis en el Hospital '
        'Universitario de Santander.', 'Cifras de violencia en Catatumbo')]
    _correr(rows)
    assert rows[-1]['Subtema_IA'] == ALERTAS


def test_noticia_que_no_esta_en_el_dossier_no_cambia():
    rows = _dossier() + [_f(
        'Titulares',
        'La Defensoría del Pueblo presentó su informe anual sobre la situación de las cárceles en '
        'Bogotá y Medellín.', 'Informe sobre cárceles')]
    assert _correr(rows)[0] == 0
    assert rows[-1]['Subtema_IA'] == 'Informe sobre cárceles'


def test_titular_normal_no_es_resumen():
    rows = _dossier() + [_f(
        'Defensoría pide garantías para los líderes del Catatumbo',
        'La Defensoría del Pueblo pidió garantías para los líderes sociales del Catatumbo.',
        'Garantías para líderes del Catatumbo')]
    assert _correr(rows)[0] == 0


def test_tono_del_subtema_fijo_si_la_regla_lo_trae():
    rows = [_f('Pico y placa en Cartagena el 23 de noviembre',
               'La Procuraduría, Contraloría, Defensoría del Pueblo y Personería Distrital tienen '
               'vehículos exentos del pico y placa en Cartagena.', 'Excepciones pico y placa', 'Neutro'),
            _f('Titulares',
               'Rige el pico y placa en Cartagena: la Defensoría del Pueblo y otros organismos de control '
               'tienen vehículos exentos.', 'Movilidad', 'Positivo')]
    _correr(rows)
    assert (rows[1]['Subtema_IA'], rows[1]['Tono_IA']) == ('Excepciones pico y placa', 'Neutro')
