from langfuse.langchain import CallbackHandler
from .config import settings

def get_langfuse_callback():
    """
    Returns a callback handler for LangChain/LangGraph.
    This allows you to see every LLM call, token count, and error in Langfuse UI.
    """
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        return CallbackHandler()
    return None