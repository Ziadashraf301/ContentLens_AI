from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class SessionResponse(BaseModel):
    id: str
    title: str
    messageCount: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    messageType: str
    text: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    timestamp: datetime
    status: str = "sent"
