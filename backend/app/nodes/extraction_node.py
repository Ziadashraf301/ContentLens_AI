from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.extractor import ExtractorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent


def extraction_node(state: AgentState):
    logger.info("--- NODE: EXTRACTION ---")

    try:
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

        return {
            "extraction": result,
            "evaluations": [evaluation],
            "errors": []
        }
    
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Extraction node catastrophic error: {str(e)}")
        return {
            "extraction": "Extraction node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "extraction"
            }],
            "errors": [f"Extraction node failed: {str(e)}"]
        }