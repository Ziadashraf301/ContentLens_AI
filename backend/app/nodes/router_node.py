
from langgraph.types import Send
from ..agents.router import RouterAgent
from ..core.logging import logger
from ..models.state.state import AgentState
from langgraph.types import Command
from ..core.config import settings
from langchain_cohere import ChatCohere

async def router_node(state: AgentState):
    """
    Router fans out to ALL tasks in parallel using Send API
    """

    if state.get("next_steps"):
        return {}
        
    agent = RouterAgent()

    try: 
        decisions = await agent.decide(state["user_request"])
    except Exception as e:
        logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")

        try:
            fallback_llm = ChatCohere(
                cohere_api_key=settings.COHERE_API_KEY, 
                model=settings.COHERE_MODEL, 
                temperature=settings.TEMPERATURE_ROUTER
            )

            fallback_chain = agent.prompt | fallback_llm
            rescue_response = await fallback_chain.ainvoke({"user_request": state["user_request"]})
            decisions = rescue_response.content.split(", ")
            logger.info("Successfully recovered routing decisions using Cohere.")

        except Exception as cohere_error:
            logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
            return {}
        
    logger.info(f"Router: Fanning out to {len(decisions)} tasks in parallel: {decisions}")
        
    # Map task names to node names
    task_to_node = {
        "summarize": "node_summarize",
        "translate": "node_translate",
        "analyze": "node_analyze",
        # "recommend": "node_recommend",
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