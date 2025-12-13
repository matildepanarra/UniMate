"""
UniMate - Financial Assistant
A Streamlit app demonstrando a integração dos serviços (Expense, Budget, Analytics)
com AI-driven data capture e Langfuse observability.
"""
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import numpy
import os
import json
# O google.genai não é necessário aqui, pois os clientes são instanciados nos serviços.

# --- Importações Corrigidas ---
# O db_connector deve estar na raiz para esta importação funcionar corretamente.
from services import db_connector 

from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.ai_service import AIService # Necessário para o assistente de chat
from utils.tracing import init_tracing

# Carregar variáveis de ambiente
load_dotenv()

# --- VARIÁVEIS DE CONFIGURAÇÃO ---
DB_FILE = db_connector.DATABASE_NAME # Usa a variável real do módulo DB
USER_ID = 1

# Inicialização de Rastreamento (Mantido)
# NOTA: Certifique-se de que utils/tracing.py existe e é funcional.
# Se falhar, comente esta linha.
init_tracing()

# --- INICIALIZAÇÃO DE STATUS E CLIENTES (Streamlit Session State) ---

# Configure page
st.set_page_config(
    page_title="UniMate - Financial Assistant",
    page_icon="💸",
    layout="wide"
)

# Inicialização da DB e dos Serviços (Executado apenas na primeira carga)
if 'services_ready' not in st.session_state:
    try:
        # 1. Inicialização da DB e Usuário
        db_connector.initialize_database() # Cria as tabelas e o ficheiro DB
        conn = db_connector.create_connection(DB_FILE) # Abre a conexão para inserir o usuário
        
        # Inserir usuário de teste
        conn.execute("INSERT OR IGNORE INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
                     (USER_ID, "Streamlit User", "ui@unimate.pt", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # 2. Instanciar e armazenar serviços
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)
        st.session_state.ai_client = AIService() # Instância correta (sem argumento DB)
        st.session_state.services_ready = True
    except Exception as e:
        st.error(f"❌ Erro Crítico na Inicialização: {e}")
        st.error("Verifique se o ficheiro 'db_connector.py' contém 'initialize_database' e 'create_connection'.")
        st.stop()


# --- ORQUESTRADOR: FUNÇÃO DE FLUXO AI ---
# Sem @traceable, conforme solicitado, mas chama os @observe internos.
def process_ai_expense(text: str):
    """Chama o serviço para processar texto com a IA."""
    expense_service = st.session_state.expense_service
    expense_id = expense_service.add_expense_from_document(USER_ID, text)
    if expense_id:
        return expense_service.get_expense(expense_id)
    return None


# --- UI PRINCIPAL ---
st.title("💸 UniMate")
st.markdown("AI-powered financial assistant.")

# Sidebar com info
with st.sidebar:
    st.header("Status")
    st.markdown("""
    Este app demonstra:
    - Expense Tracking
    - Budget Management
    - Financial Analytics
    - AI-Chat Assistant
    """)
    st.divider()

    st.subheader("Configuração")
    if st.session_state.services_ready:
        st.success("✅ Serviços Carregados")
        # Verifica a conexão com o Gemini no cliente de AI
        if st.session_state.ai_client.client:
            st.success("✅ Gemini Client Ativo")
        else:
            st.error("❌ Gemini Client OFFLINE")
    else:
        st.error("❌ Falha na Inicialização")


# Main content area - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💰 Expenses (AI)", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant"])

# ----------------------------------------
# TAB 1: EXPENSES (AI-Driven)
# ----------------------------------------
with tab1:
    st.header("Rastreamento de Despesas (AI)")
    ai_input = st.text_area("Texto da Transação:", height=150, placeholder="Cole o texto do recibo ou extrato...", key="ai_input_tab1")

    if st.button("🔍 Processar com IA e Salvar", type="primary", use_container_width=True):
        if not ai_input.strip():
            st.warning("Por favor, insira o texto.")
        else:
            with st.spinner("🧠 Processando (Extração, Classificação e Observabilidade)..."):
                new_expense = process_ai_expense(ai_input) 

            if new_expense and new_expense.get('id'):
                st.success("🎉 Despesa salva com sucesso via IA!")
                st.dataframe(pd.DataFrame([new_expense]), use_container_width=True)
            else:
                st.error("❌ Falha ao processar a despesa. Verifique os logs e a sua chave Gemini.")

# ----------------------------------------
# TAB 2: BUDGETS
# ----------------------------------------
with tab2:
    st.header("Gestão de Orçamento")
    budget_service = st.session_state.budget_service
    expense_service = st.session_state.expense_service
    
    st.subheader("1. Definir Limite Mensal")
    categories = expense_service.valid_categories 
    
    col1, col2 = st.columns(2)
    category = col1.selectbox("Categoria:", categories, key="budget_cat_select_tab2")
    amount_limit = col2.number_input(f"Limite Mensal para {category} (€)", min_value=0.0, step=10.0)

    if st.button("Salvar Orçamento", key="save_budget_btn_tab2"):
        budget_service.set_budget(USER_ID, category, amount_limit)
        st.success(f"Limite de R${amount_limit:.2f} definido para {category}.")
    
    st.divider()
    
    st.subheader("2. Status Atual e Análise de IA")
    status_report = budget_service.get_budget_status(USER_ID)
    
    if status_report:
        st.dataframe(pd.DataFrame(status_report), use_container_width=True)

        if st.button("🔍 Gerar Análise de IA do Orçamento", key="analyze_budget_tab2"):
            with st.spinner("A IA está a analisar o histórico e o orçamento..."):
                analysis_result = budget_service.analyze_budget(USER_ID)
            st.info("Recomendação da IA:")
            st.write(analysis_result.get('recommendation', 'Não foi possível gerar uma recomendação.'))
    else:
        st.info("Nenhum orçamento ativo encontrado.")


# ----------------------------------------
# TAB 3: ANALYTICS
# ----------------------------------------
with tab3:
    st.header("Analytics Financeiro")
    analytics_service = st.session_state.analytics_service
    
    # 1. Sumário Global
    summary = analytics_service.summarize_expense(USER_ID)

    st.subheader("Sumário de Gastos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Gasto Total Acumulado", f"R$ {summary.get('total_spent_lifetime', 0.0):.2f}")
    col2.metric("Total de Transações", summary.get('transaction_count', 0))
    col3.metric("Valor Médio", f"R$ {summary.get('avg_transaction_value', 0.0):.2f}")

    # 2. Distribuição e Gráfico
    st.subheader("Distribuição por Categoria")
    breakdown = analytics_service.get_category_breakdown(USER_ID)
    
    if breakdown.get('total_spent_lifetime', 0) > 0:
        data_list = [{'Categoria': cat, 'Montante': data['total']} 
                     for cat, data in breakdown.items() if cat != 'total_spent_lifetime']
        
        df = pd.DataFrame(data_list)
        st.bar_chart(df, x="Categoria", y="Montante")

        # 3. Anomalias
        st.subheader("Alerta de Anomalias")
        anomalies = analytics_service.detect_anomalies(USER_ID)
        if anomalies:
            st.warning(f"⚠️ {len(anomalies)} Despesas anómalas detectadas.")
            st.dataframe(pd.DataFrame(anomalies), use_container_width=True) 
        else:
            st.success("Nenhuma anomalia de gasto detetada.")
    else:
        st.info("Adicione despesas para ver a análise.")


# ----------------------------------------
# TAB 4: AI ASSISTANT
# ----------------------------------------
with tab4:
    st.header("Assistente AI (Chat)")
    
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
        
    ai_client = st.session_state.ai_client
    analytics_service = st.session_state.analytics_service
    budget_service = st.session_state.budget_service

    # Obter Contexto para a IA
    context_data = {
        "summary": analytics_service.summarize_expense(USER_ID),
        "budget_status": budget_service.get_budget_status(USER_ID)
    }

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]): st.write(message["content"])

    user_input = st.chat_input("Pergunte sobre seus gastos, orçamentos e tendências:")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.write(user_input)

        with st.spinner("A IA está a consultar os seus dados..."):
            answer = ai_client.ai_assistant(user_input, context_data) 

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"): st.write(answer)
        
    if len(st.session_state.chat_history) > 0:
        if st.button("🗑️ Limpar Histórico de Chat"):
            st.session_state.chat_history = []
            st.rerun()

# Footer
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini")