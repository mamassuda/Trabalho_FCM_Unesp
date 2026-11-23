"""Testes de contrato dos gráficos; backend não interativo só nos testes."""
import importlib
import sys
import unittest
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Scripts'))


class GraficosTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'Clube': ['Clube A', 'Clube B', 'Clube A', 'Clube B'],
            'Ano': [2023, 2023, 2024, 2024], 'Gasto_mi': [10., 30., 20., 40.],
            'Pts': [40, 60, 50, 70], 'Pontos_10mi': [40., 20., 25., 17.5],
            'Pos': [15, 5, 10, 1]})
        self.original = self.df.copy(deep=True)

    def tearDown(self):
        pd.testing.assert_frame_equal(self.df, self.original)
        plt.close('all')

    def api(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('graficos_financeiros'),
                             'Módulo de gráficos ainda não implementado')
        return importlib.import_module('graficos_financeiros')

    def test_barras_ordenadas_labels_destaques_e_figuras_independentes(self):
        api = self.api()
        before = dict(matplotlib.rcParams)
        fig = api.grafico_barras(self.df, 'Pts', 'Pontos', 'Média', destaques=['Clube A'])
        self.assertIsInstance(fig, Figure)
        ax = fig.axes[0]
        self.assertEqual([p.get_height() for p in ax.patches], [65., 45.])
        self.assertEqual([t.get_text() for t in ax.get_xticklabels()], ['Clube B', 'Clube A'])
        self.assertEqual([t.get_text() for t in ax.texts], ['65.0', '45.0'])
        self.assertNotEqual(ax.patches[0].get_facecolor(), ax.patches[1].get_facecolor())
        self.assertFalse(ax.spines['top'].get_visible())
        self.assertFalse(ax.spines['right'].get_visible())
        self.assertIsNot(fig, api.grafico_barras(self.df, 'Pts', 'Pontos', 'Média'))
        self.assertEqual(before, dict(matplotlib.rcParams))
        with self.assertRaisesRegex(ValueError, 'vazio'):
            api.grafico_barras(self.df.iloc[:0], 'Pts', '', '')

    def test_quadrantes_amostra_medias_sombreamentos_limites_e_nomes(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'grafico_quadrantes'), 'Scatter ainda não implementado')
        df = pd.concat([self.df] * 5, ignore_index=True)
        fig = api.grafico_quadrantes(df, destaques=['Clube A'])
        ax = fig.axes[0]
        self.assertEqual(len(ax.collections[0].get_offsets()), 20)
        self.assertEqual(len(ax.collections), 5)
        self.assertEqual(list(ax.lines[0].get_xdata()), [25., 25.])
        self.assertEqual(list(ax.lines[1].get_ydata()), [55., 55.])
        self.assertEqual(ax.lines[0].get_color(), 'red')
        self.assertEqual(ax.lines[1].get_color(), 'blue')
        for label in ['Menor gasto / mais pontos', 'Maior gasto / mais pontos',
                      'Menor gasto / menos pontos', 'Maior gasto / menos pontos']:
            self.assertIn(label, [t.get_text() for t in ax.texts])
        self.assertIsNot(fig, api.grafico_quadrantes(df, mostrar_nomes=False))
        constant = self.df.assign(Gasto_mi=0., Pts=0)
        ax2 = api.grafico_quadrantes(constant, mostrar_nomes=False).axes[0]
        self.assertGreater(ax2.get_xlim()[1] - ax2.get_xlim()[0], 0)
        self.assertGreater(ax2.get_ylim()[1] - ax2.get_ylim()[0], 0)
        with self.assertRaisesRegex(ValueError, 'vazio'):
            api.grafico_quadrantes(self.df.iloc[:0])
        fig.canvas.draw()

    def test_comparativo_pivot_nan_selecao_nominal_figuras_e_vazios(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'grafico_comparativo'), 'Comparativo ainda não implementado')
        df = self.df.drop(index=3)
        fig = api.grafico_comparativo(df, ['Clube A', 'Clube B', 'Ausente'])
        ax = fig.axes[0]
        self.assertEqual([t.get_text() for t in ax.get_legend().get_texts()], ['Clube A', 'Clube B'])
        self.assertEqual([t.get_text() for t in ax.get_xticklabels()], ['2023', '2024'])
        self.assertEqual([p.get_height() for p in ax.containers[0]], [40., 50.])
        self.assertTrue(pd.isna(ax.containers[1][1].get_height()))
        gastos = api.grafico_comparativo(df, ['Clube A'], 'Gasto_mi')
        self.assertIn('nominais', gastos.axes[0].get_ylabel())
        self.assertIn('inflação', gastos.axes[0].get_ylabel())
        self.assertIsNot(fig, api.grafico_comparativo(df, ['Clube A']))
        for dados, clubes in [(df.iloc[:0], ['Clube A']), (df, ['Ausente']), (df, [])]:
            with self.assertRaisesRegex(ValueError, 'vazio|ausente|selecionado'):
                api.grafico_comparativo(dados, clubes)
        fig.canvas.draw()


if __name__ == '__main__':
    unittest.main()
