from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class PermissionResponse(BaseModel):
    id: int
    name: str
    code: str
    module: str
    description: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class RoleCreateRequest(BaseModel):
    name: str
    code: str
    description: str | None = None


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[int]


class RoleStatusUpdate(BaseModel):
    is_active: bool


class RoleDetailResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    permissions: list[PermissionResponse]

    model_config = {
        "from_attributes": True
    }