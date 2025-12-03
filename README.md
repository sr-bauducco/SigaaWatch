# 🎓 SigaaWatch (UnB Edition)

> **Monitoramento automatizado de frequência e faltas para o SIGAA da UnB.**

O **SigaaWatch** é um bot desenvolvido em Python que acessa o portal do aluno, navega por todas as matérias matriculadas e extrai o relatório de faltas detalhado. Ele é capaz de diferenciar matérias onde o professor lança chamada na plataforma daquelas onde o controle é feito "no papel" ou ainda não foi iniciado.

## 🚀 Funcionalidades

* **Login Automático:** Suporte à Autenticação Integrada (CAS) da UnB.
* **Navegação Robusta:** Utiliza *JavaScript Injection* para interagir com menus antigos do SIGAA (evitando erros de "elemento invisível").
* **Extração Inteligente:**
    * ✅ Conta faltas reais ("2 Falta(s)") na tabela visual.
    * ⚠️ Identifica aviso "A frequência ainda não foi lançada" (Não faz chamada).
    * ⏳ Identifica tabelas vazias (Professor ainda não lançou).
* **Anti-Instabilidade:** Reseta a sessão do navegador entre as matérias para evitar que o SIGAA desconecte ou trave.
* **Output:** Gera um arquivo `dados_faltas.json` pronto para ser consumido por Dashboards.

## 🛠️ Tecnologias

* **Python 3.12+**
* **Playwright:** Automação de navegador moderna e rápida.
* **Python-dotenv:** Segurança de credenciais.

## ⚙️ Instalação (Ubuntu/Linux)

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/sr-bauducco/SigaaWatch.git
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
    ```

4.  **Instale os navegadores do Playwright:**
    ```bash
    playwright install
    sudo playwright install-deps
    ```

## 🔐 Configuração

Crie um arquivo chamado `.env` na raiz do projeto e configure suas credenciais.
**Nunca compartilhe este arquivo!**

```env
SIGAA_USER=sua_matricula (ex: 2110xxxxx)
SIGAA_PASS=sua_senha_do_sigaa
SIGAA_URL=[https://sigaa.unb.br/sigaa/verTelaLogin.do](https://sigaa.unb.br/sigaa/verTelaLogin.do)
```
## ▶️ Como Usar

Com o ambiente ativado, execute o robô:

```bash
python robo.py
```

O navegador abrirá (pode ser configurado para rodar em background), realizará o login e processará matéria por matéria. Ao final, um arquivo dados_faltas.json será gerado.
Exemplo de Saída (JSON)
```JSON

[
    {
        "materia": "LINGUAGENS DE PROGRAMACAO",
        "status": "Ativo",
        "mensagem": "Chamada ativa",
        "faltas": 6,
        "presencas": 59,
        "porcentagem": 90.7
    },
    {
        "materia": "CÁLCULO 2",
        "status": "Indisponível",
        "mensagem": "Não fazem chamada",
        "faltas": 0,
        "porcentagem": 100.0
    }
]
```
⚠️ Aviso Legal

Este projeto foi desenvolvido para fins estritamente educacionais e de produtividade pessoal. O uso excessivo de bots pode sobrecarregar os servidores da universidade. Utilize com intervalos razoáveis (ex: uma vez ao dia).

Desenvolvido por Israel Teles Bandeira com o auxilio do Gemini.
