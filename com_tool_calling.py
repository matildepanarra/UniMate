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

# ✅ Tool calling (router + schemas)
from ai.tool_schemas import TOOLS
from ai.tool_router import execute_tool

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

# ✅ flags to show success AFTER rerun
if "expense_saved_flag" not in st.session_state:
    st.session_state.expense_saved_flag = False
if "last_saved_expense" not in st.session_state:
    st.session_state.last_saved_expense = None

# ✅ used to force UI refresh across tabs when DB changes
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

def tool_args(**kwargs):
    """
    Helper: always inject db_file in tool arguments (your schema requires it).
    """
    return {"db_file": DB_FILE, **kwargs}

# Initialize the DB and Services (Executed only on first load)
if "services_ready" not in st.session_state:
    try:
        db_connector.initialize_database()

        # ✅ keep services for the parts of the app that still depend on them
        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)

        st.session_state.ai_client = AIService()
        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Verify if 'db_connector.py' contains 'initialize_database' and connection helpers.")
        st.stop()

# -------------------------------------------------------------------
# TOOL-CALLING ORCHESTRATION HELPERS (local to Streamlit)
# -------------------------------------------------------------------
def run_tools_from_model(tool_calls):
    """
    Executes tool calls (list of {"name":..,"arguments":..}) using your tool_router.
    Ensures db_file is present.
    Returns list of tool results.
    """
    results = []
    for tc in tool_calls or []:
        name = tc.get("name")
        args = tc.get("arguments") or {}

        # guarantee db_file exists (schema requires it)
        if "db_file" not in args:
            args["db_file"] = DB_FILE

        try:
            out = execute_tool(name, args)
            results.append({"name": name, "ok": True, "result": out, "arguments": args})
        except Exception as e:
            results.append({"name": name, "ok": False, "error": str(e), "arguments": args})
    return results

def has_db_side_effect(tool_results):
    """
    crude heuristic: these tools write to DB
    """
    for r in tool_results or []:
        if r.get("ok") and r.get("name") in {"add_expense", "set_budget"}:
            return True
    return False

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
- AI-Chat Assistant (Tool Calling)
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
- **Expense Tracking:** Log expenses using tool calling or document ingestion.
- **Budget Management:** Set and monitor budgets per category.
- **Financial Analytics:** Visualize spending patterns and detect anomalies.
- **AI Assistant:** Chat with an AI to query and update your finances using tools.
"""
    )

# ----------------------------------------
# TAB 1: EXPENSES  (tool calling-friendly)
# ----------------------------------------
with tab1:
    st.header("Expense Tracking")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        # ✅ show success AFTER rerun
        if st.session_state.get("expense_saved_flag"):
            st.success("Expense saved successfully!")
            last = st.session_state.get("last_saved_expense")
            if isinstance(last, dict) and last:
                st.dataframe(pd.DataFrame([last]), use_container_width=True)
            st.session_state.expense_saved_flag = False
            st.session_state.last_saved_expense = None

        st.subheader("Insert Information (Tool Calling):")
        ai_input = st.text_area(
            "Transaction Text:",
            height=150,
            placeholder="Example: 'Spent 12.50€ at Starbucks on 2025-12-16 in Food'",
            key="ai_input_tab1",
        )

        # NOTE: here we still use your AI extraction/classification pipeline,
        # then we SAVE via the tool 'add_expense' so everything matches tool calling.
        if st.button("Process Text with AI and Save (via Tool)", type="primary", use_container_width=True, key="btn_text_tab1"):
            if not ai_input.strip():
                st.warning("Please enter the text.")
            else:
                with st.spinner("Extracting + categorizing..."):
                    expense_service = st.session_state.expense_service
                    ai_client = st.session_state.ai_client

                    # Use your compat extractor to get 1 tx
                    tx = ai_client.extract_document_data(ai_input) or {}
                    amount = float(tx.get("amount", 0.0) or 0.0)
                    vendor = str(tx.get("description", "") or "").strip()
                    date_str = str(tx.get("date", "") or "").strip() or datetime.now().strftime("%Y-%m-%d")

                    if amount <= 0 or not vendor:
                        st.error("Could not extract a valid transaction (amount/description missing).")
                    else:
                        # choose category (AI classify)
                        cat = str(tx.get("category", "") or "").strip()
                        if cat not in expense_service.valid_categories:
                            cat = ai_client.classify_expense(amount, vendor, expense_service.valid_categories)

                        if cat not in expense_service.valid_categories:
                            cat = "Others"

                        # ✅ save via TOOL
                        expense_id = execute_tool("add_expense", tool_args(
                            user_id=USER_ID,
                            amount=amount,
                            category=cat,
                            vendor=vendor,
                            transaction_date=date_str,
                            notes=f"From text: {vendor}"
                        ))

                        if expense_id:
                            # fetch saved row via TOOL
                            saved = execute_tool("get_expense", tool_args(expense_id=int(expense_id)))

                            st.session_state.expense_saved_flag = True
                            st.session_state.last_saved_expense = saved if isinstance(saved, dict) else {"id": expense_id}
                            notify_db_updated()
                            st.rerun()
                        else:
                            st.error("Failed to save expense via tool. Check logs.")

        st.divider()

        st.subheader("Document Ingestion (AI parse -> save via Tool):")
        uploaded = st.file_uploader(
            "Upload receipt/invoice (PDF, JPG, PNG):",
            type=["pdf", "jpg", "jpeg", "png"],
            key="uploader_tab1"
        )

        if st.button("Ingest Document and Save (via Tools)", type="primary", use_container_width=True, key="btn_doc_tab1"):
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

                        expense_id = execute_tool("add_expense", tool_args(
                            user_id=USER_ID,
                            amount=amount,
                            category=cat,
                            vendor=vendor,
                            transaction_date=date_str,
                            notes=f"From document: {uploaded.type}"
                        ))

                        if expense_id:
                            row = execute_tool("get_expense", tool_args(expense_id=int(expense_id)))
                            if isinstance(row, dict):
                                saved_rows.append(row)

                if saved_rows:
                    st.session_state.expense_saved_flag = True
                    st.session_state.last_saved_expense = saved_rows[-1]
                    notify_db_updated()
                    st.rerun()
                else:
                    st.error("No expenses were saved from this document.")
                    st.subheader("Extracted Document Data (debug)")
                    st.json(parsed)

# ----------------------------------------
# TAB 2: BUDGETS  (use tool set_budget + tool budget_calculator)
# ----------------------------------------
with tab2:
    st.header("Budget Management")

    USER_ID = get_user_id()
    if USER_ID is None:
        st.info("Please login in the Profile tab to continue.")
    else:
        expense_service = st.session_state.expense_service

        st.subheader("Set Monthly Limit (via Tool)")
        categories = expense_service.valid_categories

        # month range
        today = date.today()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        # next month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        end_date = next_month.strftime("%Y-%m-%d")

        col1, col2 = st.columns(2)
        category = col1.selectbox("Category:", categories, key="budget_cat_select_tab2")
        amount_limit = col2.number_input(f"Monthly Limit for {category} (€)", min_value=0.0, step=10.0)

        if st.button("Save Budget", key="save_budget_btn_tab2"):
            budget_id = execute_tool("set_budget", tool_args(
                user_id=USER_ID,
                category=category,
                amount_limit=float(amount_limit),
                start_date=start_date,
                end_date=end_date
            ))
            if budget_id:
                st.success(f"Budget saved (id={budget_id}). Limit €{amount_limit:.2f} for {category}.")
                notify_db_updated()
                st.rerun()
            else:
                st.error("Failed to set budget via tool. Check logs.")

        st.divider()

        st.subheader("Current Status (via Tool)")
        df_key = f"budget_status_{USER_ID}_{st.session_state.get('_last_db_update','0')}"

        status_report = execute_tool("budget_calculator", tool_args(
            user_id=USER_ID,
            start_date=start_date,
            end_date=end_date
        ))

        if status_report:
            st.dataframe(pd.DataFrame(status_report), use_container_width=True, key=df_key)
        else:
            st.info("No active budget found for this month.")

        if st.button("🔄 Refresh Budget Status", key="refresh_budget_tab2"):
            notify_db_updated()
            st.rerun()

# ----------------------------------------
# TAB 3: ANALYTICS  (kept as-is, depends on services)
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
                "Make sure you have:\n"
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
                # You HAVE a tool for summarize_expense; use it to stay consistent
                summary = execute_tool("summarize_expense", tool_args(user_id=USER_ID)) or {}
            except Exception as e:
                st.error(f"Error summarize_expense tool: {e}")
                summary = {}

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Spent Lifetime", f"€ {float(summary.get('total_spent_lifetime', 0.0) or 0.0):.2f}")
            col2.metric("Total Transactions", int(summary.get("transaction_count", 0) or 0))
            col3.metric("Average Value", f"€ {float(summary.get('avg_transaction_value', 0.0) or 0.0):.2f}")

            st.divider()

            st.subheader("Anomaly Alert (via Tool)")
            try:
                anomalies = execute_tool("detect_anomalies", tool_args(user_id=USER_ID)) or []
            except Exception as e:
                st.error(f"Error detect_anomalies tool: {e}")
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

            st.subheader("Spending Trend (via Tool)")
            try:
                trend = execute_tool("get_spending_trend", tool_args(user_id=USER_ID)) or []
            except Exception as e:
                st.error(f"Error get_spending_trend tool: {e}")
                trend = []

            df_trend = to_df(trend)
            if not df_trend.empty and "year_month" in df_trend.columns and "total_spent" in df_trend.columns:
                st.line_chart(df_trend, x="year_month", y="total_spent", use_container_width=True)
                st.dataframe(df_trend, use_container_width=True)
            else:
                st.info("No trend data available.")

# ----------------------------------------
# TAB 4: AI ASSISTANT (tool calling via your router/schema)
# ----------------------------------------
with tab4:
    st.header("AI Assistant (Chat) — Tool Calling")

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
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # ✅ This assumes your AIService exposes ONE method that returns tool_calls OR text.
            # If your AIService doesn't yet, you need to add it (I can paste the exact code next).
            with st.spinner("AI is thinking (tool calling)..."):
                # expected dict:
                # { "text": "...", "tool_calls": [ {"name":"add_expense","arguments":{...}}, ... ] }
                model_out = ai_client.chat_with_tools(user_input, tools=TOOLS, user_id=USER_ID)

            tool_calls = model_out.get("tool_calls") or []
            if tool_calls:
                tool_results = run_tools_from_model(tool_calls)

                # If DB changed, refresh other tabs
                if has_db_side_effect(tool_results):
                    notify_db_updated()

                # Ask model to produce final response using tool results
                with st.spinner("Finalizing response..."):
                    final_text = ai_client.finalize_with_tool_results(
                        user_input,
                        tool_calls=tool_calls,
                        tool_results=tool_results
                    )
                answer = final_text or "Done."
            else:
                answer = model_out.get("text") or "..."

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)

            # refresh if DB changed
            if st.session_state.get("_last_db_update") != "0":
                st.rerun()

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
st.caption("Built with ❤️ using Streamlit and Google Gemini")
