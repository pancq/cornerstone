from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from ..database import get_db
from ..models import Site
from ..schemas import SiteCreate, SiteUpdate, SiteResponse
from .dependencies import get_current_active_user

router = APIRouter()

@router.get("/", response_model=list[SiteResponse])
async def read_sites(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Site).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{site_id}", response_model=SiteResponse)
async def read_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    stmt = insert(Site).values(**site.dict()).returning(Site)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: int,
    site: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    existing_site = result.scalar_one_or_none()
    if existing_site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    
    stmt = update(Site).where(Site.id == site_id).values(**site.dict(exclude_unset=True)).returning(Site)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await db.execute(delete(Site).where(Site.id == site_id))
    await db.commit()
