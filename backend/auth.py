from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import User, UserCreate, UserLogin, Token, Database, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context
from datetime import datetime, timedelta
import uuid
import jwt
from jwt import PyJWTError

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 密码验证与哈希
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

# 创建 JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    db = Database()
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    db.close()

    if user is None:
        raise credentials_exception
    return User(**dict(user))

# 注册接口
@router.post("/register", response_model=User)
async def register(user: UserCreate):
    db = Database()
    try:
        # 检查唯一性
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

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    db = Database()
    try:
        # 通过username或student_id查找用户
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            WHERE username=? OR student_id=?
        """, (form_data.login_id, form_data.login_id))
        user = cursor.fetchone()

        # 确保查询到用户并且密码验证成功
        if not user or not verify_password(form_data.password, user[4]):  # user[4] 是 hashed_password
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[0]}, expires_delta=access_token_expires  # user[0] 是 user_id
        )
        return {"access_token": access_token, "token_type": "bearer", "user": user[0]}
    finally:
        db.close()
