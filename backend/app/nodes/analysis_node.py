from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.analyzer import AnalyzerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings
from langchain_cohere import ChatCohere

async def analysis_node(state: AgentState):
    logger.info("--- NODE: ANALYSIS ---")
    input_content = str(state.get("extraction", "")) or state.get("raw_text") or ""
    
    analysis_text = ""
    source = "failed"
    agent = AnalyzerAgent()

    try:
        # PRIMARY: Try Local Ollama
        analysis_result = await agent.run(input_content)
        analysis_text = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
        source = "local_ollama"

    except Exception as e:
        # SECONDARY: Fallback to Cohere if Ollama fails after all retries
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")

        try:
            # Initialize Fallback
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model="command-r-plus"
            )
            
            # Reuse the agent's prompt template
            fallback_chain = agent.prompt | fallback_llm

            # Rescue Call
            rescue_response = await fallback_chain.ainvoke({"content": input_content})
            analysis_text = rescue_response.content
            source = "cloud_cohere_fallback"
            logger.info("Successfully recovered analysis using Cohere.")

        except Exception as cohere_error:
            # TOTAL FAILURE: Both local and cloud failed
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {
                "analysis": "Analysis node failed completely.",
                "evaluations": [{
                    "score": 0, 
                    "reasoning": "Both local (Ollama) and cloud (Cohere) providers are offline.", 
                    "agent_type": "analysis"
                }],
                "errors": [f"Ollama error: {e}", f"Cohere error: {cohere_error}"]
            }

    # SUCCESS PATH (Ollama OR Cohere worked)
    # Validate output format
    code_valid = OutputValidator.validate_agent_output('analysis', analysis_text)
    if not code_valid:
        logger.warning(f"Analysis output from {source} validation failed strict formatting")
    
    # LLM Judge evaluation
    evaluation = None
    if settings.EVALUATION:
        judge = JudgeAgent()
        evaluation = await judge.evaluate('analysis', state["raw_text"], analysis_text)

    input_tokens = getattr(analysis_result, 'response_metadata', {}).get('prompt_eval_count', 0) if analysis_result else 0
    output_tokens = getattr(analysis_result, 'response_metadata', {}).get('eval_count', 0) if analysis_result else 0
    
    return {
        "analysis": analysis_text,
        "evaluations": [evaluation] if evaluation else [],
        "errors": [],
        "metadata": {"source": source, "input_tokens": input_tokens, "output_tokens": output_tokens}
    }