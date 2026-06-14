from pydantic import BaseModel
from datetime import datetime

class DeviceCreate(BaseModel):
    name: str
    type: str | None = None
    vendor: str | None = None
    model: str | None = None
    sn: str | None = None
    site_id: int | None = None
    location: str | None = None
    mgmt_ip_id: int | None = None
    status: str = "active"
    purchase_date: datetime | None = None
    warranty_end: datetime | None = None
    purchase_amount: float | None = None
    owner: str | None = None
    note: str | None = None

class DeviceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    vendor: str | None = None
    model: str | None = None
    sn: str | None = None
    site_id: int | None = None
    location: str | None = None
    mgmt_ip_id: int | None = None
    status: str | None = None
    purchase_date: datetime | None = None
    warranty_end: datetime | None = None
    purchase_amount: float | None = None
    owner: str | None = None
    note: str | None = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    type: str | None
    vendor: str | None
    model: str | None
    sn: str | None
    site_id: int | None
    location: str | None
    mgmt_ip_id: int | None
    status: str
    purchase_date: datetime | None
    warranty_end: datetime | None
    purchase_amount: float | None
    owner: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True
