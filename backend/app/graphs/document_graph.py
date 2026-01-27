from langgraph.graph import StateGraph, END
from ..models.state.state import AgentState
from ..nodes.extraction_node import extraction_node
from ..nodes.refiner_node import refiner_node
from ..nodes.router_node import router_node, routing_logic
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

    # Conditional routing from router
    # Use distinct channel names to avoid collisions with node names
    workflow.add_conditional_edges(
        "node_router",
        routing_logic,
        {
            "to_summarize": "node_summarize",
            "to_translate": "node_translate",
            "to_analyze": "node_analyze",
            "to_recommend": "node_recommend",
            "to_ideate": "node_ideate",
            "to_copywrite": "node_copywrite",
            "to_compliance": "node_compliance",
            "end": END
        }
    )

    # After each task, go back to router to check for next task
    workflow.add_edge("node_summarize", "node_router")
    workflow.add_edge("node_translate", "node_router")
    workflow.add_edge("node_analyze", "node_router")
    workflow.add_edge("node_recommend", "node_router")
    workflow.add_edge("node_ideate", "node_router")
    workflow.add_edge("node_copywrite", "node_router")
    workflow.add_edge("node_compliance", "node_router")

    return workflow.compile()

app_graph = create_graph()