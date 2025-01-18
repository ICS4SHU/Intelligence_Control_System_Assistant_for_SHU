import uvicorn
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat_sessions, completions
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

app.include_router(chat_sessions.router, prefix="/api/v1/chats/{chat_id}")
app.include_router(completions.router, prefix="/api/v1/chats/{chat_id}")

if __name__ == "__main__":
    # get current IP address
    uvicorn.run(app, host=socket.gethostbyname(socket.gethostname()), port=8000)
