# app/utils/jwt_utils.py

from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.config import settings

ALGORITHM = "HS256"


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes if expires_minutes else settings.JWT_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}
