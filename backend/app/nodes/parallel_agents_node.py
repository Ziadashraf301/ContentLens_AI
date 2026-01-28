"""
Parallel Agent Execution Node

Executes multiple agents concurrently while preserving per-agent observability.
Each agent runs independently in its own async task with isolated tracing.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.state.state import AgentState, AgentMetadata, AgentOutput
from ..core.logging import logger
from ..core.langfuse import get_langfuse_client

# Import all agent nodes
from .analysis_node import analysis_node
from .recommendation_node import recommendation_node
from .ideation_node import ideation_node
from .compliance_node import compliance_node
from .summarization_node import summarization_node
from .translation_node import translation_node
from .copywriter_node import copywriter_node


# Mapping of agent names to their node functions
AGENT_NODE_MAP = {
    "analyze": analysis_node,
    "recommend": recommendation_node,
    "ideate": ideation_node,
    "compliance": compliance_node,
    "summarize": summarization_node,
    "translate": translation_node,
    "copywrite": copywriter_node,
}


async def execute_agent_with_tracing(
    agent_name: str,
    state: AgentState,
    trace_client,
) -> AgentOutput:
    """
    Execute a single agent asynchronously with Langfuse tracing.
    
    Args:
        agent_name: Name of the agent (e.g., "analyze")
        state: Current state (immutable during concurrent execution)
        trace_client: Langfuse client for tracing
    
    Returns:
        AgentOutput with metadata and result
    """
    agent_id = f"{agent_name}_{int(time.time() * 1000)}"
    
    # Initialize metadata
    metadata: AgentMetadata = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "start_time": time.time(),
        "status": "running",
    }
    
    # Create Langfuse span for this agent
    span = None
    if trace_client:
        try:
            span = trace_client.span(
                name=f"agent_{agent_name}",
                input={"agent_id": agent_id, "user_request": state.get("user_request")},
                metadata={
                    "agent_name": agent_name,
                    "agent_id": agent_id,
                    "execution_mode": "parallel",
                }
            )
            metadata["langfuse_trace_id"] = span.id if hasattr(span, 'id') else str(span)
        except Exception as trace_error:
            logger.warning(f"[{agent_id}] Failed to create Langfuse span: {trace_error}")
    
    try:
        logger.info(f"🚀 [{agent_id}] Starting {agent_name} agent execution (parallel)")
        
        # Get the agent node function
        agent_func = AGENT_NODE_MAP.get(agent_name)
        if not agent_func:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Execute agent (convert sync to async if needed)
        # Most LangGraph nodes are sync, so we wrap in executor
        loop = asyncio.get_event_loop()
        agent_result = await loop.run_in_executor(
            None, 
            agent_func, 
            state
        )
        
        # Record metadata
        end_time = time.time()
        duration_ms = (end_time - metadata["start_time"]) * 1000
        
        metadata["end_time"] = end_time
        metadata["duration_ms"] = duration_ms
        metadata["status"] = "completed"
        
        logger.info(
            f"✅ [{agent_id}] {agent_name} completed in {duration_ms:.2f}ms"
        )
        
        # Update Langfuse span
        if span:
            try:
                span.update(
                    output={"status": "success", "duration_ms": duration_ms},
                    metadata={"agent_id": agent_id}
                )
            except Exception as trace_error:
                logger.warning(f"[{agent_id}] Failed to update Langfuse span: {trace_error}")
        
        # Extract the actual output for this agent from result
        # The node returns a dict with the agent's output key
        agent_output_key = agent_name  # e.g., "analysis", "recommendation"
        output_value = agent_result.get(agent_output_key, agent_result)
        
        # Get evaluation if present
        evaluation = None
        evaluations = agent_result.get("evaluations", [])
        if evaluations:
            evaluation = evaluations[-1]  # Get the last evaluation
        
        return AgentOutput(
            agent_id=agent_id,
            agent_name=agent_name,
            output=output_value,
            metadata=metadata,
            evaluation=evaluation,
            validation_passed=True,
        )
        
    except Exception as error:
        end_time = time.time()
        duration_ms = (end_time - metadata["start_time"]) * 1000
        error_msg = f"{type(error).__name__}: {str(error)}"
        
        metadata["end_time"] = end_time
        metadata["duration_ms"] = duration_ms
        metadata["status"] = "failed"
        metadata["error"] = error_msg
        
        logger.error(
            f"❌ [{agent_id}] {agent_name} failed after {duration_ms:.2f}ms: {error_msg}",
            exc_info=True
        )
        
        # Update Langfuse span with error
        if span:
            try:
                span.update(
                    output={"status": "error", "error": error_msg},
                    metadata={"agent_id": agent_id},
                    level="error"
                )
            except Exception as trace_error:
                logger.warning(f"[{agent_id}] Failed to update Langfuse span with error: {trace_error}")
        
        return AgentOutput(
            agent_id=agent_id,
            agent_name=agent_name,
            output=None,
            metadata=metadata,
            evaluation=None,
            validation_passed=False,
        )


async def parallel_agents_node(state: AgentState) -> AgentState:
    """
    Execute selected agents in parallel while preserving observability.
    
    This node:
    1. Takes the list of agents from next_steps (set by router)
    2. Executes all agents concurrently using asyncio.gather
    3. Merges results while preserving per-agent metadata
    4. Handles errors gracefully (one agent failure doesn't stop others)
    5. Maintains Langfuse tracing at both parallel node and per-agent level
    
    Args:
        state: AgentState with next_steps populated by router
    
    Returns:
        Updated AgentState with agent_outputs and agent_metadata populated
    """
    agents_to_run = state.get("next_steps", [])
    
    if not agents_to_run:
        logger.info("⏭️  parallel_agents_node: No agents to execute, passing through")
        return state
    
    logger.info(
        f"🚀 parallel_agents_node: Starting parallel execution for {len(agents_to_run)} agents: {agents_to_run}"
    )
    
    start_time = time.time()
    trace_client = get_langfuse_client()
    
    # Create parallel execution span in Langfuse
    parallel_span = None
    if trace_client:
        try:
            parallel_span = trace_client.span(
                name="parallel_agents_execution",
                input={
                    "agents": agents_to_run,
                    "user_request": state.get("user_request"),
                },
                metadata={
                    "agent_count": len(agents_to_run),
                    "agents": agents_to_run,
                    "execution_mode": "parallel_concurrent",
                }
            )
        except Exception as trace_error:
            logger.warning(f"Failed to create Langfuse parallel span: {trace_error}")
    
    try:
        # Create async tasks for all agents
        tasks = [
            execute_agent_with_tracing(agent_name, state, trace_client)
            for agent_name in agents_to_run
        ]
        
        # Execute all agents concurrently
        # return_exceptions=True ensures one failure doesn't stop others
        agent_outputs_list = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )
        
        # Process results
        agent_outputs: Dict[str, AgentOutput] = {}
        agent_metadata: Dict[str, AgentMetadata] = {}
        agent_errors: Dict[str, str] = {}
        agent_evaluations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Legacy fields (for backward compatibility)
        legacy_updates = {}
        
        for agent_output in agent_outputs_list:
            # Handle exceptions that occurred during execution
            if isinstance(agent_output, Exception):
                logger.error(f"Task exception: {agent_output}", exc_info=agent_output)
                continue
            
            agent_name = agent_output["agent_name"]
            agent_id = agent_output["agent_id"]
            
            # Store in agent_outputs (new parallel-safe structure)
            agent_outputs[agent_name] = agent_output
            agent_metadata[agent_name] = agent_output["metadata"]
            
            # Store evaluation if present
            if agent_output.get("evaluation"):
                agent_evaluations[agent_name] = [agent_output["evaluation"]]
            
            # Track errors
            if agent_output["metadata"]["status"] == "failed":
                error_msg = agent_output["metadata"].get("error", "Unknown error")
                agent_errors[agent_name] = error_msg
                logger.warning(f"Agent {agent_name} failed: {error_msg}")
            else:
                # For backward compatibility, also update legacy field names
                if agent_name == "analyze":
                    legacy_updates["analysis"] = agent_output["output"]
                elif agent_name == "recommend":
                    legacy_updates["recommendation"] = agent_output["output"]
                elif agent_name == "ideate":
                    legacy_updates["ideation"] = agent_output["output"]
                elif agent_name == "summarize":
                    legacy_updates["summary"] = agent_output["output"]
                elif agent_name == "translate":
                    legacy_updates["translation"] = agent_output["output"]
                elif agent_name == "copywrite":
                    legacy_updates["copywriting"] = agent_output["output"]
                elif agent_name == "compliance":
                    legacy_updates["compliance"] = agent_output["output"]
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"✅ Parallel execution completed: "
            f"{len(agents_to_run)} agents in {elapsed:.2f}s, "
            f"successes: {len([a for a in agent_outputs.values() if a['metadata']['status'] == 'completed'])}, "
            f"failures: {len(agent_errors)}"
        )
        
        # Update Langfuse span
        if parallel_span:
            try:
                parallel_span.update(
                    output={
                        "total_agents": len(agents_to_run),
                        "successful": len(agents_to_run) - len(agent_errors),
                        "failed": len(agent_errors),
                        "duration_seconds": elapsed,
                    },
                    metadata={
                        "agents": agents_to_run,
                        "failed_agents": list(agent_errors.keys()),
                    }
                )
            except Exception as trace_error:
                logger.warning(f"Failed to update Langfuse parallel span: {trace_error}")
        
        # Merge results into state
        updated_state = state.copy()
        updated_state["agent_outputs"] = agent_outputs
        updated_state["agent_metadata"] = agent_metadata
        updated_state["agent_errors"] = agent_errors
        updated_state["agent_evaluations"] = agent_evaluations
        
        # Update legacy fields for backward compatibility
        updated_state.update(legacy_updates)
        
        # Add all completed agents to completed_agents list
        completed = state.get("completed_agents", [])
        completed.extend([
            name for name, output in agent_outputs.items()
            if output["metadata"]["status"] == "completed"
        ])
        updated_state["completed_agents"] = list(set(completed))
        
        # Mark execution phase complete
        updated_state["pending_agents"] = []
        
        return updated_state
        
    except Exception as error:
        logger.error(f"❌ Parallel execution failed: {error}", exc_info=True)
        
        if parallel_span:
            try:
                parallel_span.update(
                    output={"error": str(error)},
                    level="error"
                )
            except Exception as trace_error:
                logger.warning(f"Failed to update Langfuse span on error: {trace_error}")
        
        # Return state with error recorded
        updated_state = state.copy()
        error_msg = f"Parallel execution failed: {error}"
        updated_state["errors"] = state.get("errors", []) + [error_msg]
        return updated_state
