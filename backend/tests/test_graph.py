from app.graphs.document_graph import routing_logic, create_graph


def test_routing_logic():
    assert routing_logic({"next_step": "summarize"}) == "summarize"
    assert routing_logic({"next_step": "translate"}) == "translate"
    assert routing_logic({"next_step": "analyze"}) == "analyze"
    assert routing_logic({"next_step": "recommend"}) == "analyze"
    assert routing_logic({"next_step": "unknown"}) == "end"
    assert routing_logic({}) == "end"


def test_create_graph_returns_compiled():
    graph = create_graph()
    assert graph is not None
