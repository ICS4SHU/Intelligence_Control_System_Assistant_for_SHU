import uuid
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

from passlib.context import CryptContext
from .user import User
from .session import SessionCreate, AssistantSession, AgentSession
from .message import Message

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Database:
    def __init__(self, db_path: str = "chat.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            student_id TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            hashed_password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assistant_sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            session_type TEXT CHECK(session_type IN ('assistant', 'agent')),
            user_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            timestamp TEXT NOT NULL
        )
        """)
        self.conn.commit()

    # # User 相关操作
    # def get_user_by_credential(self, credential: str) -> Dict:
    #     cursor = self.conn.cursor()
    #     cursor.execute("""
    #         SELECT * FROM users
    #         WHERE username = ? OR student_id = ? OR email = ?
    #     """, (credential, credential, credential))
    #     user = cursor.fetchone()
    #     return dict(zip([col[0] for col in cursor.description], user)) if user else None

    def create_user(self, user_data: dict) -> str:
        cursor = self.conn.cursor()
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users
            (id, username, student_id, email, hashed_password, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data.get('username'),
            user_data.get('student_id'),
            user_data['email'],
            user_data['hashed_password'],
            datetime.now().isoformat()
        ))
        self.conn.commit()
        return user_id

    # Session 操作
    def create_assistant_session(self, session: SessionCreate) -> AssistantSession:
        cursor = self.conn.cursor()
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO assistant_sessions
            (id, name, user_id, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, session.name, session.user_id, now, now, True))
        self.conn.commit()
        return AssistantSession(
            id=session_id,
            name=session.name,
            user_id=session.user_id,
            created_at=now,
            updated_at=now,
            is_active=True
        )

    def create_agent_session(self, session: SessionCreate) -> AgentSession:
        cursor = self.conn.cursor()
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO agent_sessions
            (id, name, user_id, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, session.name, session.user_id, now, now, True))
        self.conn.commit()
        return AgentSession(
            id=session_id,
            name=session.name,
            user_id=session.user_id,
            created_at=now,
            updated_at=now,
            is_active=True
        )

    def get_sessions(self, session_type: str, user_id: str, active_only: bool = True) -> List[Dict]:
        cursor = self.conn.cursor()
        table_name = f"{session_type}_sessions"
        query = f"""
            SELECT id, name, created_at, updated_at, is_active
            FROM {table_name}
            WHERE user_id = ?
        """
        params = [user_id]

        if active_only:
            query += " AND is_active = ?"
            params.append(True)

        cursor.execute(query, params)
        return [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]

    # # Message 操作
    # def save_message(self, message: Message) -> None:
    #     cursor = self.conn.cursor()
    #     cursor.execute(
    #         """
    #     INSERT INTO messages
    #     (session_id, session_type, user_id, question, answer, timestamp)
    #     VALUES (?, ?, ?, ?, ?, ?)
    #     """,
    #         (
    #             message.session_id,
    #             message.session_type,
    #             message.user_id,
    #             message.question,
    #             message.answer,
    #             datetime.now().isoformat(),
    #         ),
    #     )
    #     self.conn.commit()

    def close(self):
        self.conn.close()