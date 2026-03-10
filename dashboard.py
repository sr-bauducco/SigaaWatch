import streamlit as st
import json
import os

# Configuração da página para ocupar a tela toda e ter um título legal
st.set_page_config(page_title="SigaaWatch Dashboard", page_icon="🎓", layout="wide")

st.title("🎓 Meu Painel SigaaWatch")
st.markdown("Monitoramento automatizado de faltas e frequência do SIGAA.")
st.divider()

# Função para carregar os dados salvos pelo robô
def carregar_dados():
    if not os.path.exists("dados_faltas.json"):
        return None
    with open("dados_faltas.json", "r", encoding="utf-8") as f:
        return json.load(f)

dados = carregar_dados()

if dados is None:
    st.warning("⚠️ Nenhum dado encontrado. Rode o script `robo.py` primeiro para extrair as informações do SIGAA.")
else:
    # --- RESUMO GERAL ---
    materias_ativas = [d for d in dados if d['status'] == 'Ativo']
    materias_sem_chamada = [d for d in dados if d['status'] != 'Ativo']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Disciplinas", len(dados))
    col2.metric("Com Chamada Ativa", len(materias_ativas))
    col3.metric("Sem Chamada/Pendentes", len(materias_sem_chamada))
    
    st.markdown("### 📊 Situação por Matéria")
    
    # --- GRID DE MATÉRIAS ---
    # Cria colunas para colocar os "cards" das matérias lado a lado
    colunas = st.columns(3) 
    
    for index, materia in enumerate(dados):
        # Distribui os cards entre as 3 colunas
        with colunas[index % 3]:
            # Criamos um "Card" visual para cada matéria
            with st.container(border=True):
                st.subheader(materia['materia'].title())
                
                if materia['status'] == 'Ativo':
                    freq = materia['porcentagem']
                    faltas = materia['faltas']
                    
                    # Lógica de Cores baseada na regra da UnB (mínimo de 75%)
                    if freq >= 85:
                        cor_texto = "🟢 Seguro"
                        st.success(f"{cor_texto} (Frequência: {freq}%)")
                    elif freq >= 75:
                        cor_texto = "🟡 Atenção"
                        st.warning(f"{cor_texto} (Frequência: {freq}%)")
                    else:
                        cor_texto = "🔴 Risco de Reprovação"
                        st.error(f"{cor_texto} (Frequência: {freq}%)")
                    
                    # Barra de progresso visual
                    st.progress(freq / 100)
                    
                    # Métricas de faltas e presenças
                    m_col1, m_col2 = st.columns(2)
                    m_col1.metric("Faltas", faltas)
                    m_col2.metric("Presenças", materia['presencas'])
                    
                elif materia['status'] == 'Indisponível':
                    st.info("ℹ️ **Status:** " + materia['mensagem'])
                    st.markdown("*Nenhum dado numérico para exibir.*")
                    
                elif materia['status'] == 'Pendente':
                    st.info("⏳ **Status:** " + materia['mensagem'])
                    st.markdown("*Acompanhe nas próximas semanas.*")

    st.divider()
    st.caption("Dados extraídos automaticamente. Verifique sempre o SIGAA oficial em caso de dúvidas.")