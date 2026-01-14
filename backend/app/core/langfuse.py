from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from app.core.config import settings

_langfuse_client = None
_langfuse_callback = None


def init_langfuse():
    global _langfuse_client, _langfuse_callback

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )

        # Create ONE callback instance
        _langfuse_callback = CallbackHandler()


def get_langfuse_callback():
    return _langfuse_callback
