from pydantic import BaseModel
from typing import List, Optional


# 数据模型
class Message(BaseModel):
    question: str
    session_id: Optional[str] = None
    stream: bool = True


class Session(BaseModel):
    name: str


class DeleteSessions(BaseModel):
    ids: List[str]
