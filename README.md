# 🎓 SigaaWatch

Ferramenta de automação para monitoramento de faltas e notas no sistema SIGAA (Universidade de Brasília e compatíveis). 

O sistema realiza o login automático, extrai os dados das disciplinas e apresenta em um dashboard simplificado, ajudando o estudante a gerenciar sua frequência.

## 🚀 Tecnologias

* **Python 3.12+**
* **Playwright:** Para navegação e extração de dados (Web Scraping).
* **Streamlit:** Para visualização dos dados (Dashboard).
* **Python-dotenv:** Gerenciamento seguro de credenciais.

## ⚙️ Instalação (Ubuntu/Linux)

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/SigaaWatch.git](https://github.com/SEU-USUARIO/SigaaWatch.git)
    cd SigaaWatch
    ```

2.  **Crie o ambiente virtual:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    playwright install
    sudo playwright install-deps
    ```

4.  **Configure as credenciais:**
    Crie um arquivo `.env` na raiz do projeto e preencha:
    ```env
    SIGAA_USER=sua_matricula
    SIGAA_PASS=sua_senha
    SIGAA_URL=[https://sigaa.unb.br/sigaa/verTelaLogin.do](https://sigaa.unb.br/sigaa/verTelaLogin.do)
    ```

##  ▶️ Como Usar

Para testar a coleta de dados (Login):
```bash
python robo.py
