"""
UniMate - Financial Assistant
A Streamlit app demonstrates the integration of services (Expense, Budget, Analytics, AI)
with AI-driven data capture and Langfuse observability.
"""
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Services imports
from services import db_connector
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.ai_service import AIService
from utils.tracing import init_tracing

# Loads environment variables
load_dotenv()

DB_FILE = db_connector.DATABASE_NAME
USER_ID = 1

# --- INITIALIZE TRACING/OBSERVABILITY ---
init_tracing()

# Configure page
st.set_page_config(
    page_title="UniMate - Financial Assistant",
    page_icon="💸",
    layout="wide"
)

# Initialize the DB and Services (Executed only on first load)
if "services_ready" not in st.session_state:
    try:
        # 1. Initialize the DB and User
        db_connector.initialize_database()
        conn = db_connector.create_connection(DB_FILE)

        conn.execute(
            "INSERT OR IGNORE INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
            (USER_ID, "Streamlit User", "ui@unimate.pt", datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        # 2. Store services in session state
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)

        st.session_state.ai_client = AIService()
        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Verify if the file 'db_connector.py' contains 'initialize_database' and 'create_connection'.")
        st.stop()


# --- ORQUESTRATION: FUNCTION OF AI FLOW ---
def process_ai_expense(text: str):
    """Calls the service to process text with the AI."""
    expense_service = st.session_state.expense_service
    expense_id = expense_service.add_expense_from_document(USER_ID, text)
    if expense_id:
        return expense_service.get_expense(expense_id)
    return None


# --- PRINCIPAL UI ---
st.title("💸 UniMate")
st.markdown("AI-powered financial assistant.")

# Sidebar with info
with st.sidebar:
    st.header("Status")
    st.markdown("""
    This app demonstrates:
    - Expense Tracking
    - Budget Management
    - Financial Analytics
    - AI-Chat Assistant
    """)
    st.divider()

    st.subheader("Configuração")
    if st.session_state.services_ready:
        st.success("Services Loaded")
        if st.session_state.ai_client.client:
            st.success("Gemini Client Active")
        else:
            st.error("Gemini Client OFFLINE")
    else:
        st.error("Error in Initialization")


# Main content area - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💰 Expenses (AI)", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant"])

# ----------------------------------------
# TAB 1: EXPENSES (AI-Driven)
# ----------------------------------------
with tab1:
    st.header("Expense Tracking (AI)")
    ai_input = st.text_area(
        "Transaction Text:",
        height=150,
        placeholder="Paste the receipt or statement text...",
        key="ai_input_tab1",
    )

    if st.button("Process with AI and Save", type="primary", use_container_width=True):
        if not ai_input.strip():
            st.warning("Please enter the text.")
        else:
            with st.spinner("Processing (Extraction, Classification and Observability)..."):
                new_expense = process_ai_expense(ai_input)

            if new_expense and new_expense.get("id"):
                st.success("Expense saved successfully via AI!")
                st.dataframe(pd.DataFrame([new_expense]), use_container_width=True)
            else:
                st.error("Failed to process the expense. Check logs and your Gemini key.")

# ----------------------------------------
# TAB 2: BUDGETS
# ----------------------------------------
with tab2:
    st.header("Budget Management")
    budget_service = st.session_state.budget_service
    expense_service = st.session_state.expense_service

    st.subheader("1. Set Monthly Limit")
    categories = expense_service.valid_categories

    col1, col2 = st.columns(2)
    category = col1.selectbox("Category:", categories, key="budget_cat_select_tab2")
    amount_limit = col2.number_input(f"Monthly Limit for {category} (€)", min_value=0.0, step=10.0)

    if st.button("Save Budget", key="save_budget_btn_tab2"):
        budget_service.set_budget(USER_ID, category, amount_limit)
        st.success(f"Limit of €{amount_limit:.2f} set for {category}.")

    st.divider()

    st.subheader("2. Current Status and AI Analysis")
    status_report = budget_service.get_budget_status(USER_ID)

    if status_report:
        st.dataframe(pd.DataFrame(status_report), use_container_width=True)

        if st.button("Generate AI Analysis of Budget", key="analyze_budget_tab2"):
            with st.spinner("AI is analyzing the history and budget..."):
                analysis_result = budget_service.analyze_budget(USER_ID)
            st.info("AI Recommendation:")
            st.write(analysis_result.get("recommendation", "No recommendation could be generated."))
    else:
        st.info("No active budget found.")

# ----------------------------------------
# TAB 3: ANALYTICS (USING EXPENSE SERVICE TOOLS)
# ----------------------------------------
# ----------------------------------------
# TAB 3: ANALYTICS (EXPENSE TOOLS + CHARTS)
# ----------------------------------------
with tab3:
    st.header("Financial Analytics (Expense Tools)")

    expense_service = st.session_state.expense_service
    analytics_service = st.session_state.analytics_service  # só para breakdown/anomalies

    # =========================
    # TOOL: summarize_expense
    # =========================
    summary = expense_service.summarize_expense(USER_ID)

    st.subheader("Expense Summary (via ExpenseService Tool)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spent Lifetime", f"€ {summary.get('total_spent_lifetime', 0.0):.2f}")
    col2.metric("Total Transactions", summary.get("transaction_count", 0))
    col3.metric("Average Value", f"€ {summary.get('avg_transaction_value', 0.0):.2f}")

    st.divider()

    # =========================
    # CHART: Distribution by Category
    # =========================
    st.subheader("Distribution by Category")

    breakdown = analytics_service.get_category_breakdown(USER_ID)

    if breakdown.get("total_spent_lifetime", 0) > 0:
        data_list = [
            {"Category": cat, "Amount": data["total"]}
            for cat, data in breakdown.items()
            if cat != "total_spent_lifetime"
        ]

        df = pd.DataFrame(data_list)
        st.bar_chart(df, x="Category", y="Amount")
    else:
        st.info("No expenses available to generate category distribution.")

    st.divider()

    # =========================
    # ANOMALY DETECTION
    # =========================
    st.subheader("Anomaly Alert")

    anomalies = analytics_service.detect_anomalies(USER_ID)

    if anomalies:
        st.warning(f"{len(anomalies)} anomalous expenses detected.")
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True)
    else:
        st.success("No anomalous expenses detected.")

    st.divider()

    # =========================
    # TOOL: get_expense
    # =========================
    st.subheader("Lookup Expense by ID (get_expense tool)")

    expense_id_lookup = st.number_input(
        "Expense ID",
        min_value=1,
        step=1,
        key="expense_id_lookup_tab3"
    )

    if st.button("Fetch Expense", key="fetch_expense_tab3"):
        expense = expense_service.get_expense(int(expense_id_lookup))
        if expense:
            st.success("Expense found:")
            st.json(expense)
        else:
            st.warning("No expense found with that ID.")

    st.caption(
        "This tab uses ExpenseService tools (summarize_expense, get_expense) "
        "and AnalyticsService for advanced analysis (charts & anomaly detection)."
    )

# ----------------------------------------
# TAB 4: AI ASSISTANT
# ----------------------------------------
with tab4:
    st.header("AI Assistant (Chat)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    ai_client = st.session_state.ai_client
    analytics_service = st.session_state.analytics_service
    budget_service = st.session_state.budget_service
    expense_service = st.session_state.expense_service

    # Context for the AI (uses expense tool summary + budget status)
    context_data = {
        "summary": expense_service.summarize_expense(USER_ID),  # ✅ uses tool via expense service
        "budget_status": budget_service.get_budget_status(USER_ID),
    }

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Ask about your expenses, budgets and trends:")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("AI is consulting your data..."):
            answer = ai_client.ai_assistant(user_input, context_data)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

    if len(st.session_state.chat_history) > 0:
        if st.button("Clean Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# Footer
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini")
