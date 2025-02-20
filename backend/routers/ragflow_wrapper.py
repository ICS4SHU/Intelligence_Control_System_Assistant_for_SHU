from fastapi import HTTPException, status
from datetime import datetime, timedelta
import jwt
from ..models.db import Database, SECRET_KEY, ALGORITHM

class RAGFlowWrapper:
    def __init__(self, ragflow_token: str):
        self.ragflow_token = ragflow_token
        self.db = Database()

    def create_user_session(self, user_id: str, expires_delta: timedelta = None):
        # 创建用户会话token
        payload = {
            "sub": user_id,
            "ragflow_token": self.ragflow_token,
            "exp": datetime.utcnow() + (expires_delta or timedelta(hours=1))
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def validate_user_session(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # 验证RAGFlow token是否匹配
            if payload["ragflow_token"] != self.ragflow_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session token"
                )
            return payload["sub"]  # 返回用户ID
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    async def chat(self, user_token: str, message: str):
        # 验证用户会话
        user_id = self.validate_user_session(user_token)
        
        # 获取用户上下文
        user_context = self.get_user_context(user_id)
        
        # 构造RAGFlow请求
        ragflow_request = {
            "message": message,
            "context": user_context,
            "token": self.ragflow_token
        }
        
        # 调用RAGFlow API
        response = await self._call_ragflow_api(ragflow_request)
        
        # 更新用户上下文
        self._update_user_context(user_id, response.get("new_context"))
        
        return response

    async def _call_ragflow_api(self, request: dict):
        # 这里实现实际的RAGFlow API调用
        # 示例：
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.ragflow.com/chat",
        #         json=request,
        #         headers={"Authorization": f"Bearer {self.ragflow_token}"}
        #     )
        # return response.json()
        pass

    def _update_user_context(self, user_id: str, new_context: dict):
        # 更新用户上下文到数据库
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_context (user_id, context, updated_at)
            VALUES (?, ?, ?)
        """, (user_id, str(new_context), datetime.now().isoformat()))
        self.db.conn.commit()

    def close(self):
        self.db.close()