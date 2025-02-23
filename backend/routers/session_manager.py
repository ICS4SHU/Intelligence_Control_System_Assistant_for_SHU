# from datetime import datetime, timedelta
# import jwt
# from fastapi import HTTPException, status
# from ..models.db import Database, SECRET_KEY, ALGORITHM

# class SessionManager:
#     def __init__(self, ragflow_token: str):
#         self.ragflow_token = ragflow_token
#         self.db = Database()

#     def create_user_session(self, user_id: str, expires_delta: timedelta = None):
#         # 创建用户会话token
#         payload = {
#             "sub": user_id,
#             "ragflow_token": self.ragflow_token,
#             "exp": datetime.utcnow() + (expires_delta or timedelta(hours=1))
#         }
#         return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

#     def validate_user_session(self, token: str):
#         try:
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             # 验证RAGFlow token是否匹配
#             if payload["ragflow_token"] != self.ragflow_token:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="Invalid session token"
#                 )
#             return payload["sub"]  # 返回用户ID
#         except jwt.PyJWTError:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Could not validate credentials"
#             )

#     def get_user_context(self, user_id: str):
#         # 获取用户特定的上下文信息
#         cursor = self.db.conn.cursor()
#         cursor.execute("SELECT * FROM user_context WHERE user_id=?", (user_id,))
#         return cursor.fetchone()

#     def close(self):
#         self.db.close()