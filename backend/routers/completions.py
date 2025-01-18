import os
import json
import aiohttp
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends
from ..models import Message, Database
from ..dependencies import verify_api_key


router = APIRouter()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")


@router.post("/completions")
async def create_completion(
    chat_id: str, message: Message, api_key: str = Depends(verify_api_key)
):
    db = Database()
    try:
        db.save_message(message)

        url = f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
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
