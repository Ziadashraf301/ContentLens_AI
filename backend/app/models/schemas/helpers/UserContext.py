from pydantic import BaseModel

class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    role: str
