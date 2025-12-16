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

DB_FILE = getattr(db_connector, "DATABASE_NAME", getattr(db_connector, "DATABASE_FILE", "unimate_financial_data.db"))

# Session state defaults
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# --- INITIALIZE TRACING/OBSERVABILITY ---
init_tracing()

# Configure page
st.set_page_config(
    page_title="UniMate - Financial Assistant",
    page_icon="💸",
    layout="wide"
)

def get_user_id():
    """Return logged user_id or None. (Do NOT stop the app)"""
    user_id = st.session_state.get("user_id")
    return int(user_id) if user_id is not None else None

# Initialize the DB and Services (Executed only on first load)
if "services_ready" not in st.session_state:
    try:
        # 1. Initialize the DB (no hardcoded user insert!)
        db_connector.initialize_database()

        # 2. Store services in session state
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)

        st.session_state.ai_client = AIService()
        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Verify if 'db_connector.py' contains 'initialize_database' and connection helpers.")
        st.stop()

# --- ORCHESTRATION: FUNCTION OF AI FLOW (TEXT) ---
def process_ai_expense(user_id: int, text: str):
    """Calls the service to process text with the AI."""
    expense_service = st.session_state.expense_service
    expense_id = expense_service.add_expense_from_document(user_id, text)
    if expense_id:
        return expense_service.get_expense(expense_id)
    return None

# --- ORCHESTRATION: DOCUMENT INGESTION ---
def process_ai_document(user_id: int, file_bytes: bytes, mime_type: str):
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

        category_raw = expense_service.ai_client.classify_expense(
            amount=amount,
            description=description,
            categories_list=expense_service.valid_categories
        )
        final_category = (category_raw or "").split("\n")[0].strip()
        if final_category not in expense_service.valid_categories:
            final_category = "Others"

        expense_id = expense_service.add_expense(
            user_id=user_id,
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
    st.markdown(
        """
This app demonstrates:
- Expense Tracking
- Budget Management
- Financial Analytics
- AI-Chat Assistant
"""
    )
    st.divider()

    st.subheader("Configurations")
    if st.session_state.get("services_ready"):
        st.success("Services Loaded")
        if getattr(st.session_state.ai_client, "client", None):
            st.success("Gemini Client Active")
        else:
            st.error("Gemini Client OFFLINE")
    else:
        st.error("Error in Initialization")

# Main content area - Tabs
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Welcome!", "💰 Expenses", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant", "👤 Profile"]
)

# ----------------------------------------
# TAB 0: WELCOME
# ----------------------------------------
with tab0:
    st.header("Welcome to UniMate!")
    st.markdown(
        """
UniMate is your AI-powered financial assistant that helps you track expenses, manage budgets, and gain insights into your spending habits.

**Features:**
- **Expense Tracking:** Easily log your expenses using AI-powered text processing or document ingestion.
- **Budget Management:** Set and monitor budgets for different categories.
- **Financial Analytics:** Visualize your spending patterns and detect anomalies.
- **AI Assistant:** Chat with an AI to get insights about your finances.

Navigate through the tabs to explore each feature!
"""
    )

# ----------------------------------------
# TAB 1: EXPENSES
# ----------------------------------------
with tab1:
    st.header("Expense Tracking")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        st.subheader("Insert Information:")
        ai_input = st.text_area(
            "Transaction Text:",
            height=150,
            placeholder="Paste the receipt or statement text about expense...",
            key="ai_input_tab1",
        )

        if st.button("Process Text with AI and Save", type="primary", use_container_width=True, key="btn_text_tab1"):
            if not ai_input.strip():
                st.warning("Please enter the text.")
            else:
                with st.spinner("Processing (Extraction, Classification and Observability)..."):
                    new_expense = process_ai_expense(USER_ID, ai_input)

                if new_expense and isinstance(new_expense, dict) and new_expense.get("id"):
                    st.success("Expense saved successfully via AI!")
                    st.dataframe(pd.DataFrame([new_expense]), use_container_width=True)
                else:
                    st.error("Failed to process the expense. Check logs and your Gemini key.")

        st.divider()

        st.subheader("Document Ingestion:")
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
                    parsed, saved = process_ai_document(USER_ID, uploaded.read(), uploaded.type)

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

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        budget_service = st.session_state.budget_service
        expense_service = st.session_state.expense_service

        st.subheader("Set Monthly Limit")
        categories = expense_service.valid_categories

        col1, col2 = st.columns(2)
        category = col1.selectbox("Category:", categories, key="budget_cat_select_tab2")
        amount_limit = col2.number_input(f"Monthly Limit for {category} (€)", min_value=0.0, step=10.0)

        if st.button("Save Budget", key="save_budget_btn_tab2"):
            budget_service.set_budget(USER_ID, category, amount_limit)
            st.success(f"Limit of €{amount_limit:.2f} set for {category}.")

        st.divider()

        st.subheader("Current Status and Generate AI Analysis of Budget")
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

        confirm_clear = st.button("🗑️ Clear All Budgets", type="secondary", key="clear_budgets_btn_tab2")
        if confirm_clear:
            rows_deleted = budget_service.clear_all_budgets(USER_ID)
            if rows_deleted > 0:
                st.success(f"✅ {rows_deleted} budgets deleted successfully!")
            else:
                st.info("No budgets to delete or an error occurred.")
            st.rerun()

# ----------------------------------------
# TAB 3: ANALYTICS
# ----------------------------------------
with tab3:
    st.header("Financial Analytics")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        from typing import Any

        expense_service = st.session_state.get("expense_service", None)
        analytics_service = st.session_state.get("analytics_service", None)

        if analytics_service is None:
            st.error(
                "analytics_service is not initialized in st.session_state.\n\n"
                "Make sure you have something like:\n"
                "st.session_state.analytics_service = AnalyticsService(DB_FILE)"
            )
        else:
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
                st.error(f"Error in expense_service.summarize_expense: {e}")
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
                st.error(f"Error in analytics_service.get_category_breakdown: {e}")
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
                st.error(f"Error in analytics_service.detect_anomalies: {e}")
                anomalies = []

            if anomalies:
                df_anom = to_df(anomalies)
                st.warning(
                    f"{len(df_anom)} anomalous expenses detected."
                    if not df_anom.empty else
                    f"{len(anomalies)} anomalous expenses detected."
                )
                if not df_anom.empty:
                    st.dataframe(df_anom, use_container_width=True)
                else:
                    st.json(anomalies)
            else:
                st.success("No anomalous expenses detected.")

            st.divider()

            st.subheader("Lookup Expense by ID")
            expense_id_lookup = st.number_input("Expense ID", min_value=1, step=1, key="expense_id_lookup_tab3")

            if st.button("Fetch Expense", key="fetch_expense_tab3"):
                expense = None
                try:
                    expense = expense_service.get_expense(int(expense_id_lookup))
                except Exception as e:
                    st.error(f"Error in expense_service.get_expense: {e}")

                # Safety check
                if isinstance(expense, dict) and expense.get("user_id") is not None and int(expense.get("user_id")) != USER_ID:
                    st.error("You don't have permission to view this expense.")
                    expense = None

                if expense:
                    st.success("Expense found:")
                    st.json(expense if isinstance(expense, dict) else dict(expense))
                else:
                    st.warning("No expense found with that ID.")

# ----------------------------------------
# TAB 4: AI ASSISTANT
# ----------------------------------------
with tab4:
    st.header("AI Assistant (Chat)")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
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

# ----------------------------------------
# TAB 5: USER/PROFILE (LOGIN / REGISTER / LOGOUT)
# ----------------------------------------
with tab5:
    st.header("User / Account")

    if st.session_state.user_id is None:
        mode = st.radio("Choose an option:", ["Login", "Register"], horizontal=True)

        if mode == "Login":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Login", type="primary"):
                conn = db_connector.get_connection()
                user = db_connector.authenticate_user(conn, email, password)
                conn.close()

                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.user_info = user
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        else:  # REGISTER
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm password", type="password")

            if st.button("Create account", type="primary"):
                if password != password2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        conn = db_connector.get_connection()
                        db_connector.create_user(conn, name, email, password)
                        conn.close()
                        st.success("Account created successfully! Please login.")
                    except Exception as e:
                        st.error(f"Error creating account: {e}")

    else:
        user = st.session_state.user_info or {}

        st.success(f"Logged in as {user.get('name', 'User')}")
        st.markdown("---")

        col1, col2 = st.columns(2)
        col1.metric("User ID", user.get("id", st.session_state.user_id))
        col2.metric("Email", user.get("email", ""))

        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.rerun()

# Footer
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini")
