from fastapi import APIRouter, Depends, HTTPException
from models import Session, DeleteSessions, Database
from dependencies import verify_api_key, forward_request, get_current_user_from_token
from auth import oauth2_scheme

router = APIRouter()
@router.post("/sessions")
async def create_session(
    chat_id: str, session: Session, user: dict = Depends(get_current_user_from_token)  # 获取当前用户信息
):
    try:
        current_user = user  # 获取当前用户
        user_id = current_user.id  # 获取当前用户的uid

        db = Database()
        # 保存会话时，确保会话与当前用户绑定
        session.user_id = user_id
        db.save_session(session, user_id)

        # 转发请求到外部服务
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"name": session.name},
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
    user_id: str = Depends(get_current_user_from_token)  # 获取当前用户的uid
):
    db = Database()
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at, updated_at, user_id
            FROM sessions
            WHERE user_id = ?  -- 使用user_id进行过滤，确保只返回当前用户的会话
            ORDER BY ? DESC
            LIMIT ? OFFSET ?
        """, (user_id, orderby, page_size, (page-1)*page_size))

        sessions = cursor.fetchall()

        # 过滤掉不属于当前用户的会话
        filtered_sessions = [session for session in sessions if session['user_id'] == user_id]

        return {"sessions": filtered_sessions}
    finally:
        db.close()

@router.delete("/sessions")
async def delete_sessions(
    chat_id: str, sessions: DeleteSessions, user: dict = Depends(get_current_user_from_token)
):
    try:
        current_user = user  # 获取当前用户信息
        user_id = current_user.id  # 获取当前用户的uid

        db = Database()
        for session_id in sessions.ids:
            # 确保会话属于当前用户
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE id = ? AND user_id = ?
            """, (session_id, user_id))
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
