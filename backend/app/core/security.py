from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.core.config import Settings

# Cambiando a Argon2 como default, manteniendo soporte verify para bcrypt si existieran legacy hashes
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, Settings.SECRET_KEY, algorithm=Settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Crea un refresh token de larga duración (7 días por defecto)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=Settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, Settings.SECRET_KEY, algorithm=Settings.ALGORITHM)
    return encoded_jwt

def decode_refresh_token(token: str) -> dict:
    """Decodifica y valida un refresh token. Retorna el payload o lanza excepción."""
    payload = jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])
    if payload.get("type") != "refresh":
        raise ValueError("Token no es de tipo refresh")
    return payload
