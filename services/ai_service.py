"""
AI Service - Artificial Intelligence Engine for Personal Finance.
Handles structured data extraction (documents/receipts), categorization, 
forecasting, and conversational assistance via chat, powered by the Gemini API.
"""
"""
AI Service - Artificial Intelligence Engine for Personal Finance.

Responsibilities:
- Centralize access to Gemini client
- Expose AI capabilities as high-level methods
- Delegate chat logic to ai_assistant_tool
- Handle document ingestion (image / PDF)
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

# IMPORT DA TUA TOOL
from tools import ai_assistant


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
    transactions: List[TransactionExtract]


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
                "Do not invent values.\n"
            )
            if kwargs.get("date_hint"):
                base += f"\nDate hint: {kwargs['date_hint']}\n"
            return base

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
    # CHAT / AI ASSISTANT  ✅ CHAMA A TOOL
    # --------------------------------------------------
    @observe()
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        """
        Wrapper that delegates chat logic to ai_assistant_tool
        """
        return ai_assistant(
            client=self.client,
            model=self.model,
            prompts=self.prompts,
            user_question=user_question,
            context_data=context_data,
        )

    # --------------------------------------------------
    # DOCUMENT INGESTION (PDF / IMAGE)
    # --------------------------------------------------
    @observe()
    def ingest_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        date_hint: Optional[str] = None,
    ) -> Dict:
        """
        Extract structured expense data from a receipt/invoice (PDF or image).
        """
        if not self.client:
            return {"merchant": None, "currency": "EUR", "total": None, "transactions": []}

        system_instruction = self.prompts.format(
            "document_ingestion_system",
            date_hint=date_hint
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_text(
                    text="Parse the attached document and return JSON matching the schema."
                    ),

                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                ),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DocumentIngestionResult,
                system_instruction=system_instruction,
                temperature=0.0,
            ),
        )

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"merchant": None, "currency": "EUR", "total": None, "transactions": []}

        # Normalização defensiva
        transactions = []
        for t in data.get("transactions", []):
            try:
                amount = float(t.get("amount", 0))
            except Exception:
                continue

            desc = str(t.get("description", "")).strip()
            date = str(t.get("date", "")).strip()

            if amount > 0 and desc:
                transactions.append(
                    {"amount": amount, "description": desc, "date": date}
                )

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
    def predict_future_spending(
        self,
        historical_data: str,
        prediction_period: str = "next month"
    ) -> Dict:
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
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"predicted_amount": 0.0, "justification": "Prediction failed."}

        return {
            "predicted_amount": float(data.get("predicted_amount", 0.0)),
            "justification": str(data.get("justification", "")),
        }
    @observe()
    def classify_expense(self, amount: float, description: str, categories_list: List[str]) -> str:
        """
        Classifies a transaction into one category from categories_list.
        """
        if not self.client:
            return "Others"

        system_instruction = self.prompts.format(
            "classify_expense_system",
            amount=amount,
            description=description,
            categories_list=categories_list,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents="Classify this transaction into the most appropriate category.",
            config=types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=system_instruction,
            ),
        )

        return (response.text or "").strip() or "Others"