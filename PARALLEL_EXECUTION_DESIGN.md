# Parallel Agent Execution Architecture

## Overview

This document explains the redesigned multi-agent workflow that executes agents **concurrently** while preserving **per-agent observability** and preventing **state collisions**.

## Problem Statement

The previous implementation had two critical issues:

### 1. **Sequential Execution (Not Parallel)**
```
Router → Agent 1 → Router → Agent 2 → Router → Agent 3 → END
```
- Agents ran **one-after-another** through repeated router loops
- Even though 3 agents were selected, they couldn't run in parallel
- Total execution time = Sum of all agent times
- No performance benefit from concurrent execution

### 2. **Lost Observability**
- Each agent wrote to **shared state keys** (e.g., `state["analysis"]`)
- No per-agent trace IDs in Langfuse
- Hard to debug which agent failed if one crashed
- Evaluations mixed together in a single list
- No way to isolate per-agent performance metrics
- State overwrites: if agents ran in parallel, results would collide

---

## New Architecture: Concurrent Execution Model

### Execution Flow

```
┌─────────────┐
│  Extract    │  Sequential preprocessing
└──────┬──────┘
       │
┌──────▼──────┐
│    Refine   │  Sequential preprocessing
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│  Router                          │  Determines which agents to run
│  (Returns: ["analyze", "ideate"  │
│   "recommend"])                  │
└──────┬──────────────────────────┘
       │
       │  Passes list to parallel executor
       │
┌──────▼──────────────────────────────────────────────────┐
│  Parallel Agents Node                                    │
│                                                          │
│  ┌─────────┬──────────┬─────────┐                       │
│  │ Analyze │  Ideate  │Recommend│  All run CONCURRENTLY │
│  │ Task 1  │ Task 2   │ Task 3  │                       │
│  └────┬────┴────┬─────┴────┬────┘                       │
│       │         │          │                            │
│       └─────────┼──────────┘                            │
│               AWAIT                                     │
│               asyncio.gather()                         │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────┐
│     END     │  All results merged with metadata
└─────────────┘
```

### Key Differences

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| **Execution** | Sequential looping | Concurrent with `asyncio.gather()` |
| **Agents Run** | 1 at a time, back to router each time | All at once in parallel |
| **Performance** | O(n) - sum of all times | O(max) - only the slowest agent's time |
| **State Keys** | Shared (e.g., `state["analysis"]`) | Isolated per-agent in `agent_outputs` dict |
| **Tracing** | Single global trace | Separate Langfuse span per agent |
| **Error Handling** | One error stops workflow | Errors isolated per agent |
| **Observability** | Mixed in shared arrays | Per-agent metadata tracking |

---

## Implementation Details

### 1. Enhanced State Schema

The state now includes structures for **parallel-safe storage**:

```python
class AgentMetadata(TypedDict):
    """Per-agent execution metadata"""
    agent_id: str              # Unique ID: "analyze_1674567890123"
    agent_name: str            # "analyze", "recommend", etc.
    start_time: float          # Unix timestamp
    end_time: Optional[float]
    duration_ms: Optional[float]
    status: str                # "pending", "running", "completed", "failed"
    error: Optional[str]
    langfuse_trace_id: Optional[str]

class AgentOutput(TypedDict):
    """Output from a single agent with metadata"""
    agent_id: str
    agent_name: str
    output: Any                # The actual result
    metadata: AgentMetadata
    evaluation: Optional[Dict]
    validation_passed: bool

class AgentState(TypedDict):
    # ... existing fields ...
    
    # NEW: Parallel execution tracking
    agent_outputs: Dict[str, AgentOutput]
    agent_metadata: Dict[str, AgentMetadata]
    agent_errors: Dict[str, str]           # { "analyze": "error msg" }
    agent_evaluations: Dict[str, List[Dict]]  # Per-agent evaluations
```

### 2. Parallel Execution Node

Located in `parallel_agents_node.py`:

```python
async def parallel_agents_node(state: AgentState) -> AgentState:
    """
    Executes agents in parallel while preserving observability.
    
    Process:
    1. Get list of agents from router (state.next_steps)
    2. Create async task for each agent
    3. Execute all concurrently with asyncio.gather()
    4. Collect results with metadata
    5. Merge into state with isolated per-agent data
    """
    agents_to_run = state.get("next_steps", [])  # ["analyze", "ideate", "recommend"]
    
    # Create async tasks
    tasks = [
        execute_agent_with_tracing(agent_name, state, trace_client)
        for agent_name in agents_to_run
    ]
    
    # Execute all concurrently
    agent_outputs_list = await asyncio.gather(
        *tasks,
        return_exceptions=True  # Don't fail on individual errors
    )
    
    # Merge results while preserving per-agent metadata
    # ...
```

### 3. Per-Agent Async Wrapper

Each agent gets wrapped with:
- **Unique async task** for concurrent execution
- **Langfuse span** for individual tracing
- **Metadata collection** (start time, duration, status)
- **Error handling** (isolated failures)

```python
async def execute_agent_with_tracing(
    agent_name: str,
    state: AgentState,
    trace_client
) -> AgentOutput:
    """
    Execute a single agent asynchronously with Langfuse tracing.
    Each agent gets its own Langfuse span and metadata.
    """
    agent_id = f"{agent_name}_{int(time.time() * 1000)}"
    
    # Create Langfuse span for THIS AGENT
    span = trace_client.span(
        name=f"agent_{agent_name}",
        metadata={"agent_name": agent_name, "agent_id": agent_id}
    )
    
    # Execute agent (run in executor to avoid blocking)
    agent_result = await loop.run_in_executor(
        None, 
        agent_func,  # The actual agent node
        state
    )
    
    # Collect metadata
    metadata["duration_ms"] = (end_time - start_time) * 1000
    metadata["status"] = "completed"
    
    # Return with metadata
    return AgentOutput(
        agent_id=agent_id,
        agent_name=agent_name,
        output=agent_result.get(agent_name),
        metadata=metadata,
        evaluation=evaluation
    )
```

---

## How Observability is Preserved

### 1. **Per-Agent Langfuse Spans**

Instead of one trace for all agents:

```
OLD:
├─ file_loading
├─ validation
├─ graph_execution
│  ├─ node: router
│  ├─ node: analyze        ← Mixed in one span
│  ├─ node: recommend      ← No isolation
│  └─ node: ideate         ← Hard to see individual performance
└─ ...

NEW:
├─ file_loading
├─ validation
├─ graph_execution
│  ├─ node: router
│  └─ parallel_agents_execution
│     ├─ agent_analyze      ← Individual span
│     │  ├─ duration_ms: 250
│     │  ├─ status: completed
│     │  └─ langfuse_trace_id: trace_12345
│     ├─ agent_ideate       ← Individual span
│     │  ├─ duration_ms: 180
│     │  └─ status: completed
│     └─ agent_recommend    ← Individual span
│        ├─ duration_ms: 320
│        └─ status: completed
```

Each agent has:
- ✅ Its own Langfuse span with unique trace ID
- ✅ Individual start/end times
- ✅ Per-agent evaluation results
- ✅ Isolated error tracking

### 2. **Isolated State Keys**

Results stored per-agent:

```python
state["agent_outputs"] = {
    "analyze": {
        "agent_id": "analyze_1674567890123",
        "output": "Strategic analysis result...",
        "metadata": {...},
        "evaluation": {...}
    },
    "ideate": {
        "agent_id": "ideate_1674567890456",
        "output": "Campaign ideas result...",
        "metadata": {...},
        "evaluation": {...}
    },
    "recommend": {
        "agent_id": "recommend_1674567890789",
        "output": "Recommendations result...",
        "metadata": {...},
        "evaluation": {...}
    }
}

# Per-agent evaluations
state["agent_evaluations"] = {
    "analyze": [evaluation_dict_1],
    "ideate": [evaluation_dict_1],
    "recommend": [evaluation_dict_1]
}

# Per-agent errors (if any failed)
state["agent_errors"] = {
    # "analyze": "Connection timeout"  # Only if failed
}
```

### 3. **Async Task Isolation**

Each agent runs in its own asyncio task:
- No shared variables between tasks
- Errors in one agent don't affect others
- Can independently cancel or monitor each agent

### 4. **Backward Compatibility**

For existing code, legacy fields are still updated:
```python
state["analysis"] = agent_outputs["analyze"]["output"]
state["recommendation"] = agent_outputs["recommend"]["output"]
state["ideation"] = agent_outputs["ideate"]["output"]
# ... etc
```

---

## Race Condition Prevention

### How We Avoid State Collisions

1. **Immutable Input**: All agents read from the same `state` (no mutations)
   ```python
   # Safe: each agent reads the same state
   analysis_result = agent_func(state)
   ideate_result = agent_func(state)
   ```

2. **Unique Output Keys**: Results stored in agent-specific dicts
   ```python
   agent_outputs["analyze"] = ...     # Can't collide with "ideate"
   agent_outputs["ideate"] = ...      # Separate dict entry
   ```

3. **No Shared Mutable State**: Each agent task is independent
   ```python
   tasks = [
       execute_agent_with_tracing("analyze", state, trace_client),
       execute_agent_with_tracing("ideate", state, trace_client),
       # Each task has its own local variables and metadata
   ]
   await asyncio.gather(*tasks)  # Run independently
   ```

4. **Graceful Error Isolation**
   ```python
   # One agent failing doesn't stop others
   results = await asyncio.gather(
       *tasks,
       return_exceptions=True  # Exceptions don't propagate
   )
   
   for result in results:
       if isinstance(result, Exception):
           logger.error(f"Task failed: {result}")
       else:
           # Process successful result
   ```

---

## Performance Comparison

### Example: User requests "Analyze, summarize, and recommend"

**Old Sequential Model:**
```
Extract: 1s
Refine: 1s
Router: 0.1s
├─ Analyze: 5s    (Process: 1→2→3)
├─ Summarize: 3s  (Process: 1→2→3 again!)
└─ Recommend: 4s

Total: 1 + 1 + 0.1 + 5 + 3 + 4 = 14.1 seconds
```

**New Parallel Model:**
```
Extract: 1s
Refine: 1s
Router: 0.1s
├─ Analyze: 5s     ────┐
├─ Summarize: 3s   ────┼─ Concurrent!
└─ Recommend: 4s   ────┘

Total: 1 + 1 + 0.1 + max(5, 3, 4) = 7.1 seconds

Speedup: 14.1 / 7.1 = ~2x faster
```

---

## Graph Structure

### Updated `document_graph.py`

```python
def create_graph():
    workflow = StateGraph(AgentState)

    # Phase 1: Sequential preprocessing
    workflow.add_node("node_extract", extraction_node)
    workflow.add_node("node_refine", refiner_node)
    
    # Phase 2: Determine what to execute
    workflow.add_node("node_router", router_node)
    
    # Phase 3: Execute all agents concurrently
    workflow.add_node("node_parallel_agents", parallel_agents_node)

    # Connections
    workflow.set_entry_point("node_extract")
    workflow.add_edge("node_extract", "node_refine")
    workflow.add_edge("node_refine", "node_router")
    workflow.add_edge("node_router", "node_parallel_agents")  # ← Key change
    workflow.add_edge("node_parallel_agents", END)

    return workflow.compile()
```

**Before**: 10+ nodes with conditional routing looping back to router
**After**: 4 nodes with straight-line flow (parallel node handles concurrency)

---

## Usage Example

### In Your Workflow (`process_document.py`)

```python
async def run_document_workflow(file_path: str, user_request: str):
    # ... file loading, extraction, validation ...
    
    initial_state = {
        "raw_text": clean_text,
        "user_request": user_request,
        "source_lang": source_lang,
        "errors": [],
        "agent_outputs": {},      # NEW: empty initially
        "agent_metadata": {},     # NEW: tracking per-agent
    }

    # Execute graph (same async call)
    final_state = await app_graph.ainvoke(initial_state, config=config)
    
    # Access results
    print(final_state["agent_outputs"])    # All agent results
    print(final_state["agent_metadata"])   # All agent timings
    print(final_state["agent_errors"])     # Any agent failures
    
    # Also available (backward compat):
    print(final_state["analysis"])         # Direct access
    print(final_state["ideation"])
```

### Accessing Per-Agent Metadata in API Response

```python
@app.post("/analyze")
async def analyze_document(file: UploadFile, request: str):
    final_state = await run_document_workflow(file.filename, request)
    
    return {
        "results": {
            agent_name: output["output"]
            for agent_name, output in final_state["agent_outputs"].items()
        },
        "metadata": {
            agent_name: {
                "duration_ms": meta["duration_ms"],
                "status": meta["status"],
                "trace_id": meta["langfuse_trace_id"],
                "error": meta.get("error")
            }
            for agent_name, meta in final_state["agent_metadata"].items()
        },
        "total_execution_time_ms": sum(
            m["duration_ms"] for m in final_state["agent_metadata"].values()
        )
    }
```

### Langfuse Dashboard

Each execution shows:
- **Parallel execution trace** with all agent spans as children
- **Individual agent spans** with:
  - Execution time
  - Status (completed/failed)
  - Error messages
  - Input/output
- **Performance comparison** (see which agent is slowest)

---

## Migration Guide

### If You Have Custom Nodes

Your existing agent nodes (analyze_node, ideate_node, etc.) work **unchanged**!

The parallel node wraps them automatically. No modifications needed.

### If You Read From `state` Directly

Old code still works:
```python
# Old way (still works)
analysis = state["analysis"]
recommendation = state["recommendation"]

# New way (recommended)
analysis = state["agent_outputs"]["analyze"]["output"]
recommendation = state["agent_outputs"]["recommend"]["output"]

# New way (with metadata)
analyze_meta = state["agent_metadata"]["analyze"]
if analyze_meta["status"] == "completed":
    duration = analyze_meta["duration_ms"]
```

### Rollback Instructions

If needed, revert to sequential model:
1. Restore old `document_graph.py` with conditional routing
2. Remove `parallel_agents_node.py` import
3. Keep new state schema (backward compatible)

---

## Benefits Summary

✅ **True Parallel Execution** - Agents run concurrently, not sequentially
✅ **Per-Agent Observability** - Individual Langfuse spans with metadata
✅ **Isolated State** - No collisions or overwrites
✅ **Graceful Errors** - One failure doesn't stop others
✅ **Performance** - ~2-3x speedup for multi-agent workflows
✅ **Backward Compatible** - Old code still works
✅ **Langfuse Integration** - Separate traces per agent
✅ **Testable** - Easy to test individual agents concurrently

---

## Troubleshooting

### Q: Why is my parallel execution still slow?
**A:** Check if individual agents are async-aware. If agents make blocking I/O calls, consider using thread pools. Also verify Langfuse isn't blocking with `return_exceptions=True`.

### Q: How do I debug a failed agent?
**A:** Check `state["agent_errors"]["agent_name"]` and `state["agent_metadata"]["agent_name"]["error"]`. Look at the Langfuse span for that agent.

### Q: Can agents depend on each other?
**A:** Not in the current model (parallel independent execution). For dependencies, revert to sequential or create a custom orchestrator.

### Q: Why is memory usage high?
**A:** All agents read the same state. If state is large, consider caching extracted content rather than duplicating.

---

## Future Enhancements

1. **Agent Dependencies**: Allow specifying which agents must complete before others
2. **Dynamic Scaling**: Limit concurrent agents with semaphores
3. **Streaming Results**: Stream results as each agent completes
4. **Caching**: Cache agent results to avoid re-execution
5. **Custom Metrics**: Track cost, tokens, latency per agent
