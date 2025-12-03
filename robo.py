import os
import re
import json
from time import sleep # Importante: Importando o sleep
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("SIGAA_USER")
PASSWORD = os.getenv("SIGAA_PASS")
URL_LOGIN = os.getenv("SIGAA_URL")
URL_PORTAL = "https://sigaa.unb.br/sigaa/portais/discente/discente.jsf"

# --- FUNÇÃO DE CLIQUE VIA JS (Mantida pois funcionou para burlar invisibilidade) ---
def js_click(page, locator_string):
    try:
        locator = page.locator(locator_string).first
        locator.evaluate("element => element.click()")
        return True
    except Exception as e:
        print(f"     [JS Click Falhou] {locator_string}")
        return False

def extrair_numero(texto_pagina, padrao):
    match = re.search(padrao, texto_pagina)
    if match:
        return int(match.group(1))
    return 0

def rodar_robo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()

        print("--- Iniciando SigaaWatch ---")
        
        # 1. LOGIN
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

        # 2. COOKIES
        try:
            if page.locator("text=Ciente").is_visible():
                page.click("text=Ciente")
        except: pass

        # 3. LISTAR MATÉRIAS
        print("Buscando lista de matérias...")
        if "portais/discente" not in page.url:
            page.goto(URL_PORTAL)
            page.wait_for_load_state("networkidle")

        links_materias = page.locator("td.descricao a, .lista-turmas a").all()
        nomes_materias = [link.inner_text().strip() for link in links_materias if link.inner_text().strip()]
        nomes_materias = [n for n in nomes_materias if len(n) > 5] 
        print(f"Matérias encontradas: {nomes_materias}")
        
        dados_finais = []

        # 4. LOOP
        for materia in nomes_materias:
            print(f"\n--------------------------------")
            print(f"Processando: {materia}")
            
            # Reset Navegação
            page.goto(URL_PORTAL)
            page.wait_for_load_state("networkidle")

            try:
                # Entrar na Turma
                page.click(f"text={materia}")
                page.wait_for_selector("text=Menu Turma Virtual", timeout=10000)
                
                # Menu Estudantes
                print("   > Abrindo menu Estudantes...")
                sucesso = js_click(page, ".itemMenuHeaderAlunos")
                if not sucesso: js_click(page, "text=Estudantes")
                
                sleep(1) # Pausa pequena para animação do menu
                
                print("   > Clicando em Frequência...")
                js_click(page, "text=Frequência")
                
                # --- AQUI ESTÁ A CORREÇÃO PRINCIPAL ---
                # Esperamos o navegador terminar a transição antes de ler
                print("   > Aguardando carregamento da tabela...")
                page.wait_for_load_state("domcontentloaded") 
                sleep(3) # Pausa forçada de 3 segundos para garantir que o HTML estabilizou
                
                # --- EXTRAÇÃO ---
                conteudo = page.content()
                status_materia = "Ativo"
                mensagem_materia = "Monitoramento normal"
                
                # CASO 1: Aviso Vermelho (Não faz chamada)
                if "A frequência ainda não foi lançada" in conteudo:
                    print(f"   > Caso: Aviso Vermelho detectado.")
                    status_materia = "Indisponível"
                    mensagem_materia = "Não fazem chamada"
                    faltas_somadas = 0
                    presencas = 0
                    total_aulas_reg = 0
                    freq_percent = 100.0

                else:
                    # CASO 2 e 3: Tabela Existe
                    print("   > Analisando tabela...")
                    linhas = page.locator("table tbody tr").all()
                    
                    faltas_somadas = 0
                    tem_registro_real = False # Se achou "Falta" ou "Presente"
                    
                    for linha in linhas:
                        texto = linha.inner_text()
                        
                        if "Falta" in texto:
                            match = re.search(r"(\d+)\s*Falta", texto)
                            if match:
                                faltas_somadas += int(match.group(1))
                                tem_registro_real = True
                        elif "Presente" in texto:
                            tem_registro_real = True

                    # Dados oficiais do rodapé
                    presencas = extrair_numero(conteudo, r"Presenças Registradas:\s*(\d+)")
                    total_aulas_reg = extrair_numero(conteudo, r"Número de Aulas com Registro.*:\s*(\d+)")
                    
                    # Lógica Sistemas de Info (Tabela vazia/só placeholders)
                    if not tem_registro_real and presencas == 0:
                        print(f"   > Caso: Tabela vazia.")
                        status_materia = "Pendente"
                        mensagem_materia = "O professor ainda não lançou a chamada"
                        freq_percent = 100.0
                    else:
                        # Lógica Normal (Linguagens)
                        if total_aulas_reg > 0:
                            freq_percent = (presencas / total_aulas_reg) * 100
                        else:
                            freq_percent = 100.0
                        
                        mensagem_materia = "Chamada ativa"

                    print(f"   > Resultado: {mensagem_materia} | Faltas: {faltas_somadas}")

                # Salvar
                dados_finais.append({
                    "materia": materia,
                    "status": status_materia,
                    "mensagem": mensagem_materia,
                    "faltas": faltas_somadas,
                    "presencas": presencas,
                    "total": total_aulas_reg,
                    "porcentagem": round(freq_percent, 2)
                })

            except Exception as e:
                print(f"   > ERRO: {e}")
                continue

        # Gravar JSON
        with open("dados_faltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n--- Finalizado com Sucesso! ---")
        browser.close()

if __name__ == "__main__":
    rodar_robo()
