import sys
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))


class EstadoWidgetsTests(unittest.TestCase):
    def test_rerun_destaques_nao_emite_aviso_de_default_e_sessionstate(self):
        with self.assertNoLogs('streamlit.elements.lib.policies', level='WARNING'):
            at = AppTest.from_file(ROOT / 'Scripts/dashboard.py', default_timeout=90).run()
            at.selectbox(key='fin_ano').select(2023).run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(set(at.multiselect(key='fin_destaques').value).issubset({'Flamengo'}))


if __name__ == '__main__':
    unittest.main()
