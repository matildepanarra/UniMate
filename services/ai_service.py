"""
AI Service - Artificial Intelligence Engine for Personal Finance.

Responsibilities:
- Centralize access to Gemini client
- Expose AI capabilities as high-level methods
- Delegate chat logic to tools.ai_assistant.ai_assistant
- Handle document ingestion (image / PDF)
- Provide compatibility wrapper for ExpenseService.add_expense_from_document()
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

# ✅ IMPORT CORRETO: função dentro de tools/ai_assistant.py
from tools.ai_assistant import ai_assistant as ai_assistant_fn


# --------------------------------------------------
# Schemas
# --------------------------------------------------
class TransactionExtract(BaseModel):
    amount: float = Field(description="Transaction amount")
    description: str = Field(description="Merchant or transaction summary")
    date: str = Field(description="Transaction date in YYYY-MM-DD format")


class SpendingPrediction(BaseModel):
    predicted_amount: float = Field(description="Total spend predicted")
    justification: str = Field(description="Explanation of the prediction")


class DocumentIngestionResult(BaseModel):
    merchant: Optional[str] = Field(default=None)
    currency: Optional[str] = Field(default="EUR")
    total: Optional[float] = Field(default=None)
    transactions: List[TransactionExtract] = Field(default_factory=list)


# --------------------------------------------------
# Prompt Loader
# --------------------------------------------------
class PromptLoader:
    def format(self, name: str, **kwargs) -> str:
        if name == "ai_assistant_system":
            return (
                "You are a financial AI assistant. "
                "Answer questions clearly and practically using the provided data."
            )

        if name == "document_ingestion_system":
            base = (
                "You are a receipt/invoice parser for personal finance.\n"
                "Extract merchant, currency, total and transactions.\n"
                "Each transaction must include amount, description and date (YYYY-MM-DD).\n"
                "Return ONLY JSON that matches the required schema.\n"
                "Do not invent values.\n"
            )
            if kwargs.get("date_hint"):
                base += f"\nDate hint: {kwargs['date_hint']}\n"
            return base

        if name == "classify_expense_system":
            amount = kwargs.get("amount")
            description = kwargs.get("description")
            categories_list = kwargs.get("categories_list", [])
            return (
                "You are a personal finance categorizer.\n"
                "Choose EXACTLY one category from the provided list.\n"
                "Return ONLY the category name (no extra text).\n\n"
                f"Amount: {amount}\n"
                f"Description: {description}\n"
                f"Allowed categories: {categories_list}\n"
            )

        return ""


# --------------------------------------------------
# AI Service
# --------------------------------------------------
class AIService:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.prompts = PromptLoader()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("GOOGLE_API_KEY not found. AI disabled.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"Failed to initialize Gemini client: {e}")
            self.client = None

    # --------------------------------------------------
    # CHAT / AI ASSISTANT ✅ chama a função tool certa
    # --------------------------------------------------
    @observe()
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        return ai_assistant_fn(
            self.client,
            self.model,
            self.prompts,
            user_question,
            context_data or {},
        )

    # --------------------------------------------------
    # DOCUMENT INGESTION (PDF / IMAGE)
    # --------------------------------------------------
    @observe()
    def ingest_document(self, file_bytes: bytes, mime_type: str, date_hint: Optional[str] = None) -> Dict:
        if not self.client:
            return {"merchant": None, "currency": "EUR", "total": None, "transactions": []}

        system_instruction = self.prompts.format("document_ingestion_system", date_hint=date_hint)

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_text(text="Parse the attached document and return JSON matching the schema."),
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DocumentIngestionResult,
                system_instruction=system_instruction,
                temperature=0.0,
            ),
        )

        try:
            data = json.loads(response.text or "{}")
        except json.JSONDecodeError:
            return {"merchant": None, "currency": "EUR", "total": None, "transactions": []}

        transactions = []
        for t in data.get("transactions", []) or []:
            try:
                amount = float(t.get("amount", 0) or 0)
            except Exception:
                continue

            desc = str(t.get("description", "") or "").strip()
            date = str(t.get("date", "") or "").strip()

            if amount > 0 and desc:
                transactions.append({"amount": amount, "description": desc, "date": date})

        try:
            total = float(data.get("total")) if data.get("total") is not None else None
        except Exception:
            total = None

        return {
            "merchant": data.get("merchant"),
            "currency": data.get("currency", "EUR"),
            "total": total,
            "transactions": transactions,
        }

    # --------------------------------------------------
    # FUTURE SPENDING PREDICTION
    # --------------------------------------------------
    @observe()
    def predict_future_spending(self, historical_data: str, prediction_period: str = "next month") -> Dict:
        if not self.client:
            return {"predicted_amount": 0.0, "justification": "AI Offline."}

        system_instruction = (
            "You are a financial analyst. "
            f"Predict spending for {prediction_period} based on the data."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=f"Historical data (JSON): {historical_data}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SpendingPrediction,
                system_instruction=system_instruction,
                temperature=0.5,
            ),
        )

        try:
            data = json.loads(response.text or "{}")
        except json.JSONDecodeError:
            return {"predicted_amount": 0.0, "justification": "Prediction failed."}

        return {
            "predicted_amount": float(data.get("predicted_amount", 0.0) or 0.0),
            "justification": str(data.get("justification", "") or ""),
        }

    # --------------------------------------------------
    # CLASSIFY EXPENSE
    # --------------------------------------------------
    @observe()
    def classify_expense(self, amount: float, description: str, categories_list: List[str]) -> str:
        if not self.client:
            return "Others"

        system_instruction = self.prompts.format(
            "classify_expense_system",
            amount=amount,
            description=description,
            categories_list=categories_list,
        )

        content = (
            f"Classify this transaction.\n"
            f"Amount: {amount}\n"
            f"Description: {description}\n"
            f"Allowed categories: {categories_list}\n"
            "Return only the category name."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=content,
            config=types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=system_instruction,
            ),
        )

        result = (response.text or "").strip().split("\n")[0].strip()
        return result if result in categories_list else "Others"

    # --------------------------------------------------
    # COMPAT: extract_document_data (para ExpenseService.add_expense_from_document)
    # --------------------------------------------------
    @observe()
    def extract_document_data(self, document_text: str) -> dict:
        instruction = (
            "Extract ONE transaction from the text below and return ONLY valid JSON "
            "with keys: amount (number), description (string), date (YYYY-MM-DD or empty string), "
            "category (string or empty). No markdown, no explanation.\n\n"
            f"TEXT:\n{document_text}"
        )

        result = self.ai_assistant(instruction, {})

        if isinstance(result, dict):
            return result

        try:
            return json.loads(result)
        except Exception:
            return {"amount": 0.0, "description": "", "date": "", "category": ""}
