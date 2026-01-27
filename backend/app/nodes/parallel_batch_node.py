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
    Executes a batch of agents concurrently.
    
    This node looks at the current batch in parallel_batches and executes
    all agents in that batch simultaneously, merging results back into state.
    
    Args:
        state: Current AgentState with parallel_batches and current_batch_index
    
    Returns:
        Updated state with all agent results merged
    """
    batches = state.get("parallel_batches", [])
    batch_index = state.get("current_batch_index", 0)
    
    # Initialize parallel batches on first run if not present
    if not batches and batch_index == 0:
        logger.warning("Parallel executor: No batches found in state")
        return {"current_batch_index": 0}
    
    # Check if we've completed all batches
    if batch_index >= len(batches):
        logger.info("Parallel executor: All batches completed")
        return {"current_batch_index": batch_index}
    
    current_batch = batches[batch_index]
    logger.info(f"Parallel executor: Executing batch {batch_index + 1}/{len(batches)} -> {current_batch}")
    
    # Ensure extracted_text exists
    if not state.get("extracted_text"):
        state["extracted_text"] = state.get("raw_text", "")
    
    # If single agent in batch, execute it directly
    if len(current_batch) == 1:
        agent_name = current_batch[0]
        logger.info(f"Parallel executor: Single agent in batch, executing {agent_name} sequentially")
        result = _execute_agent(agent_name, state)
        
        # Update batch index for next iteration
        return {
            **result,
            "current_batch_index": batch_index + 1
        }
    
    # Multiple agents in batch - execute in parallel
    logger.info(f"Parallel executor: Executing {len(current_batch)} agents in parallel")
    results = _execute_batch_parallel(current_batch, state)
    
    # Merge all results into state
    merged_state = {**state}
    for agent_name, agent_result in results.items():
        merged_state[agent_name] = agent_result
    
    # Increment batch index for next iteration
    merged_state["current_batch_index"] = batch_index + 1
    
    logger.info(f"Parallel executor: Batch {batch_index + 1} completed, moving to next batch")
    return merged_state


def _execute_agent(agent_name: str, state: AgentState) -> dict:
    """
    Execute a single agent and return its output.
    """
    try:
        agent_class = AGENT_MAP.get(agent_name)
        if not agent_class:
            logger.error(f"Unknown agent: {agent_name}")
            return {}
        
        agent = agent_class()
        
        # Get the appropriate input for the agent
        extracted_text = state.get("extracted_text") or state.get("raw_text", "")
        
        # Execute the agent with extracted text
        logger.info(f"Parallel executor: Running agent '{agent_name}'")
        output = agent.run(content=extracted_text)
        
        # Store output with agent name as key
        return {f"{agent_name}_output": output}
    
    except Exception as e:
        logger.error(f"Error executing agent '{agent_name}': {str(e)}")
        return {f"{agent_name}_output": {"error": str(e)}}


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
        
        # Collect results as they complete
        for future in futures:
            agent_name = futures[future]
            try:
                result = future.result(timeout=120)  # 2 minute timeout per agent
                results.update(result)
                logger.info(f"Parallel executor: Agent '{agent_name}' completed")
            except TimeoutError:
                logger.error(f"Parallel executor: Agent '{agent_name}' timed out")
                results[f"{agent_name}_output"] = {"error": "Agent execution timed out"}
            except Exception as e:
                logger.error(f"Parallel executor: Agent '{agent_name}' failed: {str(e)}")
                results[f"{agent_name}_output"] = {"error": str(e)}
    
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
