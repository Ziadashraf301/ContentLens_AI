
from langgraph.types import Send
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState
from langgraph.types import Command

def router_node(state: AgentState):
    """
    Router fans out to ALL tasks in parallel using Send API
    """

    try:
        if state.get("next_steps"):
            return {}
        
        agent = RouterAgent()
        decisions = agent.decide(state["user_request"])
        
        logger.info(f"Router: Fanning out to {len(decisions)} tasks in parallel: {decisions}")
        
        # Map task names to node names
        task_to_node = {
            "summarize": "node_summarize",
            "translate": "node_translate",
            "analyze": "node_analyze",
            "recommend": "node_recommend",
            "ideate": "node_ideate",
            "copywrite": "node_copywrite",
            "compliance": "node_compliance",
        }
        
        # Create Send objects for parallel execution
        sends = [Send(task_to_node[task], state) for task in decisions if task in task_to_node]
        
        return Command(
        update={"next_steps": decisions},
        goto=sends  
        )
    
    except Exception as e:
        logger.error(f"Router Node Error: {e}")
        return {}