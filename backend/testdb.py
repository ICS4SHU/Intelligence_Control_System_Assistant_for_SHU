from fastapi import APIRouter, Depends, HTTPException
from .models import Session, DeleteSessions, Database
from .dependencies import verify_api_key, forward_request, get_current_user_from_token
from .routers.auth import oauth2_scheme


# 创建数据库实例
db = Database("chat.db")

# 查看所有用户
users = db.get_all_users()
print("Users:", users)

# 查看所有会话
sessions = db.get_all_sessions()
print("Sessions:", sessions)

# 关闭数据库连接
db.close()
