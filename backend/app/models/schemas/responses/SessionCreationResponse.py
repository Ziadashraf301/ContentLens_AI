from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreationResponse(BaseModel):
    id: str
    created_at: datetime 
    updated_at: Optional[datetime] = None
