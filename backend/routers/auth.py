import uuid

from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime


from ..models.user import User, UserCreate, UserLogin
from ..models.db import Database, pwd_context

router = APIRouter()

# 密码验证与哈希
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

# 新增响应模型
class LoginResponse(BaseModel):
    user_id: str

# 注册接口（保持不变）
@router.post("/register", response_model=User)
async def register(user: UserCreate):
    db = Database()
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        if user.username:
            cursor.execute("SELECT * FROM users WHERE username=?", (user.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")

        if user.student_id:
            cursor.execute("SELECT * FROM users WHERE student_id=?", (user.student_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Student ID already exists")

        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user.password)
        created_at = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO users (id, username, student_id, email, hashed_password, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, user.username, user.student_id, user.email, hashed_password, created_at)
        )
        db.conn.commit()
        return User(id=user_id, **user.model_dump(), hashed_password=hashed_password, created_at=created_at)
    finally:
        db.close()

# 修改后的登录接口
@router.post("/login", response_model=LoginResponse)
async def login(form_data: UserLogin):
    db = Database()
    try:
        cursor = db.conn.cursor()
        # 通过username或student_id查找用户
        cursor.execute("""
            SELECT * FROM users
            WHERE username=? OR student_id=?
        """, (form_data.login_id, form_data.login_id))
        user = cursor.fetchone()

        if not user or not verify_password(form_data.password, user[4]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        user_id = user[0]

        # 查询助理会话ID
        cursor.execute("SELECT id FROM assistant_sessions WHERE user_id=?", (user_id,))
        assistant_sessions = cursor.fetchall()
        assistantsession_ids = [session[0] for session in assistant_sessions]

        # 查询代理会话ID
        cursor.execute("SELECT id FROM agent_sessions WHERE user_id=?", (user_id,))
        agent_sessions = cursor.fetchall()
        agentsession_ids = [session[0] for session in agent_sessions]

        return LoginResponse(
            user_id=user_id,
            assistantsession_ids=assistantsession_ids,
            agentsession_ids=agentsession_ids
        )
    finally:
        db.close()