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