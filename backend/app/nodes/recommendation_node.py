from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.recommender import RecommenderAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.recommender import RecommenderAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def recommendation_node(state: AgentState):
    logger.info("--- NODE: RECOMMENDATION ---")
    agent = RecommenderAgent()
    input_content = state.get("extraction") or state.get("raw_text")  or ""
    user_request = state.get("user_request", "")
    source = "failed"
    recommendations_response = None
    try:
        recommendations_response = await agent.run(input_content, user_request)
        recommendations_text = recommendations_response.content if hasattr(recommendations_response, 'content') else str(recommendations_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model=settings.COHERE_MODEL, 
                temperature=settings.TEMPERATURE_RECOMMENDER
            )

            fallback_chain = agent.prompt | fallback_llm
            recommendations_response = await fallback_chain.ainvoke({"content": input_content, "user_request": user_request})
            recommendations_text = recommendations_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered recommendations using Cohere.")
        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "recommendation": "Recommendation node failed completely.",
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "recommendation"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    code_valid = OutputValidator.validate_agent_output('recommendation', recommendations_text)
    if not code_valid:
        logger.warning(f"Recommendation output from {source} validation failed strict formatting")

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('recommendation', input_content + " | " + user_request, recommendations_text)

    input_tokens = getattr(recommendations_response, 'response_metadata', {}).get('prompt_eval_count', 0) if recommendations_response else 0
    output_tokens = getattr(recommendations_response, 'response_metadata', {}).get('eval_count', 0) if recommendations_response else 0

    return {
        "recommendation": recommendations_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }