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
    def validate_extraction(output: Dict[str, Any]) -> bool:
        """Validate extraction output has required structure."""
        if not isinstance(output, dict):
            return False
        # Check for at least some key fields
        required_keys = ['CampaignName', 'Brand', 'TargetAudience']
        return any(key in output for key in required_keys)

    @staticmethod
    def validate_summary(output: str) -> bool:
        """Validate summary is concise and meaningful."""
        if not isinstance(output, str) or len(output.strip()) < 10:
            return False
        # Should not be too long
        return len(output) < 500

    @staticmethod
    def validate_analysis(output: str) -> bool:
        """Validate analysis has structured format."""
        if not isinstance(output, str):
            return False
        # Check for key sections
        has_missing = "Missing or Unclear Information" in output
        has_recommendations = "Strategic Recommendations" in output
        has_risks = "Potential Risks" in output
        return has_missing or has_recommendations or has_risks

    @staticmethod
    def validate_recommendation(output: str) -> bool:
        """Validate recommendation format."""
        if not isinstance(output, str):
            return False
        # Check for numbered recommendations
        return bool(re.search(r'\d+\.\s*Recommendation:', output))

    @staticmethod
    def validate_ideation(output: str) -> bool:
        """Validate ideation has multiple ideas."""
        if not isinstance(output, str):
            return False
        # Check for numbered titles
        return len(re.findall(r'\d+\.\s*\*\*Title\*\*', output)) >= 3

    @staticmethod
    def validate_copywriter(output: str) -> bool:
        """Validate copywriter has variants."""
        if not isinstance(output, str):
            return False
        # Check for variant format
        return "Variant 1:" in output and "Subject:" in output

    @staticmethod
    def validate_translation(output: str) -> bool:
        """Validate translation is in Arabic."""
        if not isinstance(output, str):
            return False
        # Basic check for Arabic characters
        return bool(re.search(r'[\u0600-\u06FF]', output))

    @staticmethod
    def validate_compliance(output: Dict[str, Any]) -> bool:
        """Validate compliance output structure."""
        if not isinstance(output, dict):
            return False
        return 'status' in output and 'issues' in output

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
                logger.warning(f"Validation failed for {agent_name}: {type(output)}")
            return is_valid
        except Exception as e:
            logger.error(f"Validation error for {agent_name}: {e}")
            return False