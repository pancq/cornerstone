"""LDAP认证API路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
import json

from ..database import get_db
from ..models import User, Role, AuditLog, SystemConfig
from ..services.ldap_service import ldap_service, LDAPException as LDAPAuthException
from .dependencies import get_current_active_user


router = APIRouter()

# Request body models
class LDAPLoginRequest(BaseModel):
    """LDAP登录请求体"""
    username: str
    password: str

class LDAPConfigRequest(BaseModel):
    """LDAP配置请求体"""
    enabled: bool
    server: str
    port: int = 389
    use_ssl: bool = False
    use_starttls: bool = False
    verify_cert: bool = True
    bind_dn: str
    bind_password: str
    base_dn: str
    user_filter: str = "(objectClass=person)"
    username_attr: str = "sAMAccountName"
    display_attr: str = "displayName"
    email_attr: str = "mail"
    phone_attr: str = "mobile"
    department_attr: str = "department"
    group_attr: str = "memberOf"
    default_role: str = "viewer"


async def log_login_attempt(db: AsyncSession, username: str, success: bool, ip_address: str = None):
    """记录登录尝试日志"""
    detail = "LDAP登录成功" if success else "LDAP登录失败"
    stmt = insert(AuditLog).values(
        user=username,
        action="用户登录",
        resource="系统",
        detail=detail,
        ip_address=ip_address,
        success="true" if success else "false"
    )
    await db.execute(stmt)
    await db.commit()


@router.get("/ldap/enabled")
async def is_ldap_enabled(db: AsyncSession = Depends(get_db)):
    """检查LDAP是否启用"""
    config = await ldap_service.get_config(db)
    return {"enabled": config.enabled}


@router.get("/ldap/config")
async def get_ldap_config(db: AsyncSession = Depends(get_db)):
    """获取LDAP配置"""
    config = await ldap_service.get_config(db)
    return config.to_dict()


@router.put("/ldap/config")
async def update_ldap_config(
    request: LDAPConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新LDAP配置"""
    # 检查是否有权限
    stmt = select(Role).where(Role.id == current_user.role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    
    if not role or role.name != "super_admin":
        raise HTTPException(status_code=403, detail="没有权限修改系统配置")
    
    # 保存配置到数据库
    config_data = request.dict()
    
    stmt = select(SystemConfig).where(SystemConfig.key == "ldap_config")
    result = await db.execute(stmt)
    db_config = result.scalar_one_or_none()
    
    if db_config:
        stmt = update(SystemConfig).where(
            SystemConfig.key == "ldap_config"
        ).values(value=json.dumps(config_data))
        await db.execute(stmt)
    else:
        db_config = SystemConfig(
            key="ldap_config",
            value=json.dumps(config_data),
            description="LDAP认证配置"
        )
        db.add(db_config)
    
    await db.commit()
    
    # 记录审计日志
    stmt = insert(AuditLog).values(
        user=current_user.username,
        action="修改LDAP配置",
        resource="系统",
        detail="更新LDAP认证配置",
        success="true"
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "LDAP配置更新成功"}


@router.post("/ldap/test")
async def test_ldap_connection(
    request: LDAPConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """测试LDAP连接"""
    # 检查是否有权限
    stmt = select(Role).where(Role.id == current_user.role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    
    if not role or role.name != "super_admin":
        raise HTTPException(status_code=403, detail="没有权限测试LDAP配置")
    
    from ..services.ldap_service import LDAPConfig
    
    config = LDAPConfig()
    config.enabled = request.enabled
    config.server = request.server
    config.port = request.port
    config.use_ssl = request.use_ssl
    config.use_starttls = request.use_starttls
    config.verify_cert = request.verify_cert
    config.bind_dn = request.bind_dn
    config.bind_password = request.bind_password
    config.base_dn = request.base_dn
    
    try:
        success = await ldap_service.test_connection(config)
        if success:
            return {"success": True, "message": "LDAP连接测试成功"}
        else:
            return {"success": False, "message": "LDAP连接测试失败"}
    except Exception as e:
        return {"success": False, "message": f"LDAP连接测试失败: {str(e)}"}


@router.post("/ldap/login")
async def ldap_login(
    request: Request,
    body: LDAPLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """LDAP用户登录"""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")
    
    try:
        result = await ldap_service.login(db, body.username, body.password, client_ip, user_agent)
        return result
    except LDAPAuthException as e:
        await log_login_attempt(db, body.username, False, client_ip)
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        await log_login_attempt(db, body.username, False, client_ip)
        raise HTTPException(status_code=500, detail=f"LDAP登录失败: {str(e)}")
