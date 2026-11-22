"""v1.34: el TEMA de la hoja de notas analizadas no se pega a una nota que no
habla de él.

Caso real 2026-11-22: IDs 62099263 (Eluniversal.com.co) y 62099331
(Co.headtopics.com), dos notas de pico y placa en Cartagena, salieron con el
subtema «Hombres armados roban camioneta de la Defensoría». La nota diaria de
pico y placa es una plantilla: la del día anterior en la hoja se parecía en
84 % de su comienzo y el anclaje de v1.30 la tomó por la MISMA nota (solo el
titular revisaba las cifras), y la otra nota la heredó por estar en el mismo
grupo.
"""
import os, sys, types
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_s = types.ModuleType('openai'); _s.OpenAI = object; sys.modules.setdefault('openai', _s)
import memoria_cliente as mc
import analyzer_tono_tema as az
from coherencia_texto import rotulo_con_sustento, tokens_marca

KM = {'titulo': 'Título', 'resumen': 'Resumen - Aclaracion'}
HOY = datetime.now().strftime('%d/%m/%Y')
CAB = ['ID', 'FECHA', 'MEDIO', 'TÍTULO', 'RESUMEN', 'TEMA', 'TONO']
ROBO = 'Hombres armados roban camioneta de la Defensoría'
MARCA = tokens_marca('Defensoría del Pueblo', ['Defensoría', 'la Defensoría', 'DP'],
                     ['Iris Marín Ortiz'])


def _pico_placa(dia, digitos='1 y 2', taxis='5 y 6'):
    return ('Infórmate sobre las restricciones vehiculares del %s de noviembre de 2026. Consulta '
            'los horarios, dígitos restringidos y excepciones vigentes. Evita sanciones. A '
            'continuación te mostramos los detalles del pico y placa en Cartagena para vehículos '
            'particulares, motocicletas y taxis este %s de noviembre de 2026, con información sobre '
            'los dígitos afectados, los horarios de restricción y las excepciones que debes tener en '
            'cuenta. El pico y placa en Cartagena es una medida que busca mejorar el flujo vehicular '
            'y reducir la congestión en las principales vías de la ciudad. Cada día, dependiendo del '
            'último dígito de la placa de tu vehículo, podrías tener restricciones para circular. '
            'Dígitos restringidos: %s. Horario: de 7 a.m. a 9 a.m. y de 6 p.m. a 8 p.m. Taxis: %s. '
            'Vehículos al servicio de organismos de control como Procuraduría, Contraloría, '
            'Defensoría del Pueblo y Personería Distrital.' % (dia, dia, digitos, taxis))


CTX_UNIVERSAL = ('Vehículos de uso exclusivo de concejales del Distrito de Cartagena. Vehículos al '
                 'servicio de organismos de control como Procuraduría, Contraloría, Defensoría del '
                 'Pueblo y Personería Distrital. Vehículos fúnebres.')
CTX_HEADTOPICS = ('Los organismos de control y los servicios públicos esenciales están autorizados '
                  'para operar libremente. La Procuraduría, Contraloría, Defensoría del Pueblo y '
                  'Personería Distrital tienen vehículos exentos.')


def test_misma_plantilla_de_otro_dia_no_es_la_misma_nota():
    ayer = _pico_placa('22', '9 y 0', '3 y 4')
    hoy = _pico_placa('23')
    # El comienzo se parece mucho (plantilla) pero las cifras no coinciden.
    assert mc._jac(mc._gramas(ayer), mc._gramas(hoy)) >= mc.UMBRAL_TEXTO
    assert mc._cifras_en_conflicto(mc._n(ayer)[:500], hoy)
    refs = [{'titulo': 'Pico y placa del 22 de noviembre de 2026 en Cartagena: horarios y dígitos',
             'texto': mc._n(ayer)[:500], 'subtema': 'Pico y placa en Cartagena', 'fecha': ''}]
    assert mc.buscar_referencia(
        refs, 'Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos',
        [hoy]) is None


def test_misma_nota_reproducida_sigue_tomando_el_tema():
    # Misma nota, mismas cifras, otro titular: sí se retoma (v1.30 intacto).
    txt = _pico_placa('23')
    refs = [{'titulo': 'Así funciona el pico y placa este lunes', 'texto': mc._n(txt)[:500],
             'subtema': 'Pico y placa en Cartagena', 'fecha': ''}]
    assert not mc._cifras_en_conflicto(refs[0]['texto'], txt)
    assert mc.buscar_referencia(refs, 'Pico y placa en Cartagena: dígitos del lunes', [txt])


def test_caso_real_tema_sin_sustento_no_se_pega():
    """Aunque la hoja diga que es la misma nota, el TEMA del robo no tiene
    nada que ver con el texto: las dos filas conservan su subtema."""
    refs = mc.referencias_de_tabla(CAB, [
        ['1', HOY, 'El Universal', 'Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos',
         _pico_placa('23'), ROBO, 'Neutro']])
    rows = [
        {'Título': 'Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos',
         'Resumen - Aclaracion': _pico_placa('23'), 'Contexto analizado': CTX_UNIVERSAL,
         'Subtema_IA': 'Pico y placa en Cartagena'},
        {'Título': 'Pico y Placa en Cartagena el 23 de noviembre de 2026: Horarios y Dígitos',
         'Resumen - Aclaracion': 'Conozca los dígitos afectados por el pico y placa en Cartagena.',
         'Contexto analizado': CTX_HEADTOPICS, 'Subtema_IA': 'Pico y placa en Cartagena'},
    ]
    rechazos = []
    n = az.anclar_subtemas_hoja(rows, KM, refs, mapa={0: 1, 1: 1}, excluir=MARCA,
                                rechazos=rechazos)
    assert n == 0
    assert [r['Subtema_IA'] for r in rows] == ['Pico y placa en Cartagena'] * 2
    assert rechazos and rechazos[0]['subtema_hoja'] == ROBO


def test_palabras_sueltas_al_fondo_del_texto_no_dan_sustento():
    """El cuerpo real de El Universal trae, al final de la lista de excepciones,
    «personal armado» y «campero y camioneta»: eso no es un robo."""
    largo = (_pico_placa('23') + ' Excepciones al pico y placa. ' + 'Vehículos diplomáticos. ' * 40
             + 'Vehículos escoltas conducidos por personal armado autorizado. Vehículos '
               'particulares tipo automóvil, campero y camioneta, destinados a la enseñanza.')
    tit = 'Pico y placa del 23 de noviembre de 2026 en Cartagena: horarios y dígitos'
    refs = [{'titulo': tit, 'texto': mc._n(largo)[:500], 'subtema': ROBO, 'fecha': ''}]
    rows = [{'Título': tit, 'Resumen - Aclaracion': largo, 'Contexto analizado': CTX_UNIVERSAL,
             'Subtema_IA': 'Pico y placa en Cartagena'}]
    assert az.anclar_subtemas_hoja(rows, KM, refs, mapa={0: 1}, excluir=MARCA) == 0
    assert rows[0]['Subtema_IA'] == 'Pico y placa en Cartagena'


def test_la_nota_del_robo_si_retoma_su_tema():
    tit = 'Hombres armados roban camioneta de la Defensoría del Pueblo en Arauca'
    res = ('Dos hombres armados interceptaron y robaron una camioneta de la Defensoría del Pueblo '
           'en la vía entre Saravena y Tame; los funcionarios resultaron ilesos.')
    refs = mc.referencias_de_tabla(CAB, [['1', HOY, 'El Tiempo', tit, res, ROBO, 'Negativo']])
    rows = [{'Título': tit, 'Resumen - Aclaracion': res, 'Contexto analizado': res,
             'Subtema_IA': 'Robo de vehículo oficial'}]
    assert az.anclar_subtemas_hoja(rows, KM, refs, mapa={0: 1}, excluir=MARCA) == 1
    assert rows[0]['Subtema_IA'] == ROBO


def test_sustento_del_rotulo():
    assert not rotulo_con_sustento(ROBO, CTX_UNIVERSAL + ' ' + _pico_placa('23'), MARCA)
    assert rotulo_con_sustento('Reclutamiento de menores en el Cauca',
                               'La Defensoría alertó por el reclutamiento de menor en el Cauca', MARCA)
    assert rotulo_con_sustento(ROBO, 'Dos hombres armados robaron una camioneta de la Defensoría '
                                     'en Cúcuta', MARCA)
    # Solo la marca: no dice de qué habla la nota.
    assert not rotulo_con_sustento('Defensoría del Pueblo', 'La Defensoría del Pueblo dijo', MARCA)
