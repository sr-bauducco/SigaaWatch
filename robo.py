import os
from time import sleep
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

USER = os.getenv("SIGAA_USER")
PASSWORD = os.getenv("SIGAA_PASS")
URL = os.getenv("SIGAA_URL")

def testar_login():
    with sync_playwright() as p:
        # headless=False abre o navegador visível. 
        # No Ubuntu, se der erro de display, mude para True, mas tente False primeiro.
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        print(f"--- Iniciando Robô no Ubuntu ---")
        print(f"Acessando {URL}...")
        page.goto(URL)

        print("Aguardando carregamento da Autenticação Integrada...")
        # O Playwright espera os elementos aparecerem automaticamente, 
        # mas vamos garantir que estamos na tela certa procurando pelo campo de usuário
        page.wait_for_selector("#username")

        print("Preenchendo credenciais (Padrão CAS UnB)...")
        
        # 1. Preenche a Matrícula (O ID nessa tela é #username)
        page.fill("#username", USER)
        
        # 2. Preenche a Senha (O ID nessa tela é #password)
        page.fill("#password", PASSWORD)

        print("Clicando em Entrar...")
        # 3. Clica no botão. 
        # Usamos um seletor de texto ou nome que funciona especificamente nessa tela
        # A opção abaixo procura um botão que contenha o texto "ENTRAR"
        page.click("text=ENTRAR") 

        print("Aguardando login completar...")
        # Espera o redirecionamento de volta para o SIGAA
        page.wait_for_load_state("networkidle")

        # Tira um novo print para confirmar que passou dessa tela
        page.screenshot(path="comprovante_login.png")
        print("Login realizado! Verifique o arquivo 'comprovante_login.png'.")
        print("Login realizado! Aguardando carregamento do portal...")
        page.wait_for_load_state("networkidle")

        print("Login realizado! Aguardando carregamento do portal...")
        page.wait_for_load_state("networkidle")

        # --- NOVA LÓGICA DO BANNER DE COOKIES ---
        try:
            # Dá um tempinho para o banner animar e aparecer
            page.wait_for_timeout(2000)
            
            # Localiza o botão especificamente
            botao_ciente = page.locator("button:has-text('Ciente'), a:has-text('Ciente')").first
            
            if botao_ciente.is_visible():
                print("Botão de cookies detectado. Clicando...")
                botao_ciente.click(force=True) # force=True clica mesmo se o sistema achar que está bloqueado
                page.wait_for_timeout(1000) # Espera sumir
            else:
                print("Botão de cookies não estava visível. Tentando remoção forçada...")
                # Plano B: Executa JavaScript para destruir qualquer elemento que contenha 'Ciente'
                # Isso é útil se o banner for um overlay chato
                page.evaluate("""
                    const elements = [...document.querySelectorAll('div, footer, p')];
                    const banner = elements.find(el => el.innerText.includes('Nós usamos cookies'));
                    if(banner) banner.remove();
                """)
                
        except Exception as e:
            print(f"Aviso: Não foi possível interagir com o banner ({e}), mas vou continuar.")
        # 2. Encontrar a tabela de turmas
        # No SIGAA, geralmente as turmas estão numa tabela com classe "listagem" ou dentro de um div específico
        # Vamos pegar todos os links que estão na coluna de "Componente Curricular"
        
        print("Buscando lista de matérias...")
        
        # Este seletor busca links (a) dentro das células (td) da tabela de turmas
        # A classe da tabela costuma ser .listagem ou .tabelaRelatorio. Vamos tentar algo genérico primeiro:
        # Pega os links dentro do corpo da tabela de turmas
        materias = page.locator("#turmas-portal .descricao a").all()
        
        if not materias:
            # Fallback: Tenta pegar pelo texto do link se o seletor acima falhar
            print("Tentando estratégia alternativa de seleção...")
            # Pega links que parecem ser matérias (geralmente tem texto em maiúsculo na primeira coluna)
            materias = page.locator("td.descricao a").all()

        print(f"Encontrei {len(materias)} matérias.")

        if len(materias) > 0:
            # Vamos testar entrar na PRIMEIRA matéria para ver como é a página de dentro
            primeira_materia = materias[0]
            nome_materia = primeira_materia.inner_text()
            print(f"Acessando a matéria: {nome_materia}")
            
            primeira_materia.click()
            
            page.wait_for_load_state("networkidle")
            
            # Tira um print da página DA MATÉRIA
            page.screenshot(path="pagina_materia.png")
            print("Entrei na matéria! Print salvo como 'pagina_materia.png'.")
        else:
            print("ERRO: Não encontrei os links das matérias. Verifique o seletor.")
            page.screenshot(path="erro_lista_materias.png")

        sleep(3)
        browser.close()

if __name__ == "__main__":
    testar_login()
