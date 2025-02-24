from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..dependencies import verify_api_key, forward_request
from .agent_sessions import create_agent_session
from ..models.db import Database
from ..models.user import User
from ..models.session import SessionCreate

router = APIRouter()

@router.post("/agent_sessions", 
             summary="Create a new agent session for a user",
             description="Creates a new agent session associated with the given user ID",
             response_description="The created session details")
async def create_user_session(
    session_data: SessionCreate,
    user_id: str,
):
    """
    Create a new agent session for a specific user.

    Args:
        session_data (SessionCreate): The session creation data including chat_id and other metadata
        user_id (str): The ID of the user creating the session

    Returns:
        dict: The created session details
    """
    response = await create_agent_session(session_data, user_id)

    return response

@router.get("/sessions",
            summary="Get user sessions",
            description="Retrieves a list of session IDs for a user, filtered by chat or agent ID",
            response_description="List of session IDs")
async def get_user_sessions(
    user_id: str,
    chat_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List:
    """
    Retrieve user sessions with pagination and sorting support.

    Args:
        user_id (str): The ID of the user
        chat_id (Optional[str]): Filter by chat ID
        agent_id (Optional[str]): Filter by agent ID
        page (int): Page number for pagination
        page_size (int): Number of items per page
        orderby (str): Field to order by (default: update_time)
        desc (bool): Sort in descending order (default: True)

    Returns:
        List: List of session IDs with pagination metadata
    """
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
