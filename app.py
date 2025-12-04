"""
UniMate - Customer Support Financial Assistant
A Streamlit app .......
"""

import streamlit as st
#from dotenv import load_dotenv

#Import services
from services import expense_service, budget_service, analytics_service
#from tools.ai_assistant import chat_with_ai

# Load environment variables
#load_dotenv()


st.set_page_config(
    page_title="UniMate",
    page_icon="💸",
    layout="wide"
)

# -------------------------
# Page Functions
# -------------------------

def page_expenses():
    st.title("💰 Expense Tracker")

    st.subheader("Add Expense")
    category = st.selectbox("Category", ["Food", "Transport", "Rent", "Shopping", "Other"])
    amount = st.number_input("Amount (€)", min_value=0.0)
    note = st.text_input("Note (optional)")

    if st.button("Save Expense"):
        expense_service.add_expense(category, amount, note)
        st.success("Expense saved!")
#
    st.subheader("Your Expenses")
    expenses = expense_service.get_expenses()
    st.table(expenses)

def page_budget():
    st.title("📊 Budget Manager")

    monthly_budget = st.number_input("Set your monthly budget (€)", min_value=0.0)

    if st.button("Save Budget"):
        budget_service.set_budget(monthly_budget)
        st.success("Budget updated!")

    st.subheader("Current Budget")
    st.write(budget_service.get_budget())

def page_analytics():
    st.title("📈 Analytics")

    st.write("Spending Trends")
    chart = analytics_service.get_spending_chart()
    st.line_chart(chart)
#
def page_ai_assistant():
    st.title("🤖 AI Financial Assistant")

    user_input = st.text_input("Ask UniMate anything about your finances:")

#  if st.button("Ask"):
#        if user_input.strip():
#            answer = chat_with_ai(user_input)
#            st.success(answer)
#        else:
#            st.warning("Please enter a question.")

# -------------------------
# Sidebar Navigation
# -------------------------
PAGES = {
    "Expense Tracker": page_expenses,
    "Budget Manager": page_budget,
    "Analytics": page_analytics,
    "AI Assistant": page_ai_assistant,
}

st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to:", list(PAGES.keys()))

PAGES[choice]()
