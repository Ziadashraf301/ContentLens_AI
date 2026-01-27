from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.ideation import IdeationAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
 
def ideation_node(state: AgentState):
    logger.info("--- NODE: IDEATION ---")
    agent = IdeationAgent()
    input_content = state.get("extraction") or state.get("raw_text") or ""
    ideas = agent.run(input_content)
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('ideation', ideas)
    if not code_valid:
        logger.warning("Ideation output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('ideation', input_content, ideas)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)

    current_index = state.get("current_step_index", 0)
    return {
        "ideation": ideas,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }
