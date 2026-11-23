"""Painel descritivo em pandas/Matplotlib com dados financeiros rastreáveis."""
from io import BytesIO

import matplotlib.pyplot as plt
import streamlit as st

from analise_financeira import BASES, calcular_indicadores, carregar_analise
from graficos_financeiros import grafico_barras, grafico_comparativo, grafico_quadrantes


def exibir_figura(figura, nome, chave):
    """Renderiza e oferece o PNG; sempre fecha a figura para liberar memória."""
    try:
        buffer = BytesIO()
        figura.savefig(buffer, format='png', dpi=160, bbox_inches='tight', facecolor='white')
        st.pyplot(figura, width='stretch')
        st.download_button('Baixar gráfico (PNG)', buffer.getvalue(), file_name=nome,
                           mime='image/png', key=chave, on_click='ignore')
    finally:
        plt.close(figura)


def renderizar_analise_financeira():
    """Página descritiva independente; não executa coleta nem altera os CSVs."""
    st.subheader('Quanto se gasta — e quanto se pontua?')
    st.caption('Série A • 2023, 2024 e 2025 • análise descritiva de gastos e desempenho')
    controles = st.columns([2.5, 1, 2])
    with controles[0]:
        base = st.selectbox('Base financeira', list(BASES), format_func=BASES.get, key='fin_base',
                            help='A planilha enviada é a base de despesas operacionais EY. Custos de futebol ficam em uma base separada.')
    try:
        df = carregar_analise(base)
    except (ValueError, OSError) as erro:
        st.error(f'Não foi possível preparar a análise: {erro}')
        return
    anos = sorted(int(a) for a in df['Ano'].unique())
    if st.session_state.get('fin_ano') not in anos:
        st.session_state['fin_ano'] = anos[-1]
    with controles[1]:
        ano = st.selectbox('Temporada da análise', anos, key='fin_ano')
    with controles[2]:
        excluir = st.checkbox('Ocultar registros com ressalva', value=False, key='fin_excluir_ressalvas',
                              help='Exclui rubricas de escopo diferente e números com divergências entre edições; as médias são recalculadas.')
    amostra = df[df['Ano'] == ano].copy()
    alertas = amostra[amostra['Escopo_diferente'] | amostra['Divergencia_edicoes']]
    if excluir:
        amostra = amostra[~(amostra['Escopo_diferente'] | amostra['Divergencia_edicoes'])].copy()
    if amostra.empty:
        st.warning('Nenhum clube disponível com esses filtros.')
        return
    amostra = calcular_indicadores(amostra)
    destaque_opcoes = sorted(amostra['Clube'].unique())
    existentes = st.session_state.get('fin_destaques')
    if existentes is None:
        st.session_state['fin_destaques'] = [c for c in ['Flamengo', 'Mirassol'] if c in destaque_opcoes]
    else:
        validos = [c for c in existentes if c in destaque_opcoes]
        if validos != existentes:
            st.session_state['fin_destaques'] = validos
    destaques = st.multiselect('Destacar clubes nos gráficos (sem retirar os demais da análise)',
                              destaque_opcoes, key='fin_destaques')
    if base == 'operacional_EY':
        st.info('Esta é a base da planilha enviada: despesas operacionais do clube, não só do futebol. '
                'Há dados de 2023 e 2025; 2024 não foi inventado. Para ver as três temporadas, selecione a compilação de gastos com futebol.')
    else:
        st.info('Base com os 20 participantes de cada temporada: custos anuais de futebol publicados por Sports Value, '
                'PLURI e balanços oficiais. As fontes não são integralmente harmonizadas. '
                'América-MG/2023 é uma exceção de escopo, identificada na tabela e removível pelo filtro.')
    if not alertas.empty:
        st.caption(f'{len(alertas)} registro(s) com ressalva na temporada; '
                   + ('removidos da amostra atual.' if excluir else 'mantidos e sinalizados. Consulte “Dados e método”.'))
    cards = st.columns(4)
    cards[0].metric('Clubes na análise', f'{len(amostra)} / 20')
    cards[1].metric('Gasto médio publicado', f'R$ {amostra["Gasto_mi"].mean():,.1f} mi'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    cards[2].metric('Pontuação média', f'{amostra["Pts"].mean():.1f}'.replace('.', ','))
    campeao = amostra.sort_values('Pos').iloc[0]
    cards[3].metric('Melhor colocado da amostra', campeao['Clube'], f'{int(campeao["Pts"])} pontos', delta_color='off')
    abas = st.tabs(['Visão geral', 'Gasto × pontos', 'Eficiência descritiva', 'Comparar temporadas', 'Dados e método'])

    with abas[0]:
        st.markdown('#### 1. Quanto cada clube gastou?')
        st.caption('Clubes ordenados pelo gasto anual publicado, do maior para o menor.')
        exibir_figura(grafico_barras(amostra, 'Gasto_mi', f'Gasto anual publicado por clube — {ano}',
                                    'Gasto publicado (R$ milhões)', destaques=destaques),
                      f'gastos_serie_a_{ano}_{base}.png', 'fin_png_gastos')
        st.markdown('#### 2. Como foi o desempenho esportivo?')
        exibir_figura(grafico_barras(amostra, 'Pts', f'Pontos no Brasileirão Série A — {ano}',
                                    'Pontos', cor='#FD5029', destaques=destaques),
                      f'pontos_serie_a_{ano}.png', 'fin_png_pontos')
        st.caption('São gastos anuais publicados, não o custo exclusivo de disputar o Brasileirão. Valores em reais nominais.')

    with abas[1]:
        st.markdown('#### 3. Relação entre gasto e pontuação')
        st.write('Cada ponto é um clube. As linhas tracejadas indicam as médias da amostra da temporada; '
                 'os fundos dividem o gráfico em quatro regiões de gasto e pontuação.')
        mostrar_nomes = st.checkbox('Mostrar nomes de todos os clubes', True, key='fin_rotulos')
        exibir_figura(grafico_quadrantes(amostra, mostrar_nomes=mostrar_nomes, destaques=destaques),
                      f'quadrantes_serie_a_{ano}_{base}.png', 'fin_png_quadrantes')
        grupos = amostra.groupby('Quadrante')['Clube'].apply(lambda s: ', '.join(sorted(s))).reset_index(name='Clubes')
        st.dataframe(grupos, hide_index=True, width='stretch')
        favoravel = amostra[amostra['Quadrante'] == 'Menor gasto / mais pontos'].sort_values('Pts', ascending=False)
        if not favoravel.empty:
            st.success('Leitura descritiva: ' + ', '.join(favoravel['Clube'])
                       + ' ficaram abaixo da média de gasto e acima da média de pontos nesta amostra.')
        st.caption('Quadrantes descrevem posição relativa às médias. Não provam que gastar causou o resultado nem isolam qualidade da gestão.')

    with abas[2]:
        st.markdown('#### 4. Pontos a cada R$ 10 milhões publicados')
        st.latex(r'\mathrm{Pontos\ por\ R\$\ 10\ mi} = \frac{\mathrm{Pontos}\times 10}{\mathrm{Gasto\ em\ R\$\ milh\tilde{o}es}}')
        st.write('Quanto maior a razão, mais pontos foram obtidos por unidade de gasto publicado. '
                 'É um indicador simples para a apresentação, não uma medida completa de eficiência econômica.')
        exibir_figura(grafico_barras(amostra, 'Pontos_10mi', f'Pontos por R$ 10 milhões publicados — {ano}',
                                    'Pontos / R$ 10 milhões', cor='#16866B', destaques=destaques),
                      f'pontos_por_gasto_{ano}_{base}.png', 'fin_png_eficiencia')
        ranking = amostra.sort_values(['Pontos_10mi', 'Pts'], ascending=False).reset_index(drop=True)
        ranking.index += 1
        st.dataframe(ranking[['Clube', 'Pts', 'Gasto_mi', 'Pontos_10mi', 'Custo_ponto_mi', 'Aproveitamento_pct']].rename(columns={
            'Gasto_mi': 'Gasto (R$ mi)', 'Pontos_10mi': 'Pontos / R$ 10 mi',
            'Custo_ponto_mi': 'R$ mi / ponto', 'Aproveitamento_pct': 'Aproveitamento (%)'}),
            width='stretch', hide_index=False)
        st.caption('Gastos menores tendem a elevar essa razão; a interpretação exige olhar também a pontuação e a posição na tabela. '
                   'Gasto anual inclui outras competições. Dados com ressalva permanecem identificados na aba de fontes.')

    with abas[3]:
        st.markdown('#### 5. Comparação descritiva entre temporadas')
        opcoes_comparar = sorted(df['Clube'].unique())
        selecionados = st.multiselect('Clubes para comparar', opcoes_comparar,
                                      default=[c for c in ['Flamengo', 'Palmeiras', 'Fortaleza'] if c in opcoes_comparar],
                                      max_selections=6, key='fin_comparar')
        indicador = st.selectbox('Indicador da comparação', ['Pts', 'Gasto_mi'],
                                format_func=lambda c: {'Pts': 'Pontos no Brasileirão', 'Gasto_mi': 'Gasto publicado (R$ mi nominais)'}[c],
                                key='fin_comparacao_indicador')
        historico = df.copy()
        if excluir:
            historico = historico[~(historico['Escopo_diferente'] | historico['Divergencia_edicoes'])]
        presentes = [c for c in selecionados if c in set(historico['Clube'])]
        ausentes = [c for c in selecionados if c not in presentes]
        if ausentes:
            st.info('Os clubes ' + ', '.join(ausentes) + ' não possuem registros após o filtro de ressalvas.')
        if presentes:
            exibir_figura(grafico_comparativo(historico, presentes, coluna=indicador),
                          f'comparacao_temporadas_{indicador}_{base}.png', 'fin_png_comparacao')
            st.dataframe(historico[historico['Clube'].isin(presentes)][['Ano', 'Clube', 'Pos', 'Pts', 'Gasto_mi', 'Metrica', 'Fonte']],
                         hide_index=True, width='stretch')
        elif not selecionados:
            st.info('Selecione de um a seis clubes para montar a comparação.')
        st.caption('Sem barra = clube fora da Série A naquele ano, registro excluído pelo filtro ou dado indisponível. '
                   'Não significa gasto/pontos zero. Os valores monetários não foram corrigidos pela inflação; '
                   'diferenças de fontes e de escopo limitam a comparação temporal.')

    with abas[4]:
        st.markdown('#### Tabela usada na análise')
        st.caption('Fontes, rubricas, páginas e ressalvas acompanham os dados. A base original não foi sobrescrita.')
        nomes = {'Ano': 'Temporada', 'Pos': 'Posição', 'Pts': 'Pontos', 'Gasto_mi': 'Gasto publicado (R$ mi)',
                 'Pontos_10mi': 'Pontos / R$ 10 mi', 'Fonte_URL': 'Documento da fonte', 'Metrica': 'Rubrica publicada',
                 'Escopo_diferente': 'Alerta de escopo', 'Divergencia_edicoes': 'Edições divergentes', 'Observacao': 'Ressalva'}
        colunas = ['Ano', 'Clube', 'Pos', 'Pts', 'PJ', 'Gasto_mi', 'Pontos_10mi', 'Quadrante', 'Metrica',
                   'Fonte', 'Fonte_URL', 'Pagina', 'Escopo_diferente', 'Divergencia_edicoes', 'Observacao']
        st.dataframe(amostra[colunas].rename(columns=nomes), hide_index=True, width='stretch',
                     column_config={'Documento da fonte': st.column_config.LinkColumn('Documento da fonte', display_text='Abrir fonte')})
        botoes = st.columns(2)
        with botoes[0]:
            st.download_button('Baixar dados desta temporada (CSV)', amostra.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig'),
                               file_name=f'analise_serie_a_{ano}_{base}.csv', mime='text/csv', key='fin_csv_ano', on_click='ignore')
        with botoes[1]:
            st.download_button('Baixar base completa selecionada (CSV)', df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig'),
                               file_name=f'analise_serie_a_{base}.csv', mime='text/csv', key='fin_csv_todos', on_click='ignore')
        st.markdown('#### Estatísticas descritivas da amostra')
        descritiva = amostra[['Gasto_mi', 'Pts', 'Pontos_10mi']].describe().T.rename(
            index={'Gasto_mi': 'Gasto (R$ mi)', 'Pts': 'Pontos', 'Pontos_10mi': 'Pontos / R$ 10 mi'},
            columns={'count':'Clubes', 'mean':'Média', 'std':'Desvio-padrão', 'min':'Mínimo', '25%':'1º quartil',
                     '50%':'Mediana', '75%':'3º quartil', 'max':'Máximo'})
        st.dataframe(descritiva, width='stretch')
        with st.expander('Critérios e limites da análise'):
            st.markdown('''- Recorte esportivo: apenas Série A de 2023, 2024 e 2025.
- Cada clube tem um registro por temporada e por base; o cruzamento usa clube + ano, sem aproximação de nomes.
- **Custos de futebol:** Sports Value com complementos oficiais/PLURI; América-MG/2023 é a exceção operacional EY sinalizada.
- **Despesas operacionais EY:** preservam a planilha enviada e não são mescladas aos custos de futebol. Não há 2024 nessa base.
- Edições divergentes usam a tabela histórica mais recente selecionada na pesquisa, sem média entre versões. São removíveis pelo filtro.
- Cuiabá/2023 na base EY é um alerta de escopo: o valor publicado é R$ 2 milhões. Não interpretar o indicador isoladamente.
- As médias e os quadrantes usam todos os clubes da amostra após o filtro de ressalvas. Destacar nomes não muda as médias.
- Valores anuais nominais, em R$ milhões; não há correção monetária, teste causal, regressão ou previsão.
- Estatísticas descritivas resumem estes dados; a qualidade contábil das fontes limita interpretações de eficiência.''')
    st.caption('Análise descritiva • fontes e rubricas disponíveis em Dados e método')
