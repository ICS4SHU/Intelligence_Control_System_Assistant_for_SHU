from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime
import json
import asyncio
import aiohttp
from fastapi.security import APIKeyHeader
from fastapi import Security

app = FastAPI(title="Learning Assistant API")

# API 配置
API_BASE_URL = "http://223.4.250.237"
API_KEY = "ragflow-E0ZmY5M2E4YmM1MjExZWY4ZWNlMDI0Mm"
CHAT_ID = "fe9beac2bc2311efb9e60242ac120006"

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key 验证
API_KEY_HEADER = APIKeyHeader(name="Authorization")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    key = api_key.split(" ")[1]
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key

# 数据模型
class Message(BaseModel):
    question: str
    session_id: Optional[str] = None
    stream: bool = True

class Session(BaseModel):
    name: str

class DeleteSessions(BaseModel):
    ids: List[str]

async def forward_request(method: str, endpoint: str, headers: dict = None, json_data: dict = None, params: dict = None) -> Dict:
    url = f"{API_BASE_URL}{endpoint}"
    if headers is None:
        headers = {}
    headers["Authorization"] = f"Bearer {API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=json_data, params=params) as response:
            return await response.json()

@app.post("/api/v1/chats/{chat_id}/sessions")
async def create_session(chat_id: str, session: Session, api_key: str = Depends(verify_api_key)):
    try:
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"name": session.name}
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}

@app.get("/api/v1/chats/{chat_id}/sessions")
async def get_sessions(
    chat_id: str,
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    api_key: str = Depends(verify_api_key)
):
    try:
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": str(desc).lower()
        }
        response = await forward_request(
            "GET",
            f"/api/v1/chats/{chat_id}/sessions",
            params=params
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}

@app.delete("/api/v1/chats/{chat_id}/sessions")
async def delete_sessions(chat_id: str, sessions: DeleteSessions, api_key: str = Depends(verify_api_key)):
    try:
        response = await forward_request(
            "DELETE",
            f"/api/v1/chats/{chat_id}/sessions",
            json_data={"ids": sessions.ids}
        )
        return response
    except Exception as e:
        return {"code": 500, "message": str(e)}

@app.post("/api/v1/chats/{chat_id}/completions")
async def create_completion(
    chat_id: str,
    message: Message,
    api_key: str = Depends(verify_api_key)
):
    url = f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async def stream_response():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=message.dict()) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        yield f"data: {json.dumps(error_data)}\n\n".encode('utf-8')
                        return
                    
                    async for line in response.content:
                        if line:
                            yield f"data: {line.decode('utf-8')}\n\n".encode('utf-8')
        except Exception as e:
            error_response = {
                "code": 500,
                "message": f"Error during streaming: {str(e)}"
            }
            yield f"data: {json.dumps(error_response)}\n\n".encode('utf-8')

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )
