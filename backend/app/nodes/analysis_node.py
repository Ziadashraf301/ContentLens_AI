from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.analyzer import AnalyzerAgent
from ..utils.output_validator import OutputValidator
from ..agents.judge import JudgeAgent
from ..core.config import settings

def analysis_node(state: AgentState):
    logger.info("--- NODE: ANALYSIS ---")
    
    try:
        agent = AnalyzerAgent()
        input_content = str(state.get("extraction", "")) or state.get("raw_text") or ""
        analysis_result = agent.run(input_content)
        
        # Validate output
        code_valid = OutputValidator.validate_agent_output('analysis', analysis_result)
        if not code_valid:
            logger.warning("Analysis output validation failed")
        
        # LLM Judge evaluation
        evaluation = None
        if settings.EVALUATION:
            judge = JudgeAgent()
            evaluation = judge.evaluate('analysis', str(state["extraction"]), analysis_result)
        
        return {
                "analysis": analysis_result,
                "evaluations": [evaluation],  
                "errors": []
            }

    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Analysis node catastrophic error: {str(e)}")
        return {
            "analysis": "Analysis node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "analysis"
            }],
            "errors": [f"Analysis node failed: {str(e)}"]
        }