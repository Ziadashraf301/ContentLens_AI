from typing import TypedDict, List, Optional, Dict, Any


class AgentMetadata(TypedDict, total=False):
    """
    Per-agent metadata for observability and tracing.
    Allows tracking individual agent execution, performance, and state.
    """
    agent_id: str  # Unique identifier (e.g., "analyze_1", "summarize_1")
    agent_name: str  # Canonical name (e.g., "analyze", "summarize")
    start_time: float  # Unix timestamp
    end_time: Optional[float]
    duration_ms: Optional[float]
    status: str  # "pending", "running", "completed", "failed"
    error: Optional[str]
    langfuse_trace_id: Optional[str]
    input_hash: Optional[str]  # For deduplication if needed


class AgentOutput(TypedDict, total=False):
    """
    Output from a single agent execution with metadata.
    Prevents state key collisions when agents run in parallel.
    """
    agent_id: str
    agent_name: str
    output: Any  # The actual result
    metadata: AgentMetadata
    evaluation: Optional[Dict[str, Any]]
    validation_passed: bool


class AgentState(TypedDict, total=False):
    """
    Enhanced state schema supporting parallel agent execution.
    Tracks per-agent metadata to maintain observability and traceability.
    """
    # Core document data (immutable during workflow)
    raw_text: str
    user_request: str
    source_lang: str
    extraction: Optional[dict]
    trace_id: Optional[str]
    
    # Router decisions and execution control
    next_steps: Optional[List[str]]  # List of agent names to execute
    current_step_index: Optional[int]  # For sequential fallback
    pending_agents: List[str]  # Agents awaiting execution
    completed_agents: List[str]  # Successfully completed agents
    
    # Agent outputs (keyed by agent name for parallel safety)
    # These are kept for backward compatibility
    summary: Optional[str]
    translation: Optional[str]
    analysis: Optional[str]
    recommendation: Optional[str]
    ideation: Optional[str]
    copywriting: Optional[str]
    compliance: Optional[Dict[str, Any]]
    
    # NEW: Parallel execution tracking
    agent_outputs: Dict[str, AgentOutput]  # { "analyze": {...}, "summarize": {...} }
    agent_metadata: Dict[str, AgentMetadata]  # Per-agent execution metadata
    
    # Error and evaluation tracking
    errors: List[str]
    agent_errors: Dict[str, str]  # { "analyze": "error message", ... }
    evaluations: List[Dict[str, Any]]  # Global evaluations
    agent_evaluations: Dict[str, List[Dict[str, Any]]]  # Per-agent evaluations