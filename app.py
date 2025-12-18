"""
UniMate - Financial Assistant
A Streamlit app demonstrates the integration of services (Expense, Budget, Analytics, AI)
with AI-driven data capture and Langfuse observability.
"""
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, date

# Services imports
from services import db_connector
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.ai_service import AIService
from utils.tracing import init_tracing
from ai.tools_router import TOOL_IMPL



# Loads environment variables
load_dotenv()

DB_FILE = getattr(db_connector, "DATABASE_NAME", getattr(db_connector, "DATABASE_FILE", "unimate_financial_data.db"))

# -----------------------------
# SESSION STATE DEFAULTS
# -----------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# flags to show success AFTER rerun
if "expense_saved_flag" not in st.session_state:
    st.session_state.expense_saved_flag = False
if "last_saved_expense" not in st.session_state:
    st.session_state.last_saved_expense = None

# used to force UI refresh across tabs when DB changes
if "_last_db_update" not in st.session_state:
    st.session_state["_last_db_update"] = "0"

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


def notify_db_updated():
    """Bumps a token so widgets refresh + rerun the app."""
    st.session_state["_last_db_update"] = datetime.now().isoformat()


def call_tool(tool_name: str, **kwargs):
    """
    Native tool execution (local Python functions).
    Always inject db_file.
    """
    if tool_name not in TOOL_IMPL:
        raise ValueError(f"Tool '{tool_name}' not found in TOOL_IMPL.")

    args = {"db_file": DB_FILE, **kwargs}
    return TOOL_IMPL[tool_name](**args)


# Initialize the DB and Services (Executed only on first load)
if "services_ready" not in st.session_state:
    try:
        db_connector.initialize_database()

        # keep services for the parts of the app that still depend on them
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)

        st.session_state.ai_client = AIService()
        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Verify if 'db_connector.py' contains 'initialize_database' and connection helpers.")
        st.stop()

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

# Tabs
tab0, tab_users, tab_expenses, tab_budgets, tab_analytics, tab_ai = st.tabs(
    ["Welcome!", "👤 Users", "💰 Expenses", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant"]
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
- **Expense Tracking:** Log expenses using tool calling or document ingestion.
- **Budget Management:** Set and monitor budgets per category.
- **Financial Analytics:** Visualize spending patterns and detect anomalies.
- **AI Assistant:** Chat with an AI to query and update your finances using tools.
"""
    )

# ----------------------------------------
# TAB EXPENSES
# ----------------------------------------
with tab_expenses:
    st.header("Expense Tracking")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        # show success AFTER rerun
        if st.session_state.get("expense_saved_flag"):
            st.success("Expense saved successfully!")
            last = st.session_state.get("last_saved_expense")
            if isinstance(last, dict) and last:
                st.dataframe(pd.DataFrame([last]), width='stretch')
            st.session_state.expense_saved_flag = False
            st.session_state.last_saved_expense = None

        st.subheader("Insert Information:")
        ai_input = st.text_area(
            "Transaction Text:",
            height=150,
            placeholder="Example: 'Spent 12.50€ at Starbucks on 2025-12-16 in Food'",
            key="ai_input_tab1",
        )

        if st.button("Process Text with AI and Save", type="primary", width='stretch', key="btn_text_tab1"):
            if not ai_input.strip():
                st.warning("Please enter the text.")
            else:
                with st.spinner("Processing (Extraction, Classification and Observability)..."):
                    expense_service = st.session_state.expense_service
                    ai_client = st.session_state.ai_client

                    tx = ai_client.extract_document_data(ai_input) or {}
                    amount = float(tx.get("amount", 0.0) or 0.0)
                    vendor = str(tx.get("description", "") or "").strip()
                    date_str = str(tx.get("date", "") or "").strip() or datetime.now().strftime("%Y-%m-%d")

                    if amount <= 0 or not vendor:
                        st.error("Could not extract a valid transaction (amount/description missing).")
                    else:
                        cat = str(tx.get("category", "") or "").strip()
                        if cat not in expense_service.valid_categories:
                            cat = ai_client.classify_expense(amount, vendor, expense_service.valid_categories)
                        if cat not in expense_service.valid_categories:
                            cat = "Others"

                        try:
                            expense_id = call_tool(
                                "add_expense",
                                user_id=USER_ID,
                                amount=amount,
                                category=cat,
                                vendor=vendor,
                                transaction_date=date_str,
                                notes=f"From text: {vendor}",
                            )
                        except Exception as e:
                            st.error(f"Failed to save expense: {e}")
                            expense_id = None

                        if expense_id:
                            try:
                                saved = call_tool("get_expense", expense_id=int(expense_id))
                            except Exception:
                                saved = {"id": expense_id}

                            st.session_state.expense_saved_flag = True
                            st.session_state.last_saved_expense = saved if isinstance(saved, dict) else {"id": expense_id}
                            notify_db_updated()
                            st.rerun()
                        else:
                            st.error("Failed to save expense.")

        st.divider()

        st.subheader("Document Ingestion:")
        uploaded = st.file_uploader(
            "Upload receipt/invoice (PDF, JPG, PNG):",
            type=["pdf", "jpg", "jpeg", "png"],
            key="uploader_tab1",
        )

        if st.button("Ingest Document and Save", type="primary", width='stretch', key="btn_doc_tab1"):
            if uploaded is None:
                st.warning("Please upload a PDF or image file.")
            else:
                with st.spinner("Ingesting document and saving expenses..."):
                    ai_client = st.session_state.ai_client
                    expense_service = st.session_state.expense_service

                    parsed = ai_client.ingest_document(file_bytes=uploaded.read(), mime_type=uploaded.type)

                    saved_rows = []
                    for tx in parsed.get("transactions", []) or []:
                        amount = float(tx.get("amount", 0.0) or 0.0)
                        vendor = str(tx.get("description", "") or "").strip()
                        date_str = str(tx.get("date", "") or "").strip() or datetime.now().strftime("%Y-%m-%d")

                        if amount <= 0 or not vendor:
                            continue

                        cat = ai_client.classify_expense(amount, vendor, expense_service.valid_categories)
                        if cat not in expense_service.valid_categories:
                            cat = "Others"

                        try:
                            expense_id = call_tool(
                                "add_expense",
                                user_id=USER_ID,
                                amount=amount,
                                category=cat,
                                vendor=vendor,
                                transaction_date=date_str,
                                notes=f"From document: {uploaded.type}",
                            )
                        except Exception:
                            expense_id = None

                        if expense_id:
                            try:
                                row = call_tool("get_expense", expense_id=int(expense_id))
                                if isinstance(row, dict):
                                    saved_rows.append(row)
                            except Exception:
                                saved_rows.append({"id": expense_id})

                if saved_rows:
                    st.session_state.expense_saved_flag = True
                    st.session_state.last_saved_expense = saved_rows[-1]
                    notify_db_updated()
                    st.rerun()
                else:
                    st.error("No expenses were saved from this document.")
                    st.subheader("Extracted Document Data")
                    st.json(parsed)
        st.divider()
        expense_service = st.session_state.expense_service
        st.subheader("All Expenses")

        c1, c2, c3, c4 = st.columns(4)
        f_category = c1.selectbox("Filter by category", ["(all)"] + expense_service.valid_categories, key="all_exp_cat")
        f_limit = c2.number_input("Rows to show", min_value=20, max_value=2000, value=200, step=20, key="all_exp_limit")
        f_start = c3.date_input("Start date", value=None, key="all_exp_start")
        f_end = c4.date_input("End date", value=None, key="all_exp_end")

        kwargs = {"user_id": USER_ID, "limit": int(f_limit), "offset": 0}
        if f_category != "(all)":
            kwargs["category"] = f_category
        if f_start is not None:
            kwargs["start_date"] = f_start.strftime("%Y-%m-%d")
        if f_end is not None:
            kwargs["end_date"] = f_end.strftime("%Y-%m-%d")

        
        df_key = f"all_exp_{USER_ID}_{st.session_state.get('_last_db_update','0')}"

        try:
            rows = call_tool("list_expenses", **kwargs) or []
            df = pd.DataFrame(rows)
            if not df.empty:
                st.dataframe(df, width='stretch', key=df_key)
            else:
                st.info("No expenses found for the selected filters.")
        except Exception as e:
            st.error(f"Could not load expenses: {e}")

# ----------------------------------------
# TAB BUDGETS
# ----------------------------------------
with tab_budgets:
    st.header("Budget Management")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        budget_service = st.session_state.budget_service      
        expense_service = st.session_state.expense_service

        st.subheader("Set Monthly Limit")
        categories = expense_service.valid_categories

        # month range (same logic as previous)
        today = date.today()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        end_date = next_month.strftime("%Y-%m-%d")

        col1, col2 = st.columns(2)
        category = col1.selectbox("Category:", categories, key="budget_cat_select_tab2")
        amount_limit = col2.number_input(
            f"Monthly Limit for {category} (€)",
            min_value=0.0,
            step=10.0,
            key="budget_amount_tab2"
        )

        if st.button("Save Budget", key="save_budget_btn_tab2"):
            try:
                # native DB write (tool)
                budget_id = call_tool(
                    "set_budget",
                    user_id=USER_ID,
                    category=category,
                    amount_limit=float(amount_limit),
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as e:
                budget_id = None
                st.error(f"Failed to set budget via tool: {e}")

            if budget_id:
                st.success(f"Limit of €{amount_limit:.2f} set for {category}. (id={budget_id})")
                notify_db_updated()
                st.rerun()

        st.divider()

        st.subheader("Current Status and Generate AI Analysis of Budget")

    
        df_key = f"budget_status_{USER_ID}_{st.session_state.get('_last_db_update','0')}"

        
        # status table comes from a service method (like before), but internally it can use tools/DB
        # If your budget_service.get_budget_status already works, keep it.
        status_report = budget_service.get_budget_status(USER_ID)

        if status_report:
            st.dataframe(pd.DataFrame(status_report), width='stretch', key=df_key)

            if st.button("Generate AI Analysis of Budget", key="analyze_budget_tab2"):
                with st.spinner("AI is analyzing the history and budget..."):
                    analysis_result = budget_service.analyze_budget(USER_ID) or {}
                st.info("AI Recommendation:")
                st.write(analysis_result.get("recommendation", "No recommendation could be generated."))
        else:
            st.info("No active budget found for this month.")

        if st.button("🔄 Refresh Budget Status", key="refresh_budget_tab2"):
            notify_db_updated()
            st.rerun()

        if st.button("🗑️ Clear All Budgets", type="secondary", key="clear_budgets_btn_tab2"):
            rows_deleted = budget_service.clear_all_budgets(USER_ID)
            if rows_deleted and rows_deleted > 0:
                st.success(f"✅ {rows_deleted} budgets deleted successfully!")
            else:
                st.info("No budgets to delete or an error occurred.")
            notify_db_updated()
            st.rerun()


# ----------------------------------------
# TAB ANALYTICS
# ----------------------------------------
with tab_analytics:
    st.header("Financial Analytics")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        from typing import Any

        expense_service = st.session_state.get("expense_service", None)
        analytics_service = st.session_state.get("analytics_service", None)

        if analytics_service is None or expense_service is None:
            st.error(
                "expense_service / analytics_service is not initialized in st.session_state.\n\n"
                "Make sure you have:\n"
                "st.session_state.expense_service = ExpenseService(DB_FILE)\n"
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

            # -------------------------
            # Expense Summary 
            # -------------------------
            st.subheader("Expense Summary")
            try:
                summary = call_tool("summarize_expense", user_id=USER_ID) or {}
            except Exception as e:
                st.error(f"Error summarize_expense tool: {e}")
                summary = {}

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Spent Lifetime", f"€ {float(summary.get('total_spent_lifetime', 0.0) or 0.0):.2f}")
            col2.metric("Total Transactions", int(summary.get("transaction_count", 0) or 0))
            col3.metric("Average Value", f"€ {float(summary.get('avg_transaction_value', 0.0) or 0.0):.2f}")

            st.divider()

            # -------------------------
            # Distribution by Category (kept from old version)
            # -------------------------
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
                    st.bar_chart(df_cat, x="Category", y="Amount", width='stretch')
                    st.dataframe(df_cat, width='stretch')
                else:
                    st.info("No expenses available to generate category distribution.")
            else:
                st.info("No expenses available to generate category distribution.")

            st.divider()

            # -------------------------
            # Anomaly Alert (via native tool)
            # -------------------------
            st.subheader("Anomaly Alert")
            try:
                anomalies = call_tool("detect_anomalies", user_id=USER_ID) or []
            except Exception as e:
                st.error(f"Error detect_anomalies tool: {e}")
                anomalies = []

            if anomalies:
                df_anom = to_df(anomalies)
                st.warning(
                    f"{len(df_anom)} anomalous expenses detected."
                    if not df_anom.empty else
                    f"{len(anomalies)} anomalous expenses detected."
                )
                if not df_anom.empty:
                    st.dataframe(df_anom, width='stretch')
                else:
                    st.json(anomalies)
            else:
                st.success("No anomalous expenses detected.")

            st.divider()

            # -------------------------
            # Spending Trend
            # -------------------------
            st.subheader("Spending Trend")
            try:
                trend = call_tool("get_spending_trend", user_id=USER_ID) or []
            except Exception as e:
                st.error(f"Error get_spending_trend tool: {e}")
                trend = []

            df_trend = to_df(trend)
            if not df_trend.empty and "year_month" in df_trend.columns and "total_spent" in df_trend.columns:
                st.line_chart(df_trend, x="year_month", y="total_spent", width='stretch')
                st.dataframe(df_trend, width='stretch')
            else:
                st.info("No trend data available.")

            # Optional refresh button (nice for UI parity)
            if st.button("🔄 Refresh Analytics", key="refresh_analytics_tab3"):
                notify_db_updated()
                st.rerun()

# ----------------------------------------
# TAB AI ASSISTANT 
# ----------------------------------------
with tab_ai:
    st.header("AI Assistant (Chat)")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        ai_client = st.session_state.ai_client

        # show history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_input = st.chat_input("Ask about your expenses, budgets and trends (can also add/save via tools):")

        if user_input:
            # store user message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            with st.spinner("AI is thinking ..."):
                out = ai_client.ai_chat(
                    user_text=user_input,
                    db_file= DB_FILE,
                    user_id= USER_ID,
                    history = st.session_state.chat_history[:-1],
                )

                answer = out.get("answer") or "..."

                if out.get("db_updated"):
                    notify_db_updated()

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)

            st.rerun()

        if len(st.session_state.chat_history) > 0:
            if st.button("Clean Chat History"):
                st.session_state.chat_history = []
                st.rerun()

# ----------------------------------------
# TAB USER/PROFILE (LOGIN / REGISTER / LOGOUT)
# ----------------------------------------
with tab_users:
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

        else:
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
st.caption("Built using Streamlit and Google Gemini")

