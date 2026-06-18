from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceLinkCreate(BaseModel):
    source_device_id: Optional[int] = None
    source_interface: Optional[str] = None
    target_device_id: Optional[int] = None
    target_interface: Optional[str] = None
    link_type: str = "manual"
    confidence: Optional[int] = 100
    note: Optional[str] = None
    source_circuit_id: Optional[int] = None
    target_circuit_id: Optional[int] = None

class DeviceLinkUpdate(BaseModel):
    source_device_id: Optional[int] = None
    source_interface: Optional[str] = None
    target_device_id: Optional[int] = None
    target_interface: Optional[str] = None
    link_type: Optional[str] = None
    confidence: Optional[int] = None
    verified_at: Optional[datetime] = None
    note: Optional[str] = None
    source_circuit_id: Optional[int] = None
    target_circuit_id: Optional[int] = None

class DeviceLinkResponse(BaseModel):
    id: int
    source_device_id: Optional[int]
    source_interface: Optional[str]
    target_device_id: Optional[int]
    target_interface: Optional[str]
    link_type: str
    confidence: Optional[int]
    discovered_at: Optional[datetime]
    verified_at: Optional[datetime]
    note: Optional[str]
    source_circuit_id: Optional[int]
    target_circuit_id: Optional[int]
    
    class Config:
        from_attributes = True
