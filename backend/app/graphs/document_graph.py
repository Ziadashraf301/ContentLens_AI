from langgraph.graph import StateGraph, END
from ..models.state.state import AgentState
from ..nodes.extraction_node import extraction_node
from ..nodes.refiner_node import refiner_node
from ..nodes.router_node import router_node
from ..nodes.parallel_agents_node import parallel_agents_node
from ..core.logging import logger

# --- Graph Construction (PARALLEL EXECUTION MODEL) ---
def create_graph():
    """
    Creates a LangGraph workflow with the following structure:
    
    1. Extract → Refine (Sequential preprocessing)
    2. Router (Determines which agents to execute)
    3. Parallel Agents (All selected agents run concurrently)
    4. END
    
    This design ensures:
    - Per-agent observability (individual traces, metadata)
    - True concurrent execution (no sequential looping)
    - Proper error handling (one agent failure doesn't stop others)
    - Backward compatibility (legacy fields maintained)
    """
    workflow = StateGraph(AgentState)

    # Phase 1: Preprocessing (Sequential)
    workflow.add_node("node_extract", extraction_node)
    workflow.add_node("node_refine", refiner_node)
    
    # Phase 2: Routing (Determines what to execute)
    workflow.add_node("node_router", router_node)
    
    # Phase 3: Parallel Agent Execution (All agents run concurrently)
    workflow.add_node("node_parallel_agents", parallel_agents_node)

    # Define execution flow
    workflow.set_entry_point("node_extract")
    workflow.add_edge("node_extract", "node_refine")
    workflow.add_edge("node_refine", "node_router")
    
    # Router passes control to parallel agent execution
    # (Instead of conditional routing to individual agents)
    workflow.add_edge("node_router", "node_parallel_agents")
    
    # After parallel execution completes, end the workflow
    workflow.add_edge("node_parallel_agents", END)

    return workflow.compile()

app_graph = create_graph()