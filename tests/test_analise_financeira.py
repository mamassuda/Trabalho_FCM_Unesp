"""Testes da adaptação da aula: dados reais, fórmulas e fronteiras da amostra."""
import importlib
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))


class AnaliseFinanceiraTests(unittest.TestCase):
    def modulo(self):
        try:
            return importlib.import_module('analise_financeira')
        except ModuleNotFoundError as exc:
            self.fail(f'A implementação da análise ainda não existe: {exc}')

    def test_preparacao_cobre_60_clubes_temporadas_sem_inventar_2024_EY(self):
        df = self.modulo().preparar_base(ROOT)
        futebol = df[df['Base'] == 'futebol']
        ey = df[df['Base'] == 'operacional_EY']
        self.assertEqual(len(futebol), 60)
        self.assertEqual(futebol.groupby('Ano').size().to_dict(), {2023: 20, 2024: 20, 2025: 20})
        self.assertEqual(ey.groupby('Ano').size().to_dict(), {2023: 20, 2025: 20})
        self.assertFalse(df.duplicated(['Base', 'Ano', 'Clube']).any())
        self.assertTrue((df['Gasto_mi'] > 0).all())
        self.assertTrue(df['Fonte_URL'].str.startswith('https://').all())

    def test_planilha_enviada_2025_preservada(self):
        df = self.modulo().preparar_base(ROOT)
        ey = df[(df['Base'] == 'operacional_EY') & (df['Ano'] == 2025)].set_index('Clube')
        self.assertEqual(ey.loc['Flamengo', 'Gasto_mi'], 1151)
        self.assertEqual(ey.loc['Mirassol', 'Gasto_mi'], 98)
        self.assertEqual(ey.loc['Juventude', 'Gasto_mi'], 104)

    def test_custos_futebol_complementos_e_ressalvas_explicitos(self):
        df = self.modulo().preparar_base(ROOT)
        futebol = df[df['Base'] == 'futebol'].set_index(['Ano', 'Clube'])
        self.assertAlmostEqual(futebol.loc[(2024, 'Criciúma'), 'Gasto_mi'], 77.261712)
        self.assertAlmostEqual(futebol.loc[(2025, 'Juventude'), 'Gasto_mi'], 95.89817384)
        self.assertTrue(futebol.loc[(2023, 'América-MG'), 'Escopo_diferente'])
        self.assertTrue(futebol.loc[(2024, 'Fortaleza'), 'Divergencia_edicoes'])
        self.assertEqual(futebol.loc[(2024, 'Fortaleza'), 'Gasto_mi'], 117.7)
        self.assertIn('275.3', futebol.loc[(2024, 'Fortaleza'), 'Observacao'])
        self.assertFalse(futebol.loc[(2025, 'Flamengo'), 'Escopo_diferente'])
        self.assertFalse(futebol.loc[(2025, 'Flamengo'), 'Divergencia_edicoes'])

    def test_carregar_faz_merge_exato_dos_60_registros(self):
        m = self.modulo()
        df = m.carregar_analise('futebol', ROOT, m.preparar_base(ROOT))
        self.assertEqual(len(df), 60)
        self.assertEqual(set(df['Ano']), {2023, 2024, 2025})
        self.assertTrue((df['PJ'] == 38).all())
        self.assertFalse(df[['Pts', 'Pos', 'Gasto_mi']].isna().any().any())
        self.assertEqual(df.groupby('Ano')['Pos'].nunique().to_dict(), {2023: 20, 2024: 20, 2025: 20})
        self.assertTrue((df['Pts'] == 3 * df['VIT'] + df['E']).all())
        self.assertTrue((df['GM'] - df['GC'] == df['SG']).all())

    def test_rejeita_temporada_inteiramente_ausente(self):
        m = self.modulo()
        df = m.preparar_base(ROOT)
        for base, ano in [('futebol', 2024), ('operacional_EY', 2023)]:
            sem_ano = df[~((df['Base'] == base) & (df['Ano'] == ano))]
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, 'temporadas'):
                m.carregar_analise(base, ROOT, sem_ano)

    def test_merge_rejeita_dados_duplicados_ou_clube_sem_correspondencia(self):
        m = self.modulo()
        df = m.preparar_base(ROOT)
        with self.assertRaisesRegex(ValueError, 'duplicad'):
            m.carregar_analise('futebol', ROOT, pd.concat([df, df.iloc[[0]]], ignore_index=True))
        alterado = df.copy()
        alterado.loc[alterado.index[0], 'Clube'] = 'Clube que não existe'
        with self.assertRaisesRegex(ValueError, 'correspond|clubes'):
            m.carregar_analise('futebol', ROOT, alterado)

    def test_formulas_medias_por_temporada_e_nao_mutacao(self):
        m = self.modulo()
        origem = pd.DataFrame({'Ano': [2023, 2023, 2024, 2024], 'Clube': ['A', 'B', 'A', 'B'],
                               'Gasto_mi': [100., 200., 300., 500.], 'Pts': [60, 30, 90, 50], 'PJ': [38]*4})
        copia = origem.copy(deep=True)
        df = m.calcular_indicadores(origem)
        self.assertEqual(df['Pontos_10mi'].tolist(), [6., 1.5, 3., 1.])
        self.assertAlmostEqual(df.loc[0, 'Custo_ponto_mi'], 100 / 60)
        self.assertAlmostEqual(df.loc[0, 'Aproveitamento_pct'], 100 * 60 / 114)
        self.assertEqual(df['Media_Gasto'].tolist(), [150., 150., 400., 400.])
        self.assertEqual(df['Media_Pontos'].tolist(), [45., 45., 70., 70.])
        self.assertEqual(df.loc[0, 'Quadrante'], 'Menor gasto / mais pontos')
        self.assertEqual(df.loc[1, 'Quadrante'], 'Maior gasto / menos pontos')
        pd.testing.assert_frame_equal(origem, copia)

    def test_quadrantes_quatro_regioes_e_igualdade(self):
        m = self.modulo()
        casos = [(50, 70, 'Menor gasto / mais pontos'), (150, 70, 'Maior gasto / mais pontos'),
                 (50, 30, 'Menor gasto / menos pontos'), (150, 30, 'Maior gasto / menos pontos'),
                 (100, 70, 'Na linha da média'), (50, 50, 'Na linha da média')]
        for gasto, pts, esperado in casos:
            with self.subTest(gasto=gasto, pts=pts):
                self.assertEqual(m.classificar_quadrante(gasto, pts, 100, 50), esperado)

    def test_zero_ausente_negativo_e_amostra_vazia(self):
        m = self.modulo()
        d = pd.DataFrame({'Ano':[2025], 'Clube':['A'], 'Gasto_mi':[100.], 'Pts':[0], 'PJ':[38]})
        z = m.calcular_indicadores(d)
        self.assertEqual(z.loc[0, 'Pontos_10mi'], 0)
        self.assertTrue(pd.isna(z.loc[0, 'Custo_ponto_mi']))
        for col, val in [('Gasto_mi', 0), ('Gasto_mi', -1), ('Gasto_mi', float('nan')), ('PJ', 0), ('Pts', -1)]:
            bad = d.copy(); bad.loc[0,col] = val
            with self.subTest(col=col, val=val), self.assertRaises(ValueError):
                m.calcular_indicadores(bad)
        with self.assertRaisesRegex(ValueError, 'vazia'):
            m.calcular_indicadores(d.iloc[:0])


if __name__ == '__main__':
    unittest.main()
