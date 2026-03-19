import streamlit as st
import json
import os

st.set_page_config(page_title="SigaaWatch Dashboard", page_icon="🎓", layout="wide")

# --- FUNÇÕES DE DADOS ---
def carregar_dados(arquivo):
    if not os.path.exists(arquivo):
        return None
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Carrega os dados oficiais do robô
dados_oficiais = carregar_dados("dados_faltas.json")

# Carrega (ou cria) o seu controlo manual
arquivo_estimativa = "estimativa_faltas.json"
dados_estimativa = carregar_dados(arquivo_estimativa) or {}

if dados_oficiais is None:
    st.warning("⚠️ Rode o `robo.py` primeiro para procurar as disciplinas do SIGAA.")
else:
    # --- QUESTIONÁRIO DIÁRIO (BARRA LATERAL) ---
    st.sidebar.header("📝 Diário de Bordo")
    st.sidebar.markdown("Chegou da UnB? Registe as suas faltas de hoje:")
    
    materias_nomes = [m['materia'] for m in dados_oficiais]
    
    # Formulário de registo manual
    with st.sidebar.form("form_faltas"):
        faltei_hoje = st.radio("Faltou a alguma aula hoje?", ["Não", "Sim"])
        materias_faltadas = st.multiselect("Se sim, a quais?", materias_nomes)
        
        if st.form_submit_button("Guardar Registo"):
            if faltei_hoje == "Sim" and materias_faltadas:
                for mat in materias_faltadas:
                    # Adiciona +1 à disciplina escolhida
                    dados_estimativa[mat] = dados_estimativa.get(mat, 0) + 1
                salvar_dados(arquivo_estimativa, dados_estimativa)
                st.sidebar.success("Faltas registadas com sucesso!")
            elif faltei_hoje == "Não":
                st.sidebar.success("Boa! Mais um dia garantido.")

    if st.sidebar.button("Zerar as minhas estimativas"):
        salvar_dados(arquivo_estimativa, {})
        st.rerun()

    # --- PAINEL PRINCIPAL ---
    st.title("🎓 O Meu Painel SigaaWatch")
    st.markdown("Comparativo entre Faltas Oficiais (SIGAA) e Faltas Estimadas (Reais).")
    st.divider()

    st.markdown("### 📊 Situação por Disciplina")
    colunas = st.columns(3) 
    
    for index, materia in enumerate(dados_oficiais):
        nome_mat = materia['materia']
        faltas_oficiais = materia.get('faltas', 0)
        
        # Pega nas faltas manuais que registou (se não houver, é 0)
        faltas_manuais = dados_estimativa.get(nome_mat, 0)
        
        # A falta REAL é a maior entre a oficial e a sua estimativa
        faltas_reais = max(faltas_oficiais, faltas_manuais)
        
        with colunas[index % 3]:
            with st.container(border=True):
                st.subheader(nome_mat.title())
                
                # Se a disciplina tiver % oficial calculada
                if materia['status'] == 'Ativo':
                    freq_oficial = materia['porcentagem']
                    # Recalcula a % baseada na sua estimativa (aproximação simples)
                    total_aulas = materia['total']
                    if total_aulas > 0:
                        freq_real = ((materia['presencas'] - (faltas_reais - faltas_oficiais)) / total_aulas) * 100
                    else:
                        freq_real = freq_oficial

                    # Cores baseadas na estimativa REAL
                    if freq_real >= 85: 
                        st.success(f"🟢 Seguro (Freq. Real: {freq_real:.1f}%)")
                    elif freq_real >= 75: 
                        st.warning(f"🟡 Atenção (Freq. Real: {freq_real:.1f}%)")
                    else: 
                        st.error(f"🔴 Risco! (Freq. Real: {freq_real:.1f}%)")
                else:
                    st.info(f"ℹ️ {materia['mensagem']}")

                # Métricas lado a lado
                m_col1, m_col2 = st.columns(2)
                m_col1.metric("Faltas SIGAA", faltas_oficiais)
                # Mostra a sua estimativa (destacada se for maior que a do SIGAA)
                delta = faltas_manuais - faltas_oficiais if faltas_manuais > faltas_oficiais else None
                m_col2.metric("A Minha Estimativa", faltas_manuais, delta=delta, delta_color="inverse")