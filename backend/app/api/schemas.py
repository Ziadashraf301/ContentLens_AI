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
    
    # Metadata
    next_step: str = "end"
    errors: List[str] = []

class ErrorResponse(BaseModel):
    detail: str
    code: int