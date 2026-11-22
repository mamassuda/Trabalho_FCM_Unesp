
#! ===================================================================================== 
#! Esse script é responsável por tratar os dados extraídos dos PDFs e do web scraping.
#! =====================================================================================

from pathlib import Path
import unicodedata
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ARQ_JOGADORES = BASE_DIR / "arquivos_auxiliares" / "tabelas_jogadores_leitor_pdf" / "tabela_jogadores.csv"
PASTA_SCRAPING = BASE_DIR / "arquivos_auxiliares" / "tabelas_web_scraping"


def normalizar_texto(texto: str) -> str:
    """Remove acentos e padroniza em minúsculas para comparar nomes de clubes."""
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def carregar_e_tratar_jogadores() -> pd.DataFrame:
    """Lê o CSV extraído dos PDFs e converte notas e medidas para formato numérico."""
    if not ARQ_JOGADORES.exists():
        return pd.DataFrame()

    df = pd.read_csv(ARQ_JOGADORES, sep=";", encoding="utf-8-sig")
    if df.empty:
        return df

    colunas_decimais = [
        "Altura_m",
        "Nota_Forca",
        "Nota_Geral_Tecnica",
        "Nota_Geral_Tatica",
        "Nota_Geral_Fisica",
        "Nota_Geral_Mental",
    ]
    for col in colunas_decimais:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )

    for col in ["Idade", "Peso_kg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    colunas_notas = [
        "Nota_Geral_Tecnica",
        "Nota_Geral_Tatica",
        "Nota_Geral_Fisica",
        "Nota_Geral_Mental",
    ]
    df["Media_Geral"] = df[colunas_notas].mean(axis=1).round(2)
    return df


def carregar_e_tratar_classificacoes() -> pd.DataFrame:
    """Unifica os CSVs das séries A, B e C e separa posição numérica da zona."""
    arquivos = sorted(PASTA_SCRAPING.glob("*.csv"))
    if not arquivos:
        return pd.DataFrame()

    lista_dfs = []
    for arquivo in arquivos:
        df_temp = pd.read_csv(arquivo)
        extraido = df_temp["Pos"].astype(str).str.extract(r"^(.*?)\s*(\d+)$")
        df_temp["Zona"] = extraido[0].replace("", "Meio de tabela")
        df_temp["Pos"] = extraido[1].astype(int)

        _, divisao, ano = arquivo.stem.split("_")
        df_temp["Serie"] = divisao.upper()
        df_temp["Ano"] = int(ano)
        lista_dfs.append(df_temp)

    return pd.concat(lista_dfs, ignore_index=True)


def cruzar_jogadores_clubes(df_jog: pd.DataFrame, df_clas: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Relaciona cada jogador avaliado com o desempenho do seu clube na temporada."""
    df_ano = df_clas[df_clas["Ano"] == ano].copy()
    df_ano["clube_norm"] = df_ano["Clube"].apply(normalizar_texto)

    resultados = []
    for _, jog in df_jog.iterrows():
        clube_pdf_norm = normalizar_texto(jog["Clube"])
        match = df_ano[
            df_ano["clube_norm"].apply(
                lambda c: c != "" and (c in clube_pdf_norm or clube_pdf_norm in c)
            )
        ]

        if not match.empty:
            time_info = match.iloc[0]
            resultados.append({
                "Jogador": jog["Nome"],
                "Posicao": jog["Posicao"],
                "Media_Scouting": jog["Media_Geral"],
                "Decisao": jog["Decisao"],
                "Clube_PDF": jog["Clube"],
                "Serie": time_info["Serie"],
                "Posicao_Tabela": f"{time_info['Pos']}º",
                "Pontos": time_info["Pts"],
                "Situacao_Clube": time_info["Zona"],
            })
        else:
            resultados.append({
                "Jogador": jog["Nome"],
                "Posicao": jog["Posicao"],
                "Media_Scouting": jog["Media_Geral"],
                "Decisao": jog["Decisao"],
                "Clube_PDF": jog["Clube"],
                "Serie": "Não encontrado (A/B/C)",
                "Posicao_Tabela": "-",
                "Pontos": None,
                "Situacao_Clube": "-",
            })

    return pd.DataFrame(resultados)