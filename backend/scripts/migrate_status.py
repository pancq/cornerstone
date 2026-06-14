#!/usr/bin/env python3
"""一次性脚本：将IP地址状态从英文迁移到中文"""
import asyncio
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目路径
import sys
sys.path.insert(0, '/Users/pancq/Desktop/trae/基石/backend')

from src.database import async_session, Base
from src.models import IPAddress


async def migrate_status():
    """迁移IP地址状态字段"""
    async with async_session() as session:
        # 更新 assigned -> 已分配
        stmt1 = update(IPAddress).where(IPAddress.status == 'assigned').values(status='已分配')
        result1 = await session.execute(stmt1)
        print(f"更新 assigned -> 已分配: {result1.rowcount} 条记录")
        
        # 更新 reserved -> 预留
        stmt2 = update(IPAddress).where(IPAddress.status == 'reserved').values(status='预留')
        result2 = await session.execute(stmt2)
        print(f"更新 reserved -> 预留: {result2.rowcount} 条记录")
        
        # 更新 available -> 未分配
        stmt3 = update(IPAddress).where(IPAddress.status == 'available').values(status='未分配')
        result3 = await session.execute(stmt3)
        print(f"更新 available -> 未分配: {result3.rowcount} 条记录")
        
        # 更新 active -> 已分配（处理可能存在的active状态）
        stmt4 = update(IPAddress).where(IPAddress.status == 'active').values(status='已分配')
        result4 = await session.execute(stmt4)
        print(f"更新 active -> 已分配: {result4.rowcount} 条记录")
        
        # 提交更改
        await session.commit()
        print("迁移完成！")


if __name__ == '__main__':
    asyncio.run(migrate_status())
