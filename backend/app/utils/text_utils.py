import re

def clean_extra_whitespace(text: str) -> str:
    """Removes double spaces, tabs, and excessive newlines."""
    return re.sub(r'\s+', ' ', text).strip()

def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Prevents token overflow for very long documents."""
    return text[:max_chars] + "..." if len(text) > max_chars else text