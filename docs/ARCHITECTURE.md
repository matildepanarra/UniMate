# UniMate - System Architecture

This document describes the design decisions and technical structure of the UniMate project, an intelligent financial assistant.

---

## 1. Architectural Overview
UniMate follows a **Layered Architecture** pattern to ensure strict separation of concerns, making the system easier to maintain, test, and scale.



---

## 2. Project Structure

```
UNIMATE/
├── ai/                         # Tool callling auxiliar 
│   ├── tools_router.py         # Tool calling logic 
│   └── tools_schema.py         # Tool calling shcema 
│
├── services/                   # Business logic layer
│   ├── ai_service.py           # Gestão da comunicação com LLMs
│   ├── analytics_service.py    # Processamento de insights e padrões
│   ├── budget_service.py       # Regras de gestão de orçamentos
│   ├── db_connector.py         # Ligação central à base de dados
│   └── expense_service.py      # Lógica de gestão de despesas
│
├── tools/                      # Function calling tools
│   ├── add_expense.py          # New expenses addition
│   ├── budget_calculator.py    # budget related calculations
│   ├── detect_anomalies.py     # Identify expenses that might be anomalies 
│   ├── get_spending_trend.py   # Analytics on spending trends
│   └── get expense.py          # get the expense
│   └── list_expenses.py        # list all the expenses registered 
│   └── remove_expense.py       # delete any expense 
│   └── set_budget.py           # set a new budget by category
│   └── summarize_expense.py    # summary of expense
│
├── utils/                      #Utility functions
│   └── tracing.py              #Langfuse configuration
│
|
├── docs/                       # ARCHITECTURE.md
├── tests/                      # Tests 
├── unimate_env/                # Virtual environment 
│
├── app.py                      # Main application entry point (Streamlit UI)
├── unimate_financial_data.db   # Local Database SQLite3
├── requirements.txt            # Dependencies
└── .env.example                # Environment variable template
└── README.md.                  # README file