from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.translator import TranslatorAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def translation_node(state: AgentState):
    logger.info("--- NODE: TRANSLATION ---")
    agent = TranslatorAgent()
    text_to_translate = state["summary"] if state.get("summary") else state["raw_text"]
    translation = agent.run(text_to_translate, state.get("source_lang"))
    
    # Validate output
    code_valid = OutputValidator.validate_agent_output('translation', translation)
    if not code_valid:
        logger.warning("Translation output validation failed")
    
    # LLM Judge evaluation
    judge = JudgeAgent()
    evaluation = judge.evaluate('translation', text_to_translate, translation)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "translation": translation,
        "current_step_index": current_index + 1,
        "evaluations": evaluations
    }