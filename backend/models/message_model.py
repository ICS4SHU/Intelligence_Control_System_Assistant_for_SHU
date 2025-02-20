from typing import Optional
from pydantic import BaseModel

class Message(BaseModel):
    question: str
    answer: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # 新增 user_id 字段
    stream: bool = True