"""
AI Service - Motor de Inteligência Artificial para Finanças Pessoais
Lida com extração estruturada (documentos/recibos), categorização,
previsão e assistência via chat, usando a API Gemini.
"""
import os
import json
from typing import List, Dict, Optional

from google import genai
from google.genai import types

from pydantic import BaseModel, Field

try:
    from langfuse import observe  # se funcionar, ótimo
except Exception:
    from utils.observability import observe


# ----------------------------
# Schemas (Pydantic) para response_schema
# ----------------------------
class TransactionExtract(BaseModel):
    amount: float = Field(description="Montante da transação")
    description: str = Field(description="Nome do comerciante ou resumo da transação")
    date: str = Field(description="Data da transação no formato YYYY-MM-DD")


class SpendingPrediction(BaseModel):
    predicted_amount: float = Field(description="Montante total de gastos previstos")
    justification: str = Field(description="Breve explicação da previsão")


# --- Simulação de classes externas (Adaptado para o seu caso de uso) ---
class PromptLoader:
    """Simulação de um loader de prompts para o sistema."""
    def format(self, name, **kwargs):
        if name == "extract_transaction_system":
            return (
                "Você é um extrator de dados de transações. "
                "Analise o texto e extraia Montante (float), Descrição e Data (YYYY-MM-DD). "
                "Se a data não estiver explícita, inferir a mais provável."
            )
        elif name == "classify_expense_system":
            return (
                "Você é um classificador de despesas. "
                f"Classifique a transação (Descrição: '{kwargs.get('description')}', "
                f"Montante: {kwargs.get('amount')}) numa única categoria da lista: "
                f"{kwargs.get('categories_list')}."
                "Responda apenas com o nome exato da categoria."
            )
        elif name == "financial_advice_system":
            return (
                "Você é um consultor financeiro inteligente. "
                f"Analise o resumo de gastos, orçamentos e previsões do usuário "
                f"({kwargs.get('summary')}) e forneça um conselho acionável e personalizado "
                "para otimizar as finanças."
            )
        elif name == "ai_assistant_system":
            return (
                "Você é um assistente de IA focado em finanças. "
                "Responda a perguntas do usuário sobre gastos e orçamentos com base "
                "nos dados contextuais fornecidos. Seja direto e prático."
            )
        return ""


# ----------------------------
# Serviço de IA
# ----------------------------
class AIService:
    """Implementa todas as ferramentas (tools) de IA."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Inicializa o serviço de IA.
        Requer GOOGLE_API_KEY no ambiente (.env).
        """
        self.model = model
        self.prompts = PromptLoader()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Alerta: GOOGLE_API_KEY não encontrada. AI ficará offline.")
            self.client = None
            return

        try:
            # Passar api_key explicitamente evita falhas de auto-deteção
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(
                "Alerta: Falha ao inicializar o cliente Gemini. "
                f"Erro: {e}"
            )
            self.client = None

    # ----------------------------------------------------
    # TOOL: extract_document_data
    # ----------------------------------------------------
    @observe()
    def extract_document_data(self, document_text: str) -> dict:
        """
        Extrai informações estruturadas (Montante, Descrição, Data) de um texto livre.
        Usado por expense_service.
        """
        if not self.client:
            return {"amount": 0.0, "description": "AI Offline", "date": ""}

        system_instruction = self.prompts.format("extract_transaction_system")

        response = self.client.models.generate_content(
            model=self.model,
            contents=document_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TransactionExtract,  # ✅ Pydantic model
                system_instruction=system_instruction,
                temperature=0.0,
            )
        )

        # google-genai devolve JSON em response.text quando response_mime_type="application/json"
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"amount": 0.0, "description": "Erro de extração", "date": ""}

        # Garantir chaves mínimas
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
        Classifica uma transação numa das categorias.
        Usado internamente pelo ExpenseService.
        """
        if not self.client:
            return "Outros"

        system_instruction = self.prompts.format(
            "classify_expense_system",
            amount=amount,
            description=description,
            categories_list=categories_list
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents="Classifique esta transação na categoria mais adequada.",
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
        Gera conselhos personalizados com base num resumo de dados financeiros.
        Usado por budget_service.analyze_budget.
        """
        if not self.client:
            return "Serviço de IA indisponível para aconselhamento."

        summary_str = json.dumps(user_financial_summary, ensure_ascii=False)

        system_instruction = self.prompts.format("financial_advice_system", summary=summary_str)

        response = self.client.models.generate_content(
            model=self.model,
            contents="Com base no meu desempenho financeiro e metas, qual é o seu melhor conselho para mim?",
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
        Responde a perguntas do usuário sobre finanças, usando dados contextuais.
        """
        if not self.client:
            return "Assistente de IA indisponível."

        context_str = json.dumps(context_data or {}, ensure_ascii=False)
        system_instruction = self.prompts.format("ai_assistant_system")

        user_prompt = (
            f"Pergunta: {user_question}\n\n"
            f"Dados de Contexto (Gastos/Orçamentos): {context_str}"
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
    def predict_future_spending(self, historical_data: str, prediction_period: str = "próximo mês") -> dict:
        """
        Previsão de gastos futuros com base em dados históricos.
        Usado por budget_service.analyze_budget.
        """
        if not self.client:
            return {"predicted_amount": 0.0, "justification": "AI Offline."}

        system_instruction = (
            "Você é um analista financeiro. Analise os dados históricos de gastos fornecidos "
            f"e preveja o gasto total provável para {prediction_period}. "
            "Retorne um objeto JSON com a previsão e uma breve justificação."
        )

        user_prompt = f"Dados Históricos (JSON): {historical_data}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SpendingPrediction,  # ✅ Pydantic model
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
