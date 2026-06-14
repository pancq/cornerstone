from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 登录失败记录（内存存储，生产环境建议用Redis）
login_failures = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_jti() -> str:
    """生成唯一的JWT ID"""
    return str(uuid.uuid4())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """创建refresh token，有效期7天"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

def is_account_locked(username: str) -> bool:
    """检查账号是否被锁定"""
    failure_info = login_failures.get(username)
    if not failure_info:
        return False
    
    attempts, lock_time = failure_info
    if attempts >= 5:
        # 检查锁定是否已过期（15分钟）
        if datetime.now(timezone.utc) < lock_time + timedelta(minutes=15):
            return True
        else:
            # 锁定过期，重置失败计数
            del login_failures[username]
            return False
    return False

def record_login_failure(username: str):
    """记录登录失败"""
    failure_info = login_failures.get(username, (0, None))
    attempts, _ = failure_info
    new_attempts = attempts + 1
    
    if new_attempts >= 5:
        login_failures[username] = (new_attempts, datetime.now(timezone.utc))
    else:
        login_failures[username] = (new_attempts, None)

def reset_login_failures(username: str):
    """重置登录失败计数"""
    if username in login_failures:
        del login_failures[username]

def validate_password(password: str) -> bool:
    """验证密码强度：至少8位，包含字母和数字"""
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit
