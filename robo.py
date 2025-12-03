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

def voltar_para_portal(page):
    print("   > Voltando para o Menu Principal...")
    try:
        # Tenta clicar na casinha (ícone home)
        # Seletores para imagem ou link com title 'Menu Discente'
        botao_casa = page.locator("a[title='Menu Discente'], img[title='Menu Discente'], img[src*='home.png']").first
        
        if botao_casa.is_visible():
            botao_casa.click()
        else:
            # Fallback para texto
            print("     -> Casinha não visível. Tentando link de texto...")
            if page.locator("text=Portal do Discente").is_visible():
                page.click("text=Portal do Discente")
            else:
                # Último recurso: URL direta
                print("     -> Botões não encontrados. Forçando URL...")
                page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf")
            
        page.wait_for_load_state("networkidle")

        # Se ainda estiver preso no menu da turma, força a URL
        if page.locator("text=Menu Turma Virtual").is_visible():
            page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf")
            page.wait_for_load_state("networkidle")
            
    except Exception as e:
        print(f"   > Erro crítico ao voltar: {e}. Indo para URL direta...")
        page.goto("https://sigaa.unb.br/sigaa/portais/discente/discente.jsf")
        page.wait_for_load_state("networkidle")


def rodar_robo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        # Mantemos viewport grande
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
        nomes_materias = [n for n in nomes_materias if len(n) > 5] 
        
        print(f"Matérias encontradas: {nomes_materias}")
        
        dados_finais = []

        # --- 4. LOOP DE EXTRAÇÃO ---
        for materia in nomes_materias:
            print(f"\n--------------------------------")
            print(f"Processando: {materia}")
            
            # Garante Home
            if "portais/discente" not in page.url and "turma/lista.jsf" not in page.url:
                voltar_para_portal(page)

            try:
                # Clica na matéria
                page.click(f"text={materia}")
                page.wait_for_load_state("networkidle")

                # --- MUDANÇA AQUI: CLIQUE ROBUSTO NO MENU ---
                print("   > Acessando menu Estudantes...")
                
                # Usamos a classe específica que apareceu no seu erro
                menu_estudantes = page.locator(".itemMenuHeaderAlunos, text=Estudantes").first
                
                # 1. Garante que está na tela (scroll)
                menu_estudantes.scroll_into_view_if_needed()
                
                # 2. Tenta clicar (com force=True para ignorar erro de 'not visible')
                try:
                    menu_estudantes.click(timeout=2000)
                except:
                    print("     -> Clique normal falhou. Usando FORCE CLICK...")
                    menu_estudantes.click(force=True)
                
                # Pequena pausa para o menu expandir
                page.wait_for_timeout(500)
                
                # Clica em Frequência (também com force, por garantia)
                link_freq = page.locator("text=Frequência").first
                try:
                    link_freq.click(timeout=2000)
                except:
                    print("     -> Clique Frequência falhou. Usando FORCE CLICK...")
                    link_freq.click(force=True)
                    
                page.wait_for_load_state("networkidle")
                
                # --- EXTRAÇÃO ---
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

                voltar_para_portal(page)

            except Exception as e:
                print(f"   > ERRO CRÍTICO em {materia}: {e}")
                page.screenshot(path=f"erro_{materia[:5].strip()}.png")
                voltar_para_portal(page)

        # --- 5. SALVAR ---
        with open("dados_faltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n--- Finalizado! Dados salvos. ---")
        browser.close()

if __name__ == "__main__":
    rodar_robo()
