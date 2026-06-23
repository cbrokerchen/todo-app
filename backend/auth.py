"""Authentication helpers: password hashing and JWT."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS
import models

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token URL is the login endpoint (for OAuth2 compatibility / docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str, expires_minutes: Optional[int] = None) -> str:
    """Create a JWT with subject=username and a 24h expiry by default."""
    if expires_minutes is None:
        expires_minutes = ACCESS_TOKEN_EXPIRE_HOURS * 60
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Decode JWT and return the subject (username). Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> str:
    """FastAPI dependency: extract the current username from the Authorization header."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = decode_token(token)
    user = models.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
