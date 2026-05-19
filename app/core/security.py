from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Use PBKDF2-SHA256 to avoid bcrypt backend issues and length limits.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def verify_password(plain_password: str, salt: str, hashed_password: str) -> bool:
    return pwd_context.verify(f"{salt}:{plain_password}", hashed_password)


def hash_password(password: str, salt: str) -> str:
    return pwd_context.hash(f"{salt}:{password}")


def generate_salt(length: int = 16) -> str:
    return secrets.token_hex(length)
