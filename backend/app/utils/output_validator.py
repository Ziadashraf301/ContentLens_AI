"""
Output validation utilities for agent responses.
Ensures outputs meet expected formats and quality standards.
"""

import re
from typing import Dict, Any, List
from ..core.logging import logger

class OutputValidator:
    """Validates agent outputs against expected formats."""

    @staticmethod
    def validate_extraction(output: Any) -> bool:
        """Validate extraction output has required structure."""
        # Handle both dict and string outputs
        if isinstance(output, str):
            # Check if it looks like extracted information
            return len(output.strip()) > 50
        
        if not isinstance(output, dict):
            return False
        
        # Check for at least some key fields
        required_keys = ['CampaignName', 'Brand', 'TargetAudience', 'CoreMessage', 'ActionableDataPoints', 'CallToAction', 'AdvertiserContact']
        return any(key in output for key in required_keys)

    @staticmethod
    def validate_summary(output: str) -> bool:
        """Validate summary is concise and meaningful."""
        if not isinstance(output, str) or len(output.strip()) < 10:
            return False
        # Should not be too long
        return len(output) < 1000

    @staticmethod
    def validate_analysis(output: str) -> bool:
        """Validate analysis has structured format."""
        if not isinstance(output, str):
            return False
        
        # Check for meaningful content
        if len(output.strip()) < 50:
            return False
            
        # Check for key sections (case-insensitive)
        output_lower = output.lower()
        has_analysis_content = any(keyword in output_lower for keyword in [
            'missing', 'unclear', 'recommendation', 'risk', 'opportunity',
            'strength', 'weakness', 'threat', 'analysis', 'insight'
        ])
        
        return has_analysis_content

    @staticmethod
    def validate_recommendation(output: str) -> bool:
        """Validate recommendation format."""
        if not isinstance(output, str):
            return False
        
        # More flexible validation
        if len(output.strip()) < 20:
            return False
            
        # Check for numbered recommendations or bullet points
        has_numbers = bool(re.search(r'\d+[\.)]\s*', output))
        has_bullets = bool(re.search(r'[-•*]\s+', output))
        has_recommendation_keyword = 'recommendation' in output.lower()
        
        return has_numbers or has_bullets or has_recommendation_keyword

    @staticmethod
    def validate_ideation(output: str) -> bool:
        """Validate ideation has multiple ideas."""
        if not isinstance(output, str):
            return False
        
        if len(output.strip()) < 50:
            return False
            
        # Check for numbered titles or multiple ideas
        has_numbered = len(re.findall(r'\d+[\.)]\s*', output)) >= 2
        has_title_markers = len(re.findall(r'\*\*.*\*\*', output)) >= 2
        
        return has_numbered or has_title_markers

    @staticmethod
    def validate_copywriter(output: str) -> bool:
        """Validate copywriter has variants."""
        if not isinstance(output, str):
            return False
        
        if len(output.strip()) < 30:
            return False
            
        # Check for variant format (flexible)
        has_variants = 'variant' in output.lower()
        has_subject = 'subject' in output.lower()
        has_body = 'body' in output.lower()
        has_cta = 'cta' in output.lower() or 'call to action' in output.lower()
        
        # At least 2 of these should be present
        markers = sum([has_variants, has_subject, has_body, has_cta])
        return markers >= 2

    @staticmethod
    def validate_translation(output: str) -> bool:
        """Validate translation is in Arabic."""
        if not isinstance(output, str):
            return False
        
        if len(output.strip()) < 10:
            return False
            
        # Basic check for Arabic characters
        return bool(re.search(r'[\u0600-\u06FF]', output))

    @staticmethod
    def validate_compliance(output: Any) -> bool:
        """Validate ComplianceAgent output (updated for v2.0.0)."""
        
        # Compliance now returns ComplianceReport dict
        if not isinstance(output, dict):
            return False

        # Required keys from new ComplianceReport structure
        required_keys = {
            "status", 
            "overall_risk_score", 
            "issues", 
            "issue_count", 
            "categories_flagged",
            "summary",
            "recommendations",
            "checked_at",
            "compliance_version"
        }
        
        if not required_keys.issubset(output.keys()):
            logger.warning(f"Compliance output missing required keys. Has: {output.keys()}")
            return False

        # Status validation (new values)
        status = output.get("status")
        if status not in {"approved", "rejected", "needs_review"}:
            logger.warning(f"Invalid compliance status: {status}")
            return False

        # Issues validation (updated structure)
        issues = output.get("issues")
        if not isinstance(issues, list):
            return False

        for issue in issues:
            if not isinstance(issue, dict):
                return False

            # Updated required fields
            required_issue_keys = {
                "severity", 
                "category", 
                "match", 
                "description",
                "context",
                "position",
                "requires_human_review"
            }
            
            if not required_issue_keys.issubset(issue.keys()):
                logger.warning(f"Issue missing required keys: {issue.keys()}")
                return False

            # Validate severity (new values)
            if issue["severity"] not in {"critical", "high", "medium", "low", "info"}:
                logger.warning(f"Invalid severity: {issue['severity']}")
                return False
            
            # Validate category
            valid_categories = {
                "legal", "privacy", "advertising_standards", 
                "accessibility", "brand_safety", "age_restrictions",
                "financial", "health"
            }
            if issue["category"] not in valid_categories:
                logger.warning(f"Invalid category: {issue['category']}")
                return False

            # Validate types
            if not isinstance(issue["match"], str):
                return False
            if not isinstance(issue["description"], str):
                return False
            if not isinstance(issue["context"], str):
                return False
            if not isinstance(issue["position"], int):
                return False
            if not isinstance(issue["requires_human_review"], bool):
                return False

        # issue_count validation
        issue_count = output.get("issue_count")
        if not isinstance(issue_count, int) or issue_count < 0:
            return False
        if issue_count != len(issues):
            logger.warning(f"Issue count mismatch: {issue_count} != {len(issues)}")
            return False

        # overall_risk_score validation (0-100 scale now)
        risk_score = output.get("overall_risk_score")
        if not isinstance(risk_score, int):
            return False
        if not (0 <= risk_score <= 100):
            logger.warning(f"Risk score out of range: {risk_score}")
            return False

        # categories_flagged validation
        categories_flagged = output.get("categories_flagged")
        if not isinstance(categories_flagged, list):
            return False
        
        # summary validation
        summary = output.get("summary")
        if not isinstance(summary, str) or len(summary) < 10:
            logger.warning("Summary too short or invalid")
            return False

        # recommendations validation
        recommendations = output.get("recommendations")
        if not isinstance(recommendations, list):
            return False
        if not all(isinstance(r, str) for r in recommendations):
            logger.warning("Invalid recommendation format")
            return False

        # checked_at validation (ISO format timestamp)
        checked_at = output.get("checked_at")
        if not isinstance(checked_at, str):
            return False
        
        # compliance_version validation
        compliance_version = output.get("compliance_version")
        if not isinstance(compliance_version, str):
            return False

        return True


    @classmethod
    def validate_agent_output(cls, agent_name: str, output: Any) -> bool:
        """Validate output for specific agent."""
        validators = {
            'extraction': cls.validate_extraction,
            'summary': cls.validate_summary,
            'analysis': cls.validate_analysis,
            'recommendation': cls.validate_recommendation,
            'ideation': cls.validate_ideation,
            'copywriter': cls.validate_copywriter,
            'translation': cls.validate_translation,
            'compliance': cls.validate_compliance,
        }

        validator = validators.get(agent_name)
        if not validator:
            logger.warning(f"No validator for agent: {agent_name}")
            return True  # Default to valid if no validator

        try:
            is_valid = validator(output)
            if not is_valid:
                logger.warning(f"Validation failed for {agent_name}: {type(output).__name__}, length: {len(str(output))}")
            return is_valid
        except Exception as e:
            logger.error(f"Validation error for {agent_name}: {e}")
            return False