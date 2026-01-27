# Execution Flow for Your Request

## User Request
```
"Please analyze this marketing brief, point out any risks, generate campaign ideas, 
and translate the final summary to Arabic. I need a 30-second executive summary, 
the top 3 strategy recommendations, and 2 creative directions we can pitch. 
Generate multiple copy variants suitable for A/B testing. Check also the compliance of the content."
```

## Router Decision
```python
Router.decide(user_request) → [
    "analyze",      # "point out any risks"
    "ideate",       # "generate campaign ideas"
    "translate",    # "translate to Arabic"
    "summarize",    # "30-second executive summary"
    "recommend",    # "top 3 strategy recommendations"
    "copywrite",    # "2 creative directions" + "copy variants for A/B testing"
    "compliance"    # "check compliance"
]
```

## Batch Grouping
```python
group_parallel_agents([
    "analyze", "ideate", "translate", "summarize", "recommend", "copywrite", "compliance"
])

Returns:
[
    ["summarize", "analyze", "ideate", "recommend", "copywrite"],  # Batch 1: All run in parallel
    ["translate"],                                                   # Batch 2: Translation alone
    ["compliance"]                                                   # Batch 3: Compliance check last
]
```

## Execution Timeline (WITH PARALLELIZATION)

### Before (Sequential - OLD):
```
Extract → Refine → Analyze (20s) → Ideate (18s) → Translate (12s) → 
Summarize (8s) → Recommend (15s) → Copywrite (20s) → Compliance (10s)
═══════════════════════════════════════════════════════════════════════════
                                  TOTAL: ~113 seconds
```

### After (Parallel - NEW):
```
BATCH 1: Parallel Execution (T=0 to T=20s)
    Timeline:
    0s ──────────────────────────────────────────── 20s
    ├─ Analyze         ████████████████████ (20s)
    ├─ Ideate          ██████████████████ (18s)
    ├─ Summarize       ████████ (8s)
    ├─ Recommend       ███████████████ (15s)
    └─ Copywrite       ████████████████████ (20s)
    
    Result: All 5 agents complete in ~20 seconds (time of longest agent)

BATCH 2: Translate (T=20s to T=32s)
    Timeline:
    20s ───────────────────── 32s
    └─ Translate       ████████████ (12s)

BATCH 3: Compliance Check (T=32s to T=42s)
    Timeline:
    32s ──────────── 42s
    └─ Compliance     ██████████ (10s)

═══════════════════════════════════════════════════════════════════════════
                                  TOTAL: ~42 seconds
```

## Performance Improvement
```
Sequential Time: 113 seconds
Parallel Time:   42 seconds
Speed Up:        2.69x faster ✅

Time Saved:      71 seconds (63% reduction)
```

## Why These Groupings?

1. **Batch 1 (Parallel Group)**
   - `analyze`, `recommend`, `ideate`, `copywrite`, `summarize` 
   - ✅ All read from the SAME extracted text
   - ✅ No dependencies between them
   - ✅ Can execute simultaneously

2. **Batch 2 (Standalone)**
   - `translate`
   - ⚠️ Modifies the text (text → translated text)
   - ⚠️ Must run AFTER analysis (risk assessment on original)
   - ⚠️ Runs in its own batch

3. **Batch 3 (Standalone)**
   - `compliance`
   - ⚠️ Validates all the generated content
   - ⚠️ Runs AFTER everything else is generated
   - ⚠️ Checks compliance of all outputs

## Detailed Agent Outputs (Parallel Execution)

```
At T=20s (Batch 1 completes):
{
  "analyze_output": {
    "risks": [
      "Risk 1: Missing target audience validation",
      "Risk 2: Budget allocation unclear",
      "Risk 3: Timeline realistic but tight"
    ]
  },
  "ideate_output": {
    "campaign_ideas": [
      "Idea 1: ...",
      "Idea 2: ..."
    ]
  },
  "summarize_output": {
    "executive_summary": "30-second summary of the brief..."
  },
  "recommend_output": {
    "recommendations": [
      "Recommendation 1: ...",
      "Recommendation 2: ...",
      "Recommendation 3: ..."
    ]
  },
  "copywrite_output": {
    "copy_variants": [
      "Variant A: ...",
      "Variant B: ...",
      "Variant C: ..."
    ]
  }
}

At T=32s (Batch 2 completes):
{
  "translate_output": {
    "summary_ar": "الملخص بالعربية...",
    "recommendations_ar": "التوصيات بالعربية..."
  }
}

At T=42s (Batch 3 completes):
{
  "compliance_output": {
    "compliant": true,
    "issues": [],
    "warnings": []
  }
}
```

## How It Works in Code

```python
# Step 1: Router groups tasks
router_node(state) → parallel_batches = [
    ["analyze", "ideate", "recommend", "copywrite", "summarize"],
    ["translate"],
    ["compliance"]
]

# Step 2: Parallel executor runs Batch 1
parallel_batch_executor(state):
    with ThreadPoolExecutor(max_workers=5):
        futures = {
            executor.submit(analyze_agent.run, ...): "analyze",
            executor.submit(ideate_agent.run, ...): "ideate",
            executor.submit(recommend_agent.run, ...): "recommend",
            executor.submit(copywrite_agent.run, ...): "copywrite",
            executor.submit(summarize_agent.run, ...): "summarize",
        }
        # All 5 run simultaneously ⚡
        # Wait for all to complete (~20s)
        return merged_results

# Step 3: Check if more batches
if current_batch_index < len(batches):
    return "continue"  # Go back to parallel_batch_executor

# Step 4: Execute Batch 2 (translate alone)
parallel_batch_executor(state) → execute ["translate"] in isolation

# Step 5: Execute Batch 3 (compliance check)
parallel_batch_executor(state) → execute ["compliance"] in isolation

# All done → END
```

## Key Files Updated
- `backend/app/nodes/parallel_batch_node.py` - NEW: Parallel executor
- `backend/app/graphs/document_graph.py` - MODIFIED: Uses parallel executor
- `backend/app/nodes/router_node.py` - Already has grouping logic

## Monitoring Parallel Execution

Watch the logs for:
```
Router: Grouped 7 tasks into 3 batch(es)
Router: Batches -> [['analyze', 'ideate', 'recommend', 'copywrite', 'summarize'], ['translate'], ['compliance']]

Parallel executor: Executing batch 1/3 -> ['analyze', 'ideate', 'recommend', 'copywrite', 'summarize']
Parallel executor: Executing 5 agents in parallel
Parallel executor: Agent 'analyze' completed
Parallel executor: Agent 'ideate' completed
Parallel executor: Agent 'recommend' completed
Parallel executor: Agent 'copywrite' completed
Parallel executor: Agent 'summarize' completed
Parallel executor: Batch 1 completed, moving to next batch

Parallel executor: Executing batch 2/3 -> ['translate']
Parallel executor: Single agent in batch, executing translate sequentially
Parallel executor: Agent 'translate' completed
Parallel executor: Batch 2 completed, moving to next batch

Parallel executor: Executing batch 3/3 -> ['compliance']
Parallel executor: Single agent in batch, executing compliance sequentially
Parallel executor: Agent 'compliance' completed
Parallel executor: Batch 3 completed, moving to next batch

Parallel executor: All batches completed
```
