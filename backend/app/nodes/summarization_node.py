from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.summarizer import SummarizerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.summarizer import SummarizerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def summarization_node(state: AgentState):
    logger.info("--- NODE: SUMMARIZATION ---")
    agent = SummarizerAgent()
    source = "failed"
    summary_response = None
    try:
        summary_response = await agent.run(state["extraction"])
        summary_text = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)
        source = "local_ollama"
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model=settings.COHERE_MODEL, 
                temperature=settings.TEMPERATURE_SUMMARIZER
            )
            fallback_chain = agent.prompt | fallback_llm
            summary_response = await fallback_chain.ainvoke({"extraction_data": str(state["extraction"])})
            summary_text = summary_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered summary using Cohere.")
        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "summary": None,
                "evaluations": [{
                    "score": 0,
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.",
                    "agent_type": "summarizer"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    code_valid = OutputValidator.validate_agent_output('summary', summary_text)
    if not code_valid:
        logger.warning(f"Summary output from {source} validation failed strict formatting")

    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('summary', str(state["extraction"]), summary_text)

    input_tokens = getattr(summary_response, 'response_metadata', {}).get('prompt_eval_count', 0) if summary_response else 0
    output_tokens = getattr(summary_response, 'response_metadata', {}).get('eval_count', 0) if summary_response else 0

    return {
        "summary": summary_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }

