"""Aceitação da prévia local, sem navegar/coletar dados nem gravar no GitHub."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))
from streamlit.testing.v1 import AppTest


class PreviaStreamlitTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(ROOT / 'Scripts/dashboard.py', default_timeout=90).run()

    def test_site_nao_exibe_referencias_a_aula_ou_bloco_de_codigo(self):
        at = self.app()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertFalse(any('Da aula para este projeto' in e.label for e in at.expander))
        self.assertEqual(len(at.code), 0)
        textos = [str(e.value).lower() for e in list(at.caption) + list(at.markdown)]
        self.assertFalse(any('aula' in texto or 'professor' in texto for texto in textos))
        self.assertFalse(any(b.key == 'fin_codigo' for b in at.get('download_button')))

    def test_nova_aba_e_abas_originais_sem_excecao(self):
        at = self.app()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertIn('Gastos × desempenho (Série A)', [t.label for t in at.tabs])
        self.assertIn('Classificação (Web Scraping)', [t.label for t in at.tabs])
        self.assertIn('Relatórios de Scouting (Leitor de PDFs)', [t.label for t in at.tabs])
        self.assertIn('Análise Cruzada (Clube x Jogador)', [t.label for t in at.tabs])

    def test_tres_temporadas_filtro_ressalvas_e_downloads(self):
        at = self.app()
        self.assertIn('fin_ano', [s.key for s in at.selectbox])
        for ano in [2023, 2024, 2025]:
            at.selectbox(key='fin_ano').select(ano).run()
            self.assertEqual(len(at.exception), 0, str(at.exception))
            metricas = {m.label: m.value for m in at.metric}
            self.assertEqual(metricas['Clubes na análise'], '20 / 20')
            self.assertGreaterEqual(len(at.get('download_button')), 6)
            self.assertEqual(len(at.code), 0)
        at.selectbox(key='fin_ano').select(2024).run()
        at.checkbox(key='fin_excluir_ressalvas').check().run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        metricas = {m.label: m.value for m in at.metric}
        self.assertNotEqual(metricas['Clubes na análise'], '20 / 20')

    def test_comparacao_clube_inteiramente_removido_pelo_filtro(self):
        at = self.app()
        at.multiselect(key='fin_comparar').set_value(['América-MG']).run()
        at.checkbox(key='fin_excluir_ressalvas').check().run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertTrue(any('não possuem registros' in str(i.value) for i in at.info))

    def test_EY_preserva_planilha_e_nao_inventa_2024(self):
        at = self.app()
        self.assertIn('fin_base', [s.key for s in at.selectbox])
        at.selectbox(key='fin_base').select('operacional_EY').run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertEqual(at.selectbox(key='fin_ano').options, ['2023', '2025'])
        at.selectbox(key='fin_ano').select(2025).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        tabelas = [t.value for t in at.dataframe]
        fonte = next(t for t in tabelas if 'Gasto publicado (R$ mi)' in t.columns)
        self.assertEqual(fonte.set_index('Clube').loc['Flamengo', 'Gasto publicado (R$ mi)'], 1151)
        self.assertEqual(fonte.set_index('Clube').loc['Mirassol', 'Gasto publicado (R$ mi)'], 98)
        at.multiselect(key='fin_comparar').set_value([]).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))


if __name__ == '__main__':
    unittest.main()
