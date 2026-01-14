from langfuse.langchain import CallbackHandler
from .config import settings
from langfuse import Langfuse

langfuse = None

if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    langfuse = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_BASE_URL,
    )

if langfuse:
    try:
        langfuse.trace(
            name="startup-check",
            metadata={"service": "ContentLens_AI"}
        )
        print("Langfuse is connected ✅")
    except Exception as e:
        print("Langfuse connection failed ❌", e)
    
def get_langfuse_callback():
    """
    Returns a callback handler for LangChain/LangGraph.
    This allows you to see every LLM call, token count, and error in Langfuse UI.
    """
    if langfuse:
        return CallbackHandler()
    return None