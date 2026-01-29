from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.copywriter import CopywriterAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def copywriter_node(state: AgentState):
    logger.info("--- NODE: COPYWRITER ---")

    try:
        agent = CopywriterAgent()

        # Use the raw text as the brief for copywriting
        brief = str(state.get("extraction", "")) or state.get("raw_text") or ""
        user_request = state.get("user_request", "")
        copy = agent.run(str(brief), user_request)
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('copywriter', copy)
        if not code_valid:
            logger.warning("Copywriter output validation failed")
        
        # LLM Judge evaluation
        judge = JudgeAgent()
        evaluation = judge.evaluate('copywriter', brief + " | " + user_request, copy)
        
        return {
                "copywriting": copy,
                "evaluations": [evaluation],  
                "errors": []
                }

    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Copywriter node catastrophic error: {str(e)}")
        return {
            "copywriting": "Copywriter node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "copywriter"
            }],
            "errors": [f"Copywriter node failed: {str(e)}"]
        }