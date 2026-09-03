from fastapi import (
    Depends,
    HTTPException,
    status
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.session_repository import (
    SessionRepository
)
from app.repositories.user_repository import (
    UserRepository
)
from app.security.jwt import decode_token


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    user_id = payload.get("sub")
    session_uuid = payload.get(
        "session_id"
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    user = UserRepository.get_by_id(
        db,
        int(user_id)
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Usuario no autorizado"
        )

    session = (
        SessionRepository.get_by_uuid(
            db,
            session_uuid
        )
    )

    if not session or not session.is_active:
        raise HTTPException(
            status_code=401,
            detail="Sesión expirada o revocada"
        )

    SessionRepository.update_activity(
        db,
        session
    )

    return user