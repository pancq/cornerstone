from pydantic import BaseModel
from datetime import datetime

class PrefixCreate(BaseModel):
    aggregate_id: int | None = None
    network: str
    site_id: int | None = None
    vlan: str | None = None
    usage: str | None = None

class PrefixUpdate(BaseModel):
    aggregate_id: int | None = None
    network: str | None = None
    site_id: int | None = None
    vlan: str | None = None
    usage: str | None = None

class PrefixResponse(BaseModel):
    id: int
    aggregate_id: int | None
    network: str
    site_id: int | None
    vlan: str | None
    usage: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True
