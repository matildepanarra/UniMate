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

# ✅ Works whether your db_connector exposes DATABASE_NAME or DATABASE_FILE
DB_FILE = getattr(db_connector, "DATABASE_NAME", getattr(db_connector, "DATABASE_FILE", "unimate_financial_data.db"))
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

        # 2. Store services in session state (ALIGNED WITH SERVICES)
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)

        st.session_state.ai_client = AIService()  # ✅ AIService uses ai_assistant_tool internally
        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Verify if the file 'db_connector.py' contains 'initialize_database' and 'create_connection'.")
        st.stop()


# --- ORCHESTRATION: FUNCTION OF AI FLOW (TEXT) ---
def process_ai_expense(text: str):
    """Calls the service to process text with the AI."""
    expense_service = st.session_state.expense_service
    expense_id = expense_service.add_expense_from_document(USER_ID, text)
    if expense_id: 
        return expense_service.get_expense(expense_id)
    return None


# --- ORCHESTRATION: DOCUMENT INGESTION (PDF/IMAGE) ---
def process_ai_document(file_bytes: bytes, mime_type: str):
    """
    Uses AIService.ingest_document() and saves each extracted transaction using ExpenseService.add_expense().
    Returns list of saved expense dicts (via get_expense).
    """
    ai_client = st.session_state.ai_client
    expense_service = st.session_state.expense_service

    parsed = ai_client.ingest_document(file_bytes=file_bytes, mime_type=mime_type)

    saved = []
    for tx in parsed.get("transactions", []) or []:
        amount = float(tx.get("amount", 0.0) or 0.0)
        description = str(tx.get("description", "") or "").strip()
        date_str = str(tx.get("date", "") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if amount <= 0 or not description:
            continue

        # classify using the same logic you use in add_expense_from_document
        category_raw = expense_service.ai_client.classify_expense(
            amount=amount,
            description=description,
            categories_list=expense_service.valid_categories
        )
        final_category = (category_raw or "").split("\n")[0].strip()
        if final_category not in expense_service.valid_categories:
            final_category = "Others"

        expense_id = expense_service.add_expense(
            user_id=USER_ID,
            amount=amount,
            description=description,
            date_str=date_str,
            category=final_category
        )

        if expense_id:
            saved.append(expense_service.get_expense(expense_id))

    return parsed, saved


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
# TAB 1: EXPENSES (AI-Driven) + DOCUMENT INGESTION
# ----------------------------------------
with tab1:
    st.header("Expense Tracking (AI)")

    st.subheader("A) Paste Text")
    ai_input = st.text_area(
        "Transaction Text:",
        height=150,
        placeholder="Paste the receipt or statement text...",
        key="ai_input_tab1",
    )

    if st.button("Process Text with AI and Save", type="primary", use_container_width=True, key="btn_text_tab1"):
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

    st.divider()

    st.subheader("B) Document Ingestion (PDF / Image)")
    uploaded = st.file_uploader(
        "Upload receipt/invoice (PDF, JPG, PNG):",
        type=["pdf", "jpg", "jpeg", "png"],
        key="uploader_tab1"
    )

    if st.button("Ingest Document and Save", type="primary", use_container_width=True, key="btn_doc_tab1"):
        if uploaded is None:
            st.warning("Please upload a PDF or image file.")
        else:
            with st.spinner("Ingesting document and saving expenses..."):
                parsed, saved = process_ai_document(uploaded.read(), uploaded.type)

            if saved:
                st.success(f"Saved {len(saved)} expense(s) from document!")
                st.subheader("Saved Expenses")
                st.dataframe(pd.DataFrame(saved), use_container_width=True)
            else:
                st.error("No expenses were saved from this document.")

            st.subheader("Extracted Document Data (debug)")
            st.json(parsed)


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
            st.write(analysis_result.get('recommendation', 'No recommendation could be generated.'))
    else:
        st.info("No active budget found.")


# ----------------------------------------
# TAB 3: ANALYTICS (EXPENSE TOOLS + CHARTS)
# ----------------------------------------
with tab3:
    st.header("Financial Analytics")

    import pandas as pd  # garante que existe aqui
    from typing import Any

    expense_service = st.session_state.get("expense_service", None)
    analytics_service = st.session_state.get("analytics_service", None)

    if analytics_service is None:
        st.error(
            "analytics_service não está inicializado no st.session_state.\n\n"
            "Garante que tens algo tipo:\n"
            "st.session_state.analytics_service = AnalyticsService(DB_FILE)"
        )
        st.stop()

    if expense_service is None:
        st.warning(
            "expense_service não está inicializado no st.session_state. "
            "A parte de lookup por ID pode não funcionar."
        )

    def to_df(rows: Any) -> pd.DataFrame:
        if rows is None:
            return pd.DataFrame()
        if isinstance(rows, pd.DataFrame):
            return rows
        if isinstance(rows, dict):
            return pd.DataFrame([rows])
        if isinstance(rows, list):
            if len(rows) == 0:
                return pd.DataFrame()
            if isinstance(rows[0], dict):
                return pd.DataFrame(rows)
            try:
                return pd.DataFrame([dict(r) for r in rows])
            except Exception:
                return pd.DataFrame(rows)
        try:
            return pd.DataFrame([dict(rows)])
        except Exception:
            return pd.DataFrame()

    st.subheader("Expense Summary")
    try:
        summary = expense_service.summarize_expense(USER_ID) or {}
    except Exception as e:
        st.error(f"Erro em expense_service.summarize_expense: {e}")
        summary = {}

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spent Lifetime", f"€ {float(summary.get('total_spent_lifetime', 0.0) or 0.0):.2f}")
    col2.metric("Total Transactions", int(summary.get("transaction_count", 0) or 0))
    col3.metric("Average Value", f"€ {float(summary.get('avg_transaction_value', 0.0) or 0.0):.2f}")

    st.divider()

    st.subheader("Distribution by Category")
    try:
        breakdown = analytics_service.get_category_breakdown(USER_ID) or {}
    except Exception as e:
        st.error(f"Erro em analytics_service.get_category_breakdown: {e}")
        breakdown = {}

    total_lifetime = float(breakdown.get("total_spent_lifetime", 0.0) or 0.0)

    if total_lifetime > 0:
        data_list = []
        for cat, data in breakdown.items():
            if cat == "total_spent_lifetime":
                continue
            if isinstance(data, dict):
                data_list.append({"Category": cat, "Amount": float(data.get("total", 0.0) or 0.0)})
            else:
                data_list.append({"Category": str(cat), "Amount": 0.0})

        df_cat = pd.DataFrame(data_list).sort_values("Amount", ascending=False)
        if not df_cat.empty:
            st.bar_chart(df_cat, x="Category", y="Amount", use_container_width=True)
            st.dataframe(df_cat, use_container_width=True)
        else:
            st.info("No expenses available to generate category distribution.")
    else:
        st.info("No expenses available to generate category distribution.")

    st.divider()

    st.subheader("Anomaly Alert")
    try:
        anomalies = analytics_service.detect_anomalies(USER_ID) or []
    except Exception as e:
        st.error(f"Erro em analytics_service.detect_anomalies: {e}")
        anomalies = []

    if anomalies:
        df_anom = to_df(anomalies)
        st.warning(f"{len(df_anom)} anomalous expenses detected." if not df_anom.empty else f"{len(anomalies)} anomalous expenses detected.")
        if not df_anom.empty:
            st.dataframe(df_anom, use_container_width=True)
        else:
            st.json(anomalies)
    else:
        st.success("No anomalous expenses detected.")

    st.divider()

    st.subheader("Lookup Expense by ID")
    expense_id_lookup = st.number_input(
        "Expense ID",
        min_value=1,
        step=1,
        key="expense_id_lookup_tab3"
    )

    if st.button("Fetch Expense", key="fetch_expense_tab3"):
        if expense_service is None:
            st.error("expense_service não está disponível no session_state.")
        else:
            expense = None
            try:
                expense = expense_service.get_expense(int(expense_id_lookup))
            except Exception as e:
                st.error(f"Erro em expense_service.get_expense: {e}")

            if expense:
                st.success("Expense found:")
                if isinstance(expense, dict):
                    st.json(expense)
                else:
                    try:
                        st.json(dict(expense))
                    except Exception:
                        st.write(expense)
            else:
                st.warning("No expense found with that ID.")

    st.caption(
        "This tab uses AnalyticsService (summarize_expense, get_category_breakdown, detect_anomalies) "
        "and ExpenseService (get_expense)."
    )


# ----------------------------------------
# TAB 4: AI ASSISTANT
# ----------------------------------------
with tab4:
    st.header("AI Assistant (Chat)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    ai_client = st.session_state.ai_client
    budget_service = st.session_state.budget_service
    expense_service = st.session_state.expense_service

    context_data = {
        "summary": expense_service.summarize_expense(USER_ID),
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
