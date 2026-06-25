from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ..database import get_db
from ..models import AuditLog
from ..schemas import AuditLogResponse
from .dependencies import get_current_active_user

router = APIRouter()

from datetime import datetime, timezone, timedelta

@router.get("/")
async def read_logs(
    skip: int = 0,
    limit: int = 100,
    user: str = None,
    action: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    query = select(AuditLog)
    if user:
        query = query.where(AuditLog.user.like(f"%{user}%"))
    if action:
        query = query.where(AuditLog.action.like(f"%{action}%"))
    query = query.order_by(AuditLog.created_at.desc())
    result = await db.execute(query.offset(skip).limit(limit))
    logs = result.scalars().all()
    
    # 手动序列化并确保时间带时区标记
    result = []
    for log in logs:
        created_at = log.created_at
        if created_at:
            # 确保时间带时区信息
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone(timedelta(hours=8)))
            created_at_str = created_at.isoformat().replace("+08:00", "Z")
        else:
            created_at_str = None
        
        result.append({
            "id": log.id,
            "user": log.user,
            "action": log.action,
            "resource": log.resource,
            "detail": log.detail,
            "ipAddress": log.ip_address,
            "createdAt": created_at_str,
            "success": log.success
        })
    
    return result

@router.get("/{log_id}", response_model=AuditLogResponse)
async def read_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@router.post("/", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    stmt = insert(AuditLog).values(**log).returning(AuditLog)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()
