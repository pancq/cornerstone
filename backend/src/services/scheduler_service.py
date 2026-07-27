import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.database import async_session
from src.services.monitor_service import run_monitoring_task
from src.services.circuit_expire_service import circuit_expire_service

scheduler = None
current_interval = 5  # 默认5分钟


def get_scheduler() -> AsyncIOScheduler:
    """获取调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    return scheduler


async def scheduled_monitoring_task():
    """定时执行的监控任务"""
    print(f"[{datetime.now()}] Running scheduled monitoring task...")
    async with async_session() as db:
        await run_monitoring_task(db)


async def scheduled_circuit_expire_task():
    """定时执行的专线到期检查任务（每天凌晨1点执行）"""
    print(f"[{datetime.now()}] Running scheduled circuit expire check...")
    async with async_session() as db:
        await circuit_expire_service.check_expiring_circuits(db, days_before=30)
        await db.commit()


def start_scheduler(interval_minutes: int = 5):
    """启动定时任务调度器"""
    global scheduler, current_interval
    
    # 如果调度器正在运行，先停止
    if scheduler and scheduler.running:
        scheduler.shutdown()
    
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    
    # 添加设备监控定时任务
    scheduler.add_job(
        scheduled_monitoring_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="monitoring_task",
        replace_existing=True
    )
    
    # 添加专线到期检查定时任务（每天凌晨1点执行）
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        scheduled_circuit_expire_task,
        trigger=CronTrigger(hour=1, minute=0),
        id="circuit_expire_task",
        replace_existing=True
    )
    
    current_interval = interval_minutes
    scheduler.start()
    print(f"Scheduler started with {interval_minutes} minutes interval")


def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")


def update_scheduler_interval(interval_minutes: int):
    """更新定时任务间隔"""
    global scheduler, current_interval
    
    if interval_minutes == current_interval:
        return
    
    if scheduler and scheduler.running:
        # 修改现有任务的触发器
        scheduler.reschedule_job(
            "monitoring_task",
            trigger=IntervalTrigger(minutes=interval_minutes)
        )
        current_interval = interval_minutes
        print(f"Scheduler interval updated to {interval_minutes} minutes")


def get_current_interval() -> int:
    """获取当前定时任务间隔"""
    return current_interval


def is_scheduler_running() -> bool:
    """检查调度器是否正在运行"""
    return scheduler is not None and scheduler.running
