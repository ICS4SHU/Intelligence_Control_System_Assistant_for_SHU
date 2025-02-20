from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..models.db import Database
from ..models.session import SessionCreate, SessionUpdate
from ..dependencies import verify_api_key, forward_request, get_current_user_from_token
from .auth import oauth2_scheme
from ..config import AgentID

router = APIRouter()

@router.post("/sessions")
async def create_session(
    session_data: SessionCreate,
    api_key: str = Depends(verify_api_key),
):
    db = Database()
    try:
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{AgentID.HOMEWORK}/sessions",
            json_data={"name": session_data.name, "user_id": session_data.user_id},
            api_key=api_key,
        )
        return response
    finally:
        db.close()
        
@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    user: dict = Depends(get_current_user_from_token)
):
    db = Database()
    try:
        updated_session = db.update_session(session_id, user.id, update_data)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found or no changes made")
        return updated_session
    finally:
        db.close()