import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database import async_engine, async_session
from src.services.lldp_discovery import run_full_discovery

async def main():
    # 使用项目已有的 async_engine/async_session
    async with async_session() as session:
        try:
            await run_full_discovery(session)
        except Exception as e:
            print('run_full_discovery exception:', e)

if __name__ == '__main__':
    asyncio.run(main())
