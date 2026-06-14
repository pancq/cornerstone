from pydantic import BaseModel
from datetime import datetime

class VlanGroupCreate(BaseModel):
    name: str
    site_id: int | None = None
    description: str | None = None

class VlanGroupUpdate(BaseModel):
    name: str | None = None
    site_id: int | None = None
    description: str | None = None

class VlanGroupResponse(BaseModel):
    id: int
    name: str
    site_id: int | None
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True

class VlanCreate(BaseModel):
    vid: int
    name: str | None = None
    group_id: int | None = None
    site_id: int | None = None
    status: str = "active"
    description: str | None = None

class VlanUpdate(BaseModel):
    vid: int | None = None
    name: str | None = None
    group_id: int | None = None
    site_id: int | None = None
    status: str | None = None
    description: str | None = None

class VlanResponse(BaseModel):
    id: int
    vid: int
    name: str | None
    group_id: int | None
    site_id: int | None
    status: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True