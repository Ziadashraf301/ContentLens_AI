
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState


def router_node(state: AgentState):
    if not state.get("next_steps"):
        agent = RouterAgent()
        decisions = agent.decide(state["user_request"])
        return {"next_steps": decisions, "current_step_index": 0}
    return {}


def routing_logic(state: AgentState):
    """
    Routes to the next task in the list, or END if all done.
    This function returns a *channel name* (which the graph maps to a node),
    so we prefix task names with 'to_' to avoid collisions with node names.
    """
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