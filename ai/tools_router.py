from tools.add_expense import add_expense
from tools.get_expense import get_expense
from tools.set_budget import set_budget
from tools.budget_calculator import budget_calculator
from tools.detect_anomalies import detect_anomalies
from tools.get_spending_trend import get_spending_trend
from tools.summarize_expense import summarize_expense
from tools.list_expenses import list_expenses
from tools.remove_expense import remove_expense

TOOL_IMPL = {
    "add_expense": add_expense,
    "get_expense": get_expense,
    "set_budget": set_budget,
    "budget_calculator": budget_calculator,
    "detect_anomalies": detect_anomalies,
    "get_spending_trend": get_spending_trend,
    "summarize_expense": summarize_expense,
    "list_expenses": list_expenses,
    "remove_expense": remove_expense, 
}

