from langgraph.graph import StateGraph, END
from ..models.state.state import AgentState
from ..nodes.extraction_node import extraction_node
from ..nodes.refiner_node import refiner_node
from ..nodes.router_node import router_node
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

    # Add nodes
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

    # Sequential pipeline
    workflow.set_entry_point("node_extract")
    workflow.add_edge("node_extract", "node_refine")
    workflow.add_edge("node_refine", "node_router")


    # All parallel tasks end directly
    workflow.add_edge("node_summarize", END)
    workflow.add_edge("node_translate", END)
    workflow.add_edge("node_analyze", END)
    workflow.add_edge("node_recommend", END)
    workflow.add_edge("node_ideate", END)
    workflow.add_edge("node_copywrite", END)
    workflow.add_edge("node_compliance", END)
    
    # Router can also end if no tasks
    workflow.add_edge("node_router", END)

    return workflow.compile()

app_graph = create_graph()