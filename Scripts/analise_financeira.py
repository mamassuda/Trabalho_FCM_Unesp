"""Base financeira da prévia FCM: seleção explícita, cruzamento e análise descritiva.

Não coleta dados nem estima valores ausentes. A tabela da planilha original (EY)
é preservada separadamente dos custos de futebol publicados por outras fontes.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANOS = (2023, 2024, 2025)
ARQUIVO_BASE = Path('arquivos_auxiliares/financeiro/gastos_serie_a_2023_2025.csv')
BASES = {
    'futebol': 'Gastos com futebol — compilação 2023–2025',
    'operacional_EY': 'Despesas operacionais — planilha original / EY',
}


def preparar_base(raiz=ROOT):
    """Seleciona fontes existentes e retorna 60 custos + 40 despesas EY.

    Prioridade: tabela histórica Sports Value da edição 2025; complementos
    publicados na edição 2024; DREs/PLURI onde ausentes. América-MG 2023 tem
    apenas despesa operacional nesta coleta e permanece explicitamente marcado
    como escopo diferente (não se rebatiza o número como custo do futebol).
    """
    pesquisa = Path(raiz) / 'pesquisa_financeira'
    sv = pd.read_csv(pesquisa / 'custos_futebol_SportsValue_2023_2025.csv')
    ey = pd.read_csv(pesquisa / 'despesas_operacionais_EY_2023_2025.csv')
    complementos = pd.read_csv(pesquisa / 'serie_bc_fontes.csv')
    divergencias = pd.read_csv(pesquisa / 'divergencias_entre_edicoes_SportsValue.csv')
    linhas = []
    for _, r in sv[(sv['serie'] == 'A') & sv['ano'].isin(ANOS)].iterrows():
        linha = {
            'Base': 'futebol', 'Ano': int(r['ano']), 'Serie': 'A', 'Clube': r['clube'],
            'Gasto_mi': float(r['valor_rs_milhoes']), 'Metrica': 'Custos com futebol',
            'Fonte': 'Sports Value — edição 2025' if '/2026/' in r['fonte_url'] else 'Sports Value — edição 2024',
            'Fonte_URL': r['fonte_url'], 'Pagina': str(r['pagina']),
            'Escopo_diferente': False, 'Divergencia_edicoes': False,
            'Observacao': 'Gasto anual publicado; valores nominais em milhões de reais.',
        }
        div = divergencias[(divergencias['ano'] == r['ano']) & (divergencias['clube'] == r['clube'])]
        if not div.empty:
            anterior = div.iloc[0]['valor_edicao2024']
            linha['Divergencia_edicoes'] = True
            linha['Observacao'] += f' Edições divergem: anterior {anterior}; selecionada {linha["Gasto_mi"]}. Não conciliado.'
        if str(r['status']).startswith('edicao_anterior'):
            linha['Observacao'] += ' Complemento da edição anterior: não consta na tabela de 2025.'
        linhas.append(linha)

    selecoes = [
        (2023, 'Goiás', 'Despesas com Futebol'),
        (2023, 'Coritiba', 'Despesas com Futebol'),
        (2024, 'Criciúma', 'Departamento Futebol Profissional'),
        (2024, 'Juventude', 'Custo da atividade do desporto'),
        (2025, 'Juventude', 'Custo da atividade do desporto'),
    ]
    for ano, clube, metrica in selecoes:
        achado = complementos[(complementos['ano'] == ano) & (complementos['clube'] == clube)
                              & (complementos['rubrica_original'] == metrica)]
        if len(achado) != 1:
            raise ValueError(f'Complemento não unívoco: {clube} {ano} / {metrica}.')
        r = achado.iloc[0]
        linhas.append({
            'Base': 'futebol', 'Ano': ano, 'Serie': 'A', 'Clube': clube,
            'Gasto_mi': float(r['valor_brl']) / 1_000_000, 'Metrica': metrica,
            'Fonte': 'PLURI — edição 2025' if r['fonte_tipo'] == 'compilacao_PLURI' else f'Balanço oficial — {clube}',
            'Fonte_URL': r['url'], 'Pagina': str(r['pagina_fisica']),
            'Escopo_diferente': False, 'Divergencia_edicoes': False,
            'Observacao': r['observacoes'] + ' Escopos não integralmente harmonizados entre fontes.',
        })

    for _, r in ey[(ey['serie'] == 'A') & ey['ano'].isin(ANOS)].iterrows():
        alerta = r['clube'] == 'Cuiabá' and int(r['ano']) == 2023
        linha = {
            'Base': 'operacional_EY', 'Ano': int(r['ano']), 'Serie': 'A', 'Clube': r['clube'],
            'Gasto_mi': float(r['valor_rs_milhoes']), 'Metrica': 'Despesas operacionais totais',
            'Fonte': f'EY — exercício {r["ano"]}', 'Fonte_URL': r['fonte_url'], 'Pagina': str(r['pagina']),
            'Escopo_diferente': alerta, 'Divergencia_edicoes': False,
            'Observacao': ('Alerta de escopo: gráfico informa apenas R$ 2 milhões; não interpretar como eficiência excepcional.'
                           if alerta else 'Despesas operacionais do clube; não somente futebol profissional.'),
        }
        linhas.append(linha)
        if r['clube'] == 'América-MG' and int(r['ano']) == 2023:
            reserva = dict(linha)
            reserva.update(Base='futebol', Escopo_diferente=True,
                           Observacao='Exceção: despesa operacional EY, não custo exclusivo do futebol. Valor preservado sem estimativa; pode ser excluído pelo filtro de ressalvas.')
            linhas.append(reserva)

    resultado = pd.DataFrame(linhas).sort_values(['Base', 'Ano', 'Clube']).reset_index(drop=True)
    if resultado.duplicated(['Base', 'Ano', 'Clube']).any():
        raise ValueError('Registros financeiros duplicados.')
    contagens = resultado[resultado['Base'] == 'futebol'].groupby('Ano').size().to_dict()
    if contagens != {2023: 20, 2024: 20, 2025: 20}:
        raise ValueError(f'Cobertura inesperada: {contagens}.')
    return resultado


def carregar_analise(base='futebol', raiz=ROOT, financas=None):
    """Merge exato e um-para-um entre clube/ano, sem aproximação por nomes."""
    if base not in BASES:
        raise ValueError(f'Base financeira desconhecida: {base}.')
    raiz = Path(raiz)
    if financas is None:
        financas = pd.read_csv(raiz / ARQUIVO_BASE, keep_default_na=False)
    financas = financas.copy()
    if financas.duplicated(['Base', 'Ano', 'Clube']).any():
        raise ValueError('Registros financeiros duplicados.')
    for coluna in ['Escopo_diferente', 'Divergencia_edicoes']:
        financas[coluna] = financas[coluna].astype(str).str.lower().eq('true')
    fin = financas[(financas['Base'] == base) & financas['Ano'].isin(ANOS)].copy()
    anos_esperados = set(ANOS) if base == 'futebol' else {2023, 2025}
    if set(fin['Ano'].unique()) != anos_esperados:
        raise ValueError(f'Base incompleta: temporadas esperadas {sorted(anos_esperados)}; '
                         f'encontradas {sorted(fin["Ano"].unique())}.')
    tabelas = []
    for ano in sorted(fin['Ano'].unique()):
        caminho = raiz / 'arquivos_auxiliares/tabelas_web_scraping' / f'serie_a_{ano}.csv'
        tabela = pd.read_csv(caminho)
        tabela['Ano'] = int(ano)
        tabela['Pos'] = pd.to_numeric(tabela['Pos'].astype(str).str.extract(r'(\d+)$')[0], errors='raise')
        if len(tabela) != 20 or tabela['Clube'].duplicated().any() or set(tabela['Pos']) != set(range(1, 21)):
            raise ValueError(f'Cadastro esportivo de {ano} não contém 20 clubes/posições únicos.')
        tabelas.append(tabela)
    if not tabelas:
        raise ValueError('Base financeira vazia para os anos solicitados.')
    esportivo = pd.concat(tabelas, ignore_index=True)
    df = esportivo.merge(fin, on=['Ano', 'Clube'], how='outer', validate='one_to_one', indicator=True)
    faltantes = df[df['_merge'] != 'both'][['Ano', 'Clube']]
    if not faltantes.empty:
        raise ValueError(f'Clubes sem correspondência financeira/esportiva: {faltantes.to_dict("records")}')
    df = df.drop(columns='_merge')
    for coluna in ['Pts', 'PJ', 'VIT', 'E', 'DER', 'GM', 'GC', 'SG', 'Pos', 'Gasto_mi']:
        df[coluna] = pd.to_numeric(df[coluna], errors='raise')
    if not ((df['Pts'] == 3 * df['VIT'] + df['E']) & (df['PJ'] == df['VIT'] + df['E'] + df['DER'])
            & (df['SG'] == df['GM'] - df['GC'])).all():
        raise ValueError('Inconsistências nas estatísticas esportivas; revisar o CSV original.')
    return calcular_indicadores(df.sort_values(['Ano', 'Pos']).reset_index(drop=True))


def classificar_quadrante(gasto, pontos, media_gasto, media_pontos):
    """Classificação relativa às médias, não inferência causal de eficiência."""
    if gasto == media_gasto or pontos == media_pontos:
        return 'Na linha da média'
    faixa_gasto = 'Menor gasto' if gasto < media_gasto else 'Maior gasto'
    faixa_pontos = 'mais pontos' if pontos > media_pontos else 'menos pontos'
    return f'{faixa_gasto} / {faixa_pontos}'


def calcular_indicadores(df):
    """Fórmulas transparentes e médias por temporada, sem alterar a entrada."""
    if df.empty:
        raise ValueError('Amostra vazia: selecione ao menos um clube.')
    resultado = df.copy(deep=True)
    for coluna in ['Ano', 'Gasto_mi', 'Pts', 'PJ']:
        resultado[coluna] = pd.to_numeric(resultado[coluna], errors='raise')
        if resultado[coluna].isna().any() or resultado[coluna].isin([float('inf'), float('-inf')]).any():
            raise ValueError(f'Valor ausente ou não finito: {coluna}.')
    if (resultado['Gasto_mi'] <= 0).any() or (resultado['PJ'] <= 0).any() or (resultado['Pts'] < 0).any():
        raise ValueError('Gasto e jogos devem ser positivos; pontos não podem ser negativos.')
    resultado['Pontos_10mi'] = resultado['Pts'] * 10 / resultado['Gasto_mi']
    resultado['Custo_ponto_mi'] = resultado['Gasto_mi'] / resultado['Pts'].where(resultado['Pts'] != 0)
    resultado['Aproveitamento_pct'] = resultado['Pts'] / (3 * resultado['PJ']) * 100
    resultado['Media_Gasto'] = resultado.groupby('Ano')['Gasto_mi'].transform('mean')
    resultado['Media_Pontos'] = resultado.groupby('Ano')['Pts'].transform('mean')
    resultado['Quadrante'] = resultado.apply(
        lambda r: classificar_quadrante(r['Gasto_mi'], r['Pts'], r['Media_Gasto'], r['Media_Pontos']), axis=1)
    return resultado


if __name__ == '__main__':
    destino = ROOT / ARQUIVO_BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    dados = preparar_base()
    dados.to_csv(destino, index=False, encoding='utf-8-sig')
    print(dados.groupby(['Base', 'Ano']).size().to_string())
    print(f'Base salva em {destino}')
