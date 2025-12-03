import pandas as pd

# In-memory storage for demo
_expenses = []

def add_expense(category, amount, note):
    _expenses.append({
        "Category": category,
        "Amount": amount,
        "Note": note
    })

def get_expenses():
    return pd.DataFrame(_expenses)
