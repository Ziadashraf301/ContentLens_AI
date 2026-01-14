from app.graphs.document_graph import routing_logic, create_graph
from app.agents.router import RouterAgent


def test_routing_logic():
    # Use the state shape expected by routing_logic
    assert routing_logic({"next_steps": ["summarize"], "current_step_index": 0}) == "to_summarize"
    assert routing_logic({"next_steps": ["translate"], "current_step_index": 0}) == "to_translate"
    assert routing_logic({"next_steps": ["analyze"], "current_step_index": 0}) == "to_analyze"
    assert routing_logic({"next_steps": ["recommend"], "current_step_index": 0}) == "to_recommend"
    # Unknown/empty moves to END
    assert routing_logic({"next_steps": ["unknown"], "current_step_index": 0}) == "end"
    assert routing_logic({}) == "end"


def test_router_marketing_keywords():
    r = RouterAgent()
    # Use keyword fallback directly to avoid depending on LLM behavior
    tasks = r._keyword_fallback("Generate campaign ideas and headlines with subject lines and email copy")
    assert "ideate" in tasks
    assert "copywrite" in tasks


def test_create_graph_returns_compiled():
    graph = create_graph()
    compiled = graph is not None
    assert compiled
