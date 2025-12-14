def observe(*args, **kwargs):
    """Fallback decorator quando Langfuse não está disponível."""
    def decorator(func):
        return func
    return decorator