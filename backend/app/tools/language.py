from langdetect import detect, DetectorFactory
from ..core.logging import logger

# Ensures consistent results
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """
    Detects the ISO language code (e.g., 'en', 'ar').
    """
    try:
        if not text or len(text.strip()) < 10:
            return "unknown"
            
        lang = detect(text)
        logger.info(f"Tool: Language detected as '{lang}'")
        return lang
    except Exception as e:
        logger.error(f"Language Detection Error: {e}")
        return "error"

def is_arabic(text: str) -> bool:
    """Helper to check if content is primarily Arabic."""
    return detect_language(text) == "ar"