# Implementation Guide: Parallel Agent Execution

## Quick Start

### 1. Verify the Changes Are Installed

The following files have been created/updated:

```
✅ backend/app/models/state/state.py          → Updated with AgentMetadata, AgentOutput
✅ backend/app/nodes/parallel_agents_node.py  → NEW: Parallel execution engine
✅ backend/app/graphs/document_graph.py       → Updated: simplified flow
✅ backend/app/nodes/router_node.py           → Updated: initializes parallel structures
```

### 2. No Changes Needed to Existing Agent Nodes

Your existing nodes are used as-is:
- `analysis_node.py`
- `ideation_node.py`
- `recommendation_node.py`
- `summarization_node.py`
- `translation_node.py`
- `copywriter_node.py`
- `compliance_node.py`

They work unchanged in the parallel model!

---

## Code Examples

### Example 1: Simple Parallel Execution

**Request**: "Analyze this and give recommendations"

```python
from app.workflows.process_document import run_document_workflow
import asyncio

async def main():
    # Router will identify: ["analyze", "recommend"]
    result = await run_document_workflow(
        file_path="brief.pdf",
        user_request="Analyze this and give recommendations"
    )
    
    # Access parallel results
    agents = result["agent_outputs"]
    
    print("=== Parallel Execution Results ===")
    for agent_name, output in agents.items():
        meta = result["agent_metadata"][agent_name]
        print(f"\n{agent_name.upper()}")
        print(f"  Duration: {meta['duration_ms']:.1f}ms")
        print(f"  Status: {meta['status']}")
        print(f"  Trace ID: {meta['langfuse_trace_id']}")
        if meta['status'] == 'completed':
            print(f"  Result: {output['output'][:100]}...")
        else:
            print(f"  Error: {meta.get('error')}")
    
    # Legacy access (still works)
    print(f"\nAnalysis: {result.get('analysis')}")
    print(f"Recommendations: {result.get('recommendation')}")

asyncio.run(main())
```

**Output**:
```
=== Parallel Execution Results ===

ANALYZE
  Duration: 245.3ms
  Status: completed
  Trace ID: trace_analyze_12345
  Result: Strategic analysis shows...

RECOMMEND
  Duration: 189.7ms
  Status: completed
  Trace ID: trace_recommend_67890
  Result: Key recommendations: 1. Focus on...
```

### Example 2: Handling Failed Agents

**Request**: "Translate, analyze, and summarize"

```python
async def main():
    result = await run_document_workflow(
        file_path="brief.pdf",
        user_request="Translate to Arabic, analyze, and summarize"
    )
    
    # Check for agent-specific errors
    errors = result["agent_errors"]  # Dict of agent_name → error message
    
    if errors:
        print("⚠️  Some agents failed:")
        for agent_name, error_msg in errors.items():
            print(f"  ❌ {agent_name}: {error_msg}")
    
    # Successful results are available regardless
    successful = {
        name: output["output"]
        for name, output in result["agent_outputs"].items()
        if result["agent_metadata"][name]["status"] == "completed"
    }
    
    print(f"\n✅ Completed: {', '.join(successful.keys())}")
    
    # Return partial results in API
    return {
        "results": successful,
        "errors": errors,
        "partial_results": True if errors else False
    }

asyncio.run(main())
```

### Example 3: Performance Monitoring

```python
async def main():
    result = await run_document_workflow(
        file_path="large_document.pdf",
        user_request="Full analysis"  # Multiple agents
    )
    
    # Analyze performance
    metadata = result["agent_metadata"]
    
    # Find slowest agent
    slowest = max(
        metadata.items(),
        key=lambda x: x[1].get("duration_ms", 0)
    )
    
    # Total parallel execution time
    total_time = max(
        m["duration_ms"] for m in metadata.values()
    )
    
    # Sum of all agents if run sequentially
    sum_time = sum(
        m["duration_ms"] for m in metadata.values()
    )
    
    speedup = sum_time / total_time
    
    print(f"Total time (parallel): {total_time:.1f}ms")
    print(f"Total time (if sequential): {sum_time:.1f}ms")
    print(f"Speedup: {speedup:.1f}x")
    print(f"Slowest agent: {slowest[0]} ({slowest[1]['duration_ms']:.1f}ms)")

asyncio.run(main())
```

**Output**:
```
Total time (parallel): 372.5ms
Total time (if sequential): 1240.3ms
Speedup: 3.3x
Slowest agent: analysis (372.5ms)
```

### Example 4: Integrating with API

**File**: `backend/app/api/routes.py`

```python
from fastapi import FastAPI, UploadFile, File, Form
from app.workflows.process_document import run_document_workflow
from app.core.logging import logger

app = FastAPI()

@app.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    request: str = Form(...),
):
    """
    Analyze a document with parallel agent execution.
    Returns structured results with per-agent metadata.
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Run workflow (agents execute in parallel)
        result = await run_document_workflow(
            file_path=temp_path,
            user_request=request
        )
        
        # Check for errors
        if result.get("errors"):
            logger.error(f"Workflow errors: {result['errors']}")
        
        # Format response
        response = {
            "status": "success",
            "agents_executed": list(result["agent_outputs"].keys()),
            "results": {},
            "performance": {},
            "errors": result.get("agent_errors", {})
        }
        
        # Add agent results with metadata
        for agent_name, output in result["agent_outputs"].items():
            meta = result["agent_metadata"][agent_name]
            
            response["results"][agent_name] = {
                "output": output["output"],
                "status": meta["status"],
                "duration_ms": meta["duration_ms"],
                "trace_id": meta["langfuse_trace_id"]
            }
            
            # Add to performance metrics
            response["performance"][agent_name] = {
                "duration_ms": meta["duration_ms"],
                "status": meta["status"]
            }
        
        # Add execution summary
        response["summary"] = {
            "total_agents": len(result["agent_outputs"]),
            "successful": len([
                m for m in result["agent_metadata"].values()
                if m["status"] == "completed"
            ]),
            "failed": len(result.get("agent_errors", {})),
            "total_time_ms": max(
                m["duration_ms"] for m in result["agent_metadata"].values()
            ),
            "request": request
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in analyze_document: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
```

**API Response Example**:
```json
{
  "status": "success",
  "agents_executed": ["analyze", "recommend", "ideate"],
  "results": {
    "analyze": {
      "output": "Strategic analysis showing...",
      "status": "completed",
      "duration_ms": 245.3,
      "trace_id": "trace_analyze_12345"
    },
    "recommend": {
      "output": "Key recommendations...",
      "status": "completed",
      "duration_ms": 189.7,
      "trace_id": "trace_recommend_67890"
    },
    "ideate": {
      "output": "Campaign ideas...",
      "status": "completed",
      "duration_ms": 156.2,
      "trace_id": "trace_ideate_34567"
    }
  },
  "performance": {
    "analyze": {"duration_ms": 245.3, "status": "completed"},
    "recommend": {"duration_ms": 189.7, "status": "completed"},
    "ideate": {"duration_ms": 156.2, "status": "completed"}
  },
  "errors": {},
  "summary": {
    "total_agents": 3,
    "successful": 3,
    "failed": 0,
    "total_time_ms": 245.3,
    "request": "Analyze this brief and give recommendations"
  }
}
```

### Example 5: Accessing Langfuse Traces

**Monitor in Langfuse Dashboard**:

```
Document Processing Workflow (trace_12345)
├─ file_loading: 45ms
├─ validation: 22ms
├─ language_detection: 12ms
└─ graph_execution: 1500ms
   ├─ node_extract: 250ms
   ├─ node_refine: 180ms
   ├─ node_router: 15ms
   └─ parallel_agents_execution: 245ms  ← Total parallel time
      ├─ agent_analyze: 245.3ms  (slowest)
      │  ├─ input: {...}
      │  ├─ output: {...}
      │  └─ status: success
      ├─ agent_recommend: 189.7ms
      │  └─ ...
      └─ agent_ideate: 156.2ms
         └─ ...
```

Each agent span includes:
- Individual trace ID for filtering
- Input/output
- Status and error messages
- Performance metrics
- Custom metadata

---

## Accessing Per-Agent Data

### Direct Access Patterns

```python
# 1. Get all results
all_results = state["agent_outputs"]

# 2. Get specific agent output
analysis = state["agent_outputs"]["analyze"]["output"]

# 3. Get agent metadata (performance, status)
metadata = state["agent_metadata"]["analyze"]
duration = metadata["duration_ms"]
status = metadata["status"]

# 4. Get agent-specific errors
analyze_error = state["agent_errors"].get("analyze")

# 5. Get agent evaluations (from LLM Judge)
evaluations = state["agent_evaluations"].get("analyze", [])

# 6. Check if agent completed successfully
if state["agent_metadata"]["analyze"]["status"] == "completed":
    print("Analyze succeeded")
```

### Filtering Successful Agents

```python
def get_successful_results(state):
    """Get only successfully completed agent results."""
    successful = {}
    for agent_name, output in state["agent_outputs"].items():
        if state["agent_metadata"][agent_name]["status"] == "completed":
            successful[agent_name] = output["output"]
    return successful

# Usage
results = get_successful_results(final_state)
print(results)  # {"analyze": "...", "recommend": "..."}
```

### Building Reports

```python
def create_execution_report(state):
    """Create a detailed execution report."""
    report = {
        "execution_flow": {
            "router_decision": state["next_steps"],
            "agents_executed": list(state["agent_outputs"].keys()),
            "total_time_ms": max(
                m["duration_ms"] for m in state["agent_metadata"].values()
            )
        },
        "agent_results": {}
    }
    
    for agent_name, output in state["agent_outputs"].items():
        meta = state["agent_metadata"][agent_name]
        report["agent_results"][agent_name] = {
            "status": meta["status"],
            "duration_ms": meta["duration_ms"],
            "error": meta.get("error"),
            "evaluation": {
                "score": output["evaluation"].get("score") if output["evaluation"] else None,
                "feedback": output["evaluation"].get("feedback") if output["evaluation"] else None
            }
        }
    
    return report
```

---

## Testing Parallel Execution

### Test: Verify Concurrent Execution

```python
import time
import pytest
from app.workflows.process_document import run_document_workflow

@pytest.mark.asyncio
async def test_parallel_execution_is_faster():
    """Verify that parallel execution is faster than sequential."""
    # Set up test document
    test_file = "backend/tests/test_data/Midnight Brew.txt"
    request = "Analyze and give recommendations"
    
    # Run parallel execution
    start = time.time()
    result = await run_document_workflow(test_file, request)
    parallel_time = time.time() - start
    
    # Check results
    assert result["agent_metadata"]["analyze"]["status"] == "completed"
    assert result["agent_metadata"]["recommend"]["status"] == "completed"
    
    # Verify metadata
    analyze_time = result["agent_metadata"]["analyze"]["duration_ms"]
    recommend_time = result["agent_metadata"]["recommend"]["duration_ms"]
    
    # Parallel time should be close to max, not sum
    max_agent_time = max(analyze_time, recommend_time)
    sum_agent_time = analyze_time + recommend_time
    
    print(f"Parallel execution: {parallel_time:.2f}s")
    print(f"Max agent time: {max_agent_time}ms")
    print(f"Sum of agents: {sum_agent_time}ms")
    
    # Assert parallel is faster
    assert parallel_time < (sum_agent_time / 1000) * 0.8, "Parallel not faster than sequential"
```

### Test: Verify Per-Agent Traces

```python
@pytest.mark.asyncio
async def test_per_agent_langfuse_traces():
    """Verify each agent has its own Langfuse trace."""
    result = await run_document_workflow(
        "backend/tests/test_data/Midnight Brew.txt",
        "Analyze, summarize, and recommend"
    )
    
    # Check each agent has a trace ID
    for agent_name, meta in result["agent_metadata"].items():
        assert meta["langfuse_trace_id"] is not None, f"{agent_name} missing trace ID"
        assert meta["agent_id"] is not None, f"{agent_name} missing agent ID"
        assert meta["duration_ms"] > 0, f"{agent_name} missing duration"
    
    # Check trace IDs are unique
    trace_ids = [
        m["langfuse_trace_id"]
        for m in result["agent_metadata"].values()
    ]
    assert len(trace_ids) == len(set(trace_ids)), "Duplicate trace IDs found"
```

### Test: Verify Error Isolation

```python
@pytest.mark.asyncio
async def test_agent_error_isolation():
    """Verify that one agent error doesn't stop others."""
    # Use invalid/problematic input
    result = await run_document_workflow(
        "backend/tests/test_data/invalid.pdf",  # Might fail extraction
        "Analyze and recommend"
    )
    
    # At least some agents should attempt execution
    assert len(result["agent_outputs"]) > 0
    
    # Check metadata for all agents
    statuses = [
        m["status"] for m in result["agent_metadata"].values()
    ]
    
    # Either completed or failed, but all attempted
    assert all(s in ["completed", "failed"] for s in statuses)
```

---

## Troubleshooting Guide

### Issue: Agents Still Running Sequentially

**Symptom**: Total execution time = sum of all agent times

**Cause**: Agents not actually running in parallel

**Solution**:
1. Check `parallel_agents_node.py` is imported correctly
2. Verify `document_graph.py` has `parallel_agents_node` connected after router
3. Check logs for "parallel_agents_node: Starting parallel execution"

```bash
# Check logs
grep "parallel" backend/logs/*.log
```

### Issue: Missing Langfuse Traces per Agent

**Symptom**: Only one trace for all agents, not individual spans

**Cause**: Langfuse not initialized or spans not created properly

**Solution**:
```python
# Verify Langfuse is initialized
from app.core.langfuse import get_langfuse_client

client = get_langfuse_client()
assert client is not None, "Langfuse not initialized"

# Check environment variables
import os
assert os.getenv("LANGFUSE_PUBLIC_KEY"), "Missing LANGFUSE_PUBLIC_KEY"
assert os.getenv("LANGFUSE_SECRET_KEY"), "Missing LANGFUSE_SECRET_KEY"
```

### Issue: State Keys Not Found

**Symptom**: `KeyError: 'agent_outputs'`

**Cause**: Old code expecting different state structure

**Solution**: Use backward-compatible access patterns:
```python
# Old way (still works)
analysis = state.get("analysis")

# New way with defaults
agent_outputs = state.get("agent_outputs", {})
analysis = agent_outputs.get("analyze", {}).get("output")
```

### Issue: High Memory Usage

**Symptom**: Memory increases with number of agents

**Cause**: State copied for each agent execution

**Solution**:
1. Consider using file-based caching for large texts
2. Implement state slicing if only some fields needed per agent
3. Implement cleanup of intermediate results

---

## Next Steps

1. **Run Tests**: `pytest backend/tests/test_graph.py -v`
2. **Monitor Langfuse**: Go to Langfuse dashboard and watch execution traces
3. **Update API Response**: Use the example API code above
4. **Update Frontend**: Modify API client to handle new response structure
5. **Document Changes**: Update any internal documentation

---

## Rollback Instructions

If you need to revert to sequential execution:

1. Restore old graph:
```bash
git checkout HEAD~1 backend/app/graphs/document_graph.py
```

2. Keep new state schema (backward compatible)

3. Remove parallel_agents_node.py import

The old router-based conditional routing will work with new state schema without issues.

---

## Performance Metrics to Track

In your monitoring:
- `agent_duration_ms`: Individual agent execution time
- `parallel_execution_time_ms`: Total time (max of all agents)
- `agent_status`: "completed" or "failed"
- `sequential_equivalent_ms`: Sum of all agent times (for speedup calc)
- `speedup_factor`: Sequential / Parallel

```python
def calculate_speedup(state):
    meta = state["agent_metadata"]
    parallel_time = max(m["duration_ms"] for m in meta.values())
    sequential_time = sum(m["duration_ms"] for m in meta.values())
    return sequential_time / parallel_time if parallel_time > 0 else 0
```
