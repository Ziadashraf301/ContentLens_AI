from pydantic import BaseModel
from typing import Optional

class ScoreRequest(BaseModel):
    trace_id: str
    agent_name: str
    score: float
    comment: Optional[str] = None
