"""Regressões de integração: preservar o scouting atualizado junto da análise."""
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))


class IntegracaoMatheusTests(unittest.TestCase):
    def test_filtros_scouting_do_Matheus_e_analise_financeira_coexistem(self):
        at = AppTest.from_file(ROOT / 'Scripts/dashboard.py', default_timeout=90).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertIn('Gastos × desempenho (Série A)', [t.label for t in at.tabs])
        self.assertIn('Relatórios de Scouting (Leitor de PDFs)', [t.label for t in at.tabs])
        clube = next(w for w in at.multiselect if w.label == 'Filtrar por Clube:')
        posicao = next(w for w in at.multiselect if w.label == 'Filtrar por Posição:')
        from tratamento_dados import carregar_e_tratar_jogadores
        original = carregar_e_tratar_jogadores()
        self.assertEqual(len(original), 10)
        alvo = original.iloc[0]
        clube.set_value([alvo['Clube']])
        posicao.set_value([alvo['Posicao']])
        at.run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        ficha = next(t.value for t in at.dataframe if 'Nome' in t.value.columns and 'Nota_Geral_Tecnica' in t.value.columns)
        self.assertTrue((ficha['Clube'] == alvo['Clube']).all())
        self.assertTrue((ficha['Posicao'] == alvo['Posicao']).all())
        self.assertGreater(len(ficha), 0)
        self.assertEqual({m.label:m.value for m in at.metric}['Clubes na análise'], '20 / 20')
        next(w for w in at.multiselect if w.label == 'Filtrar por Clube:').set_value([]).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        self.assertTrue(any('Nenhum jogador encontrado' in str(w.value) for w in at.warning))
        self.assertEqual({m.label:m.value for m in at.metric}['Clubes na análise'], '20 / 20')


if __name__ == '__main__':
    unittest.main()
