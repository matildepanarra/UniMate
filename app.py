"""
UniMate - Financial Assistant
A Streamlit app demonstrando a integração dos serviços (Expense, Budget, Analytics)
com AI-driven data capture e Langfuse observability.
"""
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os



DB_FILE = "unimate_financial_data.db"
USER_ID = 1  # Simulação de um único usuário para este exemplo

# --- Importação de Serviços e Utilitários ---
# NOTA: Importamos as classes dos serviços, não os módulos diretamente.
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.ai_service import AIService # Necessário para o assistente de chat
from services import db_connector # Para inicializar a DB
from utils.tracing import init_tracing

# Initialize tracing (Week 7 - Langfuse)
init_tracing()

# Configure page
st.set_page_config(
    page_title="UniMate - Financial Assistant",
    page_icon="💸",
    layout="wide"
)

# Initialize service in session state
if 'expense_service' not in st.session_state:
    st.session_state.expense_service = ExpenseService(DB_FILE)
if 'budget_service' not in st.session_state:
    st.session_state.budget_service = BudgetService(DB_FILE)
if 'analytics_service' not in st.session_state:
    st.session_state.analytics_service = AnalyticsService(DB_FILE)
if 'ai_service' not in st.session_state:
    st.session_state.ai_service = AIService(DB_FILE)



def process_ai_expense(text: str):
    """Chama o serviço para processar texto com a IA."""
    expense_service = st.session_state.expense_service
    
    # Esta chamada executa o @observe aninhado em add_expense_from_document
    expense_id = expense_service.add_expense_from_document(USER_ID, text)
    if expense_id:
        return expense_service.get_expense(expense_id)
    return None

    # Main header
st.title("💸 UniMate")
st.markdown("AI-powered financial assistant.")

# Sidebar with info
with st.sidebar:
    st.header("About")
    st.markdown("""
    This app demonstrates:
    - Expense Tracking
    - Budget Management
    - Financial Analytics
    - AI-Chat Assistant
    """)

    st.divider()

    st.subheader("SLA Response Times")
    st.markdown("""
    - **Critical:** 4 hours
    - **High:** 24 hours
    - **Medium:** 48 hours
    - **Low:** 72 hours
    """)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["💰 Expenses", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant"])

with tab1:
    st.header("Expense Tracking")
with tab2:
    st.header("Budgets")
with tab3:
    st.header("Analytics")
with tab4:
    st.header("AI Chat Assistant")
    


# Footer
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini")