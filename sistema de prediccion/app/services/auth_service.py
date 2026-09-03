import uuid

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_session import UserSession

from app.repositories.refresh_token_repository import (
    RefreshTokenRepository
)
from app.repositories.role_repository import (
    RoleRepository
)
from app.repositories.session_repository import (
    SessionRepository
)
from app.repositories.user_repository import (
    UserRepository
)
from app.repositories.user_role_repository import (
    UserRoleRepository
)

from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)

from app.security.password import (
    hash_password,
    verify_password,
)

from app.services.authorization_service import (
    AuthorizationService
)


class AuthService:

    @staticmethod
    def register(
        db: Session,
        email: str,
        password: str
    ):
        email = email.lower().strip()

        existing = UserRepository.get_by_email(
            db,
            email
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo ya está registrado"
            )

        # ==========================================
        # CREAR USUARIO
        # ==========================================

        user = UserRepository.create(
            db=db,
            email=email,
            password_hash=hash_password(
                password
            )
        )

        # ==========================================
        # ASIGNAR ROL OPERATOR POR DEFECTO
        # ==========================================

        operator_role = RoleRepository.get_by_code(
            db,
            "operator"
        )

        if not operator_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "El rol operator no está "
                    "configurado en el sistema"
                )
            )

        UserRoleRepository.assign_role(
            db=db,
            user_id=user.id,
            role_id=operator_role.id
        )

        return user

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None
    ):
        email = email.lower().strip()

        user = UserRepository.get_by_email(
            db,
            email
        )

        # ==========================================
        # VALIDAR USUARIO
        # ==========================================

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        # ==========================================
        # VALIDAR CONTRASEÑA
        # ==========================================

        if not verify_password(
            password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        # ==========================================
        # VALIDAR ESTADO
        # ==========================================

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario deshabilitado"
            )

        # ==========================================
        # CREAR SESIÓN
        # ==========================================

        session_uuid = str(
            uuid.uuid4()
        )

        device_name = (
            user_agent[:150]
            if user_agent
            else None
        )

        session = SessionRepository.create(
            db=db,
            user_id=user.id,
            session_uuid=session_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name
        )

        # ==========================================
        # ACCESS TOKEN
        # ==========================================

        access_token = create_access_token(
            user_id=user.id,
            session_uuid=session_uuid
        )

        # ==========================================
        # REFRESH TOKEN
        # ==========================================

        (
            refresh_token,
            jti,
            expires_at
        ) = create_refresh_token(
            user_id=user.id,
            session_uuid=session_uuid
        )

        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_token(
                refresh_token
            ),
            jti=jti,
            expires_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def refresh(
        db: Session,
        raw_refresh_token: str
    ):
        # ==========================================
        # DECODIFICAR TOKEN
        # ==========================================

        try:
            payload = decode_token(
                raw_refresh_token
            )

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )

        # ==========================================
        # VALIDAR TIPO DE TOKEN
        # ==========================================

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        user_id = payload.get("sub")
        session_uuid = payload.get(
            "session_id"
        )
        token_jti = payload.get(
            "jti"
        )

        if (
            not user_id
            or not session_uuid
            or not token_jti
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        # ==========================================
        # BUSCAR REFRESH TOKEN EN BD
        # ==========================================

        token_hash = hash_token(
            raw_refresh_token
        )

        stored_token = (
            RefreshTokenRepository
            .get_by_hash(
                db,
                token_hash
            )
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token no reconocido"
            )

        # ==========================================
        # VALIDAR JTI
        # ==========================================

        if stored_token.jti != token_jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )

        # ==========================================
        # VALIDAR REVOCACIÓN
        # ==========================================

        if stored_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revocado"
            )

        # ==========================================
        # VALIDAR EXPIRACIÓN
        # ==========================================

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            stored_token.expires_at
        )

        if expires_at.tzinfo is None:
            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado"
            )

        # ==========================================
        # OBTENER USUARIO
        # ==========================================

        user = UserRepository.get_by_id(
            db,
            stored_token.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario deshabilitado"
            )

        # ==========================================
        # OBTENER SESIÓN
        # ==========================================

        session = db.get(
            UserSession,
            stored_token.session_id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión no encontrada"
            )

        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión cerrada"
            )

        if (
            session.session_uuid
            != session_uuid
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión inválida"
            )

        # ==========================================
        # ROTACIÓN DEL REFRESH TOKEN
        # ==========================================

        (
            new_refresh_token,
            new_jti,
            new_expires_at
        ) = create_refresh_token(
            user_id=user.id,
            session_uuid=(
                session.session_uuid
            )
        )

        RefreshTokenRepository.revoke(
            db=db,
            token=stored_token,
            reason="rotation",
            replaced_by_jti=new_jti
        )

        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_token(
                new_refresh_token
            ),
            jti=new_jti,
            expires_at=new_expires_at
        )

        # ==========================================
        # NUEVO ACCESS TOKEN
        # ==========================================

        access_token = create_access_token(
            user_id=user.id,
            session_uuid=(
                session.session_uuid
            )
        )

        # ==========================================
        # ACTUALIZAR ACTIVIDAD DE SESIÓN
        # ==========================================

        SessionRepository.update_activity(
            db=db,
            session=session
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def get_current_profile(
        db: Session,
        user
    ) -> dict:
        # ==========================================
        # OBTENER ROLES DEL USUARIO
        # ==========================================

        roles = (
            AuthorizationService
            .get_user_roles(
                db=db,
                user_id=user.id
            )
        )

        # ==========================================
        # OBTENER PERMISOS DEL USUARIO
        # ==========================================

        permissions = (
            AuthorizationService
            .get_user_permission_codes(
                db=db,
                user_id=user.id
            )
        )

        # ==========================================
        # PERFIL COMPLETO
        # ==========================================

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "roles": roles,
            "permissions": sorted(
                permissions
            )
        }