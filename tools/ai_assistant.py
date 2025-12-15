"""
ai_service.py (Trecho) - ai_assistant function
"""
# tools/ai_assistant_tool.py
import json
from typing import Dict, Optional
from google.genai import types

def ai_assistant(
    client,
    model: str,
    prompts,
    user_question: str,
    context_data: Optional[Dict] = None,
) -> str:
    if not client:
        return "Ai assistant unavailable. Please check the API credentials."

    context_str = json.dumps(context_data or {}, ensure_ascii=False)
    system_instruction = prompts.format("ai_assistant_system")

    user_prompt = (
        f"User Question: {user_question}\n"
        f"Context Data (Expenses/Budgets): {context_str}\n\n"
        "Please answer concisely and usefully, referencing the provided data."
    )

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            system_instruction=system_instruction,
        ),
    )

    return response.text or ""
