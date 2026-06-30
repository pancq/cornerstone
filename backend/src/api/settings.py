from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import json
import base64
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..database import get_db
from ..models.setting import Setting
from ..schemas.setting import SettingResponse, NotificationSettingsRequest, NotificationSettingsResponse
from ..models.audit_log import AuditLog
from ..config import settings as app_config
from ..services.alert_service import AlertService
from ..api.dependencies import require_super_admin

router = APIRouter()

NOTIFICATION_SETTINGS_KEY = "notification_settings"
LOG_SETTINGS_KEY = "log_settings"
COMPANY_INFO_KEY = "company_info"
BRAND_SETTINGS_KEY = "brand_settings"

# 默认品牌设置
BRAND_SETTINGS_DEFAULTS = {
    "brand_name_zh": "基石",
    "brand_name_en": "Cornerstone",
    "brand_slogan": "看得见，管得住",
    "brand_subtitle": "IT基础设施资源管理平台",
    "brand_logo_url": "",
}

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

@router.get("/brand", response_model=BrandSettingsResponse)
async def get_brand_settings(
    db: AsyncSession = Depends(get_db),
):
    """获取品牌设置，公共接口，不需要登录"""
    result = await db.execute(select(Setting).filter(Setting.key == BRAND_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        try:
            config = json.loads(setting.value)
            return BrandSettingsResponse(**config)
        except json.JSONDecodeError:
            pass
    
    return BrandSettingsResponse(**BRAND_SETTINGS_DEFAULTS)

@router.get("/public/brand", response_model=BrandSettingsResponse)
async def get_public_brand_settings(
    db: AsyncSession = Depends(get_db),
):
    """公开获取品牌设置，不需要登录，用于登录页显示"""
    result = await db.execute(select(Setting).filter(Setting.key == BRAND_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        try:
            config = json.loads(setting.value)
            return BrandSettingsResponse(**config)
        except json.JSONDecodeError:
            pass
    
    return BrandSettingsResponse(**BRAND_SETTINGS_DEFAULTS)

@router.put("/brand", response_model=dict)
async def update_brand_settings(
    request: BrandSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin),
):
    """更新品牌设置，仅超级管理员"""
    # 如果提交空值，重置为默认值
    config_dict = {
        "brand_name_zh": request.brand_name_zh or "基石",
        "brand_name_en": request.brand_name_en or "Cornerstone",
        "brand_slogan": request.brand_slogan or "看得见，管得住",
        "brand_subtitle": request.brand_subtitle or "IT基础设施资源管理平台",
        "brand_logo_url": request.brand_logo_url,
    }
    config_json = json.dumps(config_dict, ensure_ascii=False)
    
    result = await db.execute(select(Setting).filter(Setting.key == BRAND_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        setting.value = config_json
    else:
        setting = Setting(key=BRAND_SETTINGS_KEY, value=config_json)
        db.add(setting)
    
    await db.commit()
    
    return {"message": "品牌设置更新成功"}

@router.post("/brand/reset", response_model=dict)
async def reset_brand_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin),
):
    """重置为默认品牌设置"""
    result = await db.execute(select(Setting).filter(Setting.key == BRAND_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        await db.delete(setting)
        await db.commit()
    
    return {"message": "已恢复为默认品牌设置"}


# ============ Logo API ============


class CompanyInfoRequest(BaseModel):
    company_name: str = ""
    company_short_name: str = ""
    it_department_name: str = "信息技术部"
    it_contact_name: str = ""
    it_contact_email: str = ""


class TestNotificationRequest(BaseModel):
    channel: str  # dingtalk, wechat, feishu, email


class LogSettingsRequest(BaseModel):
    log_retention_days: int = 90
    login_log_retention_days: int = 180
    log_auto_cleanup: bool = True
    login_max_attempts: int = 5
    session_timeout_minutes: int = 120
    allow_concurrent_login: bool = True
    alert_on_foreign_login: bool = False
    log_query_operations: bool = False
    log_export_operations: bool = True
    log_login_operations: bool = True
    require_confirm_dangerous: bool = True


class LogSettingsResponse(BaseModel):
    log_retention_days: int
    login_log_retention_days: int
    log_auto_cleanup: bool
    login_max_attempts: int
    session_timeout_minutes: int
    allow_concurrent_login: bool
    alert_on_foreign_login: bool
    log_query_operations: bool
    log_export_operations: bool
    log_login_operations: bool
    require_confirm_dangerous: bool


class CleanupResponse(BaseModel):
    deleted_count: int
    duration_ms: int

@router.get("/logo", response_model=SettingResponse)
async def get_logo(db: AsyncSession = Depends(get_db)):
    """获取当前Logo"""
    result = await db.execute(select(Setting).filter(Setting.key == "company_logo"))
    setting = result.scalars().first()
    if setting:
        return {"key": setting.key, "value": setting.value}
    return {"key": "company_logo", "value": ""}

@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """上传Logo"""
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    # 验证文件大小（最大2MB）
    max_size = 2 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="图片大小不能超过2MB")
    
    # 存储到数据库
    result = await db.execute(select(Setting).filter(Setting.key == "company_logo"))
    setting = result.scalars().first()
    
    if setting:
        setting.value = base64.b64encode(content).decode('ascii')
    else:
        setting = Setting(key="company_logo", value=base64.b64encode(content).decode('ascii'))
        db.add(setting)
    await db.commit()
    
    return {"message": "Logo上传成功"}

@router.delete("/logo")
async def delete_logo(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """删除Logo"""
    result = await db.execute(select(Setting).filter(Setting.key == "company_logo"))
    setting = result.scalars().first()
    if setting:
        await db.delete(setting)
        await db.commit()
    return {"message": "Logo已删除"}

@router.get("/notification", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """获取通知渠道配置"""
    result = await db.execute(select(Setting).filter(Setting.key == NOTIFICATION_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        try:
            config = json.loads(setting.value)
            return NotificationSettingsResponse(**config)
        except json.JSONDecodeError:
            pass
    
    return NotificationSettingsResponse(
        dingtalk_webhook_url=app_config.notification.dingtalk_webhook_url,
        wechat_webhook_url=app_config.notification.wechat_webhook_url,
        feishu_webhook_url=app_config.notification.feishu_webhook_url,
        smtp_host=app_config.notification.smtp_host,
        smtp_port=app_config.notification.smtp_port,
        smtp_username=app_config.notification.smtp_username,
        smtp_password=app_config.notification.smtp_password,
        smtp_from_email=app_config.notification.smtp_from_email
    )

@router.put("/notification", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: NotificationSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """更新通知渠道配置"""
    result = await db.execute(select(Setting).filter(Setting.key == NOTIFICATION_SETTINGS_KEY))
    setting = result.scalars().first()
    
    config_dict = {
        "dingtalk_webhook_url": request.dingtalk_webhook_url,
        "wechat_webhook_url": request.wechat_webhook_url,
        "feishu_webhook_url": request.feishu_webhook_url,
        "smtp_host": request.smtp_host,
        "smtp_port": request.smtp_port,
        "smtp_username": request.smtp_username,
        "smtp_password": request.smtp_password,
        "smtp_from_email": request.smtp_from_email
    }
    
    config_json = json.dumps(config_dict)
    
    if setting:
        setting.value = config_json
    else:
        setting = Setting(key=NOTIFICATION_SETTINGS_KEY, value=config_json)
        db.add(setting)
    
    await db.commit()
    
    return NotificationSettingsResponse(**config_dict)


@router.post("/notification/test")
async def test_notification(
    request: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """测试通知渠道"""
    config = await AlertService._get_notification_config(db)
    
    test_message = "【测试通知】这是一条来自基石系统的测试消息，通知渠道配置成功！"
    
    try:
        if request.channel == "dingtalk":
            if not config.get("dingtalk_webhook_url"):
                raise HTTPException(status_code=400, detail="钉钉Webhook地址未配置")
            await AlertService._send_dingtalk_notification(config["dingtalk_webhook_url"], test_message)
            
        elif request.channel == "wechat":
            if not config.get("wechat_webhook_url"):
                raise HTTPException(status_code=400, detail="企业微信Webhook地址未配置")
            await AlertService._send_wechat_notification(config["wechat_webhook_url"], test_message)
            
        elif request.channel == "feishu":
            if not config.get("feishu_webhook_url"):
                raise HTTPException(status_code=400, detail="飞书Webhook地址未配置")
            await AlertService._send_feishu_notification(config["feishu_webhook_url"], test_message)
            
        elif request.channel == "email":
            if not all([config.get("smtp_host"), config.get("smtp_username"), 
                       config.get("smtp_password"), config.get("smtp_from_email")]):
                raise HTTPException(status_code=400, detail="邮件服务器配置不完整")
            await AlertService._send_email_notification(config, test_message)
            
        else:
            raise HTTPException(status_code=400, detail="不支持的通知渠道")
            
        return {"success": True, "message": f"{request.channel} 测试通知发送成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


# ============ 日志设置 API ============

@router.get("/logs", response_model=LogSettingsResponse)
async def get_log_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """获取日志设置（仅 super_admin）"""
    result = await db.execute(select(Setting).filter(Setting.key == LOG_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        try:
            config = json.loads(setting.value)
            return LogSettingsResponse(**config)
        except json.JSONDecodeError:
            pass
    
    # 返回默认值
    return LogSettingsResponse(
        log_retention_days=90,
        login_log_retention_days=180,
        log_auto_cleanup=True,
        login_max_attempts=5,
        session_timeout_minutes=120,
        allow_concurrent_login=True,
        alert_on_foreign_login=False,
        log_query_operations=False,
        log_export_operations=True,
        log_login_operations=True,
        require_confirm_dangerous=True
    )


@router.put("/logs", response_model=LogSettingsResponse)
async def update_log_settings(
    request: LogSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """保存日志设置（仅 super_admin）"""
    # log_login_operations 不可修改，保持为 True
    config_dict = {
        "log_retention_days": request.log_retention_days,
        "login_log_retention_days": request.login_log_retention_days,
        "log_auto_cleanup": request.log_auto_cleanup,
        "login_max_attempts": request.login_max_attempts,
        "session_timeout_minutes": request.session_timeout_minutes,
        "allow_concurrent_login": request.allow_concurrent_login,
        "alert_on_foreign_login": request.alert_on_foreign_login,
        "log_query_operations": request.log_query_operations,
        "log_export_operations": request.log_export_operations,
        "log_login_operations": True,  # 强制为 True，不可修改
        "require_confirm_dangerous": request.require_confirm_dangerous
    }
    
    config_json = json.dumps(config_dict)
    
    result = await db.execute(select(Setting).filter(Setting.key == LOG_SETTINGS_KEY))
    setting = result.scalars().first()
    
    if setting:
        setting.value = config_json
    else:
        setting = Setting(key=LOG_SETTINGS_KEY, value=config_json)
        db.add(setting)
    
    await db.commit()
    
    return LogSettingsResponse(**config_dict)


@router.post("/logs/cleanup", response_model=CleanupResponse)
async def cleanup_logs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """手动触发清理过期日志（仅 super_admin）"""
    start_time = datetime.now()
    
    # 获取日志保留设置
    result = await db.execute(select(Setting).filter(Setting.key == LOG_SETTINGS_KEY))
    setting = result.scalars().first()
    
    log_retention_days = 90
    login_log_retention_days = 180
    
    if setting:
        try:
            config = json.loads(setting.value)
            log_retention_days = config.get("log_retention_days", 90)
            login_log_retention_days = config.get("login_log_retention_days", 180)
        except json.JSONDecodeError:
            pass
    
    # 计算截止日期
    audit_cutoff = datetime.now() - timedelta(days=log_retention_days)
    login_cutoff = datetime.now() - timedelta(days=login_log_retention_days)
    
    # 删除过期审计日志
    deleted_count = 0
    
    # 删除审计日志（登录日志除外）
    audit_result = await db.execute(
        delete(AuditLog).where(
            AuditLog.created_at < audit_cutoff,
            AuditLog.action != 'login',
            AuditLog.action != 'logout'
        )
    )
    deleted_count += audit_result.rowcount
    
    # 删除登录日志
    login_result = await db.execute(
        delete(AuditLog).where(
            AuditLog.created_at < login_cutoff,
            AuditLog.action.in_(['login', 'logout'])
        )
    )
    deleted_count += login_result.rowcount
    
    await db.commit()
    
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # 记录清理操作到审计日志
    cleanup_log = AuditLog(
        user=current_user.username,
        action='log_cleanup',
        resource='system',
        detail=f"清理了 {deleted_count} 条过期日志（审计日志保留{log_retention_days}天，登录日志保留{login_log_retention_days}天）"
    )
    db.add(cleanup_log)
    await db.commit()
    
    return CleanupResponse(deleted_count=deleted_count, duration_ms=duration_ms)


# ============ 公司信息 API ============

@router.get("/company")
async def get_company_info(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """获取公司信息配置"""
    result = await db.execute(select(Setting).filter(Setting.key == COMPANY_INFO_KEY))
    setting = result.scalars().first()
    
    if setting:
        try:
            config = json.loads(setting.value)
            return config
        except json.JSONDecodeError:
            pass
    
    return {
        "company_name": "",
        "company_short_name": "",
        "it_department_name": "信息技术部",
        "it_contact_name": "",
        "it_contact_email": ""
    }


@router.put("/company")
async def update_company_info(
    request: CompanyInfoRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """保存公司信息配置"""
    config_dict = request.model_dump()
    config_json = json.dumps(config_dict, ensure_ascii=False)
    
    result = await db.execute(select(Setting).filter(Setting.key == COMPANY_INFO_KEY))
    setting = result.scalars().first()
    
    if setting:
        setting.value = config_json
    else:
        setting = Setting(key=COMPANY_INFO_KEY, value=config_json)
        db.add(setting)
    
    await db.commit()
    
    return {"message": "公司信息已更新"}
