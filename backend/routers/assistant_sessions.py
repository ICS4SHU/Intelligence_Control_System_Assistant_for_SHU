from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..models.db import Database
from ..models.session import SessionCreate, SessionUpdate
from ..dependencies import verify_api_key, forward_request
from ..config import CHAT_ID

router = APIRouter()

@router.post("/sessions")
async def create_chat_session(
    session_data: SessionCreate,
    api_key: str = Depends(verify_api_key),
):
    db = Database()
    try:
        cursor = db.conn.cursor()
        # cursor.execute("SELECT * FROM users WHERE id=?", (session_data.user_id,))
        # if not cursor.fetchone():
        #     raise HTTPException(status_code=400, detail="User not found")

        response = await forward_request(
            "POST",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            json_data={"name": session_data.name, "user_id": session_data.user_id},
        )
        user_id = session_data.user_id

        data = response.get("data")
        id = data['id']
        name = data['name']
        create_date = datetime.strptime(data['create_date'], '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y-%m-%d %H:%M:%S')
        update_date = datetime.strptime(data['update_date'], '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y-%m-%d %H:%M:%S')
        is_active = True  # 默认值

        sql = f"""
                INSERT INTO assistant_sessions (id, name, user_id, created_at, updated_at, is_active)
                VALUES (
                    '{id}',
                    '{name}',
                    '{user_id}',
                    '{create_date}',
                    '{update_date}',
                    {is_active}
                );"""

        cursor.execute(sql)
        db.conn.commit()

        response['data']['user_id'] = user_id

        return response
    finally:
        db.close()


@router.put("/sessions/{session_id}")
async def update_chat_session(
    session_id: str,
    update_data: SessionUpdate,
):
    db = Database()
    try:
        updated_session = db.update_session(session_id, update_data)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found or no changes made")
        return updated_session
    finally:
        db.close()

@router.post("/sessions/{session_id}/archive")
async def archive_chat_session(
    session_id: str,
):
    db = Database()
    try:
        if not db.archive_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success"}
    finally:
        db.close()

@router.get("/sessions")
async def get_chat_sessions(
    active_only: bool = True,
    page: int = 1,
    page_size: int = 30,
):
    db = Database()
    try:
        sessions = db.get_sessions(
            active_only=active_only,
            page=page,
            page_size=page_size
        )
        return {"sessions": sessions}
    finally:
        db.close()


@router.delete("/sessions")
async def delete_chat_sessions(
    session_ids: List[str],
):
    try:
        db = Database()
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
