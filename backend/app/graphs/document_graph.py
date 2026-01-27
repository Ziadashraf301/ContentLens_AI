from langgraph.graph import StateGraph, END
from ..models.state.state import AgentState
from ..nodes.extraction_node import extraction_node
from ..nodes.refiner_node import refiner_node
from ..nodes.router_node import router_node, routing_logic
from ..nodes.parallel_batch_node import parallel_batch_executor
from ..nodes.summarization_node import summarization_node
from ..nodes.translation_node import translation_node
from ..nodes.analysis_node import analysis_node
from ..nodes.recommendation_node import recommendation_node
from ..nodes.ideation_node import ideation_node
from ..nodes.copywriter_node import copywriter_node
from ..nodes.compliance_node import compliance_node

# --- Graph Construction ---
def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes (use distinct node names to avoid collision with channels)
    workflow.add_node("node_extract", extraction_node)
    workflow.add_node("node_refine", refiner_node)
    workflow.add_node("node_router", router_node)
    workflow.add_node("node_parallel_batch", parallel_batch_executor)  # NEW: Parallel execution node
    workflow.add_node("node_summarize", summarization_node)
    workflow.add_node("node_translate", translation_node)
    workflow.add_node("node_analyze", analysis_node)
    workflow.add_node("node_recommend", recommendation_node)
    workflow.add_node("node_ideate", ideation_node)
    workflow.add_node("node_copywrite", copywriter_node)
    workflow.add_node("node_compliance", compliance_node)

    # Entry point
    workflow.set_entry_point("node_extract")
    workflow.add_edge("node_extract", "node_refine")
    workflow.add_edge("node_refine", "node_router")
    
    # After router groups tasks, go to parallel executor instead of conditional routing
    workflow.add_edge("node_router", "node_parallel_batch")
    
    # After parallel batch completes, check if there are more batches
    workflow.add_conditional_edges(
        "node_parallel_batch",
        _batch_complete_logic,
        {
            "continue": "node_parallel_batch",  # More batches to process
            "end": END                           # All batches done
        }
    )

    return workflow.compile()


def _batch_complete_logic(state: AgentState) -> str:
    """
    Checks if there are more batches to process after parallel execution.
    """
    batches = state.get("parallel_batches", [])
    batch_index = state.get("current_batch_index", 0)
    
    if batch_index < len(batches):
        return "continue"  # More batches to process
    else:
        return "end"  # All batches completed


app_graph = create_graph()