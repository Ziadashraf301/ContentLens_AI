from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    This is the 'Memory' It tracks the document text and what each agent has produced.
    """
    raw_text: str
    user_request: str
    source_lang: str           
    extraction: Optional[dict]
    summary: Optional[str]
    translation: Optional[str]
    analysis: Optional[str]
    recommendation: Optional[str]
    next_steps: Optional[List[str]]
    current_step_index: Optional[int]
    source_lang: Optional[str]
    errors: List[str]