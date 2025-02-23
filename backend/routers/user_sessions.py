from fastapi import APIRouter, Depends, HTTPException


from .agent_sessions import create_session
from ..models.user import User
from ..models.session import SessionCreate

router = APIRouter()

@router.post("/sessions")
async def create_user_session(
    session_data: SessionCreate,
    user_id: str = User.id,
):
    response = await create_session(session_data, user_id)
    
    return response

@router.get("/sessions")
async def get_user_sessions(
    user_id: str = User.id

):
    return