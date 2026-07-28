import structlog
logger = structlog.get_logger(__name__)
from ..models.state.state import AgentState
from ..agents.ideation import IdeationAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def ideation_node(state: AgentState):
    logger.info("--- NODE: IDEATION ---")
    input_content = state.get("extraction") or state.get("raw_text") or ""
    agent = IdeationAgent()
    source = "failed"
    ideas_response = None
    try:
        ideas_response = await agent.run(input_content)
        ideas_text = ideas_response.content if hasattr(ideas_response, 'content') else str(ideas_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model=settings.COHERE_MODEL, 
                temperature=settings.TEMPERATURE_IDEATION
            )

            fallback_chain = agent.prompt | fallback_llm
            ideas_response = await fallback_chain.ainvoke({"content": input_content})
            ideas_text = ideas_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered ideation using Cohere.")
        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "ideation": "Ideation node failed completely.",
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "ideation"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    code_valid = OutputValidator.validate_agent_output('ideation', ideas_text)
    if not code_valid:
        logger.warning(f"Ideation output from {source} validation failed strict formatting")

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('ideation', input_content, ideas_text)

    input_tokens = getattr(ideas_response, 'response_metadata', {}).get('prompt_eval_count', 0) if ideas_response else 0
    output_tokens = getattr(ideas_response, 'response_metadata', {}).get('eval_count', 0) if ideas_response else 0

    return {
        "ideation": ideas_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }
