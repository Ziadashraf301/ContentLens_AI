from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.recommender import RecommenderAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent


def recommendation_node(state: AgentState):
    logger.info("--- NODE: RECOMMENDATION ---")
    try:
        agent = RecommenderAgent()

        input_content = state.get("extraction") or state.get("raw_text")  or ""
        user_request = state.get("user_request", "")
        recommendations = agent.run(input_content, user_request)
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('recommendation', recommendations)
        if not code_valid:
            logger.warning("Recommendation output validation failed")
        
        # LLM Judge evaluation
        judge = JudgeAgent()
        evaluation = judge.evaluate('recommendation', input_content + " | " + user_request, recommendations)
        
        return {
                "recommendation": recommendations,
                "evaluations": [evaluation],
                "errors": []
                }
        
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Recommendation node catastrophic error: {str(e)}")
        return {
            "recommendation": "Recommendation node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "recommendation"
            }],
            "errors": [f"Recommendation node failed: {str(e)}"]
        }