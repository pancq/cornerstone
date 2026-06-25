from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..models import User, UserSession
from ..utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    jti: str = payload.get("jti")
    
    if username is None:
        raise credentials_exception
    
    # 检查会话是否已被撤销
    stmt = select(UserSession).where(
        UserSession.jti == jti,
        UserSession.is_revoked == False
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 使用 select 查询用户，预加载role关系避免懒加载
    stmt = select(User).options(joinedload(User.role)).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限"
        )
    return current_user

async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求超级管理员权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user

def require_permission(permission: str):
    """权限依赖装饰器"""
    async def permission_check(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # 超级用户跳过权限检查
        if current_user.is_superuser:
            return current_user

        from ..services.permission_service import has_permission as check_permission

        # 解析权限字符串 (格式: module:action)
        if ':' in permission:
            module, action = permission.split(':', 1)
        else:
            module = permission
            action = 'read'

        if not await check_permission(db, current_user.id, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}"
            )
        return current_user

    return permission_check

def require_permissions(permissions: List[str]):
    """多权限依赖装饰器（满足任一即可）"""
    async def permissions_check(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # 超级用户跳过权限检查
        if current_user.is_superuser:
            return current_user
        
        from ..services.permission_service import has_permission as check_permission
        
        for permission in permissions:
            if ':' in permission:
                module, action = permission.split(':', 1)
            else:
                module = permission
                action = 'read'
            
            if await check_permission(db, current_user.id, module, action):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少必要权限，需要以下任一权限: {', '.join(permissions)}"
        )
    return permissions_check
