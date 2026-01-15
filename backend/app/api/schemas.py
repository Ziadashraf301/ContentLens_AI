from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AnalysisResponse(BaseModel):
    """
    The final object returned to the frontend.
    It contains the outputs from all agents that were triggered.
    """
    raw_text: Optional[str] = None
    source_lang: Optional[str] = "en"
    
    # Agent Outputs
    extraction: Optional[Dict[str, Any]] = Field(
        None, description="Structured data: title, summary, key points"
    )
    summary: Optional[str] = Field(
        None, description="Executive summary of the brief"
    )
    translation: Optional[str] = Field(
        None, description="Arabic translation if requested"
    )
    analysis: Optional[str] = Field(
        None, description="Strategic analysis or recommendations"
    )
    recommendation: Optional[str] = Field(
        None, description="Recommendations based on the analysis"
    )
    ideation: Optional[str] = Field(
        None, description="Creative campaign ideas"
    )
    copy: Optional[str] = Field(
        None, description="Copywriting output"
    )
    compliance: Optional[Dict[str, Any]] = Field(
        None, description="Compliance check results"
    )
    
    # Metadata
    next_steps: Optional[List[str]] = []
    current_step_index: Optional[int] = 0
    errors: List[str] = []
    trace_id: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    code: int

class ScoreRequest(BaseModel):
    trace_id: str
    agent_name: str
    score: float
    comment: Optional[str] = None
