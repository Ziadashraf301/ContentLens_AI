from typing import TypedDict, List, Optional, Dict, Any, Annotated
from operator import add

class AgentState(TypedDict):
    """
    This is the 'Memory' It tracks the document text and what each agent has produced. 
    The State with reducers for parallel execution
    """
    # Shared inputs
    raw_text: str
    user_request: str
    source_lang: str

    # Parallel outputs - each agent writes to its own field      
    extraction: Optional[dict]
    summary: Optional[str]
    translation: Optional[str]
    analysis: Optional[str]
    recommendation: Optional[str]
    ideation: Optional[str]
    copywriting: Optional[str]
    compliance: Optional[Dict[str, Any]]

    # Router metadata
    next_steps: Optional[List[str]]
    trace_id: Optional[str]

    errors: Annotated[List[str], add]  
    evaluations: Annotated[List[Dict[str, Any]], add]