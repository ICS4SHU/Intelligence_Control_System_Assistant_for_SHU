from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..models.db import Database
from ..models.session import SessionCreate, SessionUpdate
from ..dependencies import verify_api_key, forward_request, get_current_user_from_token
from .auth import oauth2_scheme
from ..config import CHAT_ID

router = APIRouter()

