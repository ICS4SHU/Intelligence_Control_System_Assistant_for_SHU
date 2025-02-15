import os
import json
import aiohttp

from starlette.config import Config
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException
from models import Message, Database
from dependencies import verify_api_key, get_current_user_from_token  # 引入get_current_user_from_token

router = APIRouter()


@router.post("/completions")
async def create_completion(
    chat_id: str, message: Message,
    user: dict = Depends(get_current_user_from_token)  # 获取当前用户信息
):
    db = Database()
    try:
        # 获取当前用户信息
        current_user = user

        # 在保存消息时将消息与当前用户绑定
        message.user_id = current_user.id  # 假设Message模型有user_id字段来保存消息的所属用户
        db.save_message(message)

        url = f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async def stream_response():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, headers=headers, json=message.dict()
                    ) as response:
                        if response.status != 200:
                            error_data = await response.json()
                            yield f"data: {json.dumps(error_data)}\n\n".encode("utf-8")
                            return

                        async for line in response.content:
                            if line:
                                yield f"data: {line.decode('utf-8')}\n\n".encode(
                                    "utf-8"
                                )
            except Exception as e:
                error_response = {
                    "code": 500,
                    "message": f"Error during streaming: {str(e)}",
                }
                yield f"data: {json.dumps(error_response)}\n\n".encode("utf-8")

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    finally:
        db.close()
