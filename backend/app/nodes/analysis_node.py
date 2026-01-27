from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.analyzer import AnalyzerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def analysis_node(state: AgentState):
    logger.info("--- NODE: ANALYSIS ---")
    agent = AnalyzerAgent()
    analysis_result = agent.run(state["extraction"])
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('analysis', analysis_result)
    if not code_valid:
        logger.warning("Analysis output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('analysis', str(state["extraction"]), analysis_result)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "analysis": analysis_result,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }