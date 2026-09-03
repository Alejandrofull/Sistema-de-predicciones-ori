from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    @staticmethod
    def get_by_email(
        db: Session,
        email: str
    ) -> User | None:
        statement = select(User).where(
            User.email == email
        )

        return db.scalar(statement)

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: int
    ) -> User | None:
        return db.get(
            User,
            user_id
        )

    @staticmethod
    def create(
        db: Session,
        email: str,
        password_hash: str
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_email(
        db: Session,
        user: User,
        email: str
    ) -> User:
        user.email = email

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def set_active(
        db: Session,
        user: User,
        is_active: bool
    ) -> User:
        user.is_active = is_active

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_all(
        db: Session
    ) -> list[User]:
        statement = (
            select(User)
            .order_by(User.id)
        )

        return list(
            db.scalars(statement).all()
        )