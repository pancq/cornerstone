from pydantic import BaseModel
from typing import Optional

class SettingResponse(BaseModel):
    key: str
    value: str
    
    class Config:
        from_attributes = True

class NotificationSettingsRequest(BaseModel):
    dingtalk_webhook_url: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

class NotificationSettingsResponse(BaseModel):
    dingtalk_webhook_url: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
