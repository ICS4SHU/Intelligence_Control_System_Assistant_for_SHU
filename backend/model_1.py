import sqlite3
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from passlib.context import CryptContext

# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    id: str
    username: Optional[str] = None
    student_id: Optional[str] = None
    email: str
    hashed_password: str
    created_at: datetime

class UserCreate(BaseModel):
    username: Optional[str] = None
    student_id: Optional[str] = None
    email: str
    password: str

class UserLogin(BaseModel):
    login_id: str  # 可以是username或student_id
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# 数据模型
class Message(BaseModel):
    question: str
    answer: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # 新增 user_id 字段
    stream: bool = True


class Session(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    uid: str  # 新增 user_id 字段

class DeleteSessions(BaseModel):
    ids: List[str]


class Database:
    def __init__(self, db_path: str = "chat.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # 新增用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            student_id TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        # 创建会话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT ,
            created_at TEXT ,
            updated_at TEXT ,
            user_id TEXT ,  -- 添加user_id字段
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        # 创建消息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,  -- 新增 user_id 字段
            question TEXT NOT NULL,
            answer TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(user_id) REFERENCES users(id)  -- 外键约束
        )
        """)
        self.conn.commit()

    def save_session(self, session: Session, user_id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (id, name, created_at, updated_at, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session.id,
            session.name,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            user_id,
        ))
        self.conn.commit()

    def save_message(self, message: Message) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        INSERT INTO messages (session_id, user_id, question, answer, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
            (
                message.session_id,
                message.user_id,  # 保存 user_id
                message.question,
                message.answer,
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        SELECT question, answer, timestamp FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_users(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        
        # 获取列名
        columns = [description[0] for description in cursor.description]
        
        # 使用列名和行数据构造字典
        users = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return users
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions")
        return [dict(row) for row in cursor.fetchall()]

    def delete_sessions(self, session_ids: List[str]) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        DELETE FROM sessions WHERE id IN ({})
        """.format(",".join("?" * len(session_ids))),
            session_ids,
        )
        cursor.execute(
            """
        DELETE FROM messages WHERE session_id IN ({})
        """.format(",".join("?" * len(session_ids))),
            session_ids,
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
