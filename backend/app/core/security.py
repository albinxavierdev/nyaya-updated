from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Union, Any
from app.core.config import settings
from jose import jwt
import warnings

# Suppress bcrypt version warning
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, settings.ALGORITHM)
    return encoded_jwt


def get_password(password: str) -> str:
    # Truncate password to 72 bytes if needed (bcrypt limitation)
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return password_context.hash(password)
    except Exception as e:
        # If there's still an error about password length, truncate and retry
        if "72 bytes" in str(e):
            password_bytes = password.encode('utf-8')[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
            return password_context.hash(password)
        raise


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)