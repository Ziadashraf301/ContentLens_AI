from typing import Dict, List
import re
from ..core.logging import logger
from ..models.schemas.Compliance import (Severity, ComplianceCategory, ComplianceRule, Issue, ComplianceReport)
from datetime import datetime

class ComplianceAgent:
    """
    Comprehensive compliance agent for marketing content.
    Mimics real compliance review with nuanced rules and context awareness.
    """

    VERSION = "2.0.0"

    # Expanded realistic ruleset
    RULES: List[ComplianceRule] = [
        # === CRITICAL - Legal/Regulatory Violations ===
        ComplianceRule(
            pattern=r"\b(guarantee(?:d)?\s+(?:results?|income|profit|return|ROI))\b",
            severity=Severity.CRITICAL,
            category=ComplianceCategory.LEGAL,
            description="Unqualified income/results guarantee (FTC violation)",
            regulation="FTC Act Section 5 (Deceptive Advertising)",
            remediation="Add clear disclaimers: 'Results may vary' or 'Typical results not guaranteed'",
            context_required=True
        ),
        ComplianceRule(
            pattern=r"\b(cure|treat|diagnose|prevent)\s+(?:cancer|diabetes|COVID|disease)\b",
            severity=Severity.CRITICAL,
            category=ComplianceCategory.HEALTH,
            description="Unauthorized health claim",
            regulation="FDA regulations - health claims require substantiation",
            remediation="Remove medical claims or add FDA disclaimer",
            context_required=False
        ),
        ComplianceRule(
            pattern=r"\b(sell|share|trade)\s+(?:your|user)?\s*(?:personal)?\s*(?:data|information)\b",
            severity=Severity.CRITICAL,
            category=ComplianceCategory.PRIVACY,
            description="Unauthorized data selling/sharing statement",
            regulation="GDPR Art. 6, CCPA",
            remediation="Remove claim or ensure proper consent mechanisms are in place"
        ),

        # === HIGH - Major Compliance Risks ===
        ComplianceRule(
            pattern=r"\b(risk[- ]?free|no risk|zero risk|100%\s+safe)\b",
            severity=Severity.HIGH,
            category=ComplianceCategory.ADVERTISING_STANDARDS,
            description="Absolute claim without substantiation",
            regulation="FTC Truth in Advertising",
            remediation="Qualify claim or provide substantiation",
            context_required=True
        ),
        ComplianceRule(
            pattern=r"\b(best|#1|top|leading|premier)\s+(?:in\s+(?:the\s+)?(?:world|industry|market))\b",
            severity=Severity.HIGH,
            category=ComplianceCategory.ADVERTISING_STANDARDS,
            description="Superlative claim requires substantiation",
            regulation="Advertising Standards (substantiation required)",
            remediation="Provide third-party verification or remove claim"
        ),
        ComplianceRule(
            pattern=r"\b(?:limited|exclusive)\s+(?:time|offer).*(?:act now|hurry|don't miss)\b",
            severity=Severity.HIGH,
            category=ComplianceCategory.ADVERTISING_STANDARDS,
            description="Artificial urgency/scarcity tactic",
            regulation="Consumer Protection regulations",
            remediation="Ensure offer terms are genuine and clearly disclosed",
            context_required=True
        ),
        ComplianceRule(
            pattern=r"\b(?:ssn|social security|credit card|passport|driver['\s]?license)\s*(?:number)?\b",
            severity=Severity.HIGH,
            category=ComplianceCategory.PRIVACY,
            description="Sensitive PII reference detected",
            regulation="GDPR Art. 9, PCI-DSS",
            remediation="Remove PII references or add security disclosures"
        ),

        # === MEDIUM - Best Practice Violations ===
        ComplianceRule(
            pattern=r"\b(earn|make)\s+\$?\d+[,\d]*\s*(?:per|a|\/)\s*(?:day|week|month|hour)\b",
            severity=Severity.MEDIUM,
            category=ComplianceCategory.FINANCIAL,
            description="Income claim requires disclaimer",
            regulation="FTC Endorsement Guidelines",
            remediation="Add income disclaimer: 'Results not typical'",
            context_required=True
        ),
        ComplianceRule(
            pattern=r"\b(click here|click now|download now)\b",
            severity=Severity.MEDIUM,
            category=ComplianceCategory.ACCESSIBILITY,
            description="Non-accessible link text",
            regulation="WCAG 2.1 AA (Web accessibility)",
            remediation="Use descriptive link text (e.g., 'Download the report')"
        ),
        ComplianceRule(
            pattern=r"\b(?:kids?|children?|teen|minor)\s+(?:under|age)\s*\d+\b",
            severity=Severity.MEDIUM,
            category=ComplianceCategory.AGE_RESTRICTIONS,
            description="Content targeting minors detected",
            regulation="COPPA (Children's Online Privacy Protection Act)",
            remediation="Ensure COPPA compliance if targeting under-13"
        ),

        # === LOW - Minor Issues ===
        ComplianceRule(
            pattern=r"\b(free trial|try free)\b(?!.*(?:terms|conditions|cancel))",
            severity=Severity.LOW,
            category=ComplianceCategory.ADVERTISING_STANDARDS,
            description="Free trial offer should include terms",
            remediation="Add link to terms and cancellation policy"
        ),
        ComplianceRule(
            pattern=r"\b(?:he|him|his|she|her)\b",
            severity=Severity.LOW,
            category=ComplianceCategory.BRAND_SAFETY,
            description="Gender-specific language detected (inclusivity best practice)",
            remediation="Consider gender-neutral language (they/them)"
        ),

        # === INFO - Good to Know ===
        ComplianceRule(
            pattern=r"\b(?:prices?|costs?|fees?)\b(?!.*subject to change)",
            severity=Severity.INFO,
            category=ComplianceCategory.ADVERTISING_STANDARDS,
            description="Price mentioned without change disclaimer",
            remediation="Consider adding: 'Prices subject to change'"
        ),
    ]

    async def run(self, content: str) -> ComplianceReport:
        """
        Perform comprehensive compliance check.
        Returns detailed report with context and remediation guidance.
        """
        logger.info("Agent: Compliance performing comprehensive review...")

        normalized = self._normalize(content)
        issues: List[Issue] = []

        for rule in self.RULES:
            issues.extend(self._check_rule(rule, content, normalized))

        # Generate human-readable summary
        summary = self._generate_summary(issues)
        recommendations = self._generate_recommendations(issues)
        status = self._resolve_status(issues)

        report: ComplianceReport = {
            "status": status,
            "overall_risk_score": self._calculate_risk(issues),
            "issues": issues,
            "issue_count": len(issues),
            "categories_flagged": list(set(i["category"] for i in issues)),
            "summary": summary,
            "recommendations": recommendations,
            "checked_at": datetime.utcnow().isoformat(),
            "compliance_version": self.VERSION
        }

        logger.info(f"Compliance: Status={status}, Issues={len(issues)}, Risk={report['overall_risk_score']}")
        return report

    def _check_rule(self, rule: ComplianceRule, original: str, normalized: str) -> List[Issue]:
        """Check a single rule and extract context."""
        issues: List[Issue] = []
        
        for match in re.finditer(rule.pattern, normalized, flags=re.IGNORECASE):
            matched_text = match.group()
            position = match.start()
            
            # Extract context (50 chars before and after)
            context_start = max(0, position - 50)
            context_end = min(len(original), position + len(matched_text) + 50)
            context = original[context_start:context_end].strip()

            issues.append({
                "severity": rule.severity.value,
                "category": rule.category.value,
                "match": matched_text,
                "description": rule.description,
                "regulation": rule.regulation,
                "remediation": rule.remediation,
                "context": f"...{context}...",
                "position": position,
                "requires_human_review": rule.context_required
            })

        return issues

    def _normalize(self, text: str) -> str:
        """Normalize text for pattern matching."""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        text = re.sub(r"[''']", "'", text)  # Normalize quotes
        return text.strip()

    def _resolve_status(self, issues: List[Issue]) -> str:
        """
        Determine overall compliance status.
        Mimics human compliance reviewer decision-making.
        """
        if any(i["severity"] == Severity.CRITICAL.value for i in issues):
            return "rejected"

        high_issues = [i for i in issues if i["severity"] == Severity.HIGH.value]
        if len(high_issues) >= 3:  # Multiple high-severity issues
            return "rejected"
        
        if high_issues or any(i["requires_human_review"] for i in issues):
            return "needs_review"

        medium_low_count = sum(1 for i in issues if i["severity"] in [Severity.MEDIUM.value, Severity.LOW.value])
        if medium_low_count >= 5:  # Many minor issues compound
            return "needs_review"

        if issues:
            return "needs_review"  # Any issues warrant review

        return "approved"

    def _calculate_risk(self, issues: List[Issue]) -> int:
        """Calculate weighted risk score (0-100 scale)."""
        weights = {
            Severity.CRITICAL.value: 25,
            Severity.HIGH.value: 10,
            Severity.MEDIUM.value: 3,
            Severity.LOW.value: 1,
            Severity.INFO.value: 0,
        }

        base_score = sum(weights.get(i["severity"], 0) for i in issues)
        
        # Cap at 100
        return min(100, base_score)

    def _generate_summary(self, issues: List[Issue]) -> str:
        """Generate human-readable summary."""
        if not issues:
            return "Content passed compliance review with no issues detected."

        critical = sum(1 for i in issues if i["severity"] == Severity.CRITICAL.value)
        high = sum(1 for i in issues if i["severity"] == Severity.HIGH.value)
        medium = sum(1 for i in issues if i["severity"] == Severity.MEDIUM.value)
        low = sum(1 for i in issues if i["severity"] == Severity.LOW.value)

        parts = []
        if critical:
            parts.append(f"{critical} critical violation(s)")
        if high:
            parts.append(f"{high} high-risk issue(s)")
        if medium:
            parts.append(f"{medium} medium-risk issue(s)")
        if low:
            parts.append(f"{low} minor issue(s)")

        return f"Detected {', '.join(parts)}. Review required before publication."

    def _generate_recommendations(self, issues: List[Issue]) -> List[str]:
        """Generate actionable recommendations."""
        if not issues:
            return ["Content is compliant. No action required."]

        recommendations = []
        
        # Group by category
        by_category: Dict[str, List[Issue]] = {}
        for issue in issues:
            by_category.setdefault(issue["category"], []).append(issue)

        # Prioritize critical/high issues
        critical_high = [i for i in issues if i["severity"] in [Severity.CRITICAL.value, Severity.HIGH.value]]
        if critical_high:
            recommendations.append(f"URGENT: Address {len(critical_high)} critical/high-severity issues immediately.")

        # Category-specific recommendations
        for category, cat_issues in sorted(by_category.items()):
            if cat_issues[0]["severity"] in [Severity.CRITICAL.value, Severity.HIGH.value]:
                recommendations.append(f"{category.replace('_', ' ').title()}: Review {len(cat_issues)} flagged item(s).")

        # Add specific remediations for top 3 issues
        for issue in sorted(issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["severity"], 3))[:3]:
            if issue["remediation"]:
                recommendations.append(f"• {issue['remediation']}")

        return recommendations[:5]  # Limit to top 5
