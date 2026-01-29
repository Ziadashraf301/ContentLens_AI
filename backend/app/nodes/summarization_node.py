from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.summarizer import SummarizerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent

def summarization_node(state: AgentState):
    logger.info("--- NODE: SUMMARIZATION ---")
    try:
        agent = SummarizerAgent()
        summary = agent.run(state["extraction"])
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('summary', summary)
        if not code_valid:
            logger.warning("Summary output validation failed")
        
        # LLM Judge evaluation
        judge = JudgeAgent()
        evaluation = judge.evaluate('summary', str(state["extraction"]), summary)
        
        return {
            "summary": summary,
            "evaluations": [evaluation],
            "errors": []
        }
    except Exception as e:
        logger.error(f"Summarization node failed with error: {str(e)}")
        return {
            "summary": None,
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "summarizer"
            }],
            "errors": [f"Summarization node failed: {str(e)}"]
        }

