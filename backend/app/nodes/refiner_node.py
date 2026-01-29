from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.refiner import RefinerAgent
from ..agents.judge import JudgeAgent
from ..core.config import settings

def refiner_node(state: AgentState):
    logger.info("--- NODE: REFINEMENT ---")
    try:
        agent = RefinerAgent()
        refined_request = agent.run(state["extraction"], state["user_request"])
        
        # LLM Judge evaluation
        evaluation = None
        if settings.EVALUATION:
            judge = JudgeAgent()
            evaluation = judge.evaluate('refinement', str(state["extraction"]) + " | " + state["user_request"], refined_request)

        return {
            "user_request": refined_request,
            "evaluations": [evaluation],
            "errors": []
        }
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Refiner node catastrophic error: {str(e)}")
        return {
            "user_request": "Refiner node failed completely.",
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "refinement"
            }],
            "errors": [f"Refiner node failed: {str(e)}"]
        }