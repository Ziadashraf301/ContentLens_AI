from langgraph.graph import StateGraph, END
from .state import AgentState
from ..agents.extractor import ExtractorAgent
from ..agents.router import RouterAgent
from ..agents.summarizer import SummarizerAgent
from ..agents.translator import TranslatorAgent
from ..agents.analyzer import AnalyzerAgent
from ..agents.recommender import RecommenderAgent
from ..agents.ideation import IdeationAgent
from ..agents.copywriter import CopywriterAgent
from ..agents.compliance import ComplianceAgent
from ..core.logging import logger

# --- Node Functions ---

def extraction_node(state: AgentState):
    logger.info("--- NODE: EXTRACTION ---")
    agent = ExtractorAgent()
    # The raw_text comes from the FileLoader in the workflow
    result = agent.run(state["raw_text"])
    return {"extraction": result}

def router_node(state: AgentState):
    if not state.get("next_steps"):
        agent = RouterAgent()
        decisions = agent.decide(state["user_request"])
        return {"next_steps": decisions, "current_step_index": 0}
    return {}

def summarization_node(state: AgentState):
    logger.info("--- NODE: SUMMARIZATION ---")
    agent = SummarizerAgent()
    summary = agent.run(state["extraction"])
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "summary": summary,
        "current_step_index": current_index + 1 
    }

def translation_node(state: AgentState):
    logger.info("--- NODE: TRANSLATION ---")
    agent = TranslatorAgent()
    text_to_translate = state["summary"] if state.get("summary") else str(state["extraction"])
    translation = agent.run(text_to_translate, state.get("source_lang"))
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "translation": translation,
        "current_step_index": current_index + 1  
    }

def analysis_node(state: AgentState):
    logger.info("--- NODE: ANALYSIS ---")
    agent = AnalyzerAgent()
    analysis_result = agent.run(state["extraction"])
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "analysis": analysis_result,
        "current_step_index": current_index + 1 
    }

def recommendation_node(state: AgentState):
    logger.info("--- NODE: RECOMMENDATION ---")
    agent = RecommenderAgent()
    input_content = state.get("extraction") or state.get("analysis") or ""
    recommendations = agent.run(input_content)
    
    # Increment step counter
    current_index = state.get("current_step_index", 0)
    return {
        "recommendation": recommendations,
        "current_step_index": current_index + 1 
    }


def ideation_node(state: AgentState):
    logger.info("--- NODE: IDEATION ---")
    agent = IdeationAgent()
    input_content = state.get("extraction") or state.get("raw_text") or ""
    ideas = agent.run(input_content)

    current_index = state.get("current_step_index", 0)
    return {
        "ideation": ideas,
        "current_step_index": current_index + 1
    }


def copywriter_node(state: AgentState):
    logger.info("--- NODE: COPYWRITER ---")
    agent = CopywriterAgent()
    # Prefer an explicit brief, else use the summary or extraction
    brief = state.get("user_request") or state.get("summary") or str(state.get("extraction", ""))
    copy = agent.run(brief)

    current_index = state.get("current_step_index", 0)
    return {
        "copy": copy,
        "current_step_index": current_index + 1
    }


def compliance_node(state: AgentState):
    logger.info("--- NODE: COMPLIANCE ---")
    agent = ComplianceAgent()
    # Check the copy first if present, else the summary or extraction
    to_check = state.get("copy") or state.get("summary") or str(state.get("extraction", ""))
    compliance_report = agent.run(to_check)

    current_index = state.get("current_step_index", 0)
    return {
        "compliance": compliance_report,
        "current_step_index": current_index + 1
    }

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


# --- Graph Construction ---
def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes (use distinct node names to avoid collision with channels)
    workflow.add_node("node_extract", extraction_node)
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
    workflow.add_edge("node_extract", "node_router")

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