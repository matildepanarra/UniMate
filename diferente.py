"""
UniMate - Financial Assistant
Streamlit app demonstrating Expense, Budget, Analytics, and AI Chat
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

# -----------------------------
# ENV + CONSTANTS
# -----------------------------
load_dotenv()

DB_FILE = db_connector.DATABASE_NAME
USER_ID = 1

# -----------------------------
# TRACING
# -----------------------------
init_tracing()

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="UniMate",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# CSS (PREMIUM UI)
# -----------------------------
st.markdown(
    """
<style>
/* Layout */
.block-container { padding-top: 2.0rem; padding-bottom: 2.2rem; max-width: 1200px; }
section[data-testid="stSidebar"] { border-right: 1px solid rgba(49,51,63,0.12); }
hr { margin: 1.15rem 0; }

/* Typography */
h1, h2, h3 { letter-spacing: -0.02em; }
.small-muted { color: rgba(49,51,63,0.62); font-size: 0.95rem; }

/* Cards */
.card {
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(49,51,63,0.12);
  border-radius: 16px;
  padding: 16px 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
}

/* Pills */
.pill {
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px;
  border: 1px solid rgba(49,51,63,0.12);
  background: rgba(240,242,246,0.65);
  font-size: 0.9rem;
  white-space: nowrap;
}

/* Buttons */
div.stButton > button {
  border-radius: 12px !important;
  padding: 0.85rem 1rem !important;
  font-weight: 650 !important;
  border: 1px solid rgba(49,51,63,0.12) !important;
}

/* Inputs */
textarea, input, div[data-baseweb="select"] > div {
  border-radius: 12px !important;
}

/* Tabs */
button[data-baseweb="tab"] {
  font-weight: 650;
  padding-top: 10px;
  padding-bottom: 10px;
}
/* FIX: remove white ghost blocks from tabs */
div[data-baseweb="tab-panel"] {
  background: transparent !important;
  padding: 0 !important;
}

div[data-baseweb="tab-list"] {
  gap: 6px;
}

div[data-baseweb="tab"] {
  background: transparent !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# INIT DB & SERVICES (FIRST LOAD ONLY)
# -----------------------------
if "services_ready" not in st.session_state:
    try:
        db_connector.initialize_database()
        conn = db_connector.create_connection(DB_FILE)

        conn.execute(
            "INSERT OR IGNORE INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
            (USER_ID, "Streamlit User", "ui@unimate.pt", datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        st.session_state.expense_service = ExpenseService(db_file=DB_FILE)
        st.session_state.budget_service = BudgetService(db_file=DB_FILE)
        st.session_state.analytics_service = AnalyticsService(db_file=DB_FILE)
        st.session_state.ai_client = AIService()

        st.session_state.services_ready = True

    except Exception as e:
        st.error(f"Critical error in initialization: {e}")
        st.error("Check db_connector.initialize_database() and db_connector.create_connection().")
        st.stop()


# -----------------------------
# HELPERS
# -----------------------------
def process_ai_expense(text: str):
    """Calls the service to process text with the AI."""
    expense_service = st.session_state.expense_service
    expense_id = expense_service.add_expense_from_document(USER_ID, text)
    if expense_id:
        return expense_service.get_expense(expense_id)
    return None


# -----------------------------
# HEADER (CLEAN)
# -----------------------------
colA, colB = st.columns([0.68, 0.32])

with colA:
    st.markdown("## 💸 **UniMate**")
    st.markdown('<div class="small-muted">AI-powered financial assistant</div>', unsafe_allow_html=True)

with colB:
    services_ok = bool(st.session_state.get("services_ready", False))
    gemini_ok = bool(getattr(st.session_state.ai_client, "client", None))

    st.markdown(
        f"""
        <div style="display:flex; gap:10px; justify-content:flex-end; flex-wrap:wrap;">
          <span class="pill">{"Services Loaded" if services_ok else "Services Not Ready"}</span>
          <span class="pill">{"Gemini Active" if gemini_ok else "Gemini Offline"}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# -----------------------------
# SIDEBAR (NO WEIRD OUTPUT)
# -----------------------------
with st.sidebar:
    st.markdown("### Status")
    st.markdown(
        """
        <div class="card">
          <div style="display:grid; gap:10px;">
            <div class="pill">💰 Expense Tracking</div>
            <div class="pill">📊 Budget Management</div>
            <div class="pill">📈 Financial Analytics</div>
            <div class="pill">💬 AI Chat Assistant</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Configuration")
    services_ready = st.session_state.get("services_ready", False)
    gemini_active = bool(getattr(st.session_state.ai_client, "client", None))

    st.markdown('<div class="card">', unsafe_allow_html=True)
    if services_ready:
        st.success("Services Loaded")
    else:
        st.error("Error in Initialization")

    if gemini_active:
        st.success("Gemini Client Active")
    else:
        st.error("Gemini Client OFFLINE")
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["💰 Expenses (AI)", "📊 Budgets", "📈 Analytics", "🤖 AI Assistant"])

# ----------------------------------------
# TAB 1: EXPENSES (AI)
# ----------------------------------------
with tab1:
    st.markdown("### Expense Tracking (AI)")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("**Transaction text**")
    ai_input = st.text_area(
        label="",
        height=170,
        placeholder="Paste the receipt or statement text…",
        key="ai_input_tab1",
    )

    left, right = st.columns([0.72, 0.28])
    with left:
        st.caption("Tip: include date, merchant and total to improve extraction accuracy.")
    with right:
        run = st.button("✨ Process with AI and Save", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if run:
        if not ai_input.strip():
            st.warning("Please enter the text.")
        else:
            with st.spinner("Processing (Extraction, Classification and Observability)…"):
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
    st.markdown("### Budget Management")

    budget_service = st.session_state.budget_service
    expense_service = st.session_state.expense_service

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**1) Set monthly limit**")

    categories = expense_service.valid_categories
    c1, c2 = st.columns(2)
    category = c1.selectbox("Category:", categories, key="budget_cat_select_tab2")
    amount_limit = c2.number_input(f"Monthly Limit for {category} (€)", min_value=0.0, step=10.0)

    if st.button("Save Budget", key="save_budget_btn_tab2", use_container_width=True):
        budget_service.set_budget(USER_ID, category, amount_limit)
        st.success(f"Limit of €{amount_limit:.2f} set for {category}.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**2) Current status and AI analysis**")

    status_report = budget_service.get_budget_status(USER_ID)
    if status_report:
        st.dataframe(pd.DataFrame(status_report), use_container_width=True)

        if st.button("Generate AI Analysis of Budget", key="analyze_budget_tab2", use_container_width=True):
            with st.spinner("AI is analyzing the history and budget…"):
                analysis_result = budget_service.analyze_budget(USER_ID)
            st.info("AI Recommendation:")
            st.write(analysis_result.get("recommendation", "No recommendation could be generated."))
    else:
        st.info("No active budget found.")

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------
# TAB 3: ANALYTICS
# ----------------------------------------
with tab3:
    st.markdown("### Financial Analytics")

    analytics_service = st.session_state.analytics_service
    summary = analytics_service.summarize_expense(USER_ID)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Expense summary**")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Spent (Lifetime)", f"R$ {summary.get('total_spent_lifetime', 0.0):.2f}")
    m2.metric("Total Transactions", summary.get("transaction_count", 0))
    m3.metric("Average Value", f"R$ {summary.get('avg_transaction_value', 0.0):.2f}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Distribution by category**")

    breakdown = analytics_service.get_category_breakdown(USER_ID)
    if breakdown.get("total_spent_lifetime", 0) > 0:
        data_list = [
            {"Category": cat, "Amount": data["total"]}
            for cat, data in breakdown.items()
            if cat != "total_spent_lifetime"
        ]
        df = pd.DataFrame(data_list)
        st.bar_chart(df, x="Category", y="Amount")

        st.markdown("---")
        st.markdown("**Anomaly alert**")
        anomalies = analytics_service.detect_anomalies(USER_ID)
        if anomalies:
            st.warning(f"{len(anomalies)} Anomalous expenses detected.")
            st.dataframe(pd.DataFrame(anomalies), use_container_width=True)
        else:
            st.success("No anomalous expenses detected.")
    else:
        st.info("Add expenses to see the analysis.")

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------
# TAB 4: AI ASSISTANT (CHAT)
# ----------------------------------------
with tab4:
    st.markdown("### AI Assistant (Chat)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    ai_client = st.session_state.ai_client
    analytics_service = st.session_state.analytics_service
    budget_service = st.session_state.budget_service

    context_data = {
        "summary": analytics_service.summarize_expense(USER_ID),
        "budget_status": budget_service.get_budget_status(USER_ID),
    }

    st.markdown('<div class="card">', unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Ask about your expenses, budgets and trends:")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("AI is consulting your data…"):
            answer = ai_client.ai_assistant(user_input, context_data)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

    if len(st.session_state.chat_history) > 0:
        if st.button("Clean Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini")
