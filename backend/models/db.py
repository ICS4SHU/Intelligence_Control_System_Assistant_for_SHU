import uuid
import sqlite3

from typing import List, Optional, Dict, Any
from datetime import datetime
from passlib.context import CryptContext

from .user_model import User
from .session_model import Session, SessionCreate, SessionUpdate
from .message_model import Message


# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            hashed_password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        # 创建会话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            user_id TEXT NOT NULL,  -- 添加user_id字段
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

    def create_session(self, session: SessionCreate) -> Session:
        cursor = self.conn.cursor()
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO sessions (id, name, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, session.name, session.user_id, now, now, True))
        self.conn.commit()
        return Session(
            id=session_id, 
            name=session.name, 
            user_id=session.user_id, 
            created_at=now, 
            updated_at=now,
            is_active=True
        )
    def update_session(self, session_id: str, user_id: str, update_data: SessionUpdate) -> Optional[Session]:
        cursor = self.conn.cursor()
        updates = []
        params = []
        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)
        if update_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(update_data.is_active)
        
        if not updates:
            return None
            
        params.extend([session_id, user_id])
        cursor.execute(f"""
            UPDATE sessions 
            SET {', '.join(updates)}, updated_at = ?
            WHERE id = ? AND user_id = ?
            RETURNING id, name, user_id, created_at, updated_at, is_active
        """, (*params, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        if result:
            return Session(
                id=result[0],
                name=result[1],
                user_id=result[2],
                created_at=result[3],
                updated_at=result[4],
                is_active=result[5]
            )
        return None

    def archive_session(self, session_id: str, user_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions 
            SET is_active = FALSE, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (datetime.now().isoformat(), session_id, user_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def save_session(self, session: Session) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions
            (id, name, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session.id,
            session.name,
            session.user_id,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
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
    
    
    def get_sessions(
        self,
        user_id: str,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 30
    ) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
            SELECT id, name, created_at, updated_at, is_active 
            FROM sessions 
            WHERE user_id = ?
        """
        params = [user_id]
        
        if active_only:
            query += " AND is_active = ?"
            params.append(True)
            
        query += """
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, (page-1)*page_size])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_details(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at, updated_at, is_active
            FROM sessions
            WHERE id = ? AND user_id = ?
        """, (session_id, user_id))
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None
    
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

    def delete_sessions(self, session_ids: List[str], user_id: str) -> None:
        cursor = self.conn.cursor()
        
        # 先验证这些会话是否属于该用户
        cursor.execute(f"""
            SELECT id FROM sessions 
            WHERE id IN ({','.join('?'*len(session_ids))}) 
            AND user_id = ?
        """, (*session_ids, user_id))
        
        valid_ids = [row[0] for row in cursor.fetchall()]
        if len(valid_ids) != len(session_ids):
            raise ValueError("Some sessions do not belong to the user")
        
        cursor.execute(f"""
            DELETE FROM sessions 
            WHERE id IN ({','.join('?'*len(valid_ids))})
        """, valid_ids)
        
        cursor.execute(f"""
            DELETE FROM messages 
            WHERE session_id IN ({','.join('?'*len(valid_ids))})
        """, valid_ids)
        
        self.conn.commit()

    def close(self):
        
        self.conn.close()
