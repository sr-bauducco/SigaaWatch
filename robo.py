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

# --- NOVA FUNÇÃO: FORÇAR VOLTA AO INÍCIO ---
def voltar_para_portal(page):
    """Garante que estamos na lista de matérias, não importa onde o robô esteja."""
    print("   > Voltando para o Menu Principal...")
    try:
        # Tenta clicar no link do topo "Portal do Discente" (Geralmente funciona melhor)
        # O seletor procura um link que tenha exatamente esse texto ou parecido
        portal_link = page.locator("a:has-text('Portal do Discente')").first
        
        if portal_link.is_visible():
            portal_link.click()
        else:
            # Se não achar o botão, força pelo ícone da casinha ou recarrega a URL base do portal
            # Dependendo do SIGAA, o link pode variar, então vamos tentar voltar pelo histórico ou re-clicar na logo
            # Se tudo falhar, usamos o goto na URL do portal discente (mas a URL muda com sessão, então é arriscado)
            # Vamos tentar clicar no "Menu Discente" que costuma ficar no topo
            page.click("text=Menu Discente")
            
        page.wait_for_load_state("networkidle")
        
        # Verificação extra: Se ainda ver o menu lateral de uma matéria, tenta de novo
        if page.locator("text=Menu Turma Virtual").is_visible():
            print("   > Ainda estou na turma. Tentando clicar em 'Turmas' > 'Ver Turmas'...")
            # Estratégia de emergência: Navegação pelo menu superior
            page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf") 
            
    except Exception as e:
        print(f"   > Erro ao tentar voltar: {e}. Tentando URL direta...")
        # Se tudo der errado, tenta voltar o histórico
        page.go_back()
    
    page.wait_for_load_state("networkidle")


def rodar_robo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        # Aumentamos o tamanho da tela para garantir que o menu lateral não fique escondido (responsividade)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
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
            page.wait_for_timeout(1000)
            if page.locator("text=Ciente").is_visible():
                page.click("text=Ciente")
        except: pass

        # --- 3. MAPEANDO MATÉRIAS ---
        print("Buscando lista de matérias...")
        links_materias = page.locator("td.descricao a, .lista-turmas a").all()
        nomes_materias = [link.inner_text().strip() for link in links_materias if link.inner_text().strip()]
        nomes_materias = [n for n in nomes_materias if len(n) > 5]
        
        print(f"Matérias encontradas: {nomes_materias}")
        
        dados_finais = []

        # --- 4. LOOP DE EXTRAÇÃO ---
        for materia in nomes_materias:
            print(f"\n--------------------------------")
            print(f"Processando: {materia}")
            
            # PASSO CRUCIAL: Antes de tentar entrar, GARANTE que está na home
            voltar_para_portal(page)

            try:
                # Entra na matéria
                # Usamos exact=True para evitar clicar em "Monitoria de Calculo 2" se existir
                page.click(f"text={materia}") 
                page.wait_for_load_state("networkidle")

                # --- TENTATIVA DE CLIQUE NO MENU "ESTUDANTES" ---
                print("   > Procurando menu Estudantes...")
                
                # Lista de tentativas de seletores para o menu
                seletores_menu = [
                    "div#menuForm >> text=Estudantes",       # Padrão
                    "text=Estudantes",                       # Genérico (Cuidado, pode clicar no topo)
                    ".itemMenu:has-text('Estudantes')",      # Classe comum no SIGAA
                    "//td[contains(text(),'Estudantes')]",   # XPath para tabela
                    "//div[contains(text(),'Estudantes')]"   # XPath para div
                ]
                
                menu_encontrado = False
                for seletor in seletores_menu:
                    try:
                        if page.locator(seletor).first.is_visible():
                            page.locator(seletor).first.click()
                            menu_encontrado = True
                            print(f"     -> Menu clicado usando: {seletor}")
                            break
                    except:
                        continue
                
                if not menu_encontrado:
                    raise Exception("Não encontrei o botão 'Estudantes' com nenhum seletor.")

                # Pequena pausa para o menu abrir (se for accordion)
                page.wait_for_timeout(500)
                
                # Clica em Frequência
                page.click("text=Frequência")
                page.wait_for_load_state("networkidle")
                
                # --- EXTRAÇÃO (Igual ao anterior) ---
                conteudo = page.content()

                if "A frequência ainda não foi lançada" in conteudo:
                    print(f"   > Status: Frequência não lançada.")
                    dados_finais.append({
                        "materia": materia,
                        "status_frequencia": "Indisponível",
                        "mensagem": "Professor não lança chamada",
                        "faltas": "N/A", "presencas": "N/A", "porcentagem": "N/A"
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
                        "porcentagem": round(freq_percent, 2)
                    })

            except Exception as e:
                print(f"   > ERRO em {materia}: {e}")
                # Salva print do erro
                page.screenshot(path=f"erro_{materia[:5].strip()}.png")
                # Não dá 'continue' aqui, deixa o loop seguir para o 'voltar_para_portal' na próxima iteração

        # --- 5. SALVAR ---
        with open("dados_faltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n--- Finalizado! ---")
        browser.close()

if __name__ == "__main__":
    rodar_robo()
