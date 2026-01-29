from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.refiner import RefinerAgent
from ..agents.judge import JudgeAgent
from ..core.config import settings

from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.refiner import RefinerAgent
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def refiner_node(state: AgentState):
    logger.info("--- NODE: REFINEMENT ---")
    agent = RefinerAgent()
    source = "failed"
    refined_response = None
    try:
        refined_response = await agent.run(state["extraction"], state["user_request"])
        refined_text = refined_response.content if hasattr(refined_response, 'content') else str(refined_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY,
                model="command-r-plus"
            )
            fallback_chain = agent.prompt | fallback_llm
            rescue_response = await fallback_chain.ainvoke({"extraction": str(state["extraction"]), "user_request": state["user_request"]})
            refined_text = rescue_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered refinement using Cohere.")
        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "user_request": "Refiner node failed completely.",
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "refinement"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('refinement', str(state["extraction"]) + " | " + state["user_request"], refined_text)

    input_tokens = getattr(refined_response, 'response_metadata', {}).get('prompt_eval_count', 0) if refined_response else 0
    output_tokens = getattr(refined_response, 'response_metadata', {}).get('eval_count', 0) if refined_response else 0

    return {
        "user_request": refined_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }