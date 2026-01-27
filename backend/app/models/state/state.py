from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    """
    This is the 'Memory' It tracks the document text and what each agent has produced.
    """
    raw_text: str
    extracted_text: str                          # Clean extracted text for agents
    user_request: str
    source_lang: str           
    extraction: Optional[dict]
    summary: Optional[str]
    translation: Optional[str]
    analysis: Optional[str]
    recommendation: Optional[str]
    ideation: Optional[str]
    copywriting: Optional[str]
    compliance: Optional[Dict[str, Any]]
    next_steps: Optional[List[str]]
    current_step_index: Optional[int]
    parallel_batches: Optional[List[List[str]]]  # Grouped batches for parallel execution
    current_batch_index: Optional[int]           # Track which batch is being processed
    trace_id: Optional[str]
    errors: List[str]
    evaluations: List[Dict[str, Any]]
    # Dynamic agent outputs (added during execution)
    summarize_output: Optional[Dict[str, Any]]
    translate_output: Optional[Dict[str, Any]]
    analyze_output: Optional[Dict[str, Any]]
    recommend_output: Optional[Dict[str, Any]]
    ideate_output: Optional[Dict[str, Any]]
    copywrite_output: Optional[Dict[str, Any]]
    compliance_output: Optional[Dict[str, Any]]