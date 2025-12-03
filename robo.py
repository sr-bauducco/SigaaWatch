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

def rodar_robo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()

        print("--- Iniciando SigaaWatch ---")
        
        # --- 1. LOGIN ---
        page.goto(URL_LOGIN)
        try:
            # Login UnB (CAS)
            page.wait_for_selector("#username", timeout=5000)
            page.fill("#username", USER)
            page.fill("#password", PASSWORD)
            page.click("text=ENTRAR")
        except:
            # Login Padrão
            page.fill("input[name='user.login']", USER)
            page.fill("input[name='user.senha']", PASSWORD)
            page.click("input[value='Entrar']")
            
        page.wait_for_load_state("networkidle")
        print("Login realizado.")

        # --- 2. COOKIES ---
        try:
            btn_cookies = page.locator("text=Ciente").first
            if btn_cookies.is_visible():
                btn_cookies.click()
        except:
            pass

        # --- 3. MAPEANDO MATÉRIAS ---
        print("Buscando lista de matérias...")
        
        # Pega links da tabela
        links_materias = page.locator("td.descricao a, .lista-turmas a").all()
        nomes_materias = [link.inner_text().strip() for link in links_materias if link.inner_text().strip()]
        # Filtro básico para remover links vazios
        nomes_materias = [n for n in nomes_materias if len(n) > 5]
        
        print(f"Matérias encontradas: {nomes_materias}")
        
        dados_finais = []

        # --- 4. LOOP DE EXTRAÇÃO ---
        for materia in nomes_materias:
            print(f"\nProcessando: {materia}...")
            
            # Garante que está no Portal do Discente
            if "portais/discente" not in page.url:
                page.locator("text=Portal do Discente").first.click()
                page.wait_for_load_state("networkidle")

            try:
                # Entra na matéria
                page.click(f"text={materia}")
                page.wait_for_load_state("networkidle")

                # Navega: Estudantes -> Frequência
                page.click("div#menuForm >> text=Estudantes")
                page.wait_for_timeout(500)
                page.click("text=Frequência")
                page.wait_for_load_state("networkidle")
                
                # Pega o HTML da página
                conteudo = page.content()

                # --- NOVIDADE: VERIFICAÇÃO DE AVISO EM VERMELHO ---
                if "A frequência ainda não foi lançada" in conteudo:
                    print(f"   > Aviso detectado: Professor não lança chamada.")
                    
                    dados_finais.append({
                        "materia": materia,
                        "status_frequencia": "Indisponível",
                        "mensagem": "o professor não faz chamada/faz no papel",
                        "faltas": "N/A",
                        "presencas": "N/A",
                        "porcentagem": "N/A"
                    })
                
                else:
                    # --- CÁLCULO NORMAL ---
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
                print(f"Erro em {materia}: {e}")
                continue

        # --- 5. SALVAR ---
        with open("dados_faltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n--- Finalizado! Dados salvos em 'dados_faltas.json' ---")
        browser.close()

if __name__ == "__main__":
    rodar_robo()
