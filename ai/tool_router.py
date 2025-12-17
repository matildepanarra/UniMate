# ai/tool_router.py

from tools.add_expense import add_expense
from tools.get_expense import get_expense

from tools.set_budget import set_budget
from tools.budget_calculator import budget_calculator

from tools.detect_anomalies import detect_anomalies
from tools.get_spending_trend import get_spending_trend
from tools.summarize_expense import summarize_expense

TOOL_MAP = {
    "add_expense": add_expense,
    "get_expense": get_expense,
    "set_budget": set_budget,
    "budget_calculator": budget_calculator,
    "detect_anomalies": detect_anomalies,
    "get_spending_trend": get_spending_trend,
    "summarize_expense": summarize_expense,
}

def execute_tool(tool_name: str, arguments: dict):
    if tool_name not in TOOL_MAP:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_MAP[tool_name](**arguments)
