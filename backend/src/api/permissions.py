from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update

from ..database import get_db
from ..models import Role, Permission, RolePermission, User
from ..schemas import RoleResponse, PermissionResponse, UserRoleUpdate
from .dependencies import get_current_active_user, get_current_superuser, require_permission

router = APIRouter()

@router.get("/roles", response_model=list[RoleResponse])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:read"))
):
    result = await db.execute(select(Role))
    return result.scalars().all()

@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:read"))
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:write"))
):
    result = await db.execute(select(Role).where(Role.name == role["name"]))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already exists")
    
    stmt = insert(Role).values(name=role["name"], description=role.get("description", "")).returning(Role)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:delete"))
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # User 通过单一 role_id 关联角色，删除前先解除该角色的用户关联
    await db.execute(update(User).where(User.role_id == role_id).values(role_id=None))
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    await db.execute(delete(Role).where(Role.id == role_id))
    await db.commit()

@router.get("/permissions", response_model=list[PermissionResponse])
async def get_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:read"))
):
    result = await db.execute(select(Permission))
    return result.scalars().all()

@router.post("/users/{user_id}/roles", status_code=204)
async def assign_role_to_user(
    user_id: int,
    role_update: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:write"))
):
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Role).where(Role.id == role_update.role_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Role not found")
    
    # User 用单一 role_id 关联角色，重复分配时返回 400
    result = await db.execute(
        select(User).where(User.id == user_id, User.role_id == role_update.role_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already assigned")
    
    await db.execute(update(User).where(User.id == user_id).values(role_id=role_update.role_id))
    await db.commit()

@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:write"))
):
    result = await db.execute(
        select(User).where(User.id == user_id, User.role_id == role_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User role not found")
    
    await db.execute(update(User).where(User.id == user_id).values(role_id=None))
    await db.commit()

@router.get("/users/{user_id}/permissions", response_model=list[str])
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:read"))
):
    from ..services.permission_service import get_user_permissions as get_perms
    return await get_perms(db, user_id)

@router.get("/users/{user_id}/roles", response_model=list[str])
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:read"))
):
    from ..services.permission_service import get_user_roles as get_roles
    return await get_roles(db, user_id)
