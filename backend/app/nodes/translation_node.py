from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.translator import TranslatorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def translation_node(state: AgentState):
    logger.info("--- NODE: TRANSLATION ---")

    try:
        agent = TranslatorAgent()
        text_to_translate = state["raw_text"] or state.get("extraction", "")
        translation = agent.run(text_to_translate, state.get("source_lang"))
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('translation', translation)
        if not code_valid:
            logger.warning("Translation output validation failed")
        
        # LLM Judge evaluation
        judge = JudgeAgent()
        evaluation = judge.evaluate('translation', text_to_translate, translation)
        
        return {
            "translation": translation,
            "evaluations": [evaluation],
            "errors": []
        }
    except Exception as e:
        logger.error(f"Translation node failed with error: {str(e)}")
        return {
            "translation": None,
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "translator"
            }],
            "errors": [f"Translation node failed: {str(e)}"]
        }