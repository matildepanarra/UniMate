# ai/tool_schemas.py

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a new expense to the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "category": {"type": "string"},
                    "vendor": {"type": "string"},
                    "transaction_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "notes": {"type": "string"}
                },
                "required": ["db_file", "user_id", "amount", "category", "vendor", "transaction_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense",
            "description": "Get an expense by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "expense_id": {"type": "integer"}
                },
                "required": ["db_file", "expense_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_budget",
            "description": "Upsert a budget limit for a user/category and period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"},
                    "category": {"type": "string"},
                    "amount_limit": {"type": "number"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                },
                "required": ["db_file", "user_id", "category", "amount_limit", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "budget_calculator",
            "description": "Compute spent vs limit per category for an active budget period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                },
                "required": ["db_file", "user_id", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "Detect anomalous expenses above 2x user average.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"}
                },
                "required": ["db_file", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_trend",
            "description": "Aggregate spending by year-month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"}
                },
                "required": ["db_file", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_expense",
            "description": "Return lifetime totals, count and average transaction value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_file": {"type": "string"},
                    "user_id": {"type": "integer"}
                },
                "required": ["db_file", "user_id"]
            }
        }
    }
]
