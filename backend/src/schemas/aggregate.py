from pydantic import BaseModel
from datetime import datetime

class AggregateCreate(BaseModel):
    network: str
    name: str | None = None

class AggregateUpdate(BaseModel):
    network: str | None = None
    name: str | None = None

class AggregateResponse(BaseModel):
    id: int
    network: str
    name: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True
