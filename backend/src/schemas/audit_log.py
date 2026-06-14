from pydantic import BaseModel, Field
from datetime import datetime, timezone

class AuditLogResponse(BaseModel):
    id: int
    user: str
    action: str
    resource: str | None
    detail: str | None
    ip_address: str | None = Field(serialization_alias="ipAddress")
    created_at: datetime = Field(serialization_alias="createdAt")
    success: str
    
    model_config = {
        "from_attributes": True,
    }
    
    @classmethod
    def from_orm(cls, obj):
        instance = super().from_orm(obj)
        # 确保created_at带时区信息
        if instance.created_at and instance.created_at.tzinfo is None:
            instance.created_at = instance.created_at.replace(tzinfo=timezone.utc)
        return instance
