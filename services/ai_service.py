"""
AI Service - Artificial Intelligence Engine for Personal Finance.

Responsibilities:
- Centralize access to Gemini client
- Expose AI capabilities as high-level methods
- Handle document ingestion (image / PDF)
- Classify expenses
- Native tool-calling orchestration using local Python tools (SQLite)
"""

import os
import re
import json
from typing import List, Dict, Optional, Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from langfuse import observe

from ai.tools_schema import TOOLS 
from ai.tools_router import TOOL_IMPL  


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
    # BASIC CHAT (no tools)
    # --------------------------------------------------
    @observe()
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        if not self.client:
            return "AI assistant unavailable. Please check the API credentials."

        context_str = json.dumps(context_data or {}, ensure_ascii=False)

        system_instruction = self.prompts.format("ai_assistant_system")

        user_prompt = (
            f"User Question: {user_question}\n"
            f"Context Data (optional): {context_str}\n\n"
            "Answer concisely. If you need fresh numbers, call tools."
        )

        response = self.client.models.generate_content(
            model = self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=system_instruction,
            ),
        )
        return response.text or ""

    # --------------------------------------------------
    # NATIVE TOOL CALLING (Gemini function calling)
    # --------------------------------------------------

    @observe()
    def run_tool_calling_flow(
        self,
        user_text: str,
        db_file: str,
        user_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Native flow with memory:
          - builds contents from chat history (user/model)
          - appends latest user_text
          - model decides -> function_call(s) or direct text
          - execute tool calls locally (Python/SQLite)
          - model writes final response

        history format expected (Streamlit):
          [ {"role":"user","content":"..."}, {"role":"assistant","content":"..."} ... ]
        """
        if not self.client:
            return {"answer": "AI offline.", "db_updated": False, "tool_results": []}

        system_instruction = (
            "You are UniMate, a personal finance adviser inside a budgeting app.\n"
            "Your job is to help the user save money, plan budgets, and improve spending habits.\n"
            "You ARE allowed to make recommendations and suggestions.\n"
            "Important:\n"
            "- You are not a licensed financial professional. Provide educational guidance only.\n"
            "- Use the user's real data via tools whenever possible before advising.\n"
            "- If the user asks 'where should I save next month?', do this:\n"
            "  1) call summarize_expense and get_spending_trend\n"
            "  2) if budgets exist, call budget_calculator for the current month\n"
            "  3) then give 3-5 concrete, personalized actions (bullets) and one simple next step.\n"
            "- Never say you 'can't make recommendations'. If data is insufficient, ask ONE targeted question.\n"
            "- Keep answers short, practical, and in the user's language.\n"
        )

        if user_id is not None:
            system_instruction += f"\nUser ID for tool calls: {int(user_id)}\n"

        # ---- Build conversation memory ----
        contents: List[types.Content] = []

        # Convert Streamlit history into GenAI roles: user/model
        if history:
            for m in history:
                role = (m.get("role") or "").strip().lower()
                text = (m.get("content") or "").strip()
                if not text:
                    continue

                if role == "user":
                    contents.append(types.Content(role="user", parts=[types.Part(text=text)]))
                elif role in ("assistant", "model"):
                    contents.append(types.Content(role="model", parts=[types.Part(text=text)]))

        # Append latest user message (avoid duplicate if history already includes it)
        if not contents or contents[-1].role != "user" or contents[-1].parts[0].text != user_text:
            contents.append(types.Content(role="user", parts=[types.Part(text=user_text)]))

        tool_results: List[Dict[str, Any]] = []
        db_updated = False

        while True:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=TOOLS,
                    temperature=0.2,
                    system_instruction=system_instruction,
                ),
            )

            cand = resp.candidates[0].content if resp.candidates else None
            if not cand or not cand.parts:
                return {
                    "answer": resp.text or "No response from model.",
                    "db_updated": db_updated,
                    "tool_results": tool_results,
                }

            # Collect function calls
            function_calls = []
            for p in cand.parts:
                fc = getattr(p, "function_call", None)
                if fc is not None:
                    function_calls.append(fc)

            # No tool calls => final response
            if not function_calls:
                return {
                    "answer": resp.text or "",
                    "db_updated": db_updated,
                    "tool_results": tool_results,
                }

            # Add model tool-call message to history
            contents.append(cand)

            # Execute tool calls and return function_response(s)
            tool_response_parts = []
            for fc in function_calls:
                name = fc.name
                args = fc.args or {}

                # Always inject db_file
                args["db_file"] = db_file

                # If tool expects user_id and model didn't provide it
                if user_id is not None and "user_id" in args and (args.get("user_id") in (None, "", 0)):
                    args["user_id"] = int(user_id)

                if name not in TOOL_IMPL:
                    result = {"error": f"Tool '{name}' not implemented."}
                    ok = False
                else:
                    try:
                        result = TOOL_IMPL[name](**args)
                        ok = True
                    except Exception as e:
                        result = {"error": str(e)}
                        ok = False

                tool_results.append({"name": name, "ok": ok, "result": result, "args": dict(args)})

                if ok and name in {"add_expense", "set_budget"} and result not in (None, -1):
                    db_updated = True

                tool_response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=name,
                            response={"result": result, "ok": ok},
                        )
                    )
                )

            contents.append(types.Content(role="tool", parts=tool_response_parts))
            # loop continues until model returns final text


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
            dt = str(t.get("date", "") or "").strip()

            if amount > 0 and desc:
                transactions.append({"amount": amount, "description": desc, "date": dt})

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

        try:
            return json.loads(result)
        except Exception:
            return {"amount": 0.0, "description": "", "date": "", "category": ""}

    # --------------------------------------------------
    # Advice (OpenAI optional fallback kept)
    # --------------------------------------------------
    def generate_financial_advice(self, context: str) -> str:
        if isinstance(context, (dict, list, tuple)):
            context = json.dumps(context, ensure_ascii=False, indent=2, default=str)
        else:
            context = str(context)

        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=api_key)

                system_msg = (
                    "You are a personal finance assistant. "
                    "Provide concise, actionable advice based on the provided budget/expense context. "
                    "Use bullets. Do not invent numbers. If context is insufficient, say what is missing."
                )

                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": context},
                    ],
                    temperature=0.4,
                )
                return (resp.choices[0].message.content or "").strip() or "No recommendation available."
            except Exception:
                pass

        lines = []
        lines.append("Here's a quick budget check based on what I can infer from your data:")

        overspent = []
        for m in re.finditer(
            r"Category\s*:\s*(.+?)\s*(?:\n|,).*?(?:Spent|spend)\s*[:€]?\s*([0-9]+(?:\.[0-9]+)?)"
            r".*?(?:Limit|budget)\s*[:€]?\s*([0-9]+(?:\.[0-9]+)?)",
            context,
            flags=re.IGNORECASE | re.DOTALL
        ):
            cat = m.group(1).strip()
            spent = float(m.group(2))
            limit = float(m.group(3))
            if limit > 0 and spent > limit:
                overspent.append((cat, spent, limit))

        if overspent:
            lines.append("")
            lines.append("⚠️ Overspent categories:")
            for cat, spent, limit in overspent[:5]:
                diff = spent - limit
                lines.append(f"- {cat}: over by €{diff:.2f} (spent €{spent:.2f} / limit €{limit:.2f})")
            lines.append("")
            lines.append("What to do next:")
            lines.append("- Reduce discretionary spending in those categories for the rest of the month.")
            lines.append("- Set a smaller weekly cap (divide the remaining budget by remaining weeks).")
            lines.append("- If this is recurring, raise the limit only if it matches your real priorities.")
        else:
            lines.append("")
            lines.append("I couldn't clearly detect category limits vs spending from the context.")
            lines.append("Suggestions (safe defaults):")
            lines.append("- Set monthly limits per category (Food, Transport, Leisure, Bills).")
            lines.append("- Review recurring subscriptions and cancel unused ones.")
            lines.append("- Flag unusual spikes (2-3x your typical transaction size) for review.")

        lines.append("")
        lines.append("Tip: For more precise advice, include category limits + spent-to-date + remaining days in month.")
        return "\n".join(lines)

