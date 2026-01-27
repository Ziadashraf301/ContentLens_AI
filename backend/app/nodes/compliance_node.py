from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.compliance import ComplianceAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent


def compliance_node(state: AgentState):
    logger.info("--- NODE: COMPLIANCE ---")
    agent = ComplianceAgent()
    # Check the copywriting first if present, else the summary or extraction
    to_check = state.get("copywriting") or state.get("summary") or str(state.get("extraction", ""))
    compliance_report = agent.run(to_check)
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('compliance', compliance_report)
    if not code_valid:
        logger.warning("Compliance output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('compliance', to_check, str(compliance_report))
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)

    current_index = state.get("current_step_index", 0)
    return {
        "compliance": compliance_report,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }
