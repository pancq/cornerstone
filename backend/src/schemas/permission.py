from pydantic import BaseModel
from typing import Optional

class PermissionResponse(BaseModel):
    id: int
    module: str
    action: str
    display_name: Optional[str]
    description: Optional[str]
    
    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role_id: int
