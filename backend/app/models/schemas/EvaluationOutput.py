from pydantic import BaseModel, Field

class EvaluationOutput(BaseModel):
    """Structured output schema for evaluation"""
    score: int = Field(ge=1, le=10, description="Quality score from 1-10")
    reasoning: str = Field(description="Brief explanation of the score")