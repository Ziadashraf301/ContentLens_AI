from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.ideation import IdeationAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

def ideation_node(state: AgentState):
    logger.info("--- NODE: IDEATION ---")

    try:
        agent = IdeationAgent()
        input_content = state.get("extraction") or state.get("raw_text") or ""
        ideas = agent.run(input_content)
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('ideation', ideas)
        if not code_valid:
            logger.warning("Ideation output validation failed")
        
        # LLM Judge evaluation
        evaluation = None
        if settings.EVALUATION:
            judge = JudgeAgent()
            evaluation = judge.evaluate('ideation', input_content, ideas)
        
        return {
                "ideation": ideas,
                "evaluations": [evaluation],
                "errors": []
                }
    
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Ideation node catastrophic error: {str(e)}")
        return {
            "ideation": "Ideation node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "ideation"
            }],
            "errors": [f"Ideation node failed: {str(e)}"]
        }
