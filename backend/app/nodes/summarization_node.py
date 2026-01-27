from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.summarizer import SummarizerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def summarization_node(state: AgentState):
    logger.info("--- NODE: SUMMARIZATION ---")
    agent = SummarizerAgent()
    summary = agent.run(state["extraction"])
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('summary', summary)
    if not code_valid:
        logger.warning("Summary output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('summary', str(state["extraction"]), summary)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "summary": summary,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }

