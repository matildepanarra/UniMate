"""
AI Service - All Gemini API interactions
Handles structured extraction, chat, and AI-powered analysis.
"""

import os
import json
from google import genai
from google.genai import types
from langfuse import observe 


class AIService:
    """Services for AI operations"""
    
    def __init__(self, model: str= "gemini-2.5-flash-lite"):
        self.client = genai.Client(api_key = os.getenv("GOOGLE_API__KEY", "AIzaSyDHoic4Vf9hyIOZucYugVAkMZDjYqr7aUk"))
        self.model = model

    #observe(as_type="service")
    def classify_ticket(self, ticket_text: str) -> dict:
        """Extract structure info from a ticket"""

        schema = {
            "category": "one of: Authentication, Billing, Technical, Account Management, Sales, General Support"
            "urgency": "one of: critical, high, medium, low",
            "customer_name": "string or not specified",
            "issue_summary": "string summarizing the issue in 10 words or less"
        }

        prompt = f""" Analyze this support ticket and extract info.

        ticket. {ticket_text}

        extract as JSON:{json.dumps(schema, indent=2)}

        Urgency guidelines:
        - critical: system down, data loss, security breach. etc.
        - high: Can not use key features, broken, features, etc.
        - medium: feature not working as expected, small bugs, minor impact on operation, etc.
        - low: Questions and feature requests

        Return only valid JSON.
        """

        response = self.client.models.generate_content(
            model = self.model,
            contents = prompt,
            config = types.GenerateContentConfig(
                temperature = 0.1,
                response_mime_type = "application/json"
            )
        )

        return json.loads(response.text)
    

if __name__ == "__main__":
    ai = AIService()
    ticket = "The button to submit my application is not working as it should. it crashes the app"
    result = ai.classify_ticket(ticket_text = ticket)
    print(json.dumps(result, indent=2))
    