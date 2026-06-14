from pydantic import BaseModel
from datetime import datetime

class SiteCreate(BaseModel):
    name: str
    location: str | None = None
    city: str | None = None
    room: str | None = None
    contact: str | None = None
    contact_phone: str | None = None
    status: str = "online"
    alert_count: int = 0

class SiteUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    city: str | None = None
    room: str | None = None
    contact: str | None = None
    contact_phone: str | None = None
    status: str | None = None
    alert_count: int | None = None

class SiteResponse(BaseModel):
    id: int
    name: str
    location: str | None
    city: str | None
    room: str | None
    contact: str | None
    contact_phone: str | None
    status: str
    alert_count: int | None = 0
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True
