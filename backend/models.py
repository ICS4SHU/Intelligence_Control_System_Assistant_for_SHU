import sqlite3
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# 数据模型
class Message(BaseModel):
    question: str
    answer: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = True


class Session(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime


class DeleteSessions(BaseModel):
    ids: List[str]


class Database:
    def __init__(self, db_path: str = "chat.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # 创建会话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        # 创建消息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
        """)
        self.conn.commit()

    def save_session(self, session: Session) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        INSERT OR REPLACE INTO sessions (id, name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
            (
                session.id,
                session.name,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
            ),
        )
        self.conn.commit()

    def save_message(self, message: Message) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        INSERT INTO messages (session_id, question, answer, timestamp)
        VALUES (?, ?, ?, ?)
        """,
            (
                message.session_id,
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
