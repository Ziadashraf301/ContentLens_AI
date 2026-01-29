
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState


def router_node(state: AgentState):
    logger.info("--- NODE: ROUTER ---")
    try:
        if not state.get("next_steps"):
            agent = RouterAgent()
            decisions = agent.decide(state["user_request"])
            return {
                "next_steps": decisions,
                "evaluations": [],
                "errors": []
                    }
    except Exception as e:
        # Only catches catastrophic failures (agent init, etc.)
        logger.error(f"Router node catastrophic error: {str(e)}")
        return {
            "next_steps": [],
            "evaluations": [{
                "score": 0,
                "reasoning": f"Node-level failure: {str(e)}",
                "agent_type": "router"
            }],
            "errors": [f"Router node failed: {str(e)}"]
        }