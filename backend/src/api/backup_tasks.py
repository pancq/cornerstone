from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update, desc, func
from datetime import datetime
import json

from ..database import get_db
from ..models import BackupTask, Backup, Credential, Device, Site
from ..tasks.backup_scheduler import add_task_to_scheduler, remove_task_from_scheduler, \
    run_backup_task, reload_tasks
from ..utils.logger import audit_log
from .dependencies import get_current_active_user

router = APIRouter()

# 获取任务列表
@router.get("/")
async def get_backup_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask))
    tasks = result.scalars().all()
    
    # 添加关联信息
    result = []
    for task in tasks:
        task_dict = {c.name: getattr(task, c.name) for c in task.__table__.columns}
        
        # 直接返回格式化的北京时间，前端不需要转换时区
        if task_dict.get('last_run_at'):
            dt = task_dict['last_run_at']
            # last_run_at 由代码设置为 UTC，转换为北京时间输出
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            dt_shanghai = dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
            task_dict['last_run_at'] = dt_shanghai.strftime('%Y-%m-%d %H:%M:%S')
        if task_dict.get('created_at'):
            dt = task_dict['created_at']
            # 数据库已经是北京时间，直接格式化输出
            task_dict['created_at'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取凭证名称
        if task.credential_id:
            cred_result = await db.execute(select(Credential).where(Credential.id == task.credential_id))
            cred = cred_result.scalar_one_or_none()
            task_dict["credential_name"] = cred.name if cred else ""
        
        # 获取站点名称
        if task.site_id:
            site_result = await db.execute(select(Site).where(Site.id == task.site_id))
            site = site_result.scalar_one_or_none()
            task_dict["site_name"] = site.name if site else ""
        
        # 解析设备列表
        if task.device_ids:
            try:
                device_id_list = json.loads(task.device_ids)
                task_dict["device_count"] = len(device_id_list)
            except:
                task_dict["device_count"] = 0
        elif task.site_id:
            dev_result = await db.execute(select(func.count(Device.id)).where(Device.site_id == task.site_id))
            task_dict["device_count"] = dev_result.scalar_one()
        else:
            dev_result = await db.execute(select(func.count(Device.id)))
            task_dict["device_count"] = dev_result.scalar_one()
        
        result.append(task_dict)
    
    return result

# 获取单个任务
@router.get("/{task_id}")
async def get_backup_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    task_dict = {c.name: getattr(task, c.name) for c in task.__table__.columns}
    
    # 获取凭证名称
    if task.credential_id:
        cred_result = await db.execute(select(Credential).where(Credential.id == task.credential_id))
        cred = cred_result.scalar_one_or_none()
        task_dict["credential_name"] = cred.name if cred else ""
    
    return task_dict

# 创建任务
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_backup_task(
    name: str = Body(..., embed=True),
    cron_expr: str = Body(..., embed=True),
    credential_id: int = Body(..., embed=True),
    device_ids: list[int] = Body(None, embed=True),
    site_id: int = Body(None, embed=True),
    vendor: str = Body(None, embed=True),
    retention_count: int = Body(30, embed=True),
    retention_days: int = Body(90, embed=True),
    notify_on_change: bool = Body(True, embed=True),
    notify_on_fail: bool = Body(True, embed=True),
    is_enabled: bool = Body(True, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # 验证名称唯一性
    result = await db.execute(select(BackupTask).where(BackupTask.name == name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="任务名称已存在")
    
    # 验证凭证存在
    result = await db.execute(select(Credential).where(Credential.id == credential_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Credential not found")
    
    # 验证站点存在
    if site_id:
        result = await db.execute(select(Site).where(Site.id == site_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Site not found")
    
    # 转换设备列表为JSON
    device_ids_json = json.dumps(device_ids) if device_ids else None
    
    task = BackupTask(
        name=name,
        cron_expr=cron_expr,
        credential_id=credential_id,
        device_ids=device_ids_json,
        site_id=site_id,
        vendor=vendor,
        retention_count=retention_count,
        retention_days=retention_days,
        notify_on_change=notify_on_change,
        notify_on_fail=notify_on_fail,
        is_enabled=is_enabled,
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 如果启用，添加到调度器
    if is_enabled:
        add_task_to_scheduler(task.id, cron_expr)
    
    await audit_log(db, current_user.id, "backup_task", task.id, "create", {"name": name})
    
    return {c.name: getattr(task, c.name) for c in task.__table__.columns}

# 更新任务
@router.put("/{task_id}")
async def update_backup_task(
    task_id: int,
    name: str = Body(None, embed=True),
    cron_expr: str = Body(None, embed=True),
    credential_id: int = Body(None, embed=True),
    device_ids: list[int] = Body(None, embed=True),
    site_id: int = Body(None, embed=True),
    vendor: str = Body(None, embed=True),
    retention_count: int = Body(None, embed=True),
    retention_days: int = Body(None, embed=True),
    notify_on_change: bool = Body(None, embed=True),
    notify_on_fail: bool = Body(None, embed=True),
    is_enabled: bool = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    # 构建更新数据
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if cron_expr is not None:
        update_data["cron_expr"] = cron_expr
    if credential_id is not None:
        update_data["credential_id"] = credential_id
    if device_ids is not None:
        update_data["device_ids"] = json.dumps(device_ids)
    if site_id is not None:
        update_data["site_id"] = site_id
    if vendor is not None:
        update_data["vendor"] = vendor
    if retention_count is not None:
        update_data["retention_count"] = retention_count
    if retention_days is not None:
        update_data["retention_days"] = retention_days
    if notify_on_change is not None:
        update_data["notify_on_change"] = notify_on_change
    if notify_on_fail is not None:
        update_data["notify_on_fail"] = notify_on_fail
    if is_enabled is not None:
        update_data["is_enabled"] = is_enabled
    
    if update_data:
        stmt = update(BackupTask).where(BackupTask.id == task_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(task)
        
        # 更新调度器
        if "is_enabled" in update_data or "cron_expr" in update_data:
            if task.is_enabled:
                add_task_to_scheduler(task.id, task.cron_expr)
            else:
                remove_task_from_scheduler(task.id)
    
    await audit_log(db, current_user.id, "backup_task", task_id, "update", {"name": name})
    
    return {c.name: getattr(task, c.name) for c in task.__table__.columns}

# 删除任务
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    # 从调度器移除
    remove_task_from_scheduler(task_id)
    
    await db.execute(delete(BackupTask).where(BackupTask.id == task_id))
    await db.commit()
    
    await audit_log(db, current_user.id, "backup_task", task_id, "delete", {})

# 启用/停用任务
@router.patch("/{task_id}/toggle")
async def toggle_backup_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    task.is_enabled = not task.is_enabled
    await db.commit()
    
    # 更新调度器
    if task.is_enabled:
        add_task_to_scheduler(task.id, task.cron_expr)
    else:
        remove_task_from_scheduler(task.id)
    
    await audit_log(db, current_user.id, "backup_task", task_id, "toggle", {"is_enabled": task.is_enabled})
    
    return {"is_enabled": task.is_enabled}

# 立即执行任务
@router.post("/{task_id}/run-now")
async def run_backup_task_now(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    import asyncio
    asyncio.create_task(run_backup_task(task_id, "manual"))
    
    await audit_log(db, current_user.id, "backup_task", task_id, "run_now", {})
    
    return {"message": "任务已启动，请在几秒后刷新历史记录查看结果"}

# 获取任务执行历史
@router.get("/{task_id}/history")
async def get_task_history(
    task_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # 先获取任务信息
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Backup task not found")
    
    # 获取任务关联的设备列表
    device_ids = []
    if task.device_ids:
        try:
            device_ids = json.loads(task.device_ids)
        except:
            device_ids = []
    elif task.site_id:
        # 按站点查询设备
        dev_result = await db.execute(select(Device.id).where(Device.site_id == task.site_id))
        device_ids = [d for d in dev_result.scalars().all()]
    else:
        # 所有设备
        dev_result = await db.execute(select(Device.id))
        device_ids = [d for d in dev_result.scalars().all()]
    
    if not device_ids:
        return []
    
    # 查询该任务关联设备的备份记录（包括scheduled和manual）
    result = await db.execute(
        select(Backup)
        .where(
            Backup.device_id.in_(device_ids),
            Backup.trigger.in_(["scheduled", "manual"])
        )
        .order_by(desc(Backup.created_at))
        .limit(limit)
    )
    
    backups = result.scalars().all()
    
    # 按日期分组统计
    history = {}
    for backup in backups:
        date_str = backup.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if date_str not in history:
            history[date_str] = {"success": 0, "failed": 0, "total": 0, "backups": []}
        history[date_str]["total"] += 1
        if backup.status == "success":
            history[date_str]["success"] += 1
        else:
            history[date_str]["failed"] += 1
        history[date_str]["backups"].append(backup)
    
    # 转换为列表并排序
    result = []
    for date_str, stats in history.items():
        result.append({
            "time": date_str,
            "success": stats["success"],
            "failed": stats["failed"],
            "total": stats["total"],
            "backups": [
                {"id": b.id, "device_id": b.device_id, "status": b.status, "duration_ms": b.duration_ms}
                for b in stats["backups"]
            ]
        })
    
    return sorted(result, key=lambda x: x["time"], reverse=True)[:limit]