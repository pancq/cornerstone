from pydantic import BaseModel
from datetime import datetime

class IPAddressCreate(BaseModel):
    address: str
    prefix_id: int | None = None
    device_id: int | None = None
    usage: str | None = None
    owner: str | None = None
    status: str = "available"
    expire_at: datetime | None = None

class IPAddressUpdate(BaseModel):
    address: str | None = None
    prefix_id: int | None = None
    device_id: int | None = None
    usage: str | None = None
    owner: str | None = None
    status: str | None = None
    expire_at: datetime | None = None

class IPAddressResponse(BaseModel):
    id: int
    address: str
    prefix_id: int | None
    device_id: int | None
    usage: str | None
    owner: str | None
    status: str
    expire_at: datetime | None
    is_online: bool | None
    last_seen_at: datetime | None
    scan_method: str | None
    open_ports: str | None
    mac_address: str | None
    last_scanned_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True

class IPExpiringResponse(BaseModel):
    id: int
    address: str
    prefix_id: int | None
    usage: str | None
    owner: str | None
    expire_at: datetime
    remaining_days: int
    
    class Config:
        from_attributes = True
