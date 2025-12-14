"""
AI Service - Artificial Intelligence Engine for Personal Finance.
Handles structured data extraction (documents/receipts), categorization, 
forecasting, and conversational assistance via chat, powered by the Gemini API.
"""
import os
import json
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
try:
    from langfuse import observe  
except Exception:
    from utils.observability import observe

# ----------------------------
# Schemas (Pydantic) to response_schema
# ----------------------------
class TransactionExtract(BaseModel):
    amount: float = Field(description="Transaction amount")
    description: str = Field(description="Merchant name or transaction summary")
    date: str = Field(description="Transaction date in YYYY-MM-DD format")


class SpendingPrediction(BaseModel):
    predicted_amount: float = Field(description="Total Spend amount predicted")
    justification: str = Field(description="Brief explanation of the prediction")

# ----------------------------
# Prompt Loader (Simulated)
# ----------------------------
class PromptLoader:
    """Simulation of a loader of prompts for the system."""
    def format(self, name, **kwargs):
        if name == "extract_transaction_system":
            return (
                "You are a transaction data extractor. "
                "Analize the text and extract Amount (float), Description and Date (YYYY-MM-DD). "
                "If the date is not explicit, infer the most likely one."
            )
        elif name == "classify_expense_system":
            return (
                "You are an expense classifier. "
                f"Classify the transaction (Description: '{kwargs.get('description')}', "
                f"Amount: {kwargs.get('amount')}) into a single category from the list: "
                f"{kwargs.get('categories_list')}."
                "Respond only with the exact category name."
            )
        elif name == "financial_advice_system":
            return (
                "You are a smart financial advisor. "
                f"Analyze the user's spending summary, budgets, and predictions "
                f"({kwargs.get('summary')}) and provide an actionable and personalized "
                "advice to optimize finances."
            )
        elif name == "ai_assistant_system":
            return (
                "You are an AI assistant focused on finance. "
                "Answer user questions about expenses and budgets based on the provided context. "
                "Be direct and practical."
            )
        return ""


# ----------------------------
# AI Service Class
# ----------------------------
class AIService:
    """Implementation of all the AI tools (tools)."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize the AI service.
        Requires GOOGLE_API_KEY in the environment (.env).
        """
        self.model = model
        self.prompts = PromptLoader()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Alert: GOOGLE_API_KEY not found. AI will be offline.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(
                "Alert: Failed to initialize the Gemini client. "
                f"Error: {e}"
            )
            self.client = None

    # ----------------------------------------------------
    # TOOL: extract_document_data
    # ----------------------------------------------------
    @observe()
    def extract_document_data(self, document_text: str) -> dict:
        """
        Extract structured information (Amount, Description, Date) from a free text.
        Used by expense_service.
        """
        if not self.client:
            return {"amount": 0.0, "description": "AI Offline", "date": ""}

        system_instruction = self.prompts.format("extract_transaction_system")

        response = self.client.models.generate_content(
            model=self.model,
            contents=document_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TransactionExtract,  
                system_instruction=system_instruction,
                temperature=0.0,
            )
        )

        # google-genai gets back JSON in response.text when response_mime_type="application/json"
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"amount": 0.0, "description": "Erro de extração", "date": ""}

        return {
            "amount": float(data.get("amount", 0.0) or 0.0),
            "description": str(data.get("description", "") or ""),
            "date": str(data.get("date", "") or ""),
        }

    # ----------------------------------------------------
    # TOOL: classify_expense
    # ----------------------------------------------------
    @observe()
    def classify_expense(self, amount: float, description: str, categories_list: List[str]) -> str:
        """
        Classifies a transaction into one of the categories.
        Used internally by ExpenseService.
        """
        if not self.client:
            return "Others"

        system_instruction = self.prompts.format(
            "classify_expense_system",
            amount=amount,
            description=description,
            categories_list=categories_list
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents="Classify this transaction into the most appropriate category.",
            config=types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=system_instruction
            )
        )

        return (response.text or "").strip()

    # ----------------------------------------------------
    # TOOL: generate_financial_advice
    # ----------------------------------------------------
    @observe()
    def generate_financial_advice(self, user_financial_summary: Dict) -> str:
        """
        Generates personalized advice based on a financial summary.
        Used by budget_service.analyze_budget.
        """
        if not self.client:
            return "AI service unavailable for advice."

        summary_str = json.dumps(user_financial_summary, ensure_ascii=False)

        system_instruction = self.prompts.format("financial_advice_system", summary=summary_str)

        response = self.client.models.generate_content(
            model=self.model,
            contents="Based on my financial performance and goals, what is your best advice for me?",
            config=types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=system_instruction
            )
        )

        return response.text or ""

    # ----------------------------------------------------
    # TOOL: ai_assistant
    # ----------------------------------------------------
    @observe()
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        """
        Answer questions from the user about finances, using contextual data.
        """
        if not self.client:
            return "I assistant unavailable."

        context_str = json.dumps(context_data or {}, ensure_ascii=False)
        system_instruction = self.prompts.format("ai_assistant_system")

        user_prompt = (
            f"Question: {user_question}\n\n"
            f"Context Data (Expenses/Budgets): {context_str}"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=system_instruction
            )
        )

        return response.text or ""

    # ----------------------------------------------------
    # TOOL: predict_future_spending
    # ----------------------------------------------------
    @observe()
    def predict_future_spending(self, historical_data: str, prediction_period: str = "next month") -> dict:
        """
        Predict future spending based on historical data.
        Used by budget_service.analyze_budget.
        """
        if not self.client:
            return {"predicted_amount": 0.0, "justification": "AI Offline."}

        system_instruction = (
            "You are a financial analyst. Analyze the provided historical spending data "
            f"and predict the likely total spending for {prediction_period}. "
            "Return a JSON object with the prediction and a brief justification."
        )

        user_prompt = f"historical_data (JSON): {historical_data}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SpendingPrediction, 
                temperature=0.5,
                system_instruction=system_instruction
            )
        )

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"predicted_amount": 0.0, "justification": "Error processing prediction."}

        return {
            "predicted_amount": float(data.get("predicted_amount", 0.0) or 0.0),
            "justification": str(data.get("justification", "") or ""),
        }
