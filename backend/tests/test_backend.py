from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import aiohttp
import json
import uvicorn
from fastapi.security import APIKeyHeader
from fastapi import Security
import sys

app = FastAPI(title="Learning Assistant API")

# API 配置
API_BASE_URL = "http://223.4.250.237"
API_KEY = "ragflow-E0ZmY5M2E4YmM1MjExZWY4ZWNlMDI0Mm"
CHAT_ID = "fe9beac2bc2311efb9e60242ac120006"

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

async def test_create_session(session_name: str):
    """测试创建会话"""
    try:
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            json_data={"name": session_name}
        )
        print("\n创建会话结果:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response.get("data", {}).get("id")
    except Exception as e:
        print(f"创建会话错误: {str(e)}")
        return None

async def test_send_message(session_id: str, question: str):
    """测试发送消息"""
    url = f"{API_BASE_URL}/api/v1/chats/{CHAT_ID}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    message_data = {
        "question": question,
        "session_id": session_id,
        "stream": True
    }
    
    try:
        print("\n发送消息中...")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=message_data) as response:
                if response.status != 200:
                    error_data = await response.json()
                    print(f"错误: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    return
                
                print("\n接收回复:")
                async for line in response.content:
                    if line:
                        response_text = line.decode('utf-8')
                        if response_text.startswith("data: "):
                            response_data = json.loads(response_text[6:])
                            if "message" in response_data:
                                print(response_data["message"], end="", flush=True)
                print("\n")
    except Exception as e:
        print(f"发送消息错误: {str(e)}")

async def test_get_sessions():
    """测试获取会话列表"""
    try:
        params = {
            "page": 1,
            "page_size": 30,
            "orderby": "create_time",
            "desc": "true"
        }
        response = await forward_request(
            "GET",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            params=params
        )
        print("\n会话列表:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response
    except Exception as e:
        print(f"获取会话列表错误: {str(e)}")
        return None

async def test_delete_sessions(session_ids: List[str]):
    """测试删除会话"""
    try:
        response = await forward_request(
            "DELETE",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            json_data={"ids": session_ids}
        )
        print("\n删除会话结果:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response
    except Exception as e:
        print(f"删除会话错误: {str(e)}")
        return None

async def main():
    while True:
        print("\n=== 对话系统测试菜单 ===")
        print("1. 创建新会话")
        print("2. 发送消息")
        print("3. 查看会话列表")
        print("4. 删除会话")
        print("5. 退出")
        
        choice = input("\n请选择操作 (1-5): ")
        
        if choice == "1":
            session_name = input("请输入会话名称: ")
            session_id = await test_create_session(session_name)
            if session_id:
                print(f"会话ID: {session_id}")
        
        elif choice == "2":
            session_id = input("请输入会话ID: ")
            question = input("请输入问题: ")
            await test_send_message(session_id, question)
        
        elif choice == "3":
            await test_get_sessions()
        
        elif choice == "4":
            session_ids = input("请输入要删除的会话ID (多个ID用逗号分隔): ").split(",")
            session_ids = [sid.strip() for sid in session_ids]
            await test_delete_sessions(session_ids)
        
        elif choice == "5":
            print("退出测试程序")
            break
        
        else:
            print("无效的选择，请重试")

if __name__ == "__main__":
    asyncio.run(main())
