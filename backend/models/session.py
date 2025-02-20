from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime




class SessionCreate(BaseModel):
    name: str
    user_id: str
    
class SessionUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class DeleteSessions(BaseModel):
    ids: List[str]
    
class Session(BaseModel):
    id: str
    name: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
