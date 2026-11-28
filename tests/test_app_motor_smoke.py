# -*- coding: utf-8 -*-
"""Smoke de la app (Streamlit AppTest), v1.55: solo limpieza y duplicados,
sin selector de motor, sin opciones de IA y sin pedir claves de API."""
import os
import unittest

from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')


def _app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets['APP_PASSWORD'] = 'prueba'
    at.secrets['REGIONES_CSV_URL'] = 'http://localhost/regiones.csv'
    at.secrets['INTERNET_CSV_URL'] = 'http://localhost/internet.csv'
    at.session_state['password_correct'] = True
    return at.run()


class TestAppSoloLimpieza(unittest.TestCase):
    def test_carga_sin_motor_ni_ia(self):
        at = _app()
        self.assertFalse(at.exception)
        self.assertFalse([r for r in at.radio if r.label == 'Motor de clasificación'])
        self.assertFalse([r for r in at.radio if r.label == 'Criterio del tono'])
        self.assertFalse(any('IA' in c.label and 'Activar' in c.label for c in at.checkbox))
        self.assertFalse(any(t.key in ('modelo_fijo', 'modelo_custom') for t in at.text_input))
        self.assertFalse(any('API_KEY' in e.value for e in at.error))

    def test_conserva_marca_y_filtro_de_analizadas(self):
        at = _app()
        self.assertTrue(any(t.key == 'brand_input' for t in at.text_input))
        self.assertTrue(any('Excluir notas ya analizadas' in c.label for c in at.checkbox))


if __name__ == '__main__':
    unittest.main()
