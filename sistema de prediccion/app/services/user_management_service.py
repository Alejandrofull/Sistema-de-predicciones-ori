from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.role_repository import (
    RoleRepository
)
from app.repositories.user_repository import (
    UserRepository
)
from app.repositories.user_role_repository import (
    UserRoleRepository
)


class UserManagementService:

    @staticmethod
    def get_user_with_roles(
        db: Session,
        user_id: int
    ) -> dict:

        user = UserRepository.get_by_id(
            db,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        roles = (
            UserRoleRepository
            .get_roles_by_user(
                db,
                user_id
            )
        )

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "roles": [
                role.code
                for role in roles
            ]
        }

    @staticmethod
    def get_all_users(
        db: Session
    ) -> list[dict]:

        users = UserRepository.get_all(db)

        result = []

        for user in users:
            roles = (
                UserRoleRepository
                .get_roles_by_user(
                    db,
                    user.id
                )
            )

            result.append({
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "roles": [
                    role.code
                    for role in roles
                ]
            })

        return result

    @staticmethod
    def update_status(
        db: Session,
        user_id: int,
        is_active: bool
    ) -> dict:

        user = UserRepository.get_by_id(
            db,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        UserRepository.set_active(
            db=db,
            user=user,
            is_active=is_active
        )

        return (
            UserManagementService
            .get_user_with_roles(
                db,
                user.id
            )
        )

    @staticmethod
    def replace_roles(
        db: Session,
        user_id: int,
        role_codes: list[str]
    ) -> dict:

        user = UserRepository.get_by_id(
            db,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if not role_codes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El usuario debe tener "
                    "al menos un rol"
                )
            )

        role_ids = []

        for code in set(role_codes):

            role = RoleRepository.get_by_code(
                db,
                code
            )

            if not role:
                raise HTTPException(
                    status_code=400,
                    detail=f"Rol inválido: {code}"
                )

            if not role.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Rol inactivo: {code}"
                )

            role_ids.append(role.id)

        UserRoleRepository.replace_roles(
            db=db,
            user_id=user.id,
            role_ids=role_ids
        )

        return (
            UserManagementService
            .get_user_with_roles(
                db,
                user.id
            )
        )