import hashlib
import uuid

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


def create_access_token(
    user_id: int,
    session_uuid: str
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "session_id": session_uuid,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def create_refresh_token(
    user_id: int,
    session_uuid: str
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)

    jti = str(uuid.uuid4())

    expires_at = now + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "session_id": session_uuid,
        "type": "refresh",
        "iat": now,
        "exp": expires_at,
        "jti": jti
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token, jti, expires_at


def decode_token(
    token: str
) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )


def hash_token(
    token: str
) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()