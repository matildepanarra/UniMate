"""
Langfuse tracing configuration.
Initialize once in app.py, then all @observe() decorators work automatically.
"""
import os
from dotenv import load_dotenv


def init_tracing():
    """
    Initialize Langfuse tracing.

    Langfuse uses environment variables automatically:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_HOST

    If these are set in .env, tracing will be enabled.
    If not, the app will still work but without tracing.
    """
    load_dotenv()

    required = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST"
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        print("⚠️  Langfuse tracing not configured")
        print(f"   Missing: {', '.join(missing)}")
        print("   App will run without tracing")
        return False
    else:
        print("✅ Langfuse tracing enabled")
        print(f"   Host: {os.getenv('LANGFUSE_HOST')}")
        return True