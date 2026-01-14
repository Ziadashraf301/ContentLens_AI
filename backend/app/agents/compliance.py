from typing import Dict, List
from ..core.logging import logger

class ComplianceAgent:
    """Simple rule-based compliance checker for marketing content.

    This agent intentionally uses deterministic checks (no LLM) so it
    can be executed safely in tests and CI without external services.
    It returns a dict with status: 'ok'|'review'|'block' and a list of issues.
    """

    BLOCK_KEYWORDS = ["spam", "sell personal", "sell data", "harvest", "cookie stuffing"]
    REVIEW_KEYWORDS = ["guarantee", "risk-free", "no risk", "best ever", "unlimited"]
    PRIVACY_KEYWORDS = ["personal data", "ssn", "social security", "credit card", "dob", "date of birth"]

    def __init__(self):
        pass

    def run(self, content: str) -> Dict[str, object]:
        logger.info("Agent: Compliance checking content...")
        issues: List[str] = []

        lower = content.lower()

        for kw in self.BLOCK_KEYWORDS:
            if kw in lower:
                issues.append(f"block: contains '{kw}'")

        for kw in self.PRIVACY_KEYWORDS:
            if kw in lower:
                issues.append(f"privacy: contains '{kw}'")

        for kw in self.REVIEW_KEYWORDS:
            if kw in lower:
                issues.append(f"review: contains marketing-claim '{kw}'")

        status = "ok"
        if any(i.startswith("block") for i in issues):
            status = "block"
        elif issues:
            status = "review"

        return {"status": status, "issues": issues}