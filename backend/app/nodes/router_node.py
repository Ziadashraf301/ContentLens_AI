
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState


def router_node(state: AgentState):
    """
    Routes the request to determine which agents should handle it.
    
    In the parallel execution model, this node:
    1. Calls RouterAgent to determine which agents are needed
    2. Returns a list of agents in next_steps
    3. The parallel_agents_node will execute all of them concurrently
    
    No longer uses routing_logic() for sequential conditional routing.
    """
    if not state.get("next_steps"):
        agent = RouterAgent()
        decisions = agent.decide(state["user_request"])
        
        logger.info(
            f"🔀 Router: Identified {len(decisions)} agents to execute in parallel: {decisions}"
        )
        
        return {
            "next_steps": decisions,
            "pending_agents": decisions,
            "current_step_index": 0,
            "agent_outputs": {},
            "agent_metadata": {},
            "agent_errors": {},
            "agent_evaluations": {},
        }

    steps = state.get("next_steps", [])
    index = state.get("current_step_index", 0)

    if index < len(steps):
        current_task = steps[index]
        logger.info(f"Routing: Task {index + 1}/{len(steps)} -> {current_task}")

        # Map a task like 'summarize' to a channel 'to_summarize'
        channel = f"to_{current_task}"
        # Validate known channels (avoid returning arbitrary values)
        valid_channels = {
            "to_summarize", "to_translate", "to_analyze", "to_recommend",
            "to_ideate", "to_copywrite", "to_compliance"
        }
        if channel in valid_channels:
            return channel
        logger.warning(f"Routing: Unknown task '{current_task}', routing to END")
        return "end"

    logger.info("Routing: All tasks completed, going to END")
    return "end"