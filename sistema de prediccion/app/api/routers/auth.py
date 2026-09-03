from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)

from app.repositories.session_repository import (
    SessionRepository,
)

from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    TokenResponse,
    UserResponse,
)

from app.security.dependencies import (
    get_current_user,
)

from app.security.jwt import (
    hash_token,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth_service import (
    AuthService,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


# ==========================================
# REGISTRO
# ==========================================

@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    body: RegisterRequest,
    db: Session = Depends(
        get_db
    ),
):

    user = (
        AuthService.register(
            db=db,
            email=body.email,
            password=body.password,
        )
    )

    user_id = (
        getattr(
            user,
            "id",
            None,
        )
    )

    if (
        user_id is None
        and isinstance(
            user,
            dict,
        )
    ):
        user_id = (
            user.get(
                "id"
            )
        )

    AuditService.log_safe(
        db=db,
        user_id=user_id,
        action="auth.register",
        entity="user",
        entity_id=user_id,
        details={
            "email": (
                body.email
            ),
        },
    )

    return user


# ==========================================
# LOGIN
# ==========================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(
        get_db
    ),
):

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    user_agent = (
        request.headers.get(
            "user-agent"
        )
    )

    result = (
        AuthService.login(
            db=db,
            email=body.email,
            password=body.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )

    # En este router no tenemos garantizado
    # el user_id dentro de TokenResponse.
    #
    # Por eso registramos el login exitoso
    # mediante email sin asumir una estructura
    # que AuthService no nos haya garantizado.
    AuditService.log_safe(
        db=db,
        user_id=None,
        action="auth.login",
        entity="authentication",
        entity_id=None,
        details={
            "email": (
                body.email
            ),
            "ip_address": (
                ip_address
            ),
            "user_agent": (
                user_agent
            ),
        },
    )

    return result


# ==========================================
# REFRESH TOKEN
# ==========================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    body: RefreshRequest,
    db: Session = Depends(
        get_db
    ),
):

    # No auditamos refresh.
    #
    # Es una operación técnica muy frecuente
    # y generaría ruido innecesario en
    # audit_logs.

    return (
        AuthService.refresh(
            db=db,
            raw_refresh_token=(
                body.refresh_token
            ),
        )
    )


# ==========================================
# LOGOUT
# ==========================================

@router.post(
    "/logout",
)
def logout(
    body: LogoutRequest,
    db: Session = Depends(
        get_db
    ),
):

    token_hash = (
        hash_token(
            body.refresh_token
        )
    )

    token = (
        RefreshTokenRepository
        .get_by_hash(
            db,
            token_hash,
        )
    )

    audit_user_id = None

    session_id = None

    if token:

        RefreshTokenRepository.revoke(
            db=db,
            token=token,
            reason="logout",
        )

        session = (
            SessionRepository
            .get_by_id(
                db,
                token.session_id,
            )
        )

        if session:

            session_id = (
                session.id
            )

            audit_user_id = (
                session.user_id
            )

            (
                RefreshTokenRepository
                .revoke_all_by_session(
                    db=db,
                    session_id=session.id,
                    reason="logout",
                )
            )

            SessionRepository.revoke(
                db=db,
                session=session,
                reason="logout",
            )

            AuditService.log_safe(
                db=db,
                user_id=(
                    audit_user_id
                ),
                action="auth.logout",
                entity="user_session",
                entity_id=(
                    session_id
                ),
                details={
                    "reason": (
                        "logout"
                    ),
                },
            )

    return {
        "message": (
            "Sesión cerrada correctamente"
        )
    }


# ==========================================
# USUARIO AUTENTICADO
# ==========================================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def me(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    return (
        AuthService
        .get_current_profile(
            db=db,
            user=current_user,
        )
    )


# ==========================================
# SESIONES ACTIVAS DEL USUARIO
# ==========================================

@router.get(
    "/sessions",
    response_model=list[
        SessionResponse
    ],
)
def get_sessions(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    return (
        SessionRepository
        .get_active_by_user(
            db=db,
            user_id=current_user.id,
        )
    )


# ==========================================
# CERRAR UNA SESIÓN ESPECÍFICA
# ==========================================

@router.delete(
    "/sessions/{session_uuid}",
)
def revoke_session(
    session_uuid: str,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    session = (
        SessionRepository
        .get_by_uuid(
            db=db,
            session_uuid=session_uuid,
        )
    )

    if (
        not session
        or session.user_id
        != current_user.id
    ):

        return {
            "message": (
                "Sesión no encontrada"
            )
        }

    session_id = (
        session.id
    )

    (
        RefreshTokenRepository
        .revoke_all_by_session(
            db=db,
            session_id=session.id,
            reason="session_revoked",
        )
    )

    SessionRepository.revoke(
        db=db,
        session=session,
        reason="session_revoked",
    )

    AuditService.log_safe(
        db=db,
        user_id=current_user.id,
        action="auth.session.revoke",
        entity="user_session",
        entity_id=session_id,
        details={
            "session_uuid": (
                session_uuid
            ),
            "reason": (
                "session_revoked"
            ),
        },
    )

    return {
        "message": (
            "Sesión revocada correctamente"
        )
    }