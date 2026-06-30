from pydantic import BaseModel
from typing import Optional

class SettingResponse(BaseModel):
    key: str
    value: str
    
    class Config:
        from_attributes = True

class BrandSettingsRequest(BaseModel):
    brand_name_zh: str = "基石"
    brand_name_en: str = "Cornerstone"
    brand_slogan: str = "看得见，管得住"
    brand_subtitle: str = "IT基础设施资源管理平台"
    brand_logo_url: str = ""

class BrandSettingsResponse(BaseModel):
    brand_name_zh: str
    brand_name_en: str
    brand_slogan: str
    brand_subtitle: str
    brand_logo_url: str

class NotificationSettingsRequest(BaseModel):
    dingtalk_webhook_url: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 25
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

class NotificationSettingsResponse(BaseModel):
    dingtalk_webhook_url: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
