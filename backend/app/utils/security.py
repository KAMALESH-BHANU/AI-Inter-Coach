import bcrypt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from app.config import settings

def get_password_hash(password: str) -> str:
    # Truncate to 72 bytes max for bcrypt standard compliance
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    
    # 1. Try standard bcrypt check
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        if bcrypt.checkpw(pwd_bytes, hash_bytes):
            return True
    except Exception:
        pass

    # 2. Try SHA-256 hex check (for legacy/imported accounts)
    try:
        sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        if sha256_hash == hashed_password:
            return True
    except Exception:
        pass

    # 3. Plaintext fallback for test/legacy accounts
    if plain_password == hashed_password:
        return True

    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
