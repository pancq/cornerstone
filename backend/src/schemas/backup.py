from pydantic import BaseModel
from datetime import datetime

class BackupCreate(BaseModel):
    device_id: int
    trigger: str = "manual"
    operator: str | None = None
    note: str | None = None
    tag: str | None = None

class BackupResponse(BaseModel):
    id: int
    device_id: int
    device_name: str | None = None
    version: int
    content: str | None
    content_hash: str | None
    file_path: str | None
    trigger: str
    operator: str | None
    status: str
    error_message: str | None
    has_change: bool
    change_summary: str | None
    tag: str | None
    duration_ms: int | None
    size: float | None
    note: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True