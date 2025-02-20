import pytest
from fastapi.testclient import TestClient
from sqlite3 import IntegrityError

from ..main import app  # 假设您的FastAPI应用在main.py中
from ..models.db import Database

client = TestClient(app)

@pytest.fixture(scope="function")  # 改为function级别
def test_db():
    # 每次测试都创建全新的内存数据库
    db = Database(":memory:")
    # 初始化数据库表
    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            email TEXT UNIQUE COLLATE NOCASE,
            hashed_password TEXT,
            created_at DATETIME
        )
    """)
    yield db
    db.close()  # 关闭连接，内存数据库会自动销毁
    
def test_user_registration_success(test_db):
    # 确保数据库为空
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 0

    # 使用唯一测试数据
    user_data = {
        "username": "testuser_" + str(hash("test_user_registration_success")),
        "email": "test+" + str(hash("test_user_registration_success")) + "@example.com",
        "password": "securepassword123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    print("Response status:", response.status_code)
    print("Response body:", response.json())
    assert response.status_code == 200

def test_user_registration_case_sensitive_email(test_db):
    # 确保数据库为空
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 0

    # 使用唯一测试数据
    base_email = "test+" + str(hash("test_user_registration_case_sensitive_email")) + "@example.com"
    
    user_data1 = {
        "username": "testuser7",
        "email": base_email.lower(),
        "password": "securepassword123"
    }
    user_data2 = {
        "username": "testuser8",
        "email": base_email.upper(),
        "password": "securepassword123"
    }

    # 注册第一个用户
    response1 = client.post("/api/v1/auth/register", json=user_data1)
    print("First registration response:", response1.status_code, response1.json())
    assert response1.status_code == 200

    # 尝试注册第二个用户
    response2 = client.post("/api/v1/auth/register", json=user_data2)
    print("Second registration response:", response2.status_code, response2.json())
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]
    
def test_user_registration_duplicate_email(test_db):
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 0
    
    # 测试数据
    user_data = {
        "username": "testuser2",
        "email": "test@example.com",  # 使用已存在的邮箱
        "password": "securepassword123"
    }

    # 发送注册请求
    response = client.post("/api/v1/auth/register", json=user_data)

    # 验证响应
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Email already registered" in response.json()["detail"]

def test_user_registration_invalid_data():
    invalid_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"  # 密码太短
    }

    response = client.post("/api/v1/auth/register", json=invalid_data)
    print("Invalid data response:", response.json())
    assert response.status_code == 422
    assert "detail" in response.json()
    assert any("Password must be at least" in err["msg"] for err in response.json()["detail"])

def test_user_registration_missing_fields():
    invalid_data = {
        "email": "test@example.com"
        # 缺少username和password
    }

    response = client.post("/api/v1/auth/register", json=invalid_data)
    print("Missing fields response:", response.json())
    assert response.status_code == 422
    assert "detail" in response.json()
    assert any("Field required" in err["msg"] for err in response.json()["detail"])
    