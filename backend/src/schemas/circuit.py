from pydantic import BaseModel
from datetime import datetime

class CircuitCreate(BaseModel):
    name: str
    provider: str | None = None
    type: str | None = None
    site_id: int | None = None
    bandwidth: int | None = None
    monthly_cost: float | None = None
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    circuit_no: str | None = None
    support_phone: str | None = None
    public_ip: str | None = None
    status: str = "active"
    note: str | None = None
    updated_by: str | None = None

class CircuitUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    type: str | None = None
    site_id: int | None = None
    bandwidth: int | None = None
    monthly_cost: float | None = None
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    circuit_no: str | None = None
    support_phone: str | None = None
    public_ip: str | None = None
    status: str | None = None
    note: str | None = None
    updated_by: str | None = None

class CircuitResponse(BaseModel):
    id: int
    name: str
    provider: str | None
    type: str | None
    site_id: int | None
    bandwidth: int | None
    monthly_cost: float | None
    contract_start: datetime | None
    contract_end: datetime | None
    circuit_no: str | None
    support_phone: str | None
    public_ip: str | None
    status: str
    note: str | None
    updated_by: str | None
    updated_at: datetime
    
    class Config:
        from_attributes = True
