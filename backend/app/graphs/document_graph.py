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
    Routes to the next task in the list, or END if all done
    """
    steps = state.get("next_steps", [])
    index = state.get("current_step_index", 0)
    
    if index < len(steps):
        current_task = steps[index]
        logger.info(f"Routing: Task {index + 1}/{len(steps)} -> {current_task}")
        return current_task
    
    logger.info("Routing: All tasks completed, going to END")
    return "end"


# --- Graph Construction ---
def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("extract", extraction_node)
    workflow.add_node("router", router_node)
    workflow.add_node("summarize", summarization_node)
    workflow.add_node("translate", translation_node)
    workflow.add_node("analyze", analysis_node)
    workflow.add_node("recommend", recommendation_node)
    workflow.add_node("ideate", ideation_node)
    workflow.add_node("copywrite", copywriter_node)
    workflow.add_node("compliance", compliance_node)

    # Entry point
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "router")

    # Conditional routing from router
    workflow.add_conditional_edges(
        "router",
        routing_logic,
        {
            "summarize": "summarize",
            "translate": "translate",
            "analyze": "analyze",
            "recommend": "recommend",
            "ideate": "ideate",
            "copywrite": "copywrite",
            "compliance": "compliance",
            "end": END
        }
    )

    # After each task, go back to router to check for next task
    workflow.add_edge("summarize", "router")
    workflow.add_edge("translate", "router")
    workflow.add_edge("analyze", "router")
    workflow.add_edge("recommend", "router")
    workflow.add_edge("ideate", "router")
    workflow.add_edge("copywrite", "router")
    workflow.add_edge("compliance", "router")

    return workflow.compile()

app_graph = create_graph()