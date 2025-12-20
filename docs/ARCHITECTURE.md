
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
│   ├── add_expense.py          # Registo de novas despesas
│   ├── budget_calculator.py    # Cálculos de limites e poupança
│   ├── detect_anomalies.py     # Identificação de gastos fora do comum
│   ├── get_spending_trend.py   # Análise de tendências temporais
│   └── get expense.py          #
│   └── get_spending_trend
│   └── list_expenses.py
│   └── remove_expense.py
│   └── set_budget.py
│   └── summarize_expense.py
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


```
project-root/
├── app.py                 # Main application entry point
├── services/              # Business logic layer
├── tools/                 # Function calling tools
├── utils/                 # Utility functions
├── docs/
│   └── ARCHITECTURE.md    # Architecture decisions and explanations
├── requirements.txt       # Dependencies
├── .env.example           # Environment variable template
└── README.md             