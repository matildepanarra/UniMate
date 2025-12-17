# ai/native_tool_loop.py
from __future__ import annotations

from google import genai
from google.genai import types

from ai.tools_native import TOOLS
from ai.tool_impl import TOOL_IMPL


def run_native_tool_calling(
    prompt: str,
    model: str = "gemini-2.0-flash",
    client: genai.Client | None = None,
) -> str:
    """
    Native tool calling loop:
    - sends prompt + tools
    - executes function_call(s)
    - returns final model text
    """
    client = client or genai.Client()

    contents = [
        types.Content(role="user", parts=[types.Part(text=prompt)])
    ]

    while True:
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
            ),
        )

        # Candidate content
        cand = resp.candidates[0].content if resp.candidates else None
        if not cand or not cand.parts:
            return resp.text or "No response from model."

        # Check for function calls
        function_calls = []
        for p in cand.parts:
            fc = getattr(p, "function_call", None)
            if fc is not None:
                function_calls.append(fc)

        # If no tool calls, it's final answer
        if not function_calls:
            return resp.text or ""

        # Add the model tool-call message to history
        contents.append(cand)

        # Execute tools and return function_response parts
        tool_response_parts = []
        for fc in function_calls:
            tool_name = fc.name
            args = fc.args or {}

            if tool_name not in TOOL_IMPL:
                result = {"error": f"Tool '{tool_name}' not implemented."}
            else:
                try:
                    result = TOOL_IMPL[tool_name](**args)
                except Exception as e:
                    result = {"error": str(e)}

            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response={"result": result},
                    )
                )
            )

        contents.append(types.Content(role="tool", parts=tool_response_parts))
