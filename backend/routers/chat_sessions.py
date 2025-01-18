from fastapi import APIRouter, Depends
from ..models import Session, DeleteSessions
from ..dependencies import verify_api_key, forward_request

router = APIRouter()


@router.post("/sessions")
async def create_session(
    chat_id: str, session: Session, api_key: str = Depends(verify_api_key)
):
    try:
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"name": session.name},
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}


@router.get("/sessions")
async def get_sessions(
    chat_id: str,
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    api_key: str = Depends(verify_api_key),
):
    try:
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": str(desc).lower(),
        }
        response = await forward_request(
            "GET", f"/api/v1/chats/{chat_id}/sessions", params=params
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}


@router.delete("/sessions")
async def delete_sessions(
    chat_id: str, sessions: DeleteSessions, api_key: str = Depends(verify_api_key)
):
    try:
        response = await forward_request(
            "DELETE",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"ids": sessions.ids},
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}
