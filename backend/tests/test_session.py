import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..models.db import Database
from ..config import API_KEY, CHAT_ID

client = TestClient(app)

def login_user(login_id: str, password: str):
    login_data = {
        "login_id": login_id,
        "password": password
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    print("Login response:", response.status_code, response.json())
    assert response.status_code == 200
    return response.json()["user_id"]

@pytest.fixture(scope="function")
def test_db():
    db = Database(":memory:")

    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            email TEXT UNIQUE,
            hashed_password TEXT,
            created_at DATETIME
        )
    """)
    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            user_id TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            is_active BOOLEAN,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    yield db
    db.close()

def test_create_session_for_different_users(test_db):
    # 确保数据库为空
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 0

    # 创建两个测试用户
    user1 = {
        "username": "user1" + str(hash("test_create_session_for_different_users")),
        "email": "user1" + str(hash("test_create_session_for_different_users")) + "@example.com",
        "password": "password123"
    }
    user2 = {
        "username": "user2" + str(hash("test_create_session_for_different_users")),
        "email": "user2" + str(hash("test_create_session_for_different_users")) + "@example.com",
        "password": "password123"
    }

    # 注册用户
    response1 = client.post("/api/v1/auth/register", json=user1)
    response2 = client.post("/api/v1/auth/register", json=user2)

    assert response1.status_code == 200
    assert response2.status_code == 200
    print("response: ", response1.json())
    # 用户登录获取token
    user1_id = login_user(user1["username"], user1["password"])
    print("user1_id: ", user1_id)
    user2_id = login_user(user2["username"], user2["password"])

    # 为每个用户创建会话
    session_data1 = {"name": "Test Session", "user_id": user1_id}
    session_data2 = {"name": "Test Session", "user_id": user2_id}
    headers1 = {"Authorization": f"Bearer {API_KEY}"}
    headers2 = {"Authorization": f"Bearer {API_KEY}"}

    # breakpoint()

    # 用户1创建会话
    response1 = client.post("/api/v1/chats/{chat_id}/sessions", json=session_data1, headers=headers1)

    assert response1.status_code == 200
    session_id1 = response1.json()
    print("session_id1: ", session_id1)

    # 用户2创建会话
    response2 = client.post("/api/v1/chats/{chat_id}/sessions", json=session_data2, headers=headers2)
    assert response2.status_code == 200
    session_id2 = response2.json()

    # 验证会话隔离
    # 用户1只能看到自己的会话
    user1_json = {
        "user_id": user1["username"],
        "chat_id": CHAT_ID
    }
    # routers.user_sessions.get_user_sessions
    # @params user_id: str, chat_id: Optional[str] = None, agent_id: Optional[str] = None
    # @return Session_ids: List
    response = client.get(f"/api/v1/users/{user1_id}/sessions", params=user1_json)
    print("Get user session_ids response: ", response.json())
    assert response.status_code == 200
    user_sessions = response.json()[0]
    assert len(user_sessions) == 1
    print("session_id1 data id: ", session_id1["data"]["id"])
    # get_user_sessions return session_ids
    assert sessions[0] == session_id1["data"]["id"]

    # 用户2只能看到自己的会话
    user2_json = {
        "user_id": user2["username"],
        "chat_id": CHAT_ID
    }
    response = client.get(f"/api/v1/users/{user2_id}/sessions", params=user2_json)
    assert response.status_code == 200
    sessions = response.json()[0]
    assert len(sessions) == 1
    assert sessions[0] == session_id2["data"]["id"]

# def test_cannot_access_other_users_sessions(test_db):
#     # 确保数据库为空
#     cursor = test_db.conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM users")
#     assert cursor.fetchone()[0] == 0

#     # 创建两个测试用户
#     # 创建两个测试用户
#     user1 = {
#         "username": "user1_" + str(hash("test_cannot_access_other_users_sessions")),
#         "email": "user1" + str(hash("test_cannot_access_other_users_sessions")) + "@example.com",
#         "password": "password123"
#     }
#     user2 = {
#         "username": "user2_" + str(hash("test_cannot_access_other_users_sessions")),
#         "email": "user2" + str(hash("test_cannot_access_other_users_sessions")) + "@example.com",
#         "password": "password123"
#     }

#     # 注册用户
#     response1 = client.post("/api/v1/auth/register", json=user1)
#     response2 = client.post("/api/v1/auth/register", json=user2)
#     assert response1.status_code == 200
#     assert response2.status_code == 200

#     # 获取用户token
#     token1 = login_user(user1["username"], user1["password"])
#     token2 = login_user(user2["username"], user2["password"])

#     # 用户1创建会话
#     session_data = {"name": "Test Session"}
#     headers1 = {"Authorization": f"Bearer {token1}"}
#     response1 = client.post("/api/v1/sessions", json=session_data, headers=headers1)
#     assert response1.status_code == 200
#     session_id1 = response1.json()["id"]

#     # 用户2尝试访问用户1的会话
#     headers2 = {"Authorization": f"Bearer {token2}"}
#     response = client.get(f"/api/v1/sessions/{session_id1}", headers=headers2)
#     assert response.status_code == 404

# def test_session_archiving(test_db):
#     # 确保数据库为空
#     cursor = test_db.conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM users")
#     assert cursor.fetchone()[0] == 0

#     # 创建测试用户
#     user = {
#         "username": "string",
#         "email": "string",
#         "password": "string"
#     }
#     response = client.post("/api/v1/auth/register", json=user)
#     print(response)
#     assert response.status_code == 200
#     token = login_user(user["username"], user["password"])
#     headers = {"Authorization": f"Bearer {token}"}

#     # 创建会话
#     session_data = {"name": "Test Session"}
#     response = client.post("/api/v1/sessions", json=session_data, headers=headers)
#     assert response.status_code == 200
#     session_id = response.json()["id"]

#     # 归档会话
#     response = client.post(f"/api/v1/sessions/{session_id}/archive", headers=headers)
#     assert response.status_code == 200

#     # 验证会话状态
#     response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
#     assert response.status_code == 200
#     assert response.json()["is_active"] is False

#     # 尝试在归档会话中添加消息
#     message_data = {"content": "Test message"}
#     response = client.post(
#         f"/api/v1/sessions/{session_id}/messages",
#         json=message_data,
#         headers=headers
#     )
#     assert response.status_code == 400