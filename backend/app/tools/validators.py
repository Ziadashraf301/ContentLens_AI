import re
import unicodedata
from ..core.logging import logger

class BriefValidator:
    """
    Validates if extracted text contains
    essential components of a Media Brief.
    """

    REQUIRED_KEYWORDS = [

        # Strategy & Objectives
        "objective", "goal", "strategy", "purpose", "vision", "mission",

        # Audience & Market
        "target", "audience", "persona", "demographic", "segment", "customer",

        # Campaign & Messaging
        "campaign", "message", "value proposition", "positioning", "branding",
        "tone", "voice", "creative",

        # Budget & Resources
        "budget", "cost", "spend", "investment", "allocation",

        # Performance & Measurement
        "kpi", "metric", "performance", "roi", "conversion", "ctr",

        # Channels & Distribution
        "channel", "platform", "social", "digital", "media plan",

        # Timeline & Delivery
        "timeline", "deadline", "schedule", "milestone", "launch",

        # Constraints & Compliance
        "requirement", "constraint", "guideline", "compliance", "approval"
    ]

    MIN_KEYWORD_MATCH = 4  # better signal than 2

    @staticmethod
    def is_valid_brief(text: str) -> bool:
        if not text or len(text) < 100:
            logger.warning("Validator: Text too short to be a real brief.")
            return False

        text_lower = text.lower()

        matches = [
            word for word in BriefValidator.REQUIRED_KEYWORDS
            if word in text_lower
        ]

        logger.info(
            f"Validator: Found {len(matches)} brief keywords → {matches}"
        )

        if len(matches) < BriefValidator.MIN_KEYWORD_MATCH:
            logger.warning("Validator: Low confidence brief document.")
            return False

        return True

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Cleans extracted text for LLM processing.
        """

        if not text:
            return ""

        # Normalize unicode (fix weird PDF chars)
        text = unicodedata.normalize("NFKC", text)

        # Remove invisible/control characters
        text = re.sub(r"[\x00-\x1F\x7F-\x9F]", " ", text)

        # Remove repeated punctuation noise
        text = re.sub(r"[•◦▪►]+", " ", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing spaces
        text = text.strip()

        return text
