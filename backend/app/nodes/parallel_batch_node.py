"""
Parallel Batch Executor Node
Executes multiple agents concurrently within a single node.
This enables true parallel execution in LangGraph.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..agents.summarizer import SummarizerAgent
from ..agents.translator import TranslatorAgent
from ..agents.analyzer import AnalyzerAgent
from ..agents.recommender import RecommenderAgent
from ..agents.ideation import IdeationAgent
from ..agents.copywriter import CopywriterAgent
from ..agents.compliance import ComplianceAgent
from ..core.logging import logger
from ..core.langfuse import get_langfuse_client
from ..models.state.state import AgentState


# Map agent names to their classes
AGENT_MAP = {
    "summarize": SummarizerAgent,
    "translate": TranslatorAgent,
    "analyze": AnalyzerAgent,
    "recommend": RecommenderAgent,
    "ideate": IdeationAgent,
    "copywrite": CopywriterAgent,
    "compliance": ComplianceAgent,
}


def parallel_batch_executor(state: AgentState) -> dict:
    """
    Executes a batch of agents concurrently without modifying graph state unnecessarily.
    """
    batches = state.get("parallel_batches", [])
    batch_index = state.get("current_batch_index", 0)
    
    # Check if we've completed all batches
    if batch_index >= len(batches):
        logger.info("Parallel executor: All batches completed")
        return {}
    
    current_batch = batches[batch_index]
    logger.info(f"Parallel executor: Executing batch {batch_index + 1}/{len(batches)} -> {current_batch}")
    
    all_results = {}
    
    # If single agent in batch, execute it directly
    if len(current_batch) == 1:
        agent_name = current_batch[0]
        logger.info(f"Parallel executor: Single agent in batch, executing {agent_name} sequentially")
        result = _execute_agent(agent_name, state)
        all_results.update(result)
        logger.info(f"Parallel executor: Single agent batch results: {all_results}")
    else:
        # Multiple agents in batch - execute in parallel
        logger.info(f"Parallel executor: Executing {len(current_batch)} agents in parallel")
        results = _execute_batch_parallel(current_batch, state)
        all_results.update(results)
        logger.info(f"Parallel executor: Parallel batch results: {all_results}")
    
    # Increment batch index
    state["current_batch_index"] = batch_index + 1
    
    logger.info(f"Parallel executor: Batch {batch_index + 1} completed, returning results: {list(all_results.keys())}")
    return all_results


def _execute_agent(agent_name: str, state: AgentState) -> dict:
    """
    Execute a single agent with its correct signature and return its output.
    """
    try:
        agent_class = AGENT_MAP.get(agent_name)
        if not agent_class:
            logger.error(f"Unknown agent: {agent_name}")
            return {}
        
        agent = agent_class()
        
        # Get the appropriate input for the agent
        extracted_text = state.get("extraction", state.get("raw_text", ""))
        user_request = state.get("user_request", "")
        
        logger.info(f"Parallel executor: Running agent '{agent_name}'")
        
        # Call agent with its specific signature
        if agent_name == "summarize":
            output = agent.run(extraction_data=extracted_text)
        elif agent_name == "translate":
            output = agent.run(content=extracted_text, source_lang=state.get("source_lang"))
        elif agent_name == "analyze":
            output = agent.run(content=extracted_text)
        elif agent_name == "recommend":
            output = agent.run(content=extracted_text, user_request=user_request)
        elif agent_name == "ideate":
            output = agent.run(content=extracted_text)
        elif agent_name == "copywrite":
            output = agent.run(brief=extracted_text, user_request=user_request)
        elif agent_name == "compliance":
            output = agent.run(content=extracted_text)
        else:
            logger.error(f"No handler for agent: {agent_name}")
            return {}
        
        # Store output with agent name as key (matches state field names)
        state_key = {
            "summarize": "summary",
            "translate": "translation",
            "analyze": "analysis",
            "recommend": "recommendation",
            "ideate": "ideation",
            "copywrite": "copywriting",
            "compliance": "compliance"
        }.get(agent_name, f"{agent_name}_output")
        
        logger.info(f"Parallel executor: Agent '{agent_name}' output received: {type(output)}")
        return {state_key: output}
    
    except Exception as e:
        logger.error(f"Error executing agent '{agent_name}': {str(e)}", exc_info=True)
        return {}


def _execute_batch_parallel(batch: list, state: AgentState) -> dict:
    """
    Execute multiple agents in parallel using ThreadPoolExecutor.
    
    Args:
        batch: List of agent names to execute in parallel
        state: Current AgentState
    
    Returns:
        Dictionary mapping agent names to their outputs
    """
    results = {}
    
    # Use ThreadPoolExecutor for concurrent execution
    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
        # Submit all agents for execution
        futures = {
            executor.submit(_execute_agent, agent_name, state): agent_name
            for agent_name in batch
        }
        
        logger.info(f"Parallel executor: Submitted {len(futures)} agents for parallel execution")
        
        # Collect results as they complete
        for future in futures:
            agent_name = futures[future]
            try:
                result = future.result(timeout=120)  # 2 minute timeout per agent
                logger.info(f"Parallel executor: Agent '{agent_name}' completed with result keys: {list(result.keys())}")
                results.update(result)
            except TimeoutError:
                logger.error(f"Parallel executor: Agent '{agent_name}' timed out")
            except Exception as e:
                logger.error(f"Parallel executor: Agent '{agent_name}' failed: {str(e)}", exc_info=True)
    
    logger.info(f"Parallel executor: All agents in batch completed. Combined results keys: {list(results.keys())}")
    return results


async def _execute_batch_async(batch: list, state: AgentState) -> dict:
    """
    Alternative: Execute multiple agents concurrently using asyncio.
    Use this if agents support async operations.
    
    Args:
        batch: List of agent names to execute in parallel
        state: Current AgentState
    
    Returns:
        Dictionary mapping agent names to their outputs
    """
    tasks = [
        asyncio.to_thread(_execute_agent, agent_name, state)
        for agent_name in batch
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    output = {}
    for agent_name, result in zip(batch, results):
        if isinstance(result, Exception):
            output[f"{agent_name}_output"] = {"error": str(result)}
        else:
            output.update(result)
    
    return output
