from typing import List, TypedDict, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"      # Legal/regulatory violation - must block
    HIGH = "high"              # Major compliance risk - needs review
    MEDIUM = "medium"          # Best practice violation - should fix
    LOW = "low"                # Minor issue - optional improvement
    INFO = "info"              # Informational - good to know


class ComplianceCategory(str, Enum):
    LEGAL = "legal"
    PRIVACY = "privacy"
    ADVERTISING_STANDARDS = "advertising_standards"
    ACCESSIBILITY = "accessibility"
    BRAND_SAFETY = "brand_safety"
    AGE_RESTRICTIONS = "age_restrictions"
    FINANCIAL = "financial"
    HEALTH = "health"


@dataclass(frozen=True)
class ComplianceRule:
    pattern: str
    severity: Severity
    category: ComplianceCategory
    description: str
    regulation: Optional[str] = None  # E.g., "GDPR Art. 5", "FTC Act Sec. 5"
    remediation: Optional[str] = None  # Suggested fix
    context_required: bool = False    # Needs human review even if matched


class Issue(TypedDict):
    severity: str
    category: str
    match: str
    description: str
    regulation: Optional[str]
    remediation: Optional[str]
    context: str  # Surrounding text for context
    position: int  # Character position in original text
    requires_human_review: bool


class ComplianceReport(TypedDict):
    status: str  # "approved", "rejected", "needs_review"
    overall_risk_score: int
    issues: List[Issue]
    issue_count: int
    categories_flagged: List[str]
    summary: str
    recommendations: List[str]
    checked_at: str
    compliance_version: str