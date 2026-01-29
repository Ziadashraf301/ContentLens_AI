from app.graphs.document_graph import create_graph
from app.agents.router import RouterAgent


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
