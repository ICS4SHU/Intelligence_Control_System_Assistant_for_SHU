import sys
import uvicorn
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


sys.path.append(str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__" and __package__ is None:
    __package__ = "backend"

from .routers import agent_completions, assistant_completions, assistant_sessions, agent_sessions, auth, user_sessions
from .config import FRONTEND_ORIGIN


app = FastAPI(title="Learning Assistant API")

origins = [FRONTEND_ORIGIN]

print(f"FRONTEND_ORIGIN: {FRONTEND_ORIGIN}")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get User Sessions
app.include_router(user_sessions.router, prefix="/api/v1/users/{user_id}", tags=["User Sessions"])

# Create Sessions
## 因为有 Chat Assistant 和 Agent 两种智能助手，为求方便，做两个路由
app.include_router(agent_sessions.router, prefix="/api/v1/agents/{agent_id}", tags=["Agent Sessions"])
app.include_router(assistant_sessions.router, prefix="/api/v1/chats/{chat_id}", tags=["Assistant Sessions"])

# Completions
## 同上的理由
app.include_router(agent_completions.router, prefix="/api/v1/agents/{agent_id}", tags=["Agent Completions"])
app.include_router(assistant_completions.router, prefix="/api/v1/chats/{chat_id}", tags=["Chat Assistant Completions"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

if __name__ == "__main__":
    # get current IP address
    uvicorn.run(app, host="127.0.0.1", port=8000)