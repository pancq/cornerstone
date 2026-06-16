import asyncio
from src.database import async_engine
from src.models import User
from src.core.security import get_password_hash

async def reset_password():
    async with async_engine.begin() as conn:
        await conn.execute(User.__table__.update().where(User.username=='admin').values(hashed_password=get_password_hash('admin123')))
        await conn.commit()
    print('Password reset')

asyncio.run(reset_password())