

#! ========================================================
#! Etapa 2 - Scripts para leitura de arquivos PDF
#! ========================================================

from pathlib import Path
import re
import PyPDF2
import pandas as pd

def executar_leitura_pdfs():

    BASE_DIR = Path(__file__).resolve().parent.parent
    PASTA_PDFS = BASE_DIR / "arquivos_auxiliares" / "relatorios_futebol_leitor_pdf"
    PASTA_SAIDA = BASE_DIR / "arquivos_auxiliares" / "tabelas_jogadores_leitor_pdf"

    relatorios = [PASTA_PDFS / f for f in PASTA_PDFS.glob("*.pdf") if f.is_file()]


    def ler_pdf(caminho_pdf):
        paginas = []
        with open(caminho_pdf, "rb") as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            for pagina in leitor.pages:
                paginas.append(pagina.extract_text() or "")
        return "\n".join(paginas)


    def flex_titulo(titulo):
        partes = [re.escape(p) for p in titulo.split()]
        return r"\s*".join(partes)


    def pegar_secao(texto, titulo_inicio, titulo_fim=None):
        ini = flex_titulo(titulo_inicio)
        if titulo_fim:
            fim = flex_titulo(titulo_fim)
            padrao = rf"{ini}(.*?)(?={fim})"
        else:
            padrao = rf"{ini}(.*)"
        match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else ""


    def extrair(padrao, texto, grupo=1):
        match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        if match:
            limpo = re.sub(r"\s+", " ", match.group(grupo)).strip()
            limpo = re.sub(r"([a-zà-ú])-\s+([a-zà-ú])", r"\1-\2", limpo)
            return limpo
        return None


    lista_jogadores = []

    for nome_arquivo in relatorios:
        caminho = PASTA_PDFS / nome_arquivo
        texto = ler_pdf(caminho)

        sec_info = pegar_secao(texto, "1. Informações do Jogador", "2. Contexto da Partida")
        sec_tecnica = pegar_secao(texto, "3. Avaliação Técnica", "4. Entendimento Tático")
        sec_tatica = pegar_secao(texto, "4. Entendimento Tático", "5. Perfil Físico")
        sec_fisica = pegar_secao(texto, "5. Perfil Físico", "6. Mentalidade e Caráter")
        sec_mental = pegar_secao(texto, "6. Mentalidade e Caráter", "7. Pontos Fortes")

        dados_jogador = {
            "Arquivo": nome_arquivo,
            "Nome": extrair(r"Nome\s*do\s*Jogador:\s*(.+?)(?=\s*Posição\(ões\):)", sec_info),
            "Posicao": extrair(r"Posição\(ões\):\s*(.+?)(?=\s*Data\s*de\s*Nascimento)", sec_info),
            "Idade": extrair(r"\((\d+)\s*anos\)", sec_info),
            "Pe_Preferido": extrair(r"Pé\s*Preferido:\s*(.+?)(?=\s*Nacionalidade:)", sec_info),
            "Clube": extrair(r"Clube\s*Atual:\s*(.+?)(?=\s*Competição\s*/\s*Nível:)", sec_info),
            "Altura_m": extrair(r"\(?(\d+,\d+)\s*m\s*/", sec_fisica),
            "Peso_kg": extrair(r"/\s*(\d+)\s*k", sec_fisica),
            "Nota_Forca": extrair(r"Força\s*/\s*Duelos\s*\|\s*Nota\s*\(1-5\):\s*([\d,]+)", sec_fisica),
            "Obs_Fisica": extrair(
                r"Força\s*/\s*Duelos.*?Observações:\s*(.+?)(?=\s*Área:|\Z)",
                sec_fisica,
            ),
            "Nota_Geral_Tecnica": extrair(r"Geral\s*\|\s*Nota\s*\(1-5\):\s*([\d,]+)", sec_tecnica),
            "Nota_Geral_Tatica": extrair(r"Geral\s*\|\s*Nota\s*\(1-5\):\s*([\d,]+)", sec_tatica),
            "Nota_Geral_Fisica": extrair(r"Geral\s*\|\s*Nota\s*\(1-5\):\s*([\d,]+)", sec_fisica),
            "Nota_Geral_Mental": extrair(r"Geral\s*\|\s*Nota\s*\(1-5\):\s*([\d,]+)", sec_mental),
            "Decisao": extrair(r"Decis.o\s*de\s*Recrutamento:\s*(.+?)(?=\s*N.vel\s*Recomendado:)", texto),
        }

        lista_jogadores.append(dados_jogador)

    df_jogadores = pd.DataFrame(lista_jogadores)

    print(df_jogadores[["Arquivo", "Nome", "Posicao", "Idade", "Clube", "Decisao"]].to_string(index=False))

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    df_jogadores.to_csv(
        PASTA_SAIDA / "tabela_jogadores.csv",
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )

if __name__ == "__main__":
    executar_leitura_pdfs()