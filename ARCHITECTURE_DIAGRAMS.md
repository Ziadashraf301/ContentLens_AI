# Architecture Diagrams

## Execution Flow Comparison

### Old Sequential Model (Problem)

```
Router Decision: ["analyze", "recommend", "ideate"]

Time ──────────────────────────────────────────────→
  0ms │
     │ ┌─────────────────────┐
     │ │     Extract         │  250ms
     │ └─────────────────────┘
     │                          │
250ms│                          ↓
     │                    ┌─────────────────────┐
     │                    │      Refine         │  180ms
     │                    └─────────────────────┘
     │                                             │
430ms│                                             ↓
     │                                      ┌─────────────────────┐
     │                                      │      Router         │  15ms
     │                                      │  Returns:           │
     │                                      │  ["analyze", ...    │
     │                                      └─────────────────────┘
     │                                                              │
445ms│                                                              ↓
     │  ┌──────────────────────────────────────────────────┐
     │  │ SEQUENTIAL ROUTING LOOP                          │
     │  │                                                  │
     │  │  1️⃣  → analyze_node  (450ms)                     │
     │  │      ↓                                           │
     │  │  2️⃣  → back to router (re-evaluates state)      │
     │  │      ↓                                           │
     │  │  3️⃣  → recommend_node (380ms)                    │
     │  │      ↓                                           │
     │  │  4️⃣  → back to router (re-evaluates state)      │
     │  │      ↓                                           │
     │  │  5️⃣  → ideate_node    (320ms)                    │
     │  │      ↓                                           │
     │  │  6️⃣  → back to router (all done, END)           │
     │  │                                                  │
     │  └──────────────────────────────────────────────────┘
     │
1595ms│ ✗ RESULT: Sequential execution = Sum of all times
     │

Execution Time = 250 + 180 + 15 + 450 + 380 + 320 = 1595ms
```

### New Parallel Model (Solution)

```
Router Decision: ["analyze", "recommend", "ideate"]

Time ──────────────────────────────────────────────→
  0ms │
     │ ┌─────────────────────┐
     │ │     Extract         │  250ms
     │ └─────────────────────┘
     │                          │
250ms│                          ↓
     │                    ┌─────────────────────┐
     │                    │      Refine         │  180ms
     │                    └─────────────────────┘
     │                                             │
430ms│                                             ↓
     │                                      ┌─────────────────────┐
     │                                      │      Router         │  15ms
     │                                      │  Returns list:      │
     │                                      │  ["analyze", ...]   │
     │                                      └─────────────────────┘
     │                                                              │
445ms│                                                              ↓
     │  ┌──────────────────────────────────────────────────┐
     │  │ PARALLEL EXECUTION (asyncio.gather)              │
     │  │                                                  │
     │  │  Task 1:  analyze_node    (450ms)  ║             │
     │  │  Task 2:  recommend_node  (380ms)  ║ Concurrent  │
     │  │  Task 3:  ideate_node     (320ms)  ║             │
     │  │                                                  │
     │  │  await asyncio.gather(*tasks)                   │
     │  │  ↓ waits for LONGEST to complete                │
     │  │                                                  │
     │  └──────────────────────────────────────────────────┘
     │
895ms│ ✓ RESULT: Parallel execution = Max agent time
     │


Execution Time = 250 + 180 + 15 + max(450, 380, 320) = 895ms
Speedup: 1595 / 895 = 1.78x faster ✨
```

---

## State Structure Evolution

### Old State Schema

```python
AgentState = {
    "raw_text": "...",
    "user_request": "...",
    "extraction": {...},
    
    # ❌ Shared keys - collision risk if parallel
    "analysis": "Result...",
    "recommendation": "Result...",
    "ideation": "Result...",
    "summary": "Result...",
    
    # ❌ Mixed arrays - no per-agent attribution
    "errors": [
        "Analysis failed",
        "Recommendation error"
    ],
    "evaluations": [
        {"score": 0.8, "feedback": "..."},
        {"score": 0.9, "feedback": "..."}
    ],
    
    # ❌ No metadata
    "next_steps": ["analyze", "recommend"],
    "current_step_index": 0
}
```

### New State Schema (Parallel-Safe)

```python
AgentState = {
    # Core data (same as before)
    "raw_text": "...",
    "user_request": "...",
    "extraction": {...},
    
    # ✓ Legacy fields still populated (backward compat)
    "analysis": "Result...",
    "recommendation": "Result...",
    "ideation": "Result...",
    
    # ✓ NEW: Parallel-safe storage
    "agent_outputs": {
        "analyze": {
            "agent_id": "analyze_1674567890123",
            "agent_name": "analyze",
            "output": "Result...",
            "metadata": {
                "start_time": 1674567890.123,
                "end_time": 1674567890.456,
                "duration_ms": 250.3,
                "status": "completed",
                "langfuse_trace_id": "trace_analyze_12345"
            },
            "evaluation": {
                "score": 0.85,
                "feedback": "High quality analysis"
            },
            "validation_passed": True
        },
        "recommend": {
            "agent_id": "recommend_1674567890789",
            "agent_name": "recommend",
            "output": "Result...",
            "metadata": {
                "duration_ms": 189.7,
                "status": "completed",
                "langfuse_trace_id": "trace_recommend_67890"
            },
            "evaluation": {...},
            "validation_passed": True
        },
        "ideate": {
            "agent_id": "ideate_1674567890456",
            "agent_name": "ideate",
            "output": "Result...",
            "metadata": {
                "duration_ms": 156.2,
                "status": "completed",
                "langfuse_trace_id": "trace_ideate_34567"
            },
            ...
        }
    },
    
    # ✓ Per-agent metadata tracking
    "agent_metadata": {
        "analyze": {
            "agent_id": "analyze_1674567890123",
            "duration_ms": 250.3,
            "status": "completed",
            "langfuse_trace_id": "trace_analyze_12345"
        },
        "recommend": {
            "agent_id": "recommend_1674567890789",
            "duration_ms": 189.7,
            "status": "completed",
            "langfuse_trace_id": "trace_recommend_67890"
        },
        "ideate": {
            "agent_id": "ideate_1674567890456",
            "duration_ms": 156.2,
            "status": "completed",
            "langfuse_trace_id": "trace_ideate_34567"
        }
    },
    
    # ✓ Isolated error tracking
    "agent_errors": {
        # Only populated if an agent failed
        # "analyze": "Connection timeout"
    },
    
    # ✓ Per-agent evaluations
    "agent_evaluations": {
        "analyze": [
            {"score": 0.85, "feedback": "High quality"}
        ],
        "recommend": [
            {"score": 0.90, "feedback": "Helpful recommendations"}
        ],
        "ideate": [
            {"score": 0.88, "feedback": "Creative ideas"}
        ]
    },
    
    # Control flow
    "next_steps": ["analyze", "recommend", "ideate"],
    "pending_agents": [],  # NEW
    "completed_agents": ["analyze", "recommend", "ideate"],  # NEW
    "errors": []  # Backward compat
}
```

---

## Graph Structure Comparison

### Old Graph (Sequential Looping)

```
┌──────────────────┐
│  node_extract    │
│  extraction_node │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  node_refine     │
│  refiner_node    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  node_router     │
│  router_node     │
│                  │
│  Returns:        │
│  next_steps =    │
│  ["analyze",     │
│   "recommend",   │
│   "ideate"]      │
└────────┬─────────┘
         │
         │ ┌─────────────────────────────────────┐
         └─┤ CONDITIONAL ROUTING LOGIC            │
           │ (routing_logic function)            │
           │ Evaluates state and returns ONE     │
           │ destination at a time               │
           └─────────────────────────────────────┘
           │
           ├─→ to_summarize ───► node_summarize ──┐
           │   (if step 0)       (summarization_  │
           │                      node)            │
           │                                       ├─→ back to node_router
           │                                       │   (loop!)
           ├─→ to_translate ───► node_translate ──┘
           │   (if step 1)       (translation_
           │                      node)
           │                      │
           │                      └─→ back to node_router (loop!)
           │
           ├─→ to_analyze ─────► node_analyze ────┐
           │   (if step 2)       (analysis_node)  │
           │                                       ├─→ back to node_router
           │                                       │   (loop!)
           ├─→ to_recommend ───► node_recommend ──┘
           │   (if step 3)       (recommendation_
           │                      node)
           │                      │
           │                      └─→ back to node_router (loop!)
           │
           ├─→ to_ideate ──────► node_ideate ────┐
           │   (if step 4)       (ideation_node) │
           │                                      ├─→ back to node_router
           │                                      │   (loop!)
           ├─→ to_copywrite ───► node_copywrite ┘
           │   (if step 5)       (copywriter_
           │                      node)
           │                      │
           │                      └─→ back to node_router (loop!)
           │
           ├─→ to_compliance ──► node_compliance ─→ back to node_router
           │   (if step 6)       (compliance_node)  (loop!)
           │
           └─→ end (if all steps done)
               │
               ▼
            [END]

⚠️ PROBLEMS:
- 10+ nodes with complex conditional routing
- Each agent loops back to router
- Sequential execution (not parallel)
- Hard to follow execution flow
```

### New Graph (Parallel Execution)

```
┌──────────────────────┐
│   node_extract       │
│  extraction_node     │
│                      │
│  Loads and extracts  │
│  raw text from file  │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│   node_refine        │
│  refiner_node        │
│                      │
│  Cleans and          │
│  validates text      │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────────────────┐
│      node_router                 │
│  router_node                     │
│                                  │
│  Determines which agents         │
│  should handle the request       │
│                                  │
│  Input:  user_request            │
│  Output: next_steps =            │
│          ["analyze", ...]        │
└─────────┬────────────────────────┘
          │
          │ Passes list to parallel executor
          │
          ▼
┌────────────────────────────────────────────────────────┐
│       node_parallel_agents                             │
│  parallel_agents_node                                  │
│                                                        │
│  ╔══════════════════════════════════════════════════╗ │
│  ║ PARALLEL EXECUTION USING asyncio.gather()        ║ │
│  ╚══════════════════════════════════════════════════╝ │
│                                                        │
│  Creates async task for each agent:                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────┐ │
│  │ Task 1:         │  │ Task 2:          │  │Task 3│ │
│  │ analyze_node    │  │ recommend_node   │  │ideate│ │
│  │                 │  │                  │  │_node │ │
│  │ ┌─────────────┐ │  │ ┌──────────────┐ │  │┌────┐│ │
│  │ │  agent_id   │ │  │ │  agent_id    │ │  ││    ││ │
│  │ │ "analyze_"  │ │  │ │ "recommend_" │ │  ││    ││ │
│  │ │ "1674567890"│ │  │ │ "1674567890" │ │  ││ .. ││ │
│  │ └─────────────┘ │  │ └──────────────┘ │  │└────┘│ │
│  │                 │  │                  │  │      │ │
│  │ Langfuse span   │  │ Langfuse span    │  │Langf.│ │
│  │ "agent_analyze" │  │ "agent_recommend"│  │span  │ │
│  │                 │  │                  │  │      │ │
│  └─────────────────┘  └──────────────────┘  └──────┘ │
│           │                   │                 │     │
│           │   All running     │                 │     │
│           │   concurrently    │                 │     │
│           └───────────┬───────┴─────────────────┘     │
│                       │                               │
│              await asyncio.gather(*tasks)            │
│              (waits for ALL to complete)             │
│                       │                               │
│  Merges results with per-agent metadata:             │
│  agent_outputs = {                                    │
│    "analyze": {...},                                  │
│    "recommend": {...},                                │
│    "ideate": {...}                                    │
│  }                                                    │
│                                                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
                 [END]

✓ BENEFITS:
- 4 nodes (simple and clean)
- Straight-line execution flow
- Parallel execution with asyncio
- Per-agent tracing
- Easy to understand and maintain
```

---

## Async Execution Timeline

### How asyncio.gather() Executes Agents

```python
# Code:
tasks = [
    execute_agent_with_tracing("analyze", state, trace_client),
    execute_agent_with_tracing("recommend", state, trace_client),
    execute_agent_with_tracing("ideate", state, trace_client)
]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Execution Timeline:

Time  │
      │ ┌─ Task 1: execute_agent_with_tracing("analyze", ...)
 0ms  │ │     ↓
      │ │ ┌─ Task 2: execute_agent_with_tracing("recommend", ...)
 0ms  │ │ │     ↓
      │ │ │ ┌─ Task 3: execute_agent_with_tracing("ideate", ...)
 0ms  │ │ │ │     ↓
      │ │ │ │
      │ │ │ │  All three tasks created and started
      │ │ │ │  at roughly the same time (0ms)
      │ │ │ │
  50ms│ │ │ ├─── Task 3 completes (156ms, ideate)
      │ │ │ │     ↓
      │ │ │ │  ┌──────────────────────┐
      │ │ │ └──│ Trying to merge      │
      │ │ │    │ BUT waiting for...   │
      │ │ │    └──────────────────────┘
      │ │
 200ms│ ├────── Task 2 completes (189ms, recommend)
      │ │       ↓
      │ │    ┌──────────────────────┐
      │ │    │ Still waiting for... │
      │ │    │ Task 1               │
      │ │    └──────────────────────┘
      │ │
 250ms│ ├────── Task 1 completes (245ms, analyze) ← SLOWEST
      │ │       ↓
      │ │    ┌──────────────────────┐
      │ │    │ ALL DONE!            │
      │ │    │ Merge results        │
      │ └────│ Return to caller     │
      │      └──────────────────────┘
      │
 250ms│ Total time = Max(250, 189, 156) = 250ms ✓

Without asyncio.gather() (sequential):
245 + 189 + 156 = 590ms ✗

Parallel speedup: 590 / 250 = 2.36x faster!
```

---

## Langfuse Trace Hierarchy

### Before (Mixed Traces)

```
Root Trace: document_processing_workflow
│
├─ Span: file_loading
│  └─ LLM: ocr or text extraction
│
├─ Span: validation
│  └─ Logic: sanitize and validate
│
└─ Span: graph_execution
   │
   ├─ Span: node_router
   │  └─ LLM: router agent (which agents?)
   │
   ├─ Span: node_analyze (❌ First agent)
   │  ├─ LLM: analyze agent
   │  └─ LLM: judge evaluation
   │
   ├─ Span: node_recommend (❌ Second agent)
   │  ├─ LLM: recommend agent
   │  └─ LLM: judge evaluation
   │
   └─ Span: node_ideate (❌ Third agent)
      ├─ LLM: ideate agent
      └─ LLM: judge evaluation

PROBLEMS:
❌ All agents under same parent span
❌ Can't filter by individual agent
❌ Can't see parallel timing visually
❌ Mixed evaluations
```

### After (Hierarchical Traces)

```
Root Trace: document_processing_workflow
│
├─ Span: file_loading
│  └─ LLM: ocr or text extraction
│
├─ Span: validation
│  └─ Logic: sanitize and validate
│
├─ Span: node_router
│  └─ LLM: router agent (which agents?)
│
└─ Span: parallel_agents_execution  (✓ Parent for all agents)
   │
   ├─ Span: agent_analyze  (✓ Individual span)
   │  │  [Started: T+0ms]
   │  │  [Duration: 250.3ms]
   │  │  [Status: completed]
   │  │  [Trace ID: trace_analyze_12345]
   │  │
   │  ├─ LLM: analyze agent
   │  └─ LLM: judge evaluation
   │  │  [Completed: T+250ms]
   │
   ├─ Span: agent_recommend  (✓ Individual span)
   │  │  [Started: T+0ms]
   │  │  [Duration: 189.7ms]
   │  │  [Status: completed]
   │  │  [Trace ID: trace_recommend_67890]
   │  │
   │  ├─ LLM: recommend agent
   │  └─ LLM: judge evaluation
   │  │  [Completed: T+189ms]
   │
   └─ Span: agent_ideate  (✓ Individual span)
      │  [Started: T+0ms]
      │  [Duration: 156.2ms]
      │  [Status: completed]
      │  [Trace ID: trace_ideate_34567]
      │
      ├─ LLM: ideate agent
      └─ LLM: judge evaluation
         [Completed: T+156ms]

BENEFITS:
✓ Each agent visible as separate span
✓ Can filter: "trace_agent_analyze"
✓ Can compare durations visually
✓ Can identify slow agents
✓ Isolated error tracking per agent
```

---

## Data Flow: Request to Response

```
┌─────────────────────────────────────────────────────────────┐
│ User Request                                                │
│ POST /analyze                                               │
│ {                                                           │
│   "file": <binary>,                                         │
│   "request": "Analyze and give recommendations"             │
│ }                                                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ FILE UPLOAD  │
        │ (temporary)  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────────────┐
        │  run_document_       │
        │  workflow()          │
        │  {                   │
        │    file_path: "..." │
        │    user_request:     │
        │    "Analyze..."      │
        │  }                   │
        └──────┬───────────────┘
               │
        ┌──────┴─────────────────────────┐
        │  Extract + Refine              │
        │  (Sequential preprocessing)    │
        │  ───────────────────────────── │
        │  extract: 250ms                │
        │  refine: 180ms                 │
        └──────┬──────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │  Router                         │
        │  ───────────────────────────── │
        │  Input: "Analyze and give      │
        │          recommendations"       │
        │  Output: ["analyze",           │
        │           "recommend"]         │
        │  Time: 15ms                    │
        └──────┬──────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │ Parallel Agents (asyncio)       │
        │ ─────────────────────────────ール│
        │ ┌───────────┬──────────────┐    │
        │ │ analyze   │ recommend    │    │
        │ │ (250ms)   │ (189ms)      │    │
        │ └─────┬─────┴──────┬───────┘    │
        │       │            │            │
        │  Concurrent!      Concurrent!  │
        │       │            │            │
        │       ▼            ▼            │
        │  returns:  returns:             │
        │  {output, {output,              │
        │   metadata metadata             │
        │   eval}    eval}                │
        │                                 │
        │  Merge into state:              │
        │  agent_outputs = {              │
        │    "analyze": {...},            │
        │    "recommend": {...}           │
        │  }                              │
        │  agent_metadata = {             │
        │    "analyze": {dur: 250.3, ..}  │
        │    "recommend": {dur: 189.7,.}  │
        │  }                              │
        │  Total time: max(250, 189)      │
        │  = 250ms                        │
        └──────┬──────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │ Return Response to API          │
        │ ─────────────────────────────ール│
        │ {                               │
        │   "status": "success",          │
        │   "results": {                  │
        │     "analyze": "...",           │
        │     "recommend": "..."          │
        │   },                            │
        │   "metadata": {                 │
        │     "analyze": {                │
        │       "duration_ms": 250.3,     │
        │       "status": "completed",    │
        │       "trace_id": "..."         │
        │     },                          │
        │     "recommend": {              │
        │       "duration_ms": 189.7,     │
        │       ...                       │
        │     }                           │
        │   },                            │
        │   "summary": {                  │
        │     "total_time_ms": 250.3,     │
        │     "speedup": 2.3              │
        │   }                             │
        │ }                               │
        └──────────────────────────────────┘
```

---

## Performance Scaling

```
Number of Agents vs. Execution Time

                    Execution Time (ms)
                    │
            Sequential (old)  Parallel (new)
                    │
            2 agents│  400ms                 200ms
                    │  
            3 agents│  600ms                 250ms
                    │  /
            4 agents│ /800ms                 300ms
                    │/
            5 agents│  1000ms                400ms
                    │
            6 agents│  1200ms                450ms
                    │
            7 agents│  1400ms                500ms
                    │
                    └────────────────────────────

Sequential: Linear increase (O(n))
Parallel: Logarithmic increase (O(log n))

For 5 agents:
- Sequential: 1000ms
- Parallel: 400ms
- Speedup: 2.5x

For 10 agents:
- Sequential: 2000ms
- Parallel: ~600ms (if agents are 50-200ms each)
- Speedup: 3.3x
```

These diagrams help visualize the transformation from sequential to parallel execution.
