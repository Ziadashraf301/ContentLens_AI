from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.extractor import ExtractorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def extraction_node(state: AgentState):
    logger.info("--- NODE: EXTRACTION ---")
    agent = ExtractorAgent()
    source = "failed"
    extraction_response = None
    try:
        extraction_response = await agent.run(state["raw_text"])
        extraction_text = agent.parser.parse(extraction_response.content) if hasattr(extraction_response, 'content') else str(extraction_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model=settings.COHERE_MODEL, 
                temperature=settings.TEMPERATURE_EXTRACTOR
            )

            fallback_chain = agent.prompt | fallback_llm
            extraction_response = await fallback_chain.ainvoke({"text": state["raw_text"]})
            extraction_text = agent.parser.parse(extraction_response.content) if hasattr(extraction_response, 'content') else str(extraction_response)
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered extraction using Cohere.")

        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "extraction": {
                    "status": "failed",
                    "message": "Extraction node failed completely."
                },
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "extraction"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    code_valid = OutputValidator.validate_agent_output('extraction', extraction_text)
    if not code_valid:
        logger.warning(f"Extraction output from {source} validation failed strict formatting")

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('extraction', state["raw_text"], str(extraction_text))

    input_tokens = getattr(extraction_response, 'response_metadata', {}).get('prompt_eval_count', 0) if extraction_response else 0
    output_tokens = getattr(extraction_response, 'response_metadata', {}).get('eval_count', 0) if extraction_response else 0

    return {
        "extraction": extraction_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }