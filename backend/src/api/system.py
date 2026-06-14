"""系统配置API"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel

from ..database import get_db
from ..models import SystemConfig
from ..api.dependencies import get_current_active_user
from ..models import User

router = APIRouter()


class SSOConfigModel(BaseModel):
    """SSO配置模型"""
    enabled: bool = False
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorize_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    redirect_url: Optional[str] = None
    login_methods: str = "local,oauth2,saml"


@router.get("/sso-config")
async def get_sso_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取SSO配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "sso_config")
    )
    config = result.scalar_one_or_none()
    
    if not config or not config.value:
        return SSOConfigModel()
    
    try:
        config_data = json.loads(config.value)
        return SSOConfigModel(**config_data)
    except Exception:
        return SSOConfigModel()


@router.post("/sso-config")
async def save_sso_config(
    config: SSOConfigModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存SSO配置"""
    # 检查权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    
    # 查询现有配置
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "sso_config")
    )
    existing_config = result.scalar_one_or_none()
    
    config_json = config.model_dump_json()
    
    if existing_config:
        # 更新现有配置
        existing_config.value = config_json
    else:
        # 创建新配置
        new_config = SystemConfig(
            key="sso_config",
            value=config_json,
            description="SSO单点登录配置"
        )
        db.add(new_config)
    
    await db.commit()
    return {"message": "SSO配置保存成功"}


@router.post("/sso-config/test")
async def test_sso_config(
    config: SSOConfigModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """测试SSO配置"""
    import httpx
    
    if not config.client_id or not config.authorize_url:
        raise HTTPException(status_code=400, detail="缺少必要的配置参数")
    
    try:
        # 测试连接到授权端点
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(config.authorize_url, follow_redirects=True)
            
            if response.status_code in [200, 302, 400, 401, 403]:
                # 这些状态码都表示端点可达
                return {"message": f"授权端点可达 (状态码: {response.status_code})"}
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"授权端点返回异常状态码: {response.status_code}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="连接超时")
    except httpx.ConnectError:
        raise HTTPException(status_code=400, detail="无法连接到授权端点")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"测试失败: {str(e)}")


@router.delete("/sso-config")
async def reset_sso_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重置SSO配置"""
    # 检查权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    
    await db.execute(
        delete(SystemConfig).where(SystemConfig.key == "sso_config")
    )
    await db.commit()
    
    return {"message": "SSO配置已重置"}
