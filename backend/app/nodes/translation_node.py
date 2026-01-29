from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.translator import TranslatorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.translator import TranslatorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def translation_node(state: AgentState):
    logger.info("--- NODE: TRANSLATION ---")
    agent = TranslatorAgent()
    text_to_translate = state["raw_text"] or state.get("extraction", "")
    source = "failed"
    translation_response = None
    try:
        translation_response = await agent.run(text_to_translate, state.get("source_lang"))
        translation_text = translation_response.content if hasattr(translation_response, 'content') else str(translation_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY,
                model="command-r-plus"
            )
            fallback_chain = agent.prompt | fallback_llm
            rescue_response = await fallback_chain.ainvoke({"content": text_to_translate})
            translation_text = rescue_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered translation using Cohere.")
        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "translation": None,
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "translator"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    code_valid = OutputValidator.validate_agent_output('translation', translation_text)
    if not code_valid:
        logger.warning(f"Translation output from {source} validation failed strict formatting")

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('translation', text_to_translate, translation_text)

    input_tokens = getattr(translation_response, 'response_metadata', {}).get('prompt_eval_count', 0) if translation_response else 0
    output_tokens = getattr(translation_response, 'response_metadata', {}).get('eval_count', 0) if translation_response else 0

    return {
        "translation": translation_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }