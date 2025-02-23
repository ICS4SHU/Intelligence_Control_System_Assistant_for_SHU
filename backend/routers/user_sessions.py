from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..dependencies import verify_api_key, forward_request
from .agent_sessions import create_agent_session
from ..models.db import Database
from ..models.user import User
from ..models.session import SessionCreate

router = APIRouter()

@router.post("/agent_sessions")
async def create_user_session(
    session_data: SessionCreate,
    user_id: str,
):
    response = await create_agent_session(session_data, user_id)

    return response

@router.get("/sessions")
async def get_user_sessions(
    user_id: str,
    chat_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List:
    db = Database()

    if chat_id is None and agent_id is None:
        raise HTTPException(status_code=400, detail="Chat ID or Agent ID is required")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        cursor = db.conn.cursor()

        if chat_id is not None:
            cursor.execute("SELECT id FROM assistant_sessions WHERE user_id=?", (user_id,))
        elif agent_id is not None:
            cursor.execute("SELECT id FROM agent_sessions WHERE user_id=?", (user_id,))

        sesssions_ids = cursor.fetchall()

        return sesssions_ids
    finally:
        db.close()
