
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState


def router_node(state: AgentState):
    """
    Router node that decides which agents to run.
    Groups agents that can run in parallel into batches.
    """
    if not state.get("next_steps"):
        agent = RouterAgent()
        decisions = agent.decide(state["user_request"])
        
        # Group parallel-safe agents into batches
        batches = group_parallel_agents(decisions)
        
        logger.info(f"Router: Grouped {len(decisions)} tasks into {len(batches)} batch(es)")
        logger.info(f"Router: Batches -> {batches}")
        
        return {
            "next_steps": decisions,
            "parallel_batches": batches,
            "current_batch_index": 0,
            "current_step_index": 0
        }
    return {}




def group_parallel_agents(tasks: list) -> list:
    """
    Groups agents into batches for parallel execution.
    
    Grouping Rules:
    - Translation: Runs alone (modifies text)
    - Analysis, Recommend, Ideate, Copywrite: Run in parallel (read-only on same text)
    - Compliance: Runs after analysis (validates content)
    - Summarize: Runs with other parallel agents
    """
    if not tasks:
        return []
    
    batches = []
    current_batch = []
    
    for task in enumerate(tasks):
        task = task[1]  # Get the task name from enumerate tuple
        
        # Translation should run alone
        if task == "translate":
            if current_batch:
                batches.append(current_batch)
                current_batch = []
            batches.append([task])
        
        # Compliance should run separately
        elif task == "compliance":
            if current_batch:
                batches.append(current_batch)
                current_batch = []
            batches.append([task])
        
        # Others can run in parallel
        else:
            current_batch.append(task)
    
    if current_batch:
        batches.append(current_batch)
    
    return batches


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