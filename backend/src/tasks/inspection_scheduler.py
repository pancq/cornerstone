from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import InspectionTask
from src.database import get_db
from src.services.inspector import InspectorService

scheduler = None


async def run_scheduled_inspection(task_id: int):
    """执行定时巡检任务"""
    async with get_db() as db:
        result = await db.execute(InspectionTask.__table__.select().where(InspectionTask.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task or not task.is_enabled:
            return
        
        try:
            await InspectorService.run_inspection(
                task=task,
                trigger="scheduled",
                operator="system",
                db=db
            )
        except Exception as e:
            # 更新任务状态为失败
            await db.execute(
                InspectionTask.__table__.update()
                .where(InspectionTask.id == task_id)
                .values({
                    "last_run_at": datetime.now(),
                    "last_run_status": "failed"
                })
            )
            await db.commit()


def init_inspection_scheduler(app_scheduler: AsyncIOScheduler):
    """初始化巡检任务调度器"""
    global scheduler
    scheduler = app_scheduler


async def reload_inspection_tasks(db: AsyncSession):
    """重新加载所有巡检任务到调度器"""
    if not scheduler:
        return
    
    # 移除所有现有的巡检任务
    for job in scheduler.get_jobs():
        if job.id.startswith("inspection_"):
            scheduler.remove_job(job.id)
    
    # 加载所有启用的巡检任务
    from sqlalchemy import select
    result = await db.execute(
        select(InspectionTask)
        .where(InspectionTask.is_enabled == True)
    )
    tasks = result.scalars().all()
    
    for task in tasks:
        # 解析cron表达式
        cron_parts = task.cron_expr.split()
        scheduler.add_job(
            run_scheduled_inspection,
            trigger='cron',
            args=[task.id],
            id=f"inspection_{task.id}",
            name=task.name,
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            replace_existing=True
        )


async def add_inspection_task(task_id: int, db: AsyncSession):
    """添加单个巡检任务到调度器"""
    if not scheduler:
        return
    
    result = await db.execute(InspectionTask.__table__.select().where(InspectionTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if task and task.is_enabled:
        scheduler.add_job(
            run_scheduled_inspection,
            trigger='cron',
            args=[task.id],
            id=f"inspection_{task.id}",
            name=task.name,
            cron_expression=task.cron_expr,
            replace_existing=True
        )


async def remove_inspection_task(task_id: int):
    """从调度器移除巡检任务"""
    if not scheduler:
        return
    
    job_id = f"inspection_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def update_inspection_task(task_id: int, db: AsyncSession):
    """更新调度器中的巡检任务"""
    await remove_inspection_task(task_id)
    await add_inspection_task(task_id, db)
