from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..models.db import Database
from ..models.session import SessionCreate, SessionUpdate
from ..dependencies import verify_api_key, forward_request, get_current_user_from_token
from .auth import oauth2_scheme
from ..config import CHAT_ID

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
            f"/api/v1/chats/{CHAT_ID}/sessions",
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

@router.post("/sessions/{session_id}/archive")
async def archive_session(
    session_id: str,
    user: dict = Depends(get_current_user_from_token)
):
    db = Database()
    try:
        if not db.archive_session(session_id, user.id):
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success"}
    finally:
        db.close()

@router.get("/sessions")
async def get_sessions(
    active_only: bool = True,
    page: int = 1,
    page_size: int = 30,
    user: dict = Depends(get_current_user_from_token)
):
    db = Database()
    try:
        sessions = db.get_sessions(
            user_id=user.id,
            active_only=active_only,
            page=page,
            page_size=page_size
        )
        return {"sessions": sessions}
    finally:
        db.close()


@router.delete("/sessions")
async def delete_sessions(
    session_ids: List[str],
    user: dict = Depends(get_current_user_from_token)
):
    try:
        # 获取当前用户信息
        current_user = user

        # 确保每个会话都属于当前用户
        db = Database()
        for session_id in session_ids:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE id = ? AND user_id = ?
            """, (session_id, current_user.id))
            session = cursor.fetchone()
            if not session:
                raise HTTPException(
                    status_code=403,
                    detail=f"Session {session_id} does not belong to the current user"
                )

        # 删除会话
        db.delete_sessions(session_ids)

        # 转发请求到外部服务
        response = await forward_request(
            "DELETE",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            json_data={"ids": session_ids},
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}
    finally:
        db.close()
