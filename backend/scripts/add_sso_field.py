"""添加 is_sso_user 字段到 users 表"""
import asyncio
import sys
sys.path.insert(0, '/Users/pancq/Desktop/trae/基石/backend')

from sqlalchemy import text
from src.database import async_session


async def migrate():
    """执行数据库迁移"""
    async with async_session() as session:
        # 检查字段是否已存在
        result = await session.execute(
            text("PRAGMA table_info(users)")
        )
        columns = [row[1] for row in result.fetchall()]
        
        if 'is_sso_user' not in columns:
            # 添加 is_sso_user 字段
            await session.execute(
                text("ALTER TABLE users ADD COLUMN is_sso_user BOOLEAN DEFAULT 0")
            )
            print("✓ 已添加 is_sso_user 字段")
        else:
            print("✓ is_sso_user 字段已存在")
        
        await session.commit()
        print("迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
