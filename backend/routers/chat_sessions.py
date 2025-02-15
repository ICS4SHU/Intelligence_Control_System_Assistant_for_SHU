from fastapi import APIRouter, Depends, HTTPException
from models import Session, DeleteSessions, Database
from dependencies import verify_api_key, forward_request, get_current_user_from_token
from auth import oauth2_scheme

router = APIRouter()

@router.post("/sessions")
async def create_session(
    chat_id: str, session: Session, user: dict = Depends(get_current_user_from_token)
):
    try:
        # 获取当前用户信息
        current_user = user

        # 将会话与用户ID关联
        db = Database()
        db.save_session(session, current_user.id)

        # 转发请求到外部服务
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"name": session.name},
            api_key=api_key,
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}
    finally:
        db.close()


@router.get("/sessions")
async def get_sessions(
    chat_id: str,
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    user: dict = Depends(get_current_user_from_token)  # 使用get_current_user_from_token
):
    # 获取当前用户信息
    current_user = user

    db = Database()
    try:
        # 根据用户ID查询属于该用户的会话
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at, updated_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY ? DESC
            LIMIT ? OFFSET ?
        """, (current_user.id, orderby, page_size, (page-1)*page_size))

        sessions = cursor.fetchall()
        return {"sessions": sessions}
    finally:
        db.close()


@router.delete("/sessions")
async def delete_sessions(
    chat_id: str, sessions: DeleteSessions, user: dict = Depends(get_current_user_from_token)
):
    try:
        # 获取当前用户信息
        current_user = user

        # 确保每个会话都属于当前用户
        db = Database()
        for session_id in sessions.ids:
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
        db.delete_sessions(sessions.ids)

        # 转发请求到外部服务
        response = await forward_request(
            "DELETE",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"ids": sessions.ids},
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}
    finally:
        db.close()
