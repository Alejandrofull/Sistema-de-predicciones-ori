from pydantic import BaseModel


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role_codes: list[str]


class UserManagementResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    roles: list[str]