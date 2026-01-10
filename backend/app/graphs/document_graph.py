from langgraph.graph import StateGraph, END
from .state import AgentState
from ..agents.extractor import ExtractorAgent
from ..agents.router import RouterAgent
from ..agents.summarizer import SummarizerAgent
from ..agents.translator import TranslatorAgent
from ..agents.analyzer import AnalyzerAgent
from ..core.logging import logger

# --- Node Functions ---

def extraction_node(state: AgentState):
    logger.info("--- NODE: EXTRACTION ---")
    agent = ExtractorAgent()
    # The raw_text comes from the FileLoader in the workflow
    result = agent.run(state["raw_text"])
    return {"extraction": result}

def router_node(state: AgentState):
    logger.info("--- NODE: ROUTER ---")
    agent = RouterAgent()
    decision = agent.decide(state["user_request"])
    return {"next_step": decision}

def summarization_node(state: AgentState):
    logger.info("--- NODE: SUMMARIZATION ---")
    agent = SummarizerAgent()
    summary = agent.run(state["extraction"])
    return {"summary": summary}

def translation_node(state: AgentState):
    logger.info("--- NODE: TRANSLATION ---")
    agent = TranslatorAgent()
    # Translate the summary if it exists, otherwise the extraction dict
    text_to_translate = state["summary"] if state.get("summary") else str(state["extraction"])
    translation = agent.run(text_to_translate, state.get("source_lang"))
    return {"translation": translation}

def analysis_node(state: AgentState):
    logger.info("--- NODE: ANALYSIS/RECOMMENDATION ---")
    agent = AnalyzerAgent()
    # Analysis is performed on the structured extraction
    analysis_result = agent.run(state["extraction"])
    # We can store this in analysis or recommendation state keys
    return {"analysis": analysis_result}

def routing_logic(state: AgentState):
    """
    Directs the flow based on the router's decision.
    """
    step = state.get("next_step", "end")
    if step in ["summarize", "translate", "analyze", "recommend"]:
        return step
    return "end"

# --- Graph Construction ---

def create_graph():
    workflow = StateGraph(AgentState)

    # 1. Add All Nodes
    workflow.add_node("extract", extraction_node)
    workflow.add_node("router", router_node)
    workflow.add_node("summarize", summarization_node)
    workflow.add_node("translate", translation_node)
    workflow.add_node("analyze", analysis_node)

    # 2. Define the Entry and Static Edge
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "router")

    # 3. Define Conditional Edges from Router
    workflow.add_conditional_edges(
        "router",
        routing_logic,
        {
            "summarize": "summarize",
            "translate": "translate",
            "analyze": "analyze",
            "recommend": "analyze",
            "end": END
        }
    )

    # 4. All task nodes lead to END
    workflow.add_edge("summarize", END)
    workflow.add_edge("translate", END)
    workflow.add_edge("analyze", END)

    return workflow.compile()

app_graph = create_graph()