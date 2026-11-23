import matplotlib.pyplot as plt


def _validar(df):
    if df.empty:
        raise ValueError('DataFrame vazio: não há dados para o gráfico.')


def _estilo(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', alpha=0.22)


def grafico_barras(df, coluna, titulo, ylabel, cor='#820FDB', destaques=()):
    """Média por clube, em ordem decrescente, sem filtrar destaques."""
    _validar(df)
    medias = df.groupby('Clube')[coluna].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(15, 7) if len(medias) >= 20 else (14, 6), facecolor='white')
    selecionados = set(destaques)
    barras = ax.bar(medias.index, medias.values,
                    color=['#E69F00' if c in selecionados else cor for c in medias.index],
                    edgecolor='black')
    ax.bar_label(barras, fmt='%.1f', padding=3)
    ax.set(title=titulo, ylabel=ylabel, xlabel='Clube')
    ax.tick_params(axis='x', labelrotation=60 if len(medias) >= 20 else 45)
    for label in ax.get_xticklabels():
        label.set_ha('right')
    ax.margins(y=0.12)
    _estilo(ax)
    fig.tight_layout()
    return fig


def grafico_quadrantes(df, mostrar_nomes=True, destaques=()):
    """Gasto versus pontos; quadrantes descritivos relativos à amostra inteira."""
    _validar(df)
    fig, ax = plt.subplots(figsize=(15, 7), facecolor='white')
    x, y = df['Gasto_mi'], df['Pts']
    mx, my = x.mean(), y.mean()
    dx = max(float(x.max() - x.min()), abs(float(mx)) * 0.15, 1.)
    dy = max(float(y.max() - y.min()), abs(float(my)) * 0.15, 1.)
    xmin, xmax = float(x.min()) - dx * .18, float(x.max()) + dx * .18
    ymin, ymax = float(y.min()) - dy * .25, float(y.max()) + dy * .25
    selecionados = set(destaques)
    ax.scatter(x, y, c=['#E69F00' if c in selecionados else '#820FDB' for c in df['Clube']],
               s=[100 if c in selecionados else 65 for c in df['Clube']],
               edgecolors='black', linewidths=.6, zorder=3)
    ax.axvline(mx, color='red', linestyle='--', label=f'Média de gasto: R$ {mx:.1f} mi')
    ax.axhline(my, color='blue', linestyle='--', label=f'Média de pontos: {my:.1f}')
    ax.fill_between([xmin, mx], my, ymax, color='green', alpha=.14)
    ax.fill_between([mx, xmax], my, ymax, color='#E6C76C', alpha=.09)
    ax.fill_between([xmin, mx], ymin, my, color='#8AA6BF', alpha=.09)
    ax.fill_between([mx, xmax], ymin, my, color='red', alpha=.12)
    for tx, ty, texto, va in [
        (.01, .99, 'Menor gasto / mais pontos', 'top'),
        (.99, .99, 'Maior gasto / mais pontos', 'top'),
        (.01, .01, 'Menor gasto / menos pontos', 'bottom'),
        (.99, .01, 'Maior gasto / menos pontos', 'bottom')]:
        ax.text(tx, ty, texto, transform=ax.transAxes, va=va,
                ha='left' if tx < .5 else 'right', fontsize=9,
                bbox=dict(facecolor='white', alpha=.75, edgecolor='none'), zorder=5)
    # Distribui rótulos por faixas em coordenadas de tela, sem bibliotecas extras.
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax))
    fig.canvas.draw()
    ocupados = []
    for clube, xv, yv in zip(df['Clube'], x, y):
        if not mostrar_nomes and clube not in selecionados:
            continue
        nome = str(clube).replace('Clube de Regatas ', '').replace('Futebol Clube', 'FC')
        nome = nome.replace('Clube Atlético ', 'Atlético ').replace('Sport Club ', '')
        px, py = ax.transData.transform((xv, yv))
        largura = max(40, len(nome) * 5)
        offset = 8
        while any(abs(px - ox) < (largura + ow) / 2 and abs(py + offset - oy) < 14
                  for ox, oy, ow in ocupados):
            offset += 15
        ocupados.append((px, py + offset, largura))
        ax.annotate(nome, (xv, yv), xytext=(4, offset * 72 / fig.dpi),
                    textcoords='offset points', fontsize=8,
                    fontweight='bold' if clube in selecionados else 'normal',
                    annotation_clip=True,
                    arrowprops=dict(arrowstyle='-', color='gray', lw=.4))
    ax.set(xlabel='Gasto (R$ milhões nominais; sem correção pela inflação)', ylabel='Pontos',
           title='Gasto e pontos — quadrantes relativos à média da amostra')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.02), ncol=2, frameon=False)
    _estilo(ax)
    fig.tight_layout()
    return fig


def grafico_comparativo(df, clubes, coluna='Pts'):
    """Barras agrupadas por ano, mantendo lacunas como NaN (não como zero)."""
    _validar(df)
    presentes = set(df['Clube'])
    selecao = list(dict.fromkeys(c for c in clubes if c in presentes))
    if not selecao:
        raise ValueError('Nenhum clube selecionado presente: seleção vazia ou ausente.')
    dados = df.loc[df['Clube'].isin(selecao)]
    pivot = dados.pivot(index='Ano', columns='Clube', values=coluna)
    pivot = pivot.reindex(index=sorted(df['Ano'].unique()), columns=selecao)
    fig, ax = plt.subplots(figsize=(14, 6), facecolor='white')
    largura = .8 / len(selecao)
    centros = list(range(len(pivot)))
    for i, clube in enumerate(selecao):
        posicoes = [p - .4 + largura / 2 + i * largura for p in centros]
        barras = ax.bar(posicoes, pivot[clube].to_numpy(dtype=float), width=largura,
                        label=clube, edgecolor='black')
        ax.bar_label(barras, fmt='%.1f', padding=3)
    ax.set_xticks(centros, [str(ano) for ano in pivot.index])
    ylabel = ('Gasto (R$ milhões nominais; sem correção pela inflação)'
              if coluna == 'Gasto_mi' else coluna)
    ax.set(xlabel='Ano', ylabel=ylabel, title='Comparativo por clube e temporada')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.02),
              ncol=min(len(selecao), 4), frameon=False)
    ax.margins(y=.15)
    _estilo(ax)
    fig.tight_layout()
    return fig
