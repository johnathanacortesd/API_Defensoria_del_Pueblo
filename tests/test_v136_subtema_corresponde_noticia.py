"""v1.36 (regla del cliente, dossier real 2026-11-22).

1. «Excepciones pico y placa» (Neutro) aplica cuando lo que la nota dice de
   la Defensoría es que sus vehículos están exentos: «La Procuraduría,
   Contraloría, Defensoría del Pueblo y Personería Distrital tienen
   vehículos exentos».
2. La misma noticia lleva el mismo subtema: el ataque al batallón de La
   Jagua de Ibirico (Cesar) salió con tres subtemas, y el informe de la
   Defensoría sobre el Catatumbo con dos.
3. Nunca un subtema que no corresponde: noticias distintas del mismo tema
   general no se unen.
"""
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_s = types.ModuleType('openai'); _s.OpenAI = object; sys.modules.setdefault('openai', _s)
import analyzer_tono_tema as az

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERFIL = json.load(open(os.path.join(RAIZ, 'clientes', 'defensoria_del_pueblo.json'), encoding='utf-8'))
REGLAS = PERFIL['subtemas_fijos']
MARCA = dict(brand=PERFIL['brand'], aliases=PERFIL['aliases'], voceros=PERFIL['voceros'])
KM = {'titulo': 'Título', 'resumen': 'Resumen - Aclaracion'}
CESAR = 'Atentado con explosivos contra batallón en Cesar'
ALERTAS = 'Alertas Defensoría del Pueblo'


def _f(tit, ctx, sub, tono='Positivo'):
    return {'Título': tit, 'Contexto analizado': ctx, 'Subtema_IA': sub, 'Tono_IA': tono}


def _fijos(rows):
    return az.garantizar_subtemas_fijos_filas(rows, KM, REGLAS, mapa={}, **MARCA)


def _evento(rows):
    det = []
    n = az.unificar_subtemas_mismo_evento_final(rows, KM, reglas=REGLAS, detalle=det, **MARCA)
    return n, det


# --- 1. excepciones del pico y placa --------------------------------------------

def test_vehiculos_exentos_de_la_defensoria():
    rows = [_f('Pico y Placa en Cartagena el 23 de noviembre de 2026: Horarios y Dígitos',
               'Los organismos de control y los servicios públicos esenciales están autorizados '
               'para operar libremente. La Procuraduría, Contraloría, Defensoría del Pueblo y '
               'Personería Distrital tienen vehículos exentos. Las empresas prestadoras de servicios '
               'de acueducto también pueden circular.', 'Hombres armados roban camioneta de la Defensoría'),
            # Sin «exentos» en la oración: lo dice el titular (pico y placa).
            _f('Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos',
               'Vehículos de uso exclusivo de concejales del Distrito de Cartagena. Vehículos al '
               'servicio de organismos de control como Procuraduría, Contraloría, Defensoría del '
               'Pueblo y Personería Distrital. Vehículos fúnebres.', 'Otro'),
            # Otro titular, la exención en la oración de la Defensoría.
            _f('Así rige la restricción en Barranquilla este lunes',
               'Están exceptuados los vehículos de la Defensoría del Pueblo, la Fiscalía y la '
               'Procuraduría.', 'Otro')]
    assert _fijos(rows) == 3
    assert {(r['Subtema_IA'], r['Tono_IA']) for r in rows} == {('Excepciones pico y placa', 'Neutro')}


def test_robo_de_un_vehiculo_de_la_defensoria_no_es_excepcion():
    rows = [_f('Hombres armados roban camioneta de la Defensoría en Arauca',
               'Dos hombres armados interceptaron un vehículo de la Defensoría del Pueblo en la vía '
               'a Tame y se lo llevaron.', 'Robo de camioneta de la Defensoría en Arauca', 'Negativo')]
    assert _fijos(rows) == 0
    assert rows[0]['Subtema_IA'] == 'Robo de camioneta de la Defensoría en Arauca'


def test_vehiculos_sin_exencion_en_la_frase_de_la_defensoria_no_aplica():
    """Caso real 62100056: «vehículos» en la nota, pero la Defensoría aparece
    en otra oración y no se habla de exenciones."""
    rows = [_f('Temor en el Norte de Antioquia por la incursión de hombres armados en motos sin placa',
               'La población exige reforzar el control en los corredores donde circulan estos vehículos. '
               'Líderes hacen un llamado a la Defensoría del Pueblo para que emita las alertas tempranas.',
               ALERTAS)]
    _fijos(rows)
    assert rows[0]['Subtema_IA'] == ALERTAS


# --- 2. misma noticia => mismo subtema -------------------------------------------

def _cesar():
    return [
        _f('Ataque con explosivos contra batallón en Cesar deja un soldado muerto y 12 militares heridos',
           'La Defensoría del Pueblo lamentó lo ocurrido y manifestó su preocupación por la utilización '
           'creciente de artefactos explosivos en el conflicto armado tras el ataque al batallón en '
           'La Jagua de Ibirico, Cesar.', CESAR),
        _f('Defensoría y Procuraduría rechazan ataque contra batallón en Cesar y exigen respeto por la vida',
           'La Defensoría del Pueblo y la Procuraduría se pronunciaron frente al ataque con explosivos '
           'contra el Batallón Especial Energético y Vial en La Jagua de Ibirico, Cesar.', CESAR),
        _f('Identifican a soldado asesinado en ataque con explosivos contra batallón del Ejército en Cesar',
           'La Defensoría del Pueblo lamentó la muerte del soldado en el ataque con explosivos contra '
           'el batallón en La Jagua de Ibirico.', CESAR),
        _f('Atentado con explosivos contra batallón en Cesar: hay un soldado muerto y 12 heridos',
           'El presidente rechazó el ataque con explosivos contra el batallón. La Defensoría del Pueblo '
           'también se pronunció sobre este hecho en La Jagua de Ibirico, Cesar.',
           'Ataque con explosivos deja soldado muerto'),
        _f('Ataque contra base militar en el Cesar',
           'En el Cesar criminales lanzaron explosivos contra el batallón del Ejército; murió un '
           'soldado. La Defensoría pidió respetar el DIH.', 'Ataque con explosivos a batallón en Cesar',
           'Neutro'),
    ]


def _catatumbo():
    return [
        _f('Catatumbo: cinco muertos y 17 heridos en diez días de escalada violenta, alerta la Defensoría',
           'La Defensoría del Pueblo emitió una alerta temprana de inminencia y advierte sobre el incremento '
           'de las acciones armadas en el Catatumbo, el uso de drones con explosivos y los desplazamientos.',
           ALERTAS),
        _f('Escalada de violencia en el Catatumbo deja cinco muertos y 17 heridos en diez días',
           'La Defensoría del Pueblo denunció al menos 17 hechos violentos en el Catatumbo entre el 12 y '
           'el 21 de noviembre, con ataques con drones explosivos y desplazamientos forzados.', ALERTAS),
        _f('Defensoría alerta por recrudecimiento del conflicto en el Catatumbo',
           'La Defensoría del Pueblo alertó sobre el agravamiento de la crisis humanitaria en el Catatumbo: '
           '17 hechos violentos entre el 12 y el 21 de noviembre, ataques con drones y desplazamientos.',
           'Alerta sobre escalada armada en Catatumbo'),
    ]


def test_ataque_en_cesar_un_solo_subtema():
    rows = _cesar()
    n, det = _evento(rows)
    assert n == 2
    assert {r['Subtema_IA'] for r in rows} == {CESAR}
    # El tono no se toca en un rótulo libre.
    assert rows[4]['Tono_IA'] == 'Neutro'


def test_informe_catatumbo_toma_el_subtema_fijo():
    rows = _catatumbo()
    _evento(rows)
    assert {r['Subtema_IA'] for r in rows} == {ALERTAS}


# --- 3. no se ponen subtemas que no corresponden ------------------------------

def test_hechos_distintos_del_mismo_tema_no_se_unen():
    """Drones en el Catatumbo y drones en el Cesar; Tibú pide intervención
    (otra noticia del Catatumbo); el balance del Acuerdo de Paz."""
    rows = _cesar() + _catatumbo() + [
        _f('En Tibú piden intervención del Gobierno ante el conflicto armado en el Catatumbo',
           'Los líderes consideran que las comunidades deben contar con garantías y solicitan la '
           'presencia de la Defensoría del Pueblo y del Gobierno en Tibú.',
           'Solicitud de intervención por conflicto en Tibú', 'Neutro'),
        _f('Juan Manuel Santos defiende el legado del acuerdo de paz con las Farc',
           'Según cifras de la Defensoría del Pueblo, 10.943 personas permanecen en reincorporación.',
           'Balance de diez años del Acuerdo de paz', 'Neutro')]
    _evento(rows)
    subs = [r['Subtema_IA'] for r in rows]
    assert set(subs[:5]) == {CESAR}
    assert set(subs[5:8]) == {ALERTAS}
    assert subs[8] == 'Solicitud de intervención por conflicto en Tibú'
    assert subs[9] == 'Balance de diez años del Acuerdo de paz'


def test_mismo_molde_en_otra_ciudad_no_se_une_por_la_marca():
    """El nombre del cliente en el titular no es un ancla del hecho."""
    marca = dict(brand='Fundación Santa Fe', aliases=['Fundación Santa Fe de Bogotá', 'FSFB'], voceros=[])
    rows = [_f('Fundación Santa Fe inaugura nueva sede de urgencias en Chía',
               'La Fundación Santa Fe de Bogotá inauguró una nueva sede de urgencias en Chía.',
               'Inauguración de sede de urgencias en Chía'),
            _f('Fundación Santa Fe abre nueva sede de urgencias en Usaquén',
               'La Fundación Santa Fe de Bogotá abrió una nueva sede de urgencias en Usaquén.',
               'Apertura de sede de urgencias'),
            _f('Fundación Santa Fe abre sede de urgencias en Usaquén',
               'La Fundación Santa Fe de Bogotá abrió una sede de urgencias en Usaquén.',
               'Apertura de sede de urgencias')]
    assert az.unificar_subtemas_mismo_evento_final(rows, KM, reglas=[], **marca) == 0
    assert rows[0]['Subtema_IA'] == 'Inauguración de sede de urgencias en Chía'


def test_notas_con_subtema_fijo_no_cambian():
    rows = _catatumbo()
    rows[2]['Subtema_IA'] = 'Excepciones pico y placa'   # fijo distinto: no se mezcla
    _evento(rows)
    assert rows[2]['Subtema_IA'] == 'Excepciones pico y placa'
