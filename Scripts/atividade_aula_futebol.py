"""FCM Unesp — adaptação do exercício Pokémon para gastos e pontos no futebol.

Execute na raiz do projeto, com o ambiente virtual ativado:
    python Scripts/atividade_aula_futebol.py --ano 2025
    python Scripts/atividade_aula_futebol.py --ano 2023 --base operacional_EY

O roteiro usa os mesmos pandas/Matplotlib da aula. As funções de gráficos apenas
organizam títulos, rótulos e quadrantes; não há regressão ou modelo preditivo.
Custos do futebol e despesas operacionais são bases separadas. Leia as fontes
no CSV exportado, especialmente para rubricas e versões com ressalvas.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from analise_financeira import BASES, ROOT, carregar_analise
from graficos_financeiros import grafico_barras, grafico_quadrantes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ano', type=int, choices=[2023, 2024, 2025], default=2025)
    parser.add_argument('--base', choices=list(BASES), default='futebol')
    parser.add_argument('--saida', type=Path, default=ROOT / 'previa_exportacoes')
    args = parser.parse_args()
    df = carregar_analise(args.base)
    df_ano = df[df['Ano'] == args.ano].copy()
    if df_ano.empty:
        parser.error('Não há dados desse ano na base escolhida. EY possui 2023 e 2025, não 2024.')
    args.saida.mkdir(parents=True, exist_ok=True)

    # Aula: groupby('type')['attack'].mean().sort_values(ascending=False)
    # Projeto: um registro por clube no ano; a média do grupo coincide com o valor.
    medias_gastos = df_ano.groupby('Clube')['Gasto_mi'].mean().sort_values(ascending=False)
    medias_pontos = df_ano.groupby('Clube')['Pts'].mean().sort_values(ascending=False)
    print(f'Série A {args.ano}: {len(df_ano)} clubes — {BASES[args.base]}')
    print('\nGasto médio da temporada (R$ mi):', medias_gastos.mean())
    print('Pontuação média:', medias_pontos.mean())
    print('\nEstatísticas descritivas:')
    print(df_ano[['Gasto_mi', 'Pts', 'Pontos_10mi']].describe().to_string())

    # As funções abaixo fazem plot(kind='bar'), bar_label, scatter,
    # fill_between e as linhas tracejadas de médias, como Atividade_Aula.py.
    figuras = {
        '01_gastos': grafico_barras(df_ano, 'Gasto_mi', f'Gasto publicado por clube — {args.ano}', 'R$ milhões'),
        '02_pontos': grafico_barras(df_ano, 'Pts', f'Pontos na Série A — {args.ano}', 'Pontos', cor='#FD5029'),
        '03_quadrantes': grafico_quadrantes(df_ano),
        '04_pontos_por_gasto': grafico_barras(df_ano, 'Pontos_10mi', f'Pontos / R$ 10 milhões — {args.ano}',
                                              'Pontos / R$ 10 milhões', cor='#16866B'),
    }
    for nome, figura in figuras.items():
        try:
            figura.savefig(args.saida / f'{nome}_{args.ano}_{args.base}.png', dpi=160, bbox_inches='tight')
        finally:
            plt.close(figura)
    df_ano.to_csv(args.saida / f'analise_{args.ano}_{args.base}.csv', index=False,
                  sep=';', decimal=',', encoding='utf-8-sig')
    print('\nArquivos exportados para:', args.saida.resolve())
    print('Leitura descritiva, não causal; gastos anuais nominais, fontes e ressalvas no CSV.')


if __name__ == '__main__':
    main()
