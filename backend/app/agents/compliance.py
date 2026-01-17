from typing import Dict, List, TypedDict
import re
from dataclasses import dataclass
from enum import Enum
from ..core.logging import logger


class Severity(str, Enum):
    BLOCK = "block"
    REVIEW = "review"
    PRIVACY = "privacy"


@dataclass(frozen=True)
class ComplianceRule:
    pattern: str
    severity: Severity
    description: str


class Issue(TypedDict):
    severity: str
    match: str
    description: str


class ComplianceAgent:
    """
    Deterministic compliance agent for marketing content.
    Safe for CI and production pipelines (no LLM usage).
    """

    RULES: List[ComplianceRule] = [
        # BLOCK
        ComplianceRule(
            pattern=r"\b(spam|cookie stuffing|harvest|sell data|sell personal)\b",
            severity=Severity.BLOCK,
            description="Illegal or unethical marketing behavior"
        ),

        # PRIVACY
        ComplianceRule(
            pattern=r"\b(ssn|social security|credit card|dob|date of birth|personal data)\b",
            severity=Severity.PRIVACY,
            description="Sensitive personal data detected"
        ),

        # REVIEW
        ComplianceRule(
            pattern=r"\b(guarantee|risk[- ]?free|best ever|unlimited)\b",
            severity=Severity.REVIEW,
            description="Potential misleading marketing claim"
        ),
    ]

    def run(self, content: str) -> Dict[str, object]:
        logger.info("Agent: Compliance checking content")

        normalized = self._normalize(content)
        issues: List[Issue] = []

        for rule in self.RULES:
            matches = re.findall(rule.pattern, normalized, flags=re.IGNORECASE)

            for match in matches:
                issues.append({
                    "severity": rule.severity.value,
                    "match": match,
                    "description": rule.description
                })

        status = self._resolve_status(issues)

        return {
            "status": status,
            "issues": issues,
            "issue_count": len(issues),
            "risk_score": self._calculate_risk(issues)
        }

    def _normalize(self, text: str) -> str:
        """Basic text normalization pipeline."""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _resolve_status(self, issues: List[Issue]) -> str:
        if any(i["severity"] == Severity.BLOCK for i in issues):
            return Severity.BLOCK.value

        if any(i["severity"] == Severity.PRIVACY for i in issues):
            return Severity.REVIEW.value

        if issues:
            return Severity.REVIEW.value

        return "ok"

    def _calculate_risk(self, issues: List[Issue]) -> int:
        """Simple weighted risk scoring for analytics."""
        weights = {
            Severity.BLOCK.value: 5,
            Severity.PRIVACY.value: 3,
            Severity.REVIEW.value: 1,
        }

        return sum(weights[i["severity"]] for i in issues)
