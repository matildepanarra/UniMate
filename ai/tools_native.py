from __future__ import annotations
from google.genai import types

def _schema_object(properties: dict, required: list[str]):
    return types.Schema(
        type="OBJECT",
        properties=properties,
        required=required,
    )

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="add_expense",
                description="Add a new expense to the database.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                        "amount": types.Schema(type="NUMBER"),
                        "category": types.Schema(type="STRING"),
                        "vendor": types.Schema(type="STRING"),
                        "transaction_date": types.Schema(type="STRING", description="YYYY-MM-DD"),
                        "notes": types.Schema(type="STRING"),
                    },
                    required=["user_id", "amount", "category", "vendor", "transaction_date"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_expense",
                description="Get an expense by id.",
                parameters=_schema_object(
                    properties={
                        "expense_id": types.Schema(type="INTEGER"),
                    },
                    required=["expense_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="set_budget",
                description="Upsert a budget limit for a user/category and period.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                        "category": types.Schema(type="STRING"),
                        "amount_limit": types.Schema(type="NUMBER"),
                        "start_date": types.Schema(type="STRING"),
                        "end_date": types.Schema(type="STRING"),
                    },
                    required=["user_id", "category", "amount_limit", "start_date", "end_date"],
                ),
            ),
            types.FunctionDeclaration(
                name="budget_calculator",
                description="Compute spent vs limit per category for an active budget period.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                        "start_date": types.Schema(type="STRING"),
                        "end_date": types.Schema(type="STRING"),
                    },
                    required=["user_id", "start_date", "end_date"],
                ),
            ),
            types.FunctionDeclaration(
                name="detect_anomalies",
                description="Detect anomalous expenses above 2x user average.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                    },
                    required=["user_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_spending_trend",
                description="Aggregate spending by year-month.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                    },
                    required=["user_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="summarize_expense",
                description="Return lifetime totals, count and average transaction value.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                    },
                    required=["user_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="list_expenses",
                description="List expenses for a user with optional filters.",
                parameters=_schema_object(
                    properties={
                        "user_id": types.Schema(type="INTEGER"),
                        "limit": types.Schema(type="INTEGER"),
                        "offset": types.Schema(type="INTEGER"),
                        "category": types.Schema(type="STRING"),
                        "start_date": types.Schema(type="STRING", description="YYYY-MM-DD"),
                        "end_date": types.Schema(type="STRING", description="YYYY-MM-DD"),
                    },
                    required=["user_id"],
                ),
            ),
        ]
    )
]

