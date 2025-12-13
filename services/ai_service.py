"""
AI Service - Motor de Inteligência Artificial para Finanças Pessoais
Lida com extração estruturada (documentos/recibos), categorização, 
previsão e assistência via chat, usando a API Gemini.
"""
import os
import json
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from langfuse import observe

# --- Simulação de classes externas (Adaptado para o seu caso de uso) ---
class PromptLoader:
    """Simulação de um loader de prompts para o sistema."""
    def format(self, name, **kwargs):
        # Prompts do Sistema para guiar a IA
        if name == "extract_transaction_system":
            return "Você é um extrator de dados de transações. Analise o texto e extraia o Montante (float), Descrição e Data (YYYY-MM-DD)."
        elif name == "classify_expense_system":
            return f"Você é um classificador de despesas. Classifique a transação (Descrição: '{kwargs.get('description')}', Montante: {kwargs.get('amount')}) numa única categoria da lista: {kwargs.get('categories_list')}."
        elif name == "financial_advice_system":
            return f"Você é um consultor financeiro inteligente. Analise o resumo de gastos, orçamentos e previsões do usuário ({kwargs.get('summary')}) e forneça um conselho acionável e personalizado para otimizar suas finanças."
        elif name == "ai_assistant_system":
            return "Você é um assistente de IA focado em finanças. Responda a perguntas do usuário sobre seus gastos e orçamentos com base nos dados contextuais fornecidos."
        return ""

# --- SERVIÇO DE IA ---
class AIService:
    """Implementa todas as ferramentas (tools) de IA."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """Inicializa o serviço de IA, assumindo que a chave da API está configurada."""
        try:
            # Assume-se que a chave está em variáveis de ambiente (GOOGLE_API_KEY)
            self.client = genai.Client()
        except Exception as e:
            # Captura erro se o ambiente não estiver configurado corretamente
            print(f"Alerta: Falha ao inicializar o cliente Gemini. Certifique-se de que a variável de ambiente GOOGLE_API_KEY está definida. Erro: {e}")
            self.client = None # Define como None para evitar chamadas
            
        self.model = model
        self.prompts = PromptLoader()

    # ----------------------------------------------------
    # TOOL: extract_document_data (Extração Estruturada - Recibos/Faturas)
    # ----------------------------------------------------
    @observe()
    def extract_document_data(self, document_text: str) -> dict:
        """
        Extrai informações estruturadas (Montante, Descrição, Data) de um texto livre.
        Usado por expense_service.
        """
        if not self.client: return {"amount": 0.0, "description": "AI Offline", "date": ""}
        
        schema = {
            "amount": "float - Montante da transação",
            "description": "string - Nome do comerciante ou resumo da transação",
            "date": "string - Data da transação no formato YYYY-MM-DD"
        }
        
        system_instruction = self.prompts.format("extract_transaction_system")

        response = self.client.models.generate_content(
            model=self.model,
            contents=document_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                system_instruction=system_instruction
            )
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"amount": 0.0, "description": "Erro de extração", "date": ""}

    # ----------------------------------------------------
    # (Interno) TOOL: classify_expense (Categorização)
    # ----------------------------------------------------
    @observe()
    def classify_expense(self, amount: float, description: str, categories_list: List[str]) -> str:
        """
        Classifica uma transação numa das categorias.
        Usado internamente pelo ExpenseService para categorização automática.
        """
        if not self.client: return "Outros"

        system_instruction = self.prompts.format(
            "classify_expense_system",
            amount=amount,
            description=description,
            categories_list=categories_list
        )
        
        user_prompt = "Classifique esta transação na categoria mais adequada."

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0, # Deterministico
                system_instruction=system_instruction
            )
        )
        
        return response.text.strip()

    # ----------------------------------------------------
    # TOOL: generate_financial_advice (Aconselhamento Financeiro)
    # ----------------------------------------------------
    @observe()
    def generate_financial_advice(self, user_financial_summary: Dict) -> str:
        """
        Gera conselhos personalizados com base num resumo de dados financeiros do usuário.
        Usado por budget_service.analyze_budget.
        """
        if not self.client: return "Serviço de IA indisponível para aconselhamento."
        
        summary_str = json.dumps(user_financial_summary)
        
        system_instruction = self.prompts.format(
            "financial_advice_system",
            summary=summary_str
        )
        
        user_prompt = "Com base no meu desempenho financeiro e metas, qual é o seu melhor conselho para mim?"

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7, 
                system_instruction=system_instruction
            )
        )
        
        return response.text

    # ----------------------------------------------------
    # TOOL: ai_assistant (Assistente de Chat)
    # ----------------------------------------------------
    @observe()
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        """
        Responde a perguntas do usuário sobre finanças, usando dados contextuais.
        """
        if not self.client: return "Assistente de IA indisponível."
        
        context_str = json.dumps(context_data or {})
        
        system_instruction = self.prompts.format("ai_assistant_system")
        
        user_prompt = (
            f"Pergunta: {user_question}\n"
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

        return response.text

    # ----------------------------------------------------
    # (Interno) TOOL: predict_future_spending (Previsão de Gastos)
    # ----------------------------------------------------
    @observe()
    def predict_future_spending(self, historical_data: str, prediction_period: str = "próximo mês") -> dict:
        """
        Simula a previsão de gastos futuros com base em dados históricos.
        Usado por budget_service.analyze_budget.
        """
        if not self.client: return {"predicted_amount": 0.0, "justification": "AI Offline."}
        
        system_instruction = (
            "Você é um analista financeiro. Analise os dados históricos de gastos fornecidos "
            f"e preveja o gasto total provável para o {prediction_period}. Retorne um objeto JSON "
            "com a previsão e uma breve justificação."
        )
        
        schema = {
            "predicted_amount": "float - Montante total de gastos previstos",
            "justification": "string - Breve explicação da previsão"
        }
        
        user_prompt = f"Dados Históricos (JSON): {historical_data}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.5,
                system_instruction=system_instruction
            )
        )
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"predicted_amount": 0.0, "justification": "Error processing prediction."}