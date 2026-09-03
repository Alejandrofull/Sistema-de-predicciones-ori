from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        session_id: int,
        token_hash: str,
        jti: str,
        expires_at: datetime
    ) -> RefreshToken:

        token = RefreshToken(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            revoked=False
        )

        db.add(token)
        db.commit()
        db.refresh(token)

        return token

    @staticmethod
    def get_by_hash(
        db: Session,
        token_hash: str
    ) -> RefreshToken | None:

        statement = select(
            RefreshToken
        ).where(
            RefreshToken.token_hash
            == token_hash
        )

        return db.scalar(statement)

    @staticmethod
    def revoke(
        db: Session,
        token: RefreshToken,
        reason: str,
        replaced_by_jti: str | None = None
    ) -> None:

        token.revoked = True

        token.revoked_reason = reason

        token.revoked_at = datetime.now(
            timezone.utc
        )

        token.replaced_by_jti = (
            replaced_by_jti
        )

        db.commit()

    @staticmethod
    def mark_used(
        db: Session,
        token: RefreshToken
    ) -> None:

        token.last_used_at = datetime.now(
            timezone.utc
        )

        db.commit()

    @staticmethod
    def revoke_all_by_session(
        db: Session,
        session_id: int,
        reason: str
    ) -> None:

        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.session_id
                == session_id,
                RefreshToken.revoked.is_(False)
            )
            .values(
                revoked=True,
                revoked_reason=reason,
                revoked_at=datetime.now(
                    timezone.utc
                )
            )
        )

        db.execute(statement)
        db.commit()