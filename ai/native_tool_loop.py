from __future__ import annotations

from google import genai
from google.genai import types

from ai.tools_native import TOOLS
from ai.tool_impl import TOOL_IMPL


def run_native_tool_calling(
    prompt: str,
    db_file: str,
    user_id: int,
    model: str = "gemini-2.0-flash",
    client: genai.Client | None = None,
    system_instruction: str | None = None,
) -> dict:
    """
    Native tool calling loop:
    - sends prompt + tools
    - executes function_call(s)
    - returns: {"answer": str, "db_updated": bool}
    """
    client = client or genai.Client()

    sys = system_instruction or (
        "You are UniMate, a personal finance assistant. "
        "Use tools when needed. Be concise. Don't invent numbers."
    )

    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part(text=f"(user_id={user_id})\n{prompt}")]
        )
    ]

    db_updated = False

    while True:
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=sys,
                temperature=0.3,
            ),
        )

        cand = resp.candidates[0].content if resp.candidates else None
        if not cand or not getattr(cand, "parts", None):
            return {"answer": (resp.text or "No response from model."), "db_updated": db_updated}

        function_calls = []
        for p in cand.parts:
            fc = getattr(p, "function_call", None)
            if fc is not None:
                function_calls.append(fc)

        # No tool calls -> final answer
        if not function_calls:
            return {"answer": (resp.text or ""), "db_updated": db_updated}

        # Append model message that contains the tool calls
        contents.append(cand)

        # Execute tools
        tool_response_parts: list[types.Part] = []
        for fc in function_calls:
            tool_name = fc.name
            args = dict(fc.args or {})

            # ALWAYS inject db_file
            args["db_file"] = db_file

            if tool_name not in TOOL_IMPL:
                result = {"error": f"Tool '{tool_name}' not implemented."}
            else:
                try:
                    result = TOOL_IMPL[tool_name](**args)
                    if tool_name in ("add_expense", "set_budget"):
                        db_updated = True
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

        # IMPORTANT: no trailing comma here
        contents.append(types.Content(role="tool", parts=tool_response_parts))
