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
    ideation: Optional[str]
    copy: Optional[str]
    compliance: Optional[Dict[str, Any]]
    next_steps: Optional[List[str]]
    current_step_index: Optional[int]
    errors: List[str]