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
CHAT_ID = "f6a7e88ee62b11efab0e0242ac120003"

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
    user_id: Optional[str] = None

class Session(BaseModel):
    name: str
    user_id: Optional[str] = None

class DeleteSessions(BaseModel):
    ids: List[str]

class User(BaseModel):
    user_id: str
    name: Optional[str] = None

async def forward_request(method: str, endpoint: str, headers: dict = None, json_data: dict = None, params: dict = None) -> Dict:
    url = f"{API_BASE_URL}{endpoint}"
    if headers is None:
        headers = {}
    headers["Authorization"] = f"Bearer {API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=json_data, params=params) as response:
            return await response.json()

async def test_create_session(session_name: str, user_id: str):
    """测试创建会话"""
    try:
        response = await forward_request(
            "POST",
            f"/api/v1/chats/{CHAT_ID}/sessions",
            json_data={"name": session_name, "user_id": user_id}
        )
        print("\n创建会话结果:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response.get("data", {}).get("id")
    except Exception as e:
        print(f"创建会话错误: {str(e)}")
        return None

async def test_send_message(session_id: str, question: str, user_id: str):
    """测试发送消息"""
    url = f"{API_BASE_URL}/api/v1/chats/{CHAT_ID}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    message_data = {
        "question": question,
        "session_id": session_id,
        "stream": True,
        "user_id": user_id
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

async def test_get_sessions(user_id: Optional[str] = None):
    """测试获取会话列表"""
    try:
        params = {
            "page": 1,
            "page_size": 30,
            "orderby": "create_time",
            "desc": "true"
        }
        if user_id:
            params["user_id"] = user_id
            
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
    current_user_id = None
    
    while True:
        print("\n=== 对话系统测试菜单 ===")
        if current_user_id:
            print(f"当前用户ID: {current_user_id}")
        print("1. 设置用户ID")
        print("2. 创建新会话")
        print("3. 发送消息")
        print("4. 查看会话列表")
        print("5. 删除会话")
        print("6. 退出")
        
        choice = input("\n请选择操作 (1-6): ")
        
        if choice == "1":
            current_user_id = input("请输入用户ID: ")
            print(f"已设置当前用户ID为: {current_user_id}")
            
        elif choice == "2":
            if not current_user_id:
                print("请先设置用户ID")
                continue
            session_name = input("请输入会话名称: ")
            session_id = await test_create_session(session_name, current_user_id)
            if session_id:
                print(f"会话ID: {session_id}")
        
        elif choice == "3":
            if not current_user_id:
                print("请先设置用户ID")
                continue
            session_id = input("请输入会话ID: ")
            question = input("请输入问题: ")
            await test_send_message(session_id, question, current_user_id)
        
        elif choice == "4":
            view_option = input("查看选项 (1: 所有会话, 2: 当前用户会话): ")
            user_id_filter = current_user_id if view_option == "2" else None
            await test_get_sessions(user_id_filter)
        
        elif choice == "5":
            session_ids = input("请输入要删除的会话ID (多个ID用逗号分隔): ").split(",")
            session_ids = [sid.strip() for sid in session_ids]
            await test_delete_sessions(session_ids)
        
        elif choice == "6":
            print("退出测试程序")
            break
        
        else:
            print("无效的选择，请重试")

if __name__ == "__main__":
    asyncio.run(main())