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
        
        # More lenient validation - check for meaningful content
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
        """Validate ComplianceAgent output used by compliance_node."""

        # Compliance node ALWAYS returns structured dict
        if not isinstance(output, dict):
            return False

        # Required schema from ComplianceAgent.run()
        required_keys = {"status", "issues", "issue_count", "risk_score"}
        if not required_keys.issubset(output):
            return False

        # Status validation
        status = output.get("status")
        if status not in {"ok", "review", "block"}:
            return False

        # Issues validation
        issues = output.get("issues")
        if not isinstance(issues, list):
            return False

        for issue in issues:
            if not isinstance(issue, dict):
                return False

            if not {"severity", "match", "description"}.issubset(issue):
                return False

            if issue["severity"] not in {"block", "review", "privacy"}:
                return False

            if not isinstance(issue["match"], str):
                return False

            if not isinstance(issue["description"], str):
                return False

        # issue_count validation
        issue_count = output.get("issue_count")
        if not isinstance(issue_count, int):
            return False

        if issue_count != len(issues):
            return False

        # risk_score validation
        risk_score = output.get("risk_score")
        if not isinstance(risk_score, int):
            return False

        if risk_score < 0:
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