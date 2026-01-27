from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.copywriter import CopywriterAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def copywriter_node(state: AgentState):
    logger.info("--- NODE: COPYWRITER ---")
    agent = CopywriterAgent()
    # Use the raw text as the brief for copywriting
    brief = state.get("raw_text") or str(state.get("extraction", ""))
    user_request = state.get("user_request", "")
    copy = agent.run(str(brief), user_request)
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('copywriter', copy)
    if not code_valid:
        logger.warning("Copywriter output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('copywriter', brief + " | " + user_request, copy)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    current_index = state.get("current_step_index", 0)
    return {
        "copywriting": copy,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }
