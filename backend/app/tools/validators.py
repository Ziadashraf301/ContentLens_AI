from ..core.logging import logger

class BriefValidator:
    """
    Validates if the extracted text contains 
    essential components of a Media Brief.
    """
    REQUIRED_KEYWORDS = ["target", "audience", "budget", "objective", "kpi", "campaign"]

    @staticmethod
    def is_valid_brief(text: str) -> bool:
        if not text:
            return False
            
        text_lower = text.lower()
        # Check if at least 2 core keywords exist
        matches = [word for word in BriefValidator.REQUIRED_KEYWORDS if word in text_lower]
        
        logger.info(f"Validator: Found {len(matches)} brief-related keywords.")
        
        if len(matches) < 2:
            logger.warning("Validator: Document does not look like a professional brief.")
            return False
            
        return True

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Removes extra whitespace and suspicious characters."""
        return " ".join(text.split())