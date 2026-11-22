
#! =================================================================
#! Etapa 1 (Web Scraping) - Classificação do Brasileirão via Google
#! =================================================================
import random
import re
import time
from urllib.parse import quote_plus
from pathlib import Path  

import pandas as pd
from playwright.sync_api import sync_playwright


def executar_scraping():


    # Se tiver o Google Chrome instalado, deixe True (o Google detecta menos).
    # Se der erro dizendo que o Chrome não foi encontrado, troque para False.
    USAR_CHROME_INSTALADO = False

    # Seletores extraídos dos prints
    BOTAO_TEMPORADA = 'g-dropdown-button:has(label:text-is("Temporada")):visible'
    ITENS_ANO = 'g-menu-item[role="menuitemradio"]:visible'
    BOTAO_EXPANDIR = 'text="Mais classificações"'
    TABELA_CLASSIFICACAO = 'table:has-text("Pts"):visible'

    # Textos possíveis do botão do diálogo de cookies/consentimento
    TEXTOS_CONSENTIMENTO = [
        "Rejeitar tudo",
        "Aceitar tudo",
        "Reject all",
        "Accept all",
    ]


    # ------------------------------------------------------------------
    # Utilitários para lidar com bloqueios (inert / consentimento)
    # ------------------------------------------------------------------
    def fechar_consentimento(page) -> bool:
        """Tenta fechar o diálogo de cookies (na página ou dentro de iframes)."""
        for frame in page.frames:
            for texto in TEXTOS_CONSENTIMENTO:
                try:
                    btn = frame.get_by_role("button", name=texto)
                    if btn.count() > 0 and btn.first.is_visible():
                        btn.first.click(timeout=3000)
                        page.wait_for_timeout(1500)
                        print(f"Consentimento fechado ({texto}).")
                        return True
                except Exception:
                    continue
        return False


    def elemento_inerte(locator) -> bool:
        """True se o elemento (ou algum ancestral) tiver o atributo inert."""
        try:
            return locator.evaluate("el => !!el.closest('[inert]')")
        except Exception:
            return True


    def achar_botao_temporada(page, timeout_s: float = 15.0):
        """Devolve a cópia do botão 'Temporada' que NÃO está inerte."""
        limite = time.time() + timeout_s
        while time.time() < limite:
            candidatos = page.locator(BOTAO_TEMPORADA)
            for i in range(candidatos.count()):
                c = candidatos.nth(i)
                if not elemento_inerte(c):
                    return c
            time.sleep(0.5)
        return None


    def clicar_com_fallback(locator):
        """Clique normal; se falhar por bloqueio, tenta clique via JavaScript."""
        try:
            locator.click(timeout=5000)
        except Exception:
            locator.evaluate("el => el.click()")


    # ------------------------------------------------------------------
    # Extração da tabela
    # ------------------------------------------------------------------
    def extrair_linhas_tabela(tabela):
        dados = []
        for linha in tabela.locator("tr").all():
            celulas = [" ".join(td.inner_text().split()) for td in linha.locator("td").all()]
            celulas = [c for c in celulas if c]

            if len(celulas) >= 9:
                match = re.match(r"^(\d+)\s+(.+)$", celulas[0])
                if match:
                    posicao, clube = match.groups()
                    stats = celulas[1:9]
                else:
                    posicao, clube, stats = celulas[0], celulas[1], celulas[2:10]

                if len(stats) == 8:
                    dados.append([posicao, clube] + stats)
        return dados


    # ------------------------------------------------------------------
    # Coleta principal
    # ------------------------------------------------------------------
    def executar_coleta(busca: str, prefixo_csv: str):
        colunas = ["Pos", "Clube", "Pts", "PJ", "VIT", "E", "DER", "GM", "GC", "SG"]
        url = f"https://www.google.com/search?q={quote_plus(busca)}"

        launch_kwargs = dict(
            user_data_dir="./perfil_chrome",
            headless=False,
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
            slow_mo=250,
            args=["--disable-blink-features=AutomationControlled"],
        )
        if USAR_CHROME_INSTALADO:
            launch_kwargs["channel"] = "chrome"

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(**launch_kwargs)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")

            if "sorry" in page.url:
                input(">>> Resolva o CAPTCHA no navegador e aperte ENTER aqui...")

            # Fecha o diálogo de cookies, se existir (causa mais comum do 'inert')
            fechar_consentimento(page)

            # PASSO 1: Clica na setinha de "Temporada"
            btn_temporada = achar_botao_temporada(page)

            if btn_temporada is None:
                page.screenshot(path="debug_bloqueio.png", full_page=True)
                print("Não achei um botão 'Temporada' clicável (provável overlay).")
                print("Screenshot salvo em debug_bloqueio.png")
                input(">>> Feche manualmente o que estiver na frente e aperte ENTER...")
                btn_temporada = achar_botao_temporada(page)

            if btn_temporada is None:
                raise RuntimeError(
                    "Botão 'Temporada' continua inacessível. "
                    "Veja o debug_bloqueio.png para entender o que está bloqueando."
                )

            btn_temporada.scroll_into_view_if_needed()
            clicar_com_fallback(btn_temporada)

            # PASSO 2: Lê cada <g-menu-item> do menu aberto
            itens = page.locator(ITENS_ANO)
            itens.first.wait_for(state="visible", timeout=5000)

            temporadas = []
            for item in itens.all():
                ano = " ".join(item.inner_text().split())
                data_season = item.get_attribute("data-season")
                if re.match(r"^20\d{2}$", ano) and data_season:
                    temporadas.append((ano, data_season))

            print(f"Temporadas encontradas: {[t[0] for t in temporadas]}")
            # PASSO 3: Percorre ano por ano, expande todas as tabelas e salva o CSV
            for ano, data_season in temporadas:
                time.sleep(random.uniform(1.2, 2.5))

                seletor_este_ano = f'g-menu-item[data-season="{data_season}"]:visible'

                # Se o menu fechou após o clique anterior, reabre a setinha
                if page.locator(seletor_este_ano).count() == 0:
                    btn = achar_botao_temporada(page) or btn_temporada
                    btn.scroll_into_view_if_needed()
                    clicar_com_fallback(btn)
                    page.locator(seletor_este_ano).first.wait_for(
                        state="visible", timeout=5000
                    )

                item_ano = page.locator(seletor_este_ano).first
                ja_marcado = item_ano.get_attribute("aria-checked") == "true"
                primeira_tabela = page.locator(TABELA_CLASSIFICACAO).first
                texto_anterior = primeira_tabela.inner_text()

                clicar_com_fallback(item_ano)

                # Aguarda a página atualizar se trocou de ano
                if not ja_marcado:
                    page.wait_for_function(
                        """(anterior) => {
                            const t = Array.from(document.querySelectorAll('table'))
                                .find(el => el.offsetParent !== null && el.innerText.includes('Pts'));
                            return t && t.innerText !== anterior;
                        }""",
                        arg=texto_anterior,
                        timeout=10000,
                    )
                    time.sleep(1.0)

                # Clica em todos os botões "Mais classificações" visíveis (se houver mais de um grupo)
                botoes_mais = page.locator(BOTAO_EXPANDIR).locator("visible=true")
                if botoes_mais.count() > 0:
                    total_linhas_antes = sum(
                        t.locator("tr").count() for t in page.locator(TABELA_CLASSIFICACAO).all()
                    )
                    for i in range(botoes_mais.count()):
                        btn_mais = botoes_mais.nth(i)
                        if btn_mais.is_visible():
                            btn_mais.scroll_into_view_if_needed()
                            clicar_com_fallback(btn_mais)
                            time.sleep(0.8)

                    try:
                        page.wait_for_function(
                            """(antes) => {
                                const tabelas = Array.from(document.querySelectorAll('table'))
                                    .filter(el => el.offsetParent !== null && el.innerText.includes('Pts'));
                                const total = tabelas.reduce((acc, t) => acc + t.querySelectorAll('tr').length, 0);
                                return total > antes;
                            }""",
                            arg=total_linhas_antes,
                            timeout=8000,
                        )
                    except Exception:
                        pass

                # Extrai as linhas de cada tabela visível na página
                tabelas_extraidas = [
                    extrair_linhas_tabela(tab)
                    for tab in page.locator(TABELA_CLASSIFICACAO).all()
                ]

                # Se houver uma tabela completa (20 clubes, como a 1ª fase da Série C),
                # usa apenas ela para evitar duplicar os times dos quadrangulares
                tabelas_completas = [t for t in tabelas_extraidas if len(t) >= 18]
                if tabelas_completas:
                    dados = tabelas_completas[0]
                else:
                    dados = [linha for t in tabelas_extraidas for linha in t]

                nome_csv = f"{prefixo_csv}_{ano}.csv"
                pd.DataFrame(dados, columns=colunas).to_csv(
                    nome_csv, index=False, encoding="utf-8-sig"
                )
                print(f"Salvo: {nome_csv} ({len(dados)} clubes)")

            context.close()



    pasta_saida = Path("arquivos_auxiliares/tabelas_web_scraping")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    # Série A:
    executar_coleta("brasileirão série a classificação", str(pasta_saida / "serie_a"))

    # Série B:
    executar_coleta("brasileirão série b classificação", str(pasta_saida / "serie_b"))

    # Série C:
    executar_coleta("brasileirão série c classificação", str(pasta_saida / "serie_c"))


if __name__ == "__main__":
    executar_scraping()
