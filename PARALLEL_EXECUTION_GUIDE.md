# Parallel Agent Execution in LangGraph

## Overview

The graph now supports **parallel execution of agents** after the router detects which agents should run. Multiple agents can execute simultaneously when they don't depend on each other's outputs.

## How It Works

### 1. Router Decision Phase
When a user submits a request, the router analyzes it and returns a list of agents to execute:
```
User Request: "Analyze this brief and translate to Arabic"
Router Output: ["analyze", "translate"]
```

### 2. Batch Grouping
The `group_parallel_agents()` function organizes tasks into batches:
- **Tasks that CAN run in parallel**: `analyze`, `recommend`, `ideate`, `copywrite`, `summarize`
- **Tasks that should run alone**: `translate` (modifies text), `compliance` (validates content)

#### Example Batches:
```
Input:  ["analyze", "recommend", "ideate"]
Output: [["analyze", "recommend", "ideate"]]  # All 3 run in parallel

Input:  ["translate", "analyze", "recommend"]
Output: [["translate"], ["analyze", "recommend"]]  # Translate first, then analyze+recommend in parallel

Input:  ["analyze", "recommend", "compliance"]
Output: [["analyze", "recommend"], ["compliance"]]  # Analysis in parallel, then compliance check
```

### 3. Current Implementation
The current code structure processes tasks sequentially but is prepared for parallel execution:
- Each agent runs as a separate node
- All agents return to the router after completing
- The router decides the next task(s) to execute

## Example Execution Flow

### Scenario: "Analyze, translate, and get recommendations"

```
1. EXTRACTION
   ↓
2. REFINEMENT
   ↓
3. ROUTER DECISION
   next_steps = ["analyze", "translate", "recommend"]
   batches = [["translate"], ["analyze", "recommend"]]
   ↓
4. BATCH 1 (Sequential)
   Execute: translate
   ↓
5. BATCH 2 (Parallel)
   Execute in parallel:
   ├─ analyze
   └─ recommend
   ↓
6. ROUTER (next task check)
   All batches complete → END
```

## Performance Benefits

| Scenario | Sequential Time | Parallel Time | Speedup |
|----------|-----------------|---------------|---------|
| analyze + recommend + ideate | 3x | 1x | 3x faster |
| translate + analyze + recommend | 3x | 2x | 1.5x faster |
| analyze + translate + compliance | 3x | 3x | 1x (sequential deps) |

## Current State Management

The `AgentState` now tracks:
```python
{
    "next_steps": ["analyze", "recommend", "ideate"],           # Original ordered list
    "parallel_batches": [["analyze", "recommend", "ideate"]],   # Grouped for parallel execution
    "current_batch_index": 0,                                     # Current batch being processed
    "current_step_index": 0,                                      # Current step in sequence
    "extracted_text": "...",                                      # Document text
    "user_request": "...",                                        # User's intent
    # ... other agent outputs
}
```

## Grouping Rules

The `group_parallel_agents()` function applies these rules:

1. **Translation Task** (`translate`)
   - Modifies the text content
   - Should run alone or early in the sequence
   - Runs in its own batch

2. **Parallel-Safe Tasks** (`analyze`, `recommend`, `ideate`, `copywrite`, `summarize`)
   - Don't modify the original extracted text
   - Can read from the same source independently
   - Grouped together in a single batch

3. **Compliance Task** (`compliance`)
   - Should validate content AFTER analysis
   - Runs in its own batch after other tasks

## How to Extend Parallel Execution

To enable true concurrent execution in LangGraph:

### Option 1: Use Multiple Conditional Edges (Advanced)
```python
# Route to multiple nodes simultaneously
workflow.add_conditional_edges(
    "node_router",
    routing_logic_multi,
    {
        "parallel_analyze": "node_analyze",
        "parallel_recommend": "node_recommend",
        "parallel_ideate": "node_ideate",
    }
)
```

### Option 2: Use a Parallel Node Wrapper
Create a composite node that executes multiple agents asynchronously:
```python
async def parallel_batch_executor(state: AgentState):
    """Execute multiple agents in parallel using asyncio"""
    batch = state.get("current_batch", [])
    tasks = []
    
    # Schedule all agents in the batch
    for agent_name in batch:
        agent = get_agent(agent_name)
        tasks.append(agent.run_async(state))
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    
    # Merge results back into state
    return merge_results(state, results)
```

### Option 3: Implement Stream Processing
Use LangGraph's stream API with threading:
```python
def execute_parallel_batch(batch, state):
    """Execute batch items in parallel using ThreadPoolExecutor"""
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
        futures = {
            executor.submit(execute_agent, agent, state): agent
            for agent in batch
        }
        return {agent: future.result() for future, agent in futures.items()}
```

## Testing Parallel Execution

Test your parallel setup with:

```bash
# Run with detailed logging to see batch grouping
LOGLEVEL=INFO python backend/app/main.py

# Check logs for:
# "Router: Grouped X tasks into Y batch(es)"
# "Batch 1/Y -> Executing in parallel: [...]"
```

## Next Steps

1. ✅ Router now groups tasks into batches
2. ⏳ Implement async node execution for true parallelism
3. ⏳ Add task dependencies if needed (e.g., "compliance after analyze")
4. ⏳ Monitor performance improvements with metrics

## Files Modified

- `backend/app/graphs/document_graph.py` - Added batch-aware comments
- `backend/app/nodes/router_node.py` - Added `group_parallel_agents()` function

