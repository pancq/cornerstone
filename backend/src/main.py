from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from .api import api_router
from .config import settings
from .utils import setup_logger
from .tasks.backup_scheduler import start_scheduler as start_backup_scheduler, reload_tasks, scheduler as backup_scheduler
from .services.scheduler_service import start_scheduler as start_monitor_scheduler
from .tasks.inspection_scheduler import init_inspection_scheduler, reload_inspection_tasks
from .tasks.log_cleanup import start_log_cleanup_scheduler
from .database import async_session

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# 设置日志
logger = setup_logger()

# CORS配置：始终允许所有来源（前端使用 JWT token 认证，不依赖 cookie credentials）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Cornerstone API", "version": settings.app_version}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    from .services.permission_service import init_permissions, init_roles, init_default_admin
    
    # 导入所有模型以确保表结构被创建
    from .models import User, Role, Permission, RolePermission, UserSession
    from .models.site import Site
    from .models.device import Device
    from .models.circuit import Circuit
    from .models.ip_address import IPAddress
    from .models.prefix import Prefix
    from .models.vlan import Vlan, VlanGroup
    from .models.audit_log import AuditLog
    from .models.system_config import SystemConfig
    from .models.backup_analysis import BackupAnalysis
    from .models.inspection import InspectionTask, InspectionResult, InspectionDeviceResult, DeviceFingerprint
    
    # 创建所有表
    from .database import async_engine, Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # 初始化权限和角色
    async with async_session() as session:
        await init_permissions(session)
        logger.info("Permissions initialized")
        
        await init_roles(session)
        logger.info("Roles initialized")
        
        await init_default_admin(session)
        logger.info("Default admin user initialized")
    
    # 启动备份调度器
    start_backup_scheduler()
    logger.info("Backup scheduler started")
    
    # 从数据库加载所有启用的任务
    async with async_session() as session:
        await reload_tasks(session)
    logger.info("Backup tasks loaded from database")
    
    # 启动监控定时任务（默认5分钟）
    start_monitor_scheduler(5)
    logger.info("Monitor scheduler started with 5 minutes interval")
    
    # 初始化巡检调度器（复用备份调度器）
    init_inspection_scheduler(backup_scheduler)
    async with async_session() as session:
        await reload_inspection_tasks(session)
    logger.info("Inspection scheduler initialized")
    
    # 启动日志清理定时任务
    await start_log_cleanup_scheduler()
    logger.info("Log cleanup scheduler started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
