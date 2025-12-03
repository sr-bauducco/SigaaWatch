import os
import re
import json
from time import sleep
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("SIGAA_USER")
PASSWORD = os.getenv("SIGAA_PASS")
URL_LOGIN = os.getenv("SIGAA_URL")

def extrair_numero(texto_pagina, padrao):
    match = re.search(padrao, texto_pagina)
    if match:
        return int(match.group(1))
    return 0

# --- FUNÇÃO DE RETORNO ATUALIZADA (LÓGICA DA CASINHA) ---
def voltar_para_portal(page):
    print("   > Voltando para o Menu Principal...")
    try:
        # 1. Tenta clicar no botão "Casinha" (Menu Discente)
        # O SIGAA costuma usar title="Menu Discente" ou "Principal" na imagem ou no link da casa
        # Procuramos um link (a) ou imagem (img) que tenha 'Menu Discente' ou 'Principal' no título
        # Também procuramos genericamente por uma imagem que tenha 'home' no nome do arquivo
        
        botao_casa = page.locator("""
            a[title='Menu Discente'], 
            img[title='Menu Discente'], 
            a[title='Principal'], 
            img[src*='home.png'],
            img[src*='icon-home']
        """).first
        
        if botao_casa.is_visible():
            print("     -> Clicando no ícone da 'Casinha'...")
            botao_casa.click()
        
        else:
            # 2. Fallback: Se a casinha não for achada, tenta o texto "Portal do Discente"
            print("     -> Casinha não visível. Tentando texto 'Portal do Discente'...")
            page.click("text=Portal do Discente")
            
        page.wait_for_load_state("networkidle")

        # Verificação de segurança: Se ainda estiver preso na turma (vendo o menu lateral), força URL
        if page.locator("text=Menu Turma Virtual").is_visible():
            print("     -> Ainda na turma. Forçando navegação direta...")
            page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf")
            page.wait_for_load_state("networkidle")
            
    except Exception as e:
        print(f"   > Erro ao voltar: {e}. Tentando URL direta de emergência...")
        page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf")
        page.wait_for_load_state("networkidle")


def rodar_robo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        # Viewport maior para garantir que o menu superior apareça
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()

        print("--- Iniciando SigaaWatch ---")
        
        # --- 1. LOGIN ---
        page.goto(URL_LOGIN)
        try:
            page.wait_for_selector("#username", timeout=5000)
            page.fill("#username", USER)
            page.fill("#password", PASSWORD)
            page.click("text=ENTRAR")
        except:
            page.fill("input[name='user.login']", USER)
            page.fill("input[name='user.senha']", PASSWORD)
            page.click("input[value='Entrar']")
            
        page.wait_for_load_state("networkidle")
        print("Login realizado.")

        # --- 2. COOKIES ---
        try:
            if page.locator("text=Ciente").is_visible():
                page.click("text=Ciente")
        except: pass

        # --- 3. MAPEANDO MATÉRIAS ---
        print("Buscando lista de matérias...")
        links_materias = page.locator("td.descricao a, .lista-turmas a").all()
        nomes_materias = [link.inner_text().strip() for link in links_materias if link.inner_text().strip()]
        nomes_materias = [n for n in nomes_materias if len(n) > 5] # Filtra nomes muito curtos
        
        print(f"Matérias encontradas: {nomes_materias}")
        
        dados_finais = []

        # --- 4. LOOP DE EXTRAÇÃO ---
        for materia in nomes_materias:
            print(f"\n--------------------------------")
            print(f"Processando: {materia}")
            
            # Antes de entrar, garante que está na home
            # (Na primeira vez já está, mas nas próximas precisa voltar)
            if "portais/discente" not in page.url and "turma/lista.jsf" not in page.url:
                voltar_para_portal(page)

            try:
                # Clica na matéria
                page.click(f"text={materia}")
                page.wait_for_load_state("networkidle")

                # Navega até Frequência
                print("   > Acessando Frequência...")
                
                # Tenta clicar em "Estudantes" (Vários seletores para garantir)
                try:
                    page.locator("div#menuForm >> text=Estudantes").click()
                except:
                    # Tenta clicar apenas no texto se o div falhar
                    page.locator("text=Estudantes").first.click()
                
                page.wait_for_timeout(500)
                page.click("text=Frequência")
                page.wait_for_load_state("networkidle")
                
                # Extrai dados
                conteudo = page.content()

                if "A frequência ainda não foi lançada" in conteudo:
                    print(f"   > Status: Frequência não lançada.")
                    dados_finais.append({
                        "materia": materia,
                        "status_frequencia": "Indisponível",
                        "mensagem": "Professor não lança chamada",
                        "faltas": 0, "presencas": 0, "total_aulas": 0, "porcentagem": 100
                    })
                else:
                    presencas = extrair_numero(conteudo, r"Presenças Registradas:\s*(\d+)")
                    total_aulas = extrair_numero(conteudo, r"Número de Aulas com Registro.*:\s*(\d+)")
                    faltas = total_aulas - presencas
                    freq_percent = (presencas / total_aulas * 100) if total_aulas > 0 else 100.0
                    
                    print(f"   > Faltas: {faltas} | Frequência: {freq_percent:.1f}%")
                    dados_finais.append({
                        "materia": materia,
                        "status_frequencia": "Ativo",
                        "mensagem": "Monitoramento normal",
                        "faltas": faltas,
                        "presencas": presencas,
                        "total_aulas": total_aulas,
                        "porcentagem": round(freq_percent, 2)
                    })

                # IMPORTANTE: Voltar para o portal ao final do processamento desta matéria
                voltar_para_portal(page)

            except Exception as e:
                print(f"   > ERRO em {materia}: {e}")
                page.screenshot(path=f"erro_{materia[:5].strip()}.png")
                # Tenta recuperar voltando para o portal antes do próximo loop
                voltar_para_portal(page)

        # --- 5. SALVAR ---
        with open("dados_faltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n--- Finalizado! Dados salvos. ---")
        browser.close()

if __name__ == "__main__":
    rodar_robo()
