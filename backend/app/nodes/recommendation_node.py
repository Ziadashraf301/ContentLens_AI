from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.recommender import RecommenderAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent


def recommendation_node(state: AgentState):
    logger.info("--- NODE: RECOMMENDATION ---")
    agent = RecommenderAgent()
    input_content = state.get("raw_text") or state.get("extraction") or state.get("analysis") or ""
    user_request = state.get("user_request", "")
    recommendations = agent.run(input_content, user_request)
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('recommendation', recommendations)
    if not code_valid:
        logger.warning("Recommendation output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('recommendation', input_content + " | " + user_request, recommendations)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "recommendation": recommendations,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }