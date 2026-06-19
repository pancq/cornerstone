from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    display_name: Optional[str]
    description: Optional[str]
    is_builtin: bool = False
    permissions: List[str] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_builtin: bool = False
    permissions: List[str] = []

class UserRoleUpdate(BaseModel):
    role_id: int
