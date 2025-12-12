"""
ai_service.py (Trecho) - Função ai_assistant
"""
import json
from typing import Dict, Optional
from google import genai
from google.genai import types

# Assumindo que a classe AIService e a PromptLoader estão definidas no ficheiro...

class AIService:
    # ... (init e outros métodos) ...

    # ----------------------------------------------------
    # TOOL: ai_assistant (Assistente de Chat)
    # ----------------------------------------------------
    def ai_assistant(self, user_question: str, context_data: Optional[Dict] = None) -> str:
        """
        Responde a perguntas do usuário sobre finanças, usando dados contextuais.
        
        Args:
            user_question: A pergunta do usuário (ex: "Porque é que o meu orçamento de Mercearia está no vermelho?").
            context_data: Dados financeiros recuperados de outros serviços (Budget/Analytics).
            
        Returns: A resposta gerada pelo modelo de IA.
        """
        
        if not self.client: 
            return "Assistente de IA indisponível. Por favor, verifique as credenciais da API."
        
        # 1. Preparar o Contexto
        # Converte o dicionário de dados (gastos, orçamentos) para uma string JSON legível pela IA
        context_str = json.dumps(context_data or {})
        
        # 2. Obter a Instrução do Sistema (para manter o foco financeiro)
        # O prompt do sistema garante que a IA atua como um consultor financeiro.
        system_instruction = self.prompts.format("ai_assistant_system")
        
        # 3. Criar o Prompt Final
        user_prompt = (
            f"Pergunta do Usuário: {user_question}\n"
            f"Dados de Contexto (Gastos/Orçamentos): {context_str}\n\n"
            "Por favor, responda de forma concisa e útil, referenciando os dados fornecidos."
        )

        # 4. Chamar a API Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3, # Mantemos a temperatura baixa para respostas mais factuais
                system_instruction=system_instruction
            )
        )

        return response.text