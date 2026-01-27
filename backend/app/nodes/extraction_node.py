from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.extractor import ExtractorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent


def extraction_node(state: AgentState):
    logger.info("--- NODE: EXTRACTION ---")
    agent = ExtractorAgent()
    # The raw_text comes from the FileLoader in the workflow
    result = agent.run(state["raw_text"])
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('extraction', result)
    if not code_valid:
        logger.warning("Extraction output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('extraction', state["raw_text"], str(result))
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    return {"extraction": result, "evaluations": evaluations}