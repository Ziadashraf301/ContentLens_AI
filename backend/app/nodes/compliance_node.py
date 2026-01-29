from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.compliance import ComplianceAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

def compliance_node(state: AgentState):
    logger.info("--- NODE: COMPLIANCE ---")
    
    try:
        agent = ComplianceAgent()

        # Check the copywriting first if present, else the summary or extraction
        to_check = str(state.get("extraction", "")) or state.get("raw_text") or ""
        compliance_report = agent.run(to_check)
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('compliance', compliance_report)
        if not code_valid:
            logger.warning("Compliance output validation failed")
        
        # LLM Judge evaluation
        evaluation = None
        if settings.EVALUATION:
            judge = JudgeAgent()
            evaluation = judge.evaluate('compliance', to_check, str(compliance_report))
        
        return {
            "compliance": compliance_report,
            "evaluations": [evaluation],
            "errors": []
        }
        
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Compliance node catastrophic error: {str(e)}")
        return {
            "compliance": {
                "status": "needs_review",
                "overall_risk_score": 0,
                "issues": [],
                "issue_count": 0,
                "categories_flagged": [],
                "summary": f"Compliance check failed: {str(e)}",
                "recommendations": [],
                "checked_at": "",
                "compliance_version": "2.0.0"
            },
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "compliance"
            }],
            "errors": [f"Compliance node failed: {str(e)}"]
        }
