from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.copywriter import CopywriterAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

from langchain_cohere import ChatCohere

async def copywriter_node(state: AgentState):
    logger.info("--- NODE: COPYWRITER ---")

    brief = str(state.get("extraction", "")) or state.get("raw_text") or ""
    user_request = state.get("user_request", "")
    agent = CopywriterAgent()
    source = "failed"
    copy_response = None
    
    try:
        copy_response = await agent.run(brief, user_request)
        copy_text = copy_response.content if hasattr(copy_response, 'content') else str(copy_response)
        source = "local_ollama"

    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY,
                model="command-r-plus"
            )

            fallback_chain = agent.prompt | fallback_llm
            rescue_response = await fallback_chain.ainvoke({"brief": brief, "user_request": user_request})
            
            copy_text = rescue_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered copywriting using Cohere.")

        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "copywriting": "Copywriter node failed completely.",
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "copywriter"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    # Validate output format
    code_valid = OutputValidator.validate_agent_output('copywriter', copy_text)
    if not code_valid:
        logger.warning(f"Copywriter output from {source} validation failed strict formatting")

    # LLM Judge evaluation
    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('copywriter', brief + " | " + user_request, copy_text)

    # Extract token counts if available
    input_tokens = getattr(copy_response, 'response_metadata', {}).get('prompt_eval_count', 0) if copy_response else 0
    output_tokens = getattr(copy_response, 'response_metadata', {}).get('eval_count', 0) if copy_response else 0

    return {
        "copywriting": copy_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }