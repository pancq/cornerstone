from typing import Optional, List
from pydantic import BaseModel

class AlertRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    device_id: Optional[int] = None
    condition_type: str
    operator: str
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    notification_channels: Optional[List[str]] = None

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    device_id: Optional[int] = None
    condition_type: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    notification_channels: Optional[List[str]] = None
